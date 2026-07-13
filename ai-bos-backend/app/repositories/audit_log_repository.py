from __future__ import annotations

import secrets
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_org(self, org_id: str, limit: int = 100) -> list[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.org_id == org_id)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        return list(self._session.scalars(stmt).all())

    def count_all(self) -> int:
        return len(list(self._session.scalars(select(AuditLog)).all()))

    def create(
        self,
        *,
        org_id: str,
        user_id: str,
        user_name: str,
        action: str,
        resource: str,
        resource_id: str | None = None,
        ip: str = "127.0.0.1",
        details: str | None = None,
        timestamp: datetime | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            id=f"audit-{secrets.token_hex(6)}",
            org_id=org_id,
            timestamp=timestamp or datetime.now(timezone.utc),
            user_id=user_id,
            user_name=user_name,
            action=action,
            resource=resource,
            resource_id=resource_id,
            ip=ip,
            details=details,
        )
        self._session.add(entry)
        self._session.flush()
        return entry
