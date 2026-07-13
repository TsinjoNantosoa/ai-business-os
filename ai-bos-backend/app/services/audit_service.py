from __future__ import annotations

from fastapi import Request
from sqlalchemy.orm import Session

from app.presentation.deps import claims_org_id, claims_user_id
from app.repositories.audit_log_repository import AuditLogRepository


def record_audit(
    db: Session,
    claims: dict,
    *,
    action: str,
    resource: str,
    resource_id: str | None = None,
    details: str | None = None,
    request: Request | None = None,
) -> None:
    """Persiste une entrée d'audit (best-effort, ne lève pas)."""
    try:
        ip = "127.0.0.1"
        if request and request.client:
            ip = request.client.host
        user_name = f"{claims.get('first_name', '')} {claims.get('last_name', '')}".strip() or "User"
        AuditLogRepository(db).create(
            org_id=claims_org_id(claims),
            user_id=claims_user_id(claims) or "unknown",
            user_name=user_name,
            action=action,
            resource=resource,
            resource_id=resource_id,
            ip=ip,
            details=details,
        )
    except Exception:
        # Ne jamais bloquer la mutation métier pour un échec d'audit
        pass
