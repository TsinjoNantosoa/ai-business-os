"""Repositories for Lot B entities (orders, campaigns, projects, events, meetings)."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ops import CalendarEvent, Campaign, Meeting, Project, SalesOrder

ModelT = TypeVar("ModelT", SalesOrder, Campaign, Project, CalendarEvent, Meeting)


class _OpsRepository(Generic[ModelT]):
    model: type[ModelT]
    id_prefix: str
    order_by_column: str = "created_at"

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_org(self, org_id: str) -> list[ModelT]:
        order_col = getattr(self.model, self.order_by_column)
        stmt = select(self.model).where(self.model.org_id == org_id).order_by(order_col.desc())
        return list(self._session.scalars(stmt).all())

    def get_by_id(self, org_id: str, entity_id: str) -> ModelT | None:
        stmt = select(self.model).where(self.model.org_id == org_id, self.model.id == entity_id)
        return self._session.scalars(stmt).first()

    def count_all(self) -> int:
        return int(self._session.scalar(select(func.count()).select_from(self.model)) or 0)

    def create(self, org_id: str, **fields: Any) -> ModelT:
        now = datetime.now(timezone.utc)
        entity = self.model(
            id=fields.pop("id", None) or f"{self.id_prefix}-{secrets.token_hex(6)}",
            org_id=org_id,
            created_at=now,
            updated_at=now,
            **fields,
        )
        self._session.add(entity)
        self._session.flush()
        return entity

    def update(self, entity: ModelT, **fields: Any) -> ModelT:
        for key, value in fields.items():
            if value is not None:
                setattr(entity, key, value)
        entity.updated_at = datetime.now(timezone.utc)
        self._session.flush()
        return entity


class SalesOrderRepository(_OpsRepository[SalesOrder]):
    model = SalesOrder
    id_prefix = "so"
    order_by_column = "date"

    def next_order_number(self, org_id: str) -> str:
        count = int(
            self._session.scalar(
                select(func.count()).select_from(SalesOrder).where(SalesOrder.org_id == org_id)
            )
            or 0
        )
        return f"SO-{2000 + count}"


class CampaignRepository(_OpsRepository[Campaign]):
    model = Campaign
    id_prefix = "camp"
    order_by_column = "start_date"


class ProjectRepository(_OpsRepository[Project]):
    model = Project
    id_prefix = "proj"
    order_by_column = "created_at"


class CalendarEventRepository(_OpsRepository[CalendarEvent]):
    model = CalendarEvent
    id_prefix = "ev"
    order_by_column = "start_date"


class MeetingRepository(_OpsRepository[Meeting]):
    model = Meeting
    id_prefix = "mt"
    order_by_column = "date"
