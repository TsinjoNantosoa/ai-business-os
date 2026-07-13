from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.presentation.deps import claims_org_id, require_permission
from app.presentation.schemas import TaskAssignBody, TaskStatusUpdateBody
from app.presentation.serializers import task_to_dict
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_service import record_audit

VALID_STATUSES = {"todo", "in_progress", "review", "done"}


def build_tasks_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["tasks"])

    @router.get("/tasks")
    def list_tasks(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("task.read")),
    ) -> list[dict]:
        tasks = TaskRepository(db).list_by_org(claims_org_id(claims))
        return [task_to_dict(task) for task in tasks]

    @router.patch("/tasks/{task_id}/status")
    def update_task_status(
        task_id: str,
        body: TaskStatusUpdateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("task.write")),
    ) -> dict:
        if body.status not in VALID_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut invalide")
        repo = TaskRepository(db)
        task = repo.get_by_id(claims_org_id(claims), task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche introuvable")
        repo.update_status(task, body.status)
        record_audit(db, claims, action="UPDATE", resource="Task", resource_id=task.id, details=f"status={body.status}", request=request)
        db.commit()
        db.refresh(task)
        return task_to_dict(task)

    @router.patch("/tasks/{task_id}/assign")
    def assign_task(
        task_id: str,
        body: TaskAssignBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("task.write")),
    ) -> dict:
        org_id = claims_org_id(claims)
        repo = TaskRepository(db)
        task = repo.get_by_id(org_id, task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche introuvable")

        assignee_name = body.assigneeName
        assignee_color = body.assigneeAvatarColor
        user = UserRepository(db).get_by_id(body.assigneeId)
        if not user or user.org_id != org_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee introuvable dans ce tenant")
        assignee_name = assignee_name or f"{user.first_name} {user.last_name}".strip()
        assignee_color = assignee_color or "bg-primary-100"

        if not assignee_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assignee introuvable")

        repo.assign(
            task,
            assignee_id=body.assigneeId,
            assignee_name=assignee_name,
            assignee_avatar_color=assignee_color,
        )
        record_audit(db, claims, action="UPDATE", resource="Task", resource_id=task.id, details=f"assign={body.assigneeId}", request=request)
        db.commit()
        db.refresh(task)
        return task_to_dict(task)

    return router
