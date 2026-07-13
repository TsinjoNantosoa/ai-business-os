from __future__ import annotations

import secrets
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lead import Lead

STAGE_PROBABILITY = {
    "new": 10.0,
    "qualified": 30.0,
    "proposal": 50.0,
    "negotiation": 75.0,
    "won": 100.0,
    "lost": 0.0,
}


class LeadRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_org(self, org_id: str) -> list[Lead]:
        stmt = select(Lead).where(Lead.org_id == org_id).order_by(Lead.created_at.desc())
        return list(self._session.scalars(stmt).all())

    def get_by_id(self, org_id: str, lead_id: str) -> Lead | None:
        stmt = select(Lead).where(Lead.org_id == org_id, Lead.id == lead_id)
        return self._session.scalars(stmt).first()

    def count_all(self) -> int:
        return len(list(self._session.scalars(select(Lead)).all()))

    def create(
        self,
        *,
        org_id: str,
        title: str,
        company: str,
        contact_name: str,
        value: int,
        owner_id: str,
        owner_name: str,
        currency: str = "EUR",
        stage: str = "new",
        owner_avatar_color: str = "bg-primary-100",
        expected_close_date: datetime,
    ) -> Lead:
        now = datetime.now(timezone.utc)
        lead = Lead(
            id=f"lead-{secrets.token_hex(6)}",
            org_id=org_id,
            title=title,
            company=company,
            contact_name=contact_name,
            value=value,
            currency=currency,
            stage=stage,
            probability=STAGE_PROBABILITY.get(stage, 10.0),
            owner_id=owner_id,
            owner_name=owner_name,
            owner_avatar_color=owner_avatar_color,
            expected_close_date=expected_close_date,
            stage_changed_at=now,
            created_at=now,
            updated_at=now,
        )
        self._session.add(lead)
        self._session.flush()
        return lead

    def update_stage(self, lead: Lead, stage: str) -> Lead:
        lead.stage = stage
        lead.probability = STAGE_PROBABILITY.get(stage, lead.probability)
        lead.stage_changed_at = datetime.now(timezone.utc)
        lead.updated_at = datetime.now(timezone.utc)
        return lead
