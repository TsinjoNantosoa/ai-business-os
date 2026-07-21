from __future__ import annotations

from fastapi import APIRouter, Depends

from app.data.seed_ops import DEMO_CALENDAR_EVENTS, DEMO_MEETINGS, DEMO_PROJECTS
from app.presentation.deps import require_auth


def build_projects_calendar_meetings_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["projects-calendar-meetings"])

    @router.get("/projects")
    def projects(_claims: dict = Depends(require_auth)) -> list[dict]:
        return DEMO_PROJECTS

    @router.get("/calendar/events")
    def events(_claims: dict = Depends(require_auth)) -> list[dict]:
        return DEMO_CALENDAR_EVENTS

    @router.get("/meetings")
    def meetings(_claims: dict = Depends(require_auth)) -> list[dict]:
        return DEMO_MEETINGS

    return router
