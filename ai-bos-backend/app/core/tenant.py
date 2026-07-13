from __future__ import annotations

from contextvars import ContextVar

from fastapi import Header, HTTPException, status

_current_org_id: ContextVar[str | None] = ContextVar("current_org_id", default=None)


def get_current_org_id() -> str | None:
    return _current_org_id.get()


def set_current_org_id(org_id: str | None) -> None:
    _current_org_id.set(org_id)


def clear_current_org_id() -> None:
    _current_org_id.set(None)


def validate_tenant_header(
    jwt_org_id: str,
    x_tenant_id: str | None,
) -> None:
    """If X-Tenant-Id is present, it must match the JWT org_id."""
    header = (x_tenant_id or "").strip()
    if not header:
        return
    if header != jwt_org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="X-Tenant-Id ne correspond pas au tenant du token",
        )


def tenant_header_dep(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
) -> str | None:
    return x_tenant_id
