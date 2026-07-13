from __future__ import annotations

import time

from sqlalchemy.orm import Session

from app.models.workflow import Workflow, WorkflowExecution
from app.repositories.workflow_repository import WorkflowRepository


class WorkflowEngine:
    def __init__(self, session: Session) -> None:
        self._repo = WorkflowRepository(session)
        self._session = session

    def run(self, workflow: Workflow, org_id: str) -> WorkflowExecution:
        if workflow.status not in {"active", "inactive"}:
            raise ValueError("Workflow non exécutable")

        execution = self._repo.create_execution(org_id=org_id, workflow_id=workflow.id)
        started = time.perf_counter()

        try:
            actions = workflow.actions or []
            result_message = f"{len(actions)} action(s) exécutée(s): {', '.join(actions) or 'aucune'}"
            duration_ms = max(1, int((time.perf_counter() - started) * 1000))
            self._repo.finish_execution(
                execution,
                status="success",
                duration_ms=duration_ms,
                result_message=result_message,
            )
            self._repo.record_workflow_run(workflow, success=True)
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
