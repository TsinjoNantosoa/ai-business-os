from __future__ import annotations

from fastapi import APIRouter, Depends

from app.presentation.deps import claims_org_id, require_permission
from app.services.auth_service import AuthService


def build_rbac_router(auth_service: AuthService) -> APIRouter:
    router = APIRouter(prefix="/api/v1/rbac", tags=["rbac"])

    admin_required = Depends(require_permission("admin.audit"))

    @router.get("/permissions")
    def permissions(claims: dict = admin_required):
        _roles, permissions_list = auth_service.roles_and_permissions_for_rbac(claims_org_id(claims))
        return {"items": permissions_list}

    @router.get("/roles")
    def roles(claims: dict = admin_required):
        roles_list, _permissions = auth_service.roles_and_permissions_for_rbac(claims_org_id(claims))
        return {"items": roles_list}

    @router.get("/users")
    def users(claims: dict = admin_required):
        return {"items": auth_service.list_users_for_rbac(claims_org_id(claims))}

    return router
