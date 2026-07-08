from __future__ import annotations

from typing import Any

from fastapi import Depends, Header, HTTPException, status

from app.core.security import decode_token


def require_auth(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization Bearer requis")

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token invalide") from exc

    return payload


def require_permission(permission: str):
    def _dep(claims: dict[str, Any] = Depends(require_auth)) -> dict[str, Any]:
        permissions = claims.get("permissions") or []
        if permission not in permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission insuffisante")
        return claims

    return _dep

