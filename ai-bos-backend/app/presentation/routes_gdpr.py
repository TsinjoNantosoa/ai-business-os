from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.presentation.deps import claims_org_id, claims_user_id, require_auth
from app.repositories.user_repository import UserRepository
from app.services.audit_service import record_audit
from app.services.gdpr_service import build_gdpr_export


def build_gdpr_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/platform/gdpr", tags=["gdpr"])

    @router.get("/export")
    def export_my_data(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> dict:
        if claims.get("auth_type") == "api_key":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Export GDPR réservé aux utilisateurs")
        return build_gdpr_export(db, org_id=claims_org_id(claims), user_id=claims_user_id(claims))

    @router.post("/erase-request")
    def erase_request(
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> dict:
        if claims.get("auth_type") == "api_key":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Effacement réservé aux utilisateurs")
        user_id = claims_user_id(claims)
        org_id = claims_org_id(claims)
        user = UserRepository(db).get_by_id(user_id)
        if not user or user.org_id != org_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
        if user.role == "owner":
            # Prevent accidental lockout of demo org owner in MVP.
            owners = [u for u in UserRepository(db).list_by_org(org_id) if u.role == "owner" and u.active]
            if len(owners) <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Impossible d'effacer le dernier owner actif — transférez le rôle d'abord",
                )
        user.active = False
        db.commit()
        record_audit(
            db,
            claims,
            action="DELETE",
            resource="User",
            resource_id=user.id,
            details="gdpr_erase_request",
            request=request,
        )
        return {"status": "accepted", "userId": user.id, "active": False}

    return router
