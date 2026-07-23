"""In-process event bus: persist domain events and dispatch matching workflows."""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.events import DomainEvent, WebhookEndpoint
from app.models.workflow import Workflow
from app.services.email_service import EmailService
from app.services.event_catalog import labels_for_event
from app.services.workflow_engine import WorkflowEngine

logger = logging.getLogger("aibos.events")

_email_service_holder: EmailService | None = None


def set_email_service(service: EmailService) -> None:
    global _email_service_holder
    _email_service_holder = service


def _resolve_email_service() -> EmailService | None:
    if _email_service_holder is not None:
        return _email_service_holder
    try:
        from app.core.config import settings
        from app.services.email_service import EmailService

        return EmailService(
            mode=settings.email_mode,
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_use_tls=settings.smtp_use_tls,
            smtp_user=settings.smtp_user,
            smtp_password=settings.smtp_password,
            sender=settings.smtp_from,
        )
    except Exception:
        return None


class EventBus:
    def __init__(self, session: Session) -> None:
        self._session = session

    def publish(
        self,
        *,
        org_id: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
        source: str = "api",
    ) -> DomainEvent:
        event = DomainEvent(
            id=f"evt-{secrets.token_hex(8)}",
            org_id=org_id,
            event_type=event_type,
            source=source,
            payload=payload or {},
            triggered_workflow_ids=[],
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(event)
        self._session.flush()

        matched = self._matching_workflows(org_id, event_type)
        run_ids: list[str] = []
        engine = WorkflowEngine(self._session, email_service=_resolve_email_service())
        for workflow in matched:
            try:
                execution = engine.run(
                    workflow,
                    org_id,
                    event_id=event.id,
                    trigger_source=source,
                    event_type=event_type,
                    context=payload or {},
                )
                run_ids.append(workflow.id)
                logger.info(
                    "event_dispatched",
                    extra={
                        "event_id": event.id,
                        "event_type": event_type,
                        "workflow_id": workflow.id,
                        "execution_id": execution.id,
                    },
                )
            except Exception:
                logger.exception(
                    "event_dispatch_failed event=%s workflow=%s",
                    event.id,
                    workflow.id,
                )

        event.triggered_workflow_ids = run_ids
        self._session.flush()
        return event

    def _matching_workflows(self, org_id: str, event_type: str) -> list[Workflow]:
        labels = labels_for_event(event_type)
        stmt = select(Workflow).where(Workflow.org_id == org_id, Workflow.status == "active")
        workflows = list(self._session.scalars(stmt).all())
        return [wf for wf in workflows if (wf.trigger or "") in labels]

    def list_events(self, org_id: str, limit: int = 50) -> list[DomainEvent]:
        stmt = (
            select(DomainEvent)
            .where(DomainEvent.org_id == org_id)
            .order_by(DomainEvent.created_at.desc())
            .limit(limit)
        )
        return list(self._session.scalars(stmt).all())


class WebhookEndpointRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_org(self, org_id: str) -> list[WebhookEndpoint]:
        stmt = (
            select(WebhookEndpoint)
            .where(WebhookEndpoint.org_id == org_id)
            .order_by(WebhookEndpoint.created_at.desc())
        )
        return list(self._session.scalars(stmt).all())

    def get_by_id(self, org_id: str, endpoint_id: str) -> WebhookEndpoint | None:
        stmt = select(WebhookEndpoint).where(
            WebhookEndpoint.org_id == org_id,
            WebhookEndpoint.id == endpoint_id,
        )
        return self._session.scalars(stmt).first()

    def get_by_token(self, token: str) -> WebhookEndpoint | None:
        stmt = select(WebhookEndpoint).where(WebhookEndpoint.token == token)
        return self._session.scalars(stmt).first()

    def count_by_org(self, org_id: str) -> int:
        return len(self.list_by_org(org_id))

    def create(
        self,
        *,
        org_id: str,
        name: str,
        description: str = "",
        event_types: list[str] | None = None,
        secret: str | None = None,
    ) -> WebhookEndpoint:
        now = datetime.now(timezone.utc)
        endpoint = WebhookEndpoint(
            id=f"wh-{secrets.token_hex(6)}",
            org_id=org_id,
            name=name,
            token=secrets.token_urlsafe(24),
            secret=secret or secrets.token_hex(16),
            event_types=event_types or [],
            is_active=True,
            description=description,
            receive_count=0,
            created_at=now,
            updated_at=now,
        )
        self._session.add(endpoint)
        self._session.flush()
        return endpoint

    def touch_received(self, endpoint: WebhookEndpoint) -> None:
        endpoint.last_received_at = datetime.now(timezone.utc)
        endpoint.receive_count = int(endpoint.receive_count or 0) + 1
        endpoint.updated_at = datetime.now(timezone.utc)

    def set_active(self, endpoint: WebhookEndpoint, active: bool) -> WebhookEndpoint:
        endpoint.is_active = active
        endpoint.updated_at = datetime.now(timezone.utc)
        return endpoint

    def delete(self, endpoint: WebhookEndpoint) -> None:
        self._session.delete(endpoint)
