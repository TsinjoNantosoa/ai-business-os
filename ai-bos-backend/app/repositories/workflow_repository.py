from __future__ import annotations

import secrets
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workflow import Workflow, WorkflowExecution, WorkflowStepExecution


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

    def get_execution_for_event(self, org_id: str, workflow_id: str, event_id: str) -> WorkflowExecution | None:
        return self._session.scalars(
            select(WorkflowExecution).where(
                WorkflowExecution.org_id == org_id,
                WorkflowExecution.workflow_id == workflow_id,
                WorkflowExecution.event_id == event_id,
            )
        ).first()

    def list_steps(self, org_id: str, execution_id: str) -> list[WorkflowStepExecution]:
        stmt = (
            select(WorkflowStepExecution)
            .where(
                WorkflowStepExecution.org_id == org_id,
                WorkflowStepExecution.execution_id == execution_id,
            )
            .order_by(WorkflowStepExecution.started_at)
        )
        return list(self._session.scalars(stmt).all())

    def create_step(self, *, org_id: str, workflow_id: str, execution_id: str, step_key: str, action: str, input_data: dict) -> WorkflowStepExecution:
        row = WorkflowStepExecution(
            id=f"wfs-{secrets.token_hex(8)}",
            org_id=org_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            step_key=step_key,
            action=action,
            status="running",
            input_data=input_data,
            attempts=1,
            idempotency_key=f"{execution_id}:{step_key}",
            started_at=datetime.now(timezone.utc),
        )
        self._session.add(row)
        self._session.flush()
        return row

    def finish_step(self, row: WorkflowStepExecution, *, status: str, output_data: dict | None, error_message: str | None, attempts: int, duration_ms: int) -> WorkflowStepExecution:
        row.status = status
        row.output_data = output_data
        row.error_message = error_message
        row.attempts = attempts
        row.duration_ms = duration_ms
        row.finished_at = datetime.now(timezone.utc)
        return row

    def create_execution(
        self,
        *,
        org_id: str,
        workflow_id: str,
        event_id: str | None = None,
        trigger_source: str | None = None,
    ) -> WorkflowExecution:
        execution = WorkflowExecution(
            id=f"wfx-{secrets.token_hex(6)}",
            org_id=org_id,
            workflow_id=workflow_id,
            status="running",
            started_at=datetime.now(timezone.utc),
            event_id=event_id,
            trigger_source=trigger_source,
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

    def create(
        self,
        *,
        org_id: str,
        name: str,
        description: str,
        status: str,
        trigger: str,
        actions: list[str],
        definition: dict | None,
    ) -> Workflow:
        now = datetime.now(timezone.utc)
        workflow = Workflow(
            id=f"wf-{secrets.token_hex(6)}",
            org_id=org_id,
            name=name,
            description=description,
            status=status,
            trigger=trigger,
            actions=actions,
            definition=definition,
            run_count=0,
            success_rate=100.0,
            created_at=now,
            updated_at=now,
        )
        self._session.add(workflow)
        self._session.flush()
        return workflow

    def update(
        self,
        workflow: Workflow,
        *,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
        trigger: str | None = None,
        actions: list[str] | None = None,
        definition: dict | None = None,
    ) -> Workflow:
        if name is not None:
            workflow.name = name
        if description is not None:
            workflow.description = description
        if status is not None:
            workflow.status = status
        if trigger is not None:
            workflow.trigger = trigger
        if actions is not None:
            workflow.actions = actions
        if definition is not None:
            workflow.definition = definition
        workflow.updated_at = datetime.now(timezone.utc)
        return workflow
