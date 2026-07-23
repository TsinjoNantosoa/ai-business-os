"""Lot F / S33 — domain events catalog + inbound webhooks."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.presentation.deps import claims_org_id, require_permission
from app.services.audit_service import record_audit
from app.services.event_bus import EventBus, WebhookEndpointRepository
from app.services.event_catalog import EVENT_CATALOG


class WebhookCreateBody(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=512)
    eventTypes: list[str] = Field(default_factory=list)


class WebhookInboundBody(BaseModel):
    eventType: str | None = Field(default=None, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict)


def _endpoint_to_dict(endpoint, *, include_secret: bool = False) -> dict:
    base = settings.api_public_url.rstrip("/")
    data = {
        "id": endpoint.id,
        "name": endpoint.name,
        "description": endpoint.description,
        "token": endpoint.token,
        "url": f"{base}/api/v1/webhooks/inbound/{endpoint.token}",
        "eventTypes": endpoint.event_types or [],
        "isActive": endpoint.is_active,
        "receiveCount": endpoint.receive_count,
        "lastReceivedAt": endpoint.last_received_at.isoformat() if endpoint.last_received_at else None,
        "createdAt": endpoint.created_at.isoformat(),
    }
    if include_secret:
        data["secret"] = endpoint.secret
    return data


def _event_to_dict(event) -> dict:
    return {
        "id": event.id,
        "eventType": event.event_type,
        "source": event.source,
        "payload": event.payload or {},
        "triggeredWorkflowIds": event.triggered_workflow_ids or [],
        "createdAt": event.created_at.isoformat(),
    }


def _verify_hmac(secret: str | None, body: bytes, signature: str | None) -> bool:
    """Token URL authenticates; HMAC optional when header is sent."""
    if not signature:
        return True
    if not secret:
        return False
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    expected = f"sha256={digest}"
    return hmac.compare_digest(signature.strip(), expected) or hmac.compare_digest(signature.strip(), digest)


def build_events_router() -> APIRouter:
    router = APIRouter(tags=["events"])

    @router.get("/api/v1/events/catalog")
    def event_catalog(
        _claims: dict = Depends(require_permission("workflow.read")),
    ) -> list[dict]:
        return EVENT_CATALOG

    @router.get("/api/v1/events")
    def list_events(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("workflow.read")),
    ) -> list[dict]:
        events = EventBus(db).list_events(claims_org_id(claims))
        return [_event_to_dict(e) for e in events]

    @router.get("/api/v1/webhooks/endpoints")
    def list_webhook_endpoints(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("workflow.read")),
    ) -> list[dict]:
        rows = WebhookEndpointRepository(db).list_by_org(claims_org_id(claims))
        return [_endpoint_to_dict(r) for r in rows]

    @router.post("/api/v1/webhooks/endpoints", status_code=status.HTTP_201_CREATED)
    def create_webhook_endpoint(
        body: WebhookCreateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("workflow.write")),
    ) -> dict:
        endpoint = WebhookEndpointRepository(db).create(
            org_id=claims_org_id(claims),
            name=body.name.strip(),
            description=(body.description or "").strip(),
            event_types=body.eventTypes,
        )
        record_audit(
            db,
            claims,
            action="CREATE",
            resource="WebhookEndpoint",
            resource_id=endpoint.id,
            details=endpoint.name,
            request=request,
        )
        db.commit()
        db.refresh(endpoint)
        return _endpoint_to_dict(endpoint, include_secret=True)

    @router.delete("/api/v1/webhooks/endpoints/{endpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_webhook_endpoint(
        endpoint_id: str,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("workflow.write")),
    ) -> None:
        repo = WebhookEndpointRepository(db)
        endpoint = repo.get_by_id(claims_org_id(claims), endpoint_id)
        if not endpoint:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook introuvable")
        record_audit(
            db,
            claims,
            action="DELETE",
            resource="WebhookEndpoint",
            resource_id=endpoint.id,
            details=endpoint.name,
            request=request,
        )
        repo.delete(endpoint)
        db.commit()

    @router.post("/api/v1/webhooks/inbound/{token}")
    async def inbound_webhook(
        token: str,
        request: Request,
        db: Session = Depends(get_db),
        x_webhook_signature: str | None = Header(default=None, alias="X-Webhook-Signature"),
    ) -> dict:
        repo = WebhookEndpointRepository(db)
        endpoint = repo.get_by_token(token)
        if not endpoint or not endpoint.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook introuvable")

        raw = await request.body()
        if not _verify_hmac(endpoint.secret, raw, x_webhook_signature):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Signature webhook invalide")

        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="JSON invalide") from exc

        if not isinstance(data, dict):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Body JSON objet requis")

        event_type = (data.get("eventType") or data.get("type") or "webhook.inbound").strip()
        allowed = endpoint.event_types or []
        if allowed and event_type not in allowed and "webhook.inbound" not in allowed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"eventType non autorisé pour ce webhook: {event_type}",
            )

        payload = data.get("payload") if isinstance(data.get("payload"), dict) else data
        repo.touch_received(endpoint)
        event = EventBus(db).publish(
            org_id=endpoint.org_id,
            event_type=event_type,
            payload=payload if isinstance(payload, dict) else {"raw": payload},
            source="webhook",
        )
        db.commit()
        return {
            "accepted": True,
            "eventId": event.id,
            "eventType": event.event_type,
            "triggeredWorkflowIds": event.triggered_workflow_ids or [],
        }

    return router
