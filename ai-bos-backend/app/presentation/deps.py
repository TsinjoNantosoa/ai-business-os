from __future__ import annotations

import hmac
from collections.abc import Generator
from typing import Any

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import decode_token
from app.core.tenant import set_current_org_id, validate_tenant_header
from app.presentation.chatbot_rate_limit import ChatbotRateLimiter
from app.repositories.api_key_repository import API_KEY_PREFIX, ApiKeyRepository, hash_api_key
from app.services.feature_flag_service import is_feature_enabled

chatbot_rate_limiter = ChatbotRateLimiter(max_per_minute=settings.chatbot_query_rate_limit)


def _claims_from_api_key(raw_key: str) -> dict[str, Any] | None:
    if not raw_key.startswith(API_KEY_PREFIX):
        return None
    with SessionLocal() as session:
        key_hash = hash_api_key(raw_key)
        if not settings.is_sqlite:
            session.execute(
                text("SELECT set_config('app.auth_api_key_hash', :value, true)"),
                {"value": key_hash},
            )
        repo = ApiKeyRepository(session)
        row = repo.get_by_hash(key_hash)
        if not row:
            return None
        apply_tenant_rls(session, row.org_id)
        repo.touch_last_used(row)
        return {
            "sub": f"apk:{row.id}",
            "email": f"api-key@{row.org_id}.aibos",
            "role": "api_key",
            "permissions": list(row.scopes or []),
            "org_id": row.org_id,
            "first_name": "API",
            "last_name": "Key",
            "auth_type": "api_key",
            "api_key_id": row.id,
        }


def require_auth(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-Api-Key"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
) -> dict[str, Any]:
    raw_api_key = (x_api_key or "").strip()
    bearer = ""
    if authorization and authorization.lower().startswith("bearer "):
        bearer = authorization.split(" ", 1)[1].strip()

    candidate = raw_api_key or (bearer if bearer.startswith(API_KEY_PREFIX) else "")
    if candidate:
        claims = _claims_from_api_key(candidate)
        if not claims:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Clé API invalide ou révoquée")
        org_id = str(claims.get("org_id") or "")
        validate_tenant_header(org_id, x_tenant_id)
        set_current_org_id(org_id or None)
        return claims

    if not bearer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization Bearer requis")

    try:
        payload = decode_token(bearer)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token invalide") from exc

    org_id = str(payload.get("org_id") or "")
    validate_tenant_header(org_id, x_tenant_id)
    set_current_org_id(org_id or None)
    payload["auth_type"] = "jwt"
    return payload


def require_permission(permission: str):
    def _dep(claims: dict[str, Any] = Depends(require_auth)) -> dict[str, Any]:
        permissions = claims.get("permissions") or []
        if "*" in permissions:
            return claims
        if permission not in permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission insuffisante")
        return claims

    return _dep


def require_feature(feature_key: str):
    def _dep(
        claims: dict[str, Any] = Depends(require_auth),
        db: Session = Depends(get_tenant_db),
    ) -> dict[str, Any]:
        org_id = claims_org_id(claims)
        if not is_feature_enabled(db, org_id, feature_key):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Fonctionnalité désactivée: {feature_key}",
            )
        return claims

    return _dep


def claims_org_id(claims: dict[str, Any]) -> str:
    return str(claims.get("org_id") or "")


def claims_user_id(claims: dict[str, Any]) -> str:
    return str(claims.get("sub") or "")


def apply_tenant_rls(db: Session, org_id: str) -> None:
    """Set PostgreSQL session GUC used by RLS policies (no-op on SQLite)."""
    if settings.is_sqlite or not org_id:
        return
    db.execute(text("SELECT set_config('app.current_org_id', :org, true)"), {"org": org_id})


def get_tenant_db(
    claims: dict[str, Any] = Depends(require_auth),
) -> Generator[Session, None, None]:
    """Open a request-scoped DB session with the tenant RLS context applied.

    The authentication dependency is intentionally declared here so PostgreSQL
    receives the tenant GUC before any route-level query can execute.
    """
    db = SessionLocal()
    try:
        apply_tenant_rls(db, claims_org_id(claims))
        yield db
    finally:
        db.close()


def verify_chatbot_token(
    x_chatbot_token: str | None = Header(default=None, alias="X-Chatbot-Token"),
) -> None:
    expected = settings.chatbot_api_token
    if not expected:
        return
    provided = (x_chatbot_token or "").strip()
    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token chatbot invalide")
