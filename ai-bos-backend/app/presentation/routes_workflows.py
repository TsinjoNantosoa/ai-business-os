from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.presentation.deps import claims_org_id, require_permission
from app.presentation.serializers import workflow_execution_to_dict, workflow_to_dict
from app.repositories.workflow_repository import WorkflowRepository
from app.services.audit_service import record_audit
from app.services.workflow_engine import WorkflowEngine


def build_workflows_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])

    @router.get("")
    def list_workflows(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("workflow.read")),
    ) -> list[dict]:
        workflows = WorkflowRepository(db).list_by_org(claims_org_id(claims))
        return [workflow_to_dict(workflow) for workflow in workflows]

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
            execution = WorkflowEngine(db).run(workflow, org_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        record_audit(db, claims, action="UPDATE", resource="Workflow", resource_id=workflow.id, details=f"run={execution.id}", request=request)
        db.commit()
        db.refresh(execution)
        db.refresh(workflow)
        return {
            "execution": workflow_execution_to_dict(execution, workflow.name),
            "workflow": workflow_to_dict(workflow),
        }

    @router.get("/executions")
    def list_executions(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("workflow.read")),
    ) -> list[dict]:
        repo = WorkflowRepository(db)
        org_id = claims_org_id(claims)
        workflows = {wf.id: wf.name for wf in repo.list_by_org(org_id)}
        executions = repo.list_executions(org_id)
        return [
            workflow_execution_to_dict(execution, workflows.get(execution.workflow_id))
            for execution in executions
        ]

    return router
