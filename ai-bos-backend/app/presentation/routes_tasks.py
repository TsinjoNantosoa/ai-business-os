from __future__ import annotations

from fastapi import APIRouter, Depends

from app.presentation.deps import require_auth


def build_tasks_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["tasks"])

    @router.get("/tasks")
    def tasks(_claims: dict = Depends(require_auth)) -> list[dict]:
        # Shape alignée avec `ai-bos-frontend/src/lib/api/types.ts` (Task, TaskStatus, TaskPriority)
        return [
            {
                "id": "task-1",
                "title": "Préparer présentation Q4",
                "description": "Synthèse KPI + recommandations (dashboard + finance).",
                "status": "in_progress",
                "priority": "high",
                "assigneeId": "u-staff-1",
                "assigneeName": "Demo Staff",
                "assigneeAvatarColor": "bg-slate-100",
                "projectId": "proj-1",
                "projectName": "Growth Strategy",
                "dueDate": "2026-07-10",
                "tags": ["kpi", "q4"],
                "createdAt": "2026-06-20",
            },
            {
                "id": "task-2",
                "title": "Réviser contrat TechSolutions",
                "status": "review",
                "priority": "urgent",
                "assigneeId": "u-owner-1",
                "assigneeName": "Aina CEO",
                "assigneeAvatarColor": "bg-primary-100",
                "projectId": "proj-2",
                "projectName": "Contracts & Legal",
                "dueDate": "2026-07-09",
                "tags": ["legal", "contract"],
                "createdAt": "2026-06-28",
            },
            {
                "id": "task-3",
                "title": "Formation équipe CRM",
                "status": "todo",
                "priority": "medium",
                "assigneeId": "u-owner-1",
                "assigneeName": "Aina CEO",
                "assigneeAvatarColor": "bg-primary-100",
                "projectId": "proj-1",
                "projectName": "Growth Strategy",
                "dueDate": "2026-07-15",
                "tags": ["crm", "training"],
                "createdAt": "2026-06-30",
            },
            {
                "id": "task-4",
                "title": "Audit sécurité mensuel",
                "status": "done",
                "priority": "low",
                "assigneeId": "u-staff-1",
                "assigneeName": "Demo Staff",
                "assigneeAvatarColor": "bg-slate-100",
                "projectId": "proj-3",
                "projectName": "Security Baseline",
                "dueDate": "2026-06-30",
                "tags": ["security", "audit"],
                "createdAt": "2026-06-10",
            },
        ]

    return router

