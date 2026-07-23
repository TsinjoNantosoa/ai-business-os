from __future__ import annotations

import time
from typing import Any

from sqlalchemy.orm import Session

from app.models.workflow import Workflow, WorkflowExecution
from app.repositories.workflow_repository import WorkflowRepository
from app.services.email_service import EmailService
from app.services.workflow_actions import run_actions


class WorkflowEngine:
    def __init__(self, session: Session, email_service: EmailService | None = None) -> None:
        self._repo = WorkflowRepository(session)
        self._session = session
        self._email_service = email_service

    def run(
        self,
        workflow: Workflow,
        org_id: str,
        *,
        event_id: str | None = None,
        trigger_source: str | None = "manual",
        event_type: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> WorkflowExecution:
        if workflow.status not in {"active", "inactive"}:
            raise ValueError("Workflow non exécutable")

        execution = self._repo.create_execution(
            org_id=org_id,
            workflow_id=workflow.id,
            event_id=event_id,
            trigger_source=trigger_source or "manual",
        )
        started = time.perf_counter()

        try:
            actions = list(workflow.actions or [])
            if workflow.definition:
                from app.services.workflow_graph import derive_trigger_actions, normalize_definition

                _, derived = derive_trigger_actions(normalize_definition(workflow.definition))
                if derived:
                    actions = derived

            results = run_actions(
                self._session,
                org_id=org_id,
                actions=actions,
                context=context,
                workflow_name=workflow.name,
                email_service=self._email_service,
            )
            details = "; ".join(r.as_text() for r in results) or "aucune action"
            failed = [r for r in results if not r.ok]
            prefix = f"[{event_type}] " if event_type else ""
            result_message = f"{prefix}{len(results)} action(s): {details}"
            duration_ms = max(1, int((time.perf_counter() - started) * 1000))
            status = "error" if failed and len(failed) == len(results) else "success"
            self._repo.finish_execution(
                execution,
                status=status,
                duration_ms=duration_ms,
                result_message=result_message,
                error_message="; ".join(r.detail for r in failed) if failed and status == "error" else None,
            )
            self._repo.record_workflow_run(workflow, success=status == "success")
        except Exception as exc:
            duration_ms = max(1, int((time.perf_counter() - started) * 1000))
            self._repo.finish_execution(
                execution,
                status="error",
                duration_ms=duration_ms,
                error_message=str(exc),
            )
            self._repo.record_workflow_run(workflow, success=False)
            raise

        self._session.flush()
        return execution
