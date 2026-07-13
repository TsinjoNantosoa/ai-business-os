from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity import Activity


class ActivityRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_org(self, org_id: str) -> list[Activity]:
        stmt = select(Activity).where(Activity.org_id == org_id).order_by(Activity.created_at.desc())
        return list(self._session.scalars(stmt).all())

    def list_by_contact(self, org_id: str, contact_id: str) -> list[Activity]:
        stmt = (
            select(Activity)
            .where(Activity.org_id == org_id, Activity.contact_id == contact_id)
            .order_by(Activity.created_at.desc())
        )
        return list(self._session.scalars(stmt).all())

    def count_all(self) -> int:
        return len(list(self._session.scalars(select(Activity)).all()))
