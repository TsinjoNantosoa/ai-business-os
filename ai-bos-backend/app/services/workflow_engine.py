from __future__ import annotations

import re
import time
from typing import Any

from sqlalchemy.orm import Session

from app.models.workflow import Workflow, WorkflowExecution
from app.repositories.workflow_repository import WorkflowRepository
from app.services.email_service import EmailService
from app.services.workflow_actions import run_actions

_SECRET_KEY_RE = re.compile(r"token|secret|password|authorization|api.?key|cookie", re.I)


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if _SECRET_KEY_RE.search(str(key)) else _sanitize(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_sanitize(item) for item in value[:100]]
    if isinstance(value, str):
        return value[:4000]
    return value


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
        if workflow.org_id != org_id:
            raise ValueError("Workflow hors tenant")
        if event_id:
            existing = self._repo.get_execution_for_event(org_id, workflow.id, event_id)
            if existing:
                return existing

        execution = self._repo.create_execution(
            org_id=org_id,
            workflow_id=workflow.id,
            event_id=event_id,
            trigger_source=trigger_source or "manual",
        )
        started = time.perf_counter()
        try:
            steps = [
                {"key": str(index + 1), "action": action, "config": {}}
                for index, action in enumerate(workflow.actions or [])
            ]
            if workflow.definition:
                from app.services.workflow_graph import derive_action_steps, normalize_definition

                derived = derive_action_steps(normalize_definition(workflow.definition))
                if derived:
                    steps = derived

            results = []
            for index, step_definition in enumerate(steps):
                action = str(step_definition["action"])
                step_context = {**(context or {}), **(step_definition.get("config") or {})}
                step_started = time.perf_counter()
                step = self._repo.create_step(
                    org_id=org_id,
                    workflow_id=workflow.id,
                    execution_id=execution.id,
                    step_key=str(step_definition.get("key") or f"{index + 1}:{action}"),
                    action=action,
                    input_data=_sanitize(step_context),
                )
                result = run_actions(
                    self._session,
                    org_id=org_id,
                    actions=[action],
                    context=step_context,
                    workflow_name=workflow.name,
                    email_service=self._email_service,
                )[0]
                results.append(result)
                self._repo.finish_step(
                    step,
                    status="success" if result.ok else "error",
                    output_data={"detail": _sanitize(result.detail)} if result.ok else None,
                    error_message=None if result.ok else str(_sanitize(result.detail)),
                    attempts=result.attempts,
                    duration_ms=max(1, int((time.perf_counter() - step_started) * 1000)),
                )

            details = "; ".join(result.as_text() for result in results) or "aucune action"
            failed = [result for result in results if not result.ok]
            prefix = f"[{event_type}] " if event_type else ""
            final_status = "error" if failed else "success"
            self._repo.finish_execution(
                execution,
                status=final_status,
                duration_ms=max(1, int((time.perf_counter() - started) * 1000)),
                result_message=f"{prefix}{len(results)} action(s): {details}",
                error_message="; ".join(result.detail for result in failed) if failed else None,
            )
            self._repo.record_workflow_run(workflow, success=not failed)
        except Exception as exc:
            self._repo.finish_execution(
                execution,
                status="error",
                duration_ms=max(1, int((time.perf_counter() - started) * 1000)),
                error_message=str(exc)[:4000],
            )
            self._repo.record_workflow_run(workflow, success=False)
            self._session.flush()
            raise

        self._session.flush()
        return execution
