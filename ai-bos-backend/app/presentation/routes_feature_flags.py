from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.presentation.deps import claims_org_id, claims_user_id, require_auth, require_permission
from app.repositories.feature_flag_repository import FeatureFlagRepository
from app.services.audit_service import record_audit
from app.services.feature_flag_service import is_feature_enabled, list_resolved_flags


class FeatureFlagUpdateBody(BaseModel):
    enabled: bool
    reset: bool = Field(default=False, description="If true, remove tenant override and fall back to plan/default")


def build_feature_flags_router() -> APIRouter:
    router = APIRouter(tags=["feature-flags"])

    @router.get("/api/v1/platform/feature-flags")
    def platform_feature_flags(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> list[dict]:
        return list_resolved_flags(db, claims_org_id(claims))

    @router.get("/api/v1/admin/feature-flags")
    def admin_feature_flags(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("admin.flags")),
    ) -> list[dict]:
        return list_resolved_flags(db, claims_org_id(claims))

    @router.patch("/api/v1/admin/feature-flags/{flag_key}")
    def update_feature_flag(
        flag_key: str,
        body: FeatureFlagUpdateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("admin.flags")),
    ) -> dict:
        org_id = claims_org_id(claims)
        repo = FeatureFlagRepository(db)
        flag = repo.get_flag(flag_key)
        if not flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature flag introuvable")

        if body.reset:
            repo.delete_override(org_id, flag_key)
            record_audit(
                db,
                claims,
                action="UPDATE",
                resource="FeatureFlag",
                resource_id=flag_key,
                details="reset_override",
                request=request,
            )
        else:
            repo.upsert_override(
                org_id=org_id,
                flag_key=flag_key,
                enabled=body.enabled,
                updated_by=claims_user_id(claims),
            )
            record_audit(
                db,
                claims,
                action="UPDATE",
                resource="FeatureFlag",
                resource_id=flag_key,
                details=f"enabled={body.enabled}",
                request=request,
            )

        resolved = next((f for f in list_resolved_flags(db, org_id) if f["key"] == flag_key), None)
        return resolved or {
            "key": flag_key,
            "enabled": is_feature_enabled(db, org_id, flag_key),
        }

    return router
