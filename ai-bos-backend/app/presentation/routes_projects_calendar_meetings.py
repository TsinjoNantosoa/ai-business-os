from __future__ import annotations

from fastapi import APIRouter, Depends

from app.presentation.deps import require_auth


def build_projects_calendar_meetings_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["projects-calendar-meetings"])

    @router.get("/projects")
    def projects(_claims: dict = Depends(require_auth)) -> list[dict]:
        return [
            {
                "id": "proj-1",
                "name": "Growth Strategy",
                "description": "Plan de croissance Q3/Q4 et priorisation CRM/Finance.",
                "status": "active",
                "progress": 62,
                "startDate": "2026-05-01",
                "endDate": "2026-12-15",
                "budget": 250000,
                "spent": 155000,
                "teamMembers": [
                    {"id": "u-owner-1", "name": "Aina CEO", "avatarColor": "bg-primary-100", "role": "owner"},
                    {"id": "u-staff-1", "name": "Demo Staff", "avatarColor": "bg-slate-100", "role": "staff"},
                ],
                "taskCount": 24,
                "completedTasks": 15,
                "color": "#4f46e5",
            },
            {
                "id": "proj-2",
                "name": "Contracts & Legal",
                "description": "Revue contrats, NDA, et conformité sécurité.",
                "status": "on_hold",
                "progress": 28,
                "startDate": "2026-06-01",
                "endDate": "2026-09-30",
                "budget": 80000,
                "spent": 21000,
                "teamMembers": [
                    {"id": "u-owner-1", "name": "Aina CEO", "avatarColor": "bg-primary-100", "role": "owner"},
                ],
                "taskCount": 8,
                "completedTasks": 2,
                "color": "#f59e0b",
            },
        ]

    @router.get("/calendar/events")
    def events(_claims: dict = Depends(require_auth)) -> list[dict]:
        return [
            {
                "id": "ev-1",
                "title": "Réunion de lancement CRM",
                "type": "meeting",
                "startDate": "2026-07-08T10:00:00Z",
                "endDate": "2026-07-08T10:45:00Z",
                "color": "#4f46e5",
                "location": "Room A / Zoom",
                "attendees": ["Aina CEO", "Demo Staff"],
                "description": "Synchronisation initiale et validation roadmap.",
            },
            {
                "id": "ev-2",
                "title": "Deadline audit sécurité",
                "type": "deadline",
                "startDate": "2026-07-10T09:00:00Z",
                "endDate": "2026-07-10T12:00:00Z",
                "color": "#ef4444",
                "location": "HQ",
            },
            {
                "id": "ev-3",
                "title": "Reminder : relance facture",
                "type": "reminder",
                "startDate": "2026-07-15T14:00:00Z",
                "endDate": "2026-07-15T14:15:00Z",
                "color": "#f59e0b",
                "description": "Relance automatique J+3.",
            },
        ]

    @router.get("/meetings")
    def meetings(_claims: dict = Depends(require_auth)) -> list[dict]:
        return [
            {
                "id": "mt-1",
                "title": "Monthly Finance Sync",
                "date": "2026-07-05",
                "duration": 45,
                "status": "upcoming",
                "location": "Room Finance",
                "attendees": [
                    {"id": "u-owner-1", "name": "Aina CEO", "avatarColor": "bg-primary-100"},
                    {"id": "u-staff-1", "name": "Demo Staff", "avatarColor": "bg-slate-100"},
                ],
                "agenda": [
                    "AR aging",
                    "Cashflow et alertes",
                    "Prochaines actions paiement",
                ],
                "summary": "Alignement sur les priorités de recouvrement et les alertes trésorerie.",
                "actionItems": [
                    {"id": "ai-1", "text": "Relancer 3 factures en retard", "done": False, "assignee": "Demo Staff"},
                    {"id": "ai-2", "text": "Valider budget Q4", "done": True, "assignee": "Aina CEO"},
                ],
            }
        ]

    return router

