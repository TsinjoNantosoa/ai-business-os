from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select, text

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.refresh_session import RefreshSession as RefreshSessionModel


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RefreshSession:
    session_id: str
    org_id: str
    user_id: str
    family_id: str
    token_hash: str
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None
    replaced_by_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None

    @property
    def revoked(self) -> bool:
        return self.revoked_at is not None


def _set_guc(session, name: str, value: str) -> None:
    if not settings.is_sqlite:
        session.execute(text("SELECT set_config(:name, :value, true)"), {"name": name, "value": value})


def _snapshot(row: RefreshSessionModel) -> RefreshSession:
    return RefreshSession(
        session_id=row.id,
        org_id=row.org_id,
        user_id=row.user_id,
        family_id=row.family_id,
        token_hash=row.token_hash,
        created_at=row.created_at,
        expires_at=row.expires_at,
        revoked_at=row.revoked_at,
        replaced_by_id=row.replaced_by_id,
        ip_address=row.ip_address,
        user_agent=row.user_agent,
    )


class DatabaseRefreshSessionStore:
    """Persistent, rotation-aware refresh-token session store."""

    def save(self, refresh_session: RefreshSession) -> None:
        with SessionLocal() as db:
            _set_guc(db, "app.current_org_id", refresh_session.org_id)
            db.add(
                RefreshSessionModel(
                    id=refresh_session.session_id,
                    org_id=refresh_session.org_id,
                    user_id=refresh_session.user_id,
                    family_id=refresh_session.family_id,
                    token_hash=refresh_session.token_hash,
                    created_at=refresh_session.created_at,
                    expires_at=refresh_session.expires_at,
                    revoked_at=refresh_session.revoked_at,
                    replaced_by_id=refresh_session.replaced_by_id,
                    ip_address=refresh_session.ip_address,
                    user_agent=refresh_session.user_agent,
                )
            )
            db.commit()

    def get(self, session_id: str) -> RefreshSession | None:
        with SessionLocal() as db:
            _set_guc(db, "app.auth_refresh_sid", session_id)
            row = db.get(RefreshSessionModel, session_id)
            return _snapshot(row) if row else None

    def revoke(self, session_id: str, *, replaced_by_id: str | None = None) -> None:
        existing = self.get(session_id)
        if not existing:
            return
        with SessionLocal() as db:
            _set_guc(db, "app.current_org_id", existing.org_id)
            row = db.get(RefreshSessionModel, session_id)
            if row and row.revoked_at is None:
                row.revoked_at = datetime.now(timezone.utc)
                row.replaced_by_id = replaced_by_id
                db.commit()

    def revoke_family(self, family_id: str, org_id: str) -> None:
        with SessionLocal() as db:
            _set_guc(db, "app.current_org_id", org_id)
            rows = db.scalars(
                select(RefreshSessionModel).where(RefreshSessionModel.family_id == family_id)
            ).all()
            now = datetime.now(timezone.utc)
            for row in rows:
                row.revoked_at = row.revoked_at or now
            db.commit()

    def revoke_all_for_user(self, user_id: str, org_id: str | None = None) -> None:
        with SessionLocal() as db:
            if org_id:
                _set_guc(db, "app.current_org_id", org_id)
            else:
                _set_guc(db, "app.auth_user_id", user_id)
            rows = db.scalars(
                select(RefreshSessionModel).where(RefreshSessionModel.user_id == user_id)
            ).all()
            now = datetime.now(timezone.utc)
            for row in rows:
                row.revoked_at = row.revoked_at or now
            db.commit()

    def count_active_for_user(self, user_id: str, org_id: str) -> int:
        with SessionLocal() as db:
            _set_guc(db, "app.current_org_id", org_id)
            now = datetime.now(timezone.utc)
            rows = db.scalars(
                select(RefreshSessionModel).where(
                    RefreshSessionModel.user_id == user_id,
                    RefreshSessionModel.revoked_at.is_(None),
                    RefreshSessionModel.expires_at > now,
                )
            ).all()
            return len(list(rows))
