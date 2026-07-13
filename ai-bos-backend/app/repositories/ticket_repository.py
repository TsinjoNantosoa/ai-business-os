from __future__ import annotations

import secrets
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.ticket import Ticket, TicketMessage


class TicketRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_org(self, org_id: str) -> list[Ticket]:
        stmt = (
            select(Ticket)
            .where(Ticket.org_id == org_id)
            .options(selectinload(Ticket.messages))
            .order_by(Ticket.updated_at.desc())
        )
        return list(self._session.scalars(stmt).all())

    def get_by_id(self, org_id: str, ticket_id: str) -> Ticket | None:
        stmt = (
            select(Ticket)
            .where(Ticket.org_id == org_id, Ticket.id == ticket_id)
            .options(selectinload(Ticket.messages))
        )
        return self._session.scalars(stmt).first()

    def count_all(self) -> int:
        return len(list(self._session.scalars(select(Ticket)).all()))

    def add_message(
        self,
        ticket: Ticket,
        *,
        org_id: str,
        author: str,
        content: str,
        is_internal: bool = False,
    ) -> TicketMessage:
        now = datetime.now(timezone.utc)
        message = TicketMessage(
            id=f"tm-{secrets.token_hex(6)}",
            org_id=org_id,
            ticket_id=ticket.id,
            author=author,
            content=content,
            is_internal=is_internal,
            created_at=now,
        )
        ticket.updated_at = now
        if not is_internal and ticket.status == "open":
            ticket.status = "pending"
        self._session.add(message)
        self._session.flush()
        return message

    def update_status(self, ticket: Ticket, status: str) -> Ticket:
        ticket.status = status
        ticket.updated_at = datetime.now(timezone.utc)
        return ticket
