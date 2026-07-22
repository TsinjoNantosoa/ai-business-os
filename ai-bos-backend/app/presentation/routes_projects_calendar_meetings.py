from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.presentation.deps import claims_org_id, claims_user_id, require_auth, require_permission
from app.presentation.schemas import (
    CalendarEventCreateBody,
    CalendarEventUpdateBody,
    MeetingCreateBody,
    MeetingUpdateBody,
    ProjectCreateBody,
    ProjectUpdateBody,
)
from app.presentation.serializers import (
    calendar_event_to_dict,
    meeting_to_dict,
    project_to_dict,
)
from app.repositories.ops_repository import (
    CalendarEventRepository,
    MeetingRepository,
    ProjectRepository,
)
from app.repositories.user_repository import UserRepository
from app.services.audit_service import record_audit

PROJECT_STATUSES = {"planning", "active", "on_hold", "completed", "cancelled"}
EVENT_TYPES = {"meeting", "deadline", "reminder", "call", "task"}
MEETING_STATUSES = {"upcoming", "completed", "cancelled"}


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def build_projects_calendar_meetings_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["projects-calendar-meetings"])

    # --- Projects ---

    @router.get("/projects")
    def projects(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> list[dict]:
        items = ProjectRepository(db).list_by_org(claims_org_id(claims))
        return [project_to_dict(project) for project in items]

    @router.post("/projects", status_code=status.HTTP_201_CREATED)
    def create_project(
        body: ProjectCreateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("project.write")),
    ) -> dict:
        if body.status not in PROJECT_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut invalide")

        user = UserRepository(db).get_by_id(claims_user_id(claims))
        members = []
        if user:
            members.append(
                {
                    "id": user.id,
                    "name": f"{user.first_name} {user.last_name}".strip() or user.email,
                    "avatarColor": "bg-primary-100",
                    "role": user.role,
                }
            )

        project = ProjectRepository(db).create(
            claims_org_id(claims),
            name=body.name.strip(),
            description=(body.description or "").strip() or None,
            status=body.status,
            progress=0,
            start_date=body.startDate or _today(),
            end_date=body.endDate,
            budget=body.budget,
            spent=0,
            team_members=members,
            task_count=0,
            completed_tasks=0,
            color=body.color,
        )
        record_audit(db, claims, action="CREATE", resource="Project", resource_id=project.id, details=project.name, request=request)
        db.commit()
        db.refresh(project)
        return project_to_dict(project)

    @router.patch("/projects/{project_id}")
    def update_project(
        project_id: str,
        body: ProjectUpdateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("project.write")),
    ) -> dict:
        if body.status is not None and body.status not in PROJECT_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut invalide")
        repo = ProjectRepository(db)
        project = repo.get_by_id(claims_org_id(claims), project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet introuvable")

        repo.update(
            project,
            name=body.name,
            description=body.description,
            status=body.status,
            progress=body.progress,
            start_date=body.startDate,
            end_date=body.endDate,
            budget=body.budget,
            spent=body.spent,
            color=body.color,
        )
        record_audit(db, claims, action="UPDATE", resource="Project", resource_id=project.id, details=f"status={body.status}", request=request)
        db.commit()
        db.refresh(project)
        return project_to_dict(project)

    # --- Calendar events ---

    @router.get("/calendar/events")
    def events(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> list[dict]:
        items = CalendarEventRepository(db).list_by_org(claims_org_id(claims))
        return [calendar_event_to_dict(event) for event in items]

    @router.post("/calendar/events", status_code=status.HTTP_201_CREATED)
    def create_event(
        body: CalendarEventCreateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("calendar.write")),
    ) -> dict:
        if body.type not in EVENT_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Type invalide")

        event = CalendarEventRepository(db).create(
            claims_org_id(claims),
            title=body.title.strip(),
            type=body.type,
            start_date=body.startDate,
            end_date=body.endDate,
            color=body.color,
            location=body.location,
            attendees=body.attendees,
            description=body.description,
        )
        record_audit(db, claims, action="CREATE", resource="CalendarEvent", resource_id=event.id, details=event.title, request=request)
        db.commit()
        db.refresh(event)
        return calendar_event_to_dict(event)

    @router.patch("/calendar/events/{event_id}")
    def update_event(
        event_id: str,
        body: CalendarEventUpdateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("calendar.write")),
    ) -> dict:
        if body.type is not None and body.type not in EVENT_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Type invalide")
        repo = CalendarEventRepository(db)
        event = repo.get_by_id(claims_org_id(claims), event_id)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Événement introuvable")

        repo.update(
            event,
            title=body.title,
            type=body.type,
            start_date=body.startDate,
            end_date=body.endDate,
            color=body.color,
            location=body.location,
            attendees=body.attendees,
            description=body.description,
        )
        record_audit(db, claims, action="UPDATE", resource="CalendarEvent", resource_id=event.id, details=event.title, request=request)
        db.commit()
        db.refresh(event)
        return calendar_event_to_dict(event)

    # --- Meetings ---

    @router.get("/meetings")
    def meetings(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> list[dict]:
        items = MeetingRepository(db).list_by_org(claims_org_id(claims))
        return [meeting_to_dict(meeting) for meeting in items]

    @router.post("/meetings", status_code=status.HTTP_201_CREATED)
    def create_meeting(
        body: MeetingCreateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("meeting.write")),
    ) -> dict:
        user = UserRepository(db).get_by_id(claims_user_id(claims))
        attendees = []
        if user:
            attendees.append(
                {
                    "id": user.id,
                    "name": f"{user.first_name} {user.last_name}".strip() or user.email,
                    "avatarColor": "bg-primary-100",
                }
            )

        meeting = MeetingRepository(db).create(
            claims_org_id(claims),
            title=body.title.strip(),
            date=body.date,
            duration=body.duration,
            status="upcoming",
            location=body.location,
            attendees=attendees,
            agenda=body.agenda,
            summary=None,
            action_items=[],
        )
        record_audit(db, claims, action="CREATE", resource="Meeting", resource_id=meeting.id, details=meeting.title, request=request)
        db.commit()
        db.refresh(meeting)
        return meeting_to_dict(meeting)

    @router.patch("/meetings/{meeting_id}")
    def update_meeting(
        meeting_id: str,
        body: MeetingUpdateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("meeting.write")),
    ) -> dict:
        if body.status is not None and body.status not in MEETING_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut invalide")
        repo = MeetingRepository(db)
        meeting = repo.get_by_id(claims_org_id(claims), meeting_id)
        if not meeting:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Réunion introuvable")

        repo.update(
            meeting,
            title=body.title,
            date=body.date,
            duration=body.duration,
            status=body.status,
            location=body.location,
            agenda=body.agenda,
            summary=body.summary,
        )
        record_audit(db, claims, action="UPDATE", resource="Meeting", resource_id=meeting.id, details=f"status={body.status}", request=request)
        db.commit()
        db.refresh(meeting)
        return meeting_to_dict(meeting)

    return router
