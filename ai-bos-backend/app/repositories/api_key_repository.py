from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.api_key import ApiKey

API_KEY_PREFIX = "aibos_sk_"
DEFAULT_SCOPES = [
    "dashboard.read",
    "crm.contact.read",
    "crm.lead.read",
    "finance.invoice.read",
    "task.read",
    "document.read",
]

# API keys are integration credentials, never tenant administrators. Sensitive
# account, billing, approval, and audit capabilities are intentionally excluded.
API_KEY_SCOPE_ALLOWLIST = {
    "dashboard.read",
    "crm.contact.read",
    "crm.contact.write",
    "crm.lead.read",
    "crm.lead.write",
    "sales.order.read",
    "sales.order.write",
    "marketing.campaign.read",
    "marketing.campaign.write",
    "finance.invoice.read",
    "finance.invoice.write",
    "finance.payment.read",
    "finance.payment.write",
    "project.read",
    "project.write",
    "task.read",
    "task.write",
    "document.read",
    "document.write",
    "inventory.read",
    "inventory.write",
    "support.ticket.read",
    "support.ticket.write",
    "knowledge.read",
    "knowledge.write",
    "workflow.read",
    "workflow.write",
}


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_raw_api_key() -> str:
    return f"{API_KEY_PREFIX}{secrets.token_urlsafe(32)}"


def mask_api_key(prefix: str) -> str:
    return f"{prefix}••••••••••••••••"


class ApiKeyRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_org(self, org_id: str, *, include_revoked: bool = False) -> list[ApiKey]:
        stmt = select(ApiKey).where(ApiKey.org_id == org_id)
        if not include_revoked:
            stmt = stmt.where(ApiKey.active.is_(True))
        stmt = stmt.order_by(ApiKey.created_at.desc())
        return list(self._session.scalars(stmt).all())

    def get_by_id(self, org_id: str, key_id: str) -> ApiKey | None:
        stmt = select(ApiKey).where(ApiKey.org_id == org_id, ApiKey.id == key_id)
        return self._session.scalars(stmt).first()

    def get_by_hash(self, key_hash: str) -> ApiKey | None:
        stmt = select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.active.is_(True))
        return self._session.scalars(stmt).first()

    def count_all(self) -> int:
        return len(list(self._session.scalars(select(ApiKey)).all()))

    def create(
        self,
        *,
        org_id: str,
        name: str,
        scopes: list[str],
        created_by: str,
        created_by_name: str,
        raw_key: str | None = None,
    ) -> tuple[ApiKey, str]:
        raw = raw_key or generate_raw_api_key()
        row = ApiKey(
            id=f"apk-{secrets.token_hex(8)}",
            org_id=org_id,
            name=name.strip(),
            key_prefix=raw[:16],
            key_hash=hash_api_key(raw),
            scopes=scopes or list(DEFAULT_SCOPES),
            created_by=created_by,
            created_by_name=created_by_name,
            active=True,
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return row, raw

    def revoke(self, api_key: ApiKey) -> ApiKey:
        api_key.active = False
        api_key.revoked_at = datetime.now(timezone.utc)
        self._session.commit()
        self._session.refresh(api_key)
        return api_key

    def touch_last_used(self, api_key: ApiKey) -> None:
        api_key.last_used_at = datetime.now(timezone.utc)
        self._session.commit()
