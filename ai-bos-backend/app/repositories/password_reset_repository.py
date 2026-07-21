from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.password_reset_token import PasswordResetToken

MAX_VERIFY_ATTEMPTS = 5


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


class PasswordResetRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, user_id: str, *, expires_minutes: int) -> tuple[PasswordResetToken, str]:
        now = datetime.now(timezone.utc)
        self._session.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.user_id == user_id)
            .where(PasswordResetToken.used_at.is_(None))
            .values(used_at=now)
        )

        raw_code = _generate_code()
        reset = PasswordResetToken(
            id=f"prt-{secrets.token_hex(8)}",
            user_id=user_id,
            token_hash=hash_reset_token(raw_code),
            attempts=0,
            created_at=now,
            expires_at=now + timedelta(minutes=expires_minutes),
        )
        self._session.add(reset)
        self._session.flush()
        return reset, raw_code

    def get_active_for_user(self, user_id: str) -> PasswordResetToken | None:
        stmt = (
            select(PasswordResetToken)
            .where(PasswordResetToken.user_id == user_id)
            .where(PasswordResetToken.used_at.is_(None))
            .order_by(PasswordResetToken.created_at.desc())
        )
        return self._session.scalars(stmt).first()

    def register_failed_attempt(self, reset: PasswordResetToken) -> None:
        reset.attempts = (reset.attempts or 0) + 1
        if reset.attempts >= MAX_VERIFY_ATTEMPTS:
            reset.used_at = datetime.now(timezone.utc)
        self._session.flush()

    def mark_used(self, reset: PasswordResetToken) -> None:
        reset.used_at = datetime.now(timezone.utc)
        self._session.flush()
