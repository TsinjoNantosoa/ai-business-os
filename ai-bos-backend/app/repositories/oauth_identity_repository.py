from __future__ import annotations

import secrets
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.oauth_identity import OAuthIdentity


class OAuthIdentityRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_provider_subject(self, provider: str, provider_subject: str) -> OAuthIdentity | None:
        stmt = select(OAuthIdentity).where(
            OAuthIdentity.provider == provider,
            OAuthIdentity.provider_subject == provider_subject,
        )
        return self._session.scalars(stmt).first()

    def upsert(
        self,
        *,
        user_id: str,
        org_id: str,
        provider: str,
        provider_subject: str,
        email: str,
    ) -> OAuthIdentity:
        existing = self.get_by_provider_subject(provider, provider_subject)
        now = datetime.now(timezone.utc)
        if existing:
            existing.user_id = user_id
            existing.org_id = org_id
            existing.email = email.lower().strip()
            existing.last_login_at = now
            self._session.commit()
            self._session.refresh(existing)
            return existing

        row = OAuthIdentity(
            id=f"oauth-{secrets.token_hex(8)}",
            user_id=user_id,
            org_id=org_id,
            provider=provider,
            provider_subject=provider_subject,
            email=email.lower().strip(),
            created_at=now,
            last_login_at=now,
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return row
