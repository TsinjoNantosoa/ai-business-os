from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.presentation.deps import claims_org_id, claims_user_id, require_permission
from app.presentation.serializers import api_key_to_dict
from app.repositories.api_key_repository import DEFAULT_SCOPES, ApiKeyRepository
from app.services.audit_service import record_audit


class ApiKeyCreateBody(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    scopes: list[str] = Field(default_factory=lambda: list(DEFAULT_SCOPES))


def build_api_keys_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/platform", tags=["api-keys"])

    @router.get("/api-keys")
    def list_api_keys(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("settings.org")),
    ) -> list[dict]:
        keys = ApiKeyRepository(db).list_by_org(claims_org_id(claims), include_revoked=True)
        return [api_key_to_dict(k) for k in keys]

    @router.post("/api-keys", status_code=status.HTTP_201_CREATED)
    def create_api_key(
        body: ApiKeyCreateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("settings.org")),
    ) -> dict:
        org_id = claims_org_id(claims)
        created_by_name = f"{claims.get('first_name', '')} {claims.get('last_name', '')}".strip() or "Admin"
        scopes = [s.strip() for s in body.scopes if s.strip()] or list(DEFAULT_SCOPES)
        row, raw = ApiKeyRepository(db).create(
            org_id=org_id,
            name=body.name,
            scopes=scopes,
            created_by=claims_user_id(claims),
            created_by_name=created_by_name,
        )
        record_audit(
            db,
            claims,
            action="CREATE",
            resource="ApiKey",
            resource_id=row.id,
            details=row.name,
            request=request,
        )
        data = api_key_to_dict(row)
        data["secret"] = raw  # shown once
        return data

    @router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
    def revoke_api_key(
        key_id: str,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("settings.org")),
    ) -> None:
        org_id = claims_org_id(claims)
        repo = ApiKeyRepository(db)
        row = repo.get_by_id(org_id, key_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clé API introuvable")
        if not row.active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Clé déjà révoquée")
        repo.revoke(row)
        record_audit(
            db,
            claims,
            action="DELETE",
            resource="ApiKey",
            resource_id=row.id,
            details=row.name,
            request=request,
        )

    return router
