from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.presentation.deps import claims_org_id, claims_user_id, require_permission
from app.presentation.schemas import LeadCreateBody, LeadStageUpdateBody
from app.presentation.serializers import activity_to_dict, lead_to_dict, parse_iso_datetime
from app.repositories.activity_repository import ActivityRepository
from app.repositories.lead_repository import LeadRepository


def build_crm_leads_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/crm", tags=["crm"])

    @router.get("/leads")
    def list_leads(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("crm.lead.read")),
    ) -> list[dict]:
        leads = LeadRepository(db).list_by_org(claims_org_id(claims))
        return [lead_to_dict(lead) for lead in leads]

    @router.post("/leads", status_code=status.HTTP_201_CREATED)
    def create_lead(
        body: LeadCreateBody,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("crm.lead.write")),
    ) -> dict:
        lead = LeadRepository(db).create(
            org_id=claims_org_id(claims),
            title=body.title,
            company=body.company,
            contact_name=body.contactName,
            value=body.value,
            owner_id=claims_user_id(claims),
            owner_name=f"{claims.get('first_name', '')} {claims.get('last_name', '')}".strip() or "Owner",
            currency=body.currency,
            stage=body.stage,
            expected_close_date=parse_iso_datetime(body.expectedCloseDate),
        )
        from app.services.event_bus import EventBus

        EventBus(db).publish(
            org_id=claims_org_id(claims),
            event_type="crm.lead.created",
            payload={"leadId": lead.id, "title": lead.title, "company": lead.company, "value": lead.value},
            source="crm",
        )
        db.commit()
        db.refresh(lead)
        return lead_to_dict(lead)

    @router.patch("/leads/{lead_id}/stage")
    def update_lead_stage(
        lead_id: str,
        body: LeadStageUpdateBody,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("crm.lead.write")),
    ) -> dict:
        repo = LeadRepository(db)
        lead = repo.get_by_id(claims_org_id(claims), lead_id)
        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead introuvable")
        repo.update_stage(lead, body.stage)
        db.commit()
        db.refresh(lead)
        return lead_to_dict(lead)

    @router.get("/activities")
    def list_activities(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("crm.lead.read")),
    ) -> list[dict]:
        activities = ActivityRepository(db).list_by_org(claims_org_id(claims))
        return [activity_to_dict(activity) for activity in activities]

    return router
