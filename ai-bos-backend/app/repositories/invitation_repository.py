from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.invitation import Invitation


class InvitationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_org(self, org_id: str, status: str | None = None) -> list[Invitation]:
        stmt = select(Invitation).where(Invitation.org_id == org_id)
        if status:
            stmt = stmt.where(Invitation.status == status)
        stmt = stmt.order_by(Invitation.created_at.desc())
        return list(self._session.scalars(stmt).all())

    def get_by_id(self, invitation_id: str) -> Invitation | None:
        return self._session.get(Invitation, invitation_id)

    def get_by_token(self, token: str) -> Invitation | None:
        stmt = select(Invitation).where(Invitation.token == token)
        return self._session.scalars(stmt).first()

    def get_pending_by_email(self, org_id: str, email: str) -> Invitation | None:
        stmt = (
            select(Invitation)
            .where(Invitation.org_id == org_id)
            .where(Invitation.email == email.lower().strip())
            .where(Invitation.status == "pending")
        )
        return self._session.scalars(stmt).first()

    def get_pending_by_email_any_org(self, email: str) -> Invitation | None:
        stmt = (
            select(Invitation)
            .where(Invitation.email == email.lower().strip())
            .where(Invitation.status == "pending")
            .order_by(Invitation.created_at.desc())
        )
        return self._session.scalars(stmt).first()

    def count_all(self) -> int:
        return len(list(self._session.scalars(select(Invitation)).all()))

    def create(
        self,
        *,
        org_id: str,
        email: str,
        role: str,
        invited_by: str,
        invited_by_name: str,
        message: str | None = None,
        expires_days: int = 7,
    ) -> Invitation:
        now = datetime.now(timezone.utc)
        invitation = Invitation(
            id=f"inv-{secrets.token_hex(8)}",
            org_id=org_id,
            email=email.lower().strip(),
            role=role,
            token=secrets.token_urlsafe(32),
            status="pending",
            invited_by=invited_by,
            invited_by_name=invited_by_name,
            message=message,
            created_at=now,
            expires_at=now + timedelta(days=expires_days),
        )
        self._session.add(invitation)
        self._session.commit()
        self._session.refresh(invitation)
        return invitation

    def mark_accepted(self, invitation: Invitation) -> Invitation:
        invitation.status = "accepted"
        invitation.accepted_at = datetime.now(timezone.utc)
        self._session.commit()
        self._session.refresh(invitation)
        return invitation

    def revoke(self, invitation: Invitation) -> Invitation:
        invitation.status = "revoked"
        self._session.commit()
        self._session.refresh(invitation)
        return invitation
