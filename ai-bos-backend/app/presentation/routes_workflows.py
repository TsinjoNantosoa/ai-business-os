from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.presentation.deps import claims_org_id, require_permission
from app.presentation.schemas import WorkflowCreateBody, WorkflowUpdateBody
from app.presentation.serializers import (
    workflow_execution_to_dict,
    workflow_step_execution_to_dict,
    workflow_to_dict,
)
from app.repositories.workflow_repository import WorkflowRepository
from app.services.audit_service import record_audit
from app.services.workflow_engine import WorkflowEngine
from app.services.workflow_graph import (
    derive_trigger_actions,
    empty_definition,
    normalize_definition,
)


def build_workflows_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])

    @router.get("/templates")
    def list_workflow_templates(
        _claims: dict = Depends(require_permission("workflow.read")),
    ) -> list[dict]:
        from app.services.agent_docs import WORKFLOW_TEMPLATES

        return WORKFLOW_TEMPLATES

    @router.get("")
    def list_workflows(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("workflow.read")),
    ) -> list[dict]:
        workflows = WorkflowRepository(db).list_by_org(claims_org_id(claims))
        return [workflow_to_dict(workflow) for workflow in workflows]

    @router.get("/executions")
    def list_executions(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("workflow.read")),
    ) -> list[dict]:
        repo = WorkflowRepository(db)
        org_id = claims_org_id(claims)
        workflows = {wf.id: wf.name for wf in repo.list_by_org(org_id)}
        executions = repo.list_executions(org_id)
        payload = []
        for execution in executions:
            item = workflow_execution_to_dict(execution, workflows.get(execution.workflow_id))
            item["steps"] = [
                workflow_step_execution_to_dict(step)
                for step in repo.list_steps(org_id, execution.id)
            ]
            payload.append(item)
        return payload

    @router.get("/{workflow_id}")
    def get_workflow(
        workflow_id: str,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("workflow.read")),
    ) -> dict:
        workflow = WorkflowRepository(db).get_by_id(claims_org_id(claims), workflow_id)
        if not workflow:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow introuvable")
        return workflow_to_dict(workflow)

    @router.post("")
    def create_workflow(
        body: WorkflowCreateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("workflow.write")),
    ) -> dict:
        status_value = (body.status or "draft").strip().lower()
        if status_value not in {"draft", "active", "inactive"}:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="status invalide")

        definition = normalize_definition(body.definition.model_dump() if body.definition else empty_definition())
        trigger, actions = derive_trigger_actions(definition)
        workflow = WorkflowRepository(db).create(
            org_id=claims_org_id(claims),
            name=body.name.strip(),
            description=(body.description or "").strip(),
            status=status_value,
            trigger=trigger,
            actions=actions,
            definition=definition,
        )
        record_audit(
            db,
            claims,
            action="CREATE",
            resource="Workflow",
            resource_id=workflow.id,
            details=workflow.name,
            request=request,
        )
        db.commit()
        db.refresh(workflow)
        return workflow_to_dict(workflow)

    @router.patch("/{workflow_id}")
    def update_workflow(
        workflow_id: str,
        body: WorkflowUpdateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("workflow.write")),
    ) -> dict:
        repo = WorkflowRepository(db)
        workflow = repo.get_by_id(claims_org_id(claims), workflow_id)
        if not workflow:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow introuvable")

        status_value = workflow.status
        if body.status is not None:
            status_value = body.status.strip().lower()
            if status_value not in {"draft", "active", "inactive"}:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="status invalide")

        definition = None
        trigger = None
        actions = None
        if body.definition is not None:
            definition = normalize_definition(body.definition.model_dump())
            trigger, actions = derive_trigger_actions(definition)

        repo.update(
            workflow,
            name=body.name.strip() if body.name is not None else None,
            description=body.description.strip() if body.description is not None else None,
            status=status_value if body.status is not None else None,
            trigger=trigger,
            actions=actions,
            definition=definition,
        )
        record_audit(
            db,
            claims,
            action="UPDATE",
            resource="Workflow",
            resource_id=workflow.id,
            details=workflow.name,
            request=request,
        )
        db.commit()
        db.refresh(workflow)
        return workflow_to_dict(workflow)

    @router.post("/{workflow_id}/run")
    def run_workflow(
        workflow_id: str,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("workflow.write")),
    ) -> dict:
        repo = WorkflowRepository(db)
        org_id = claims_org_id(claims)
        workflow = repo.get_by_id(org_id, workflow_id)
        if not workflow:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow introuvable")
        if workflow.status == "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workflow en brouillon non exécutable")

        try:
            from app.services.event_bus import _resolve_email_service

            execution = WorkflowEngine(db, email_service=_resolve_email_service()).run(
                workflow,
                org_id,
                trigger_source="manual",
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        record_audit(
            db,
            claims,
            action="UPDATE",
            resource="Workflow",
            resource_id=workflow.id,
            details=f"run={execution.id}",
            request=request,
        )
        db.commit()
        db.refresh(execution)
        db.refresh(workflow)
        return {
            "execution": workflow_execution_to_dict(execution, workflow.name),
            "workflow": workflow_to_dict(workflow),
        }

    return router
