from __future__ import annotations

import secrets
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workflow import Workflow, WorkflowExecution


class WorkflowRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_org(self, org_id: str) -> list[Workflow]:
        stmt = select(Workflow).where(Workflow.org_id == org_id).order_by(Workflow.name)
        return list(self._session.scalars(stmt).all())

    def get_by_id(self, org_id: str, workflow_id: str) -> Workflow | None:
        stmt = select(Workflow).where(Workflow.org_id == org_id, Workflow.id == workflow_id)
        return self._session.scalars(stmt).first()

    def count_all(self) -> int:
        return len(list(self._session.scalars(select(Workflow)).all()))

    def list_executions(self, org_id: str, limit: int = 50) -> list[WorkflowExecution]:
        stmt = (
            select(WorkflowExecution)
            .where(WorkflowExecution.org_id == org_id)
            .order_by(WorkflowExecution.started_at.desc())
            .limit(limit)
        )
        return list(self._session.scalars(stmt).all())

    def create_execution(self, *, org_id: str, workflow_id: str) -> WorkflowExecution:
        execution = WorkflowExecution(
            id=f"wfx-{secrets.token_hex(6)}",
            org_id=org_id,
            workflow_id=workflow_id,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self._session.add(execution)
        self._session.flush()
        return execution

    def finish_execution(
        self,
        execution: WorkflowExecution,
        *,
        status: str,
        duration_ms: int,
        result_message: str | None = None,
        error_message: str | None = None,
    ) -> WorkflowExecution:
        now = datetime.now(timezone.utc)
        execution.status = status
        execution.finished_at = now
        execution.duration_ms = duration_ms
        execution.result_message = result_message
        execution.error_message = error_message
        return execution

    def record_workflow_run(self, workflow: Workflow, *, success: bool) -> Workflow:
        workflow.run_count += 1
        workflow.last_run = datetime.now(timezone.utc)
        if workflow.run_count == 1:
            workflow.success_rate = 100.0 if success else 0.0
        else:
            prior_successes = round(workflow.success_rate * (workflow.run_count - 1) / 100)
            if success:
                prior_successes += 1
            workflow.success_rate = round(prior_successes / workflow.run_count * 100, 1)
        workflow.updated_at = datetime.now(timezone.utc)
        return workflow
