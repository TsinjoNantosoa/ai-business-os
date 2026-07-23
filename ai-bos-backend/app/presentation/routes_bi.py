from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.presentation.deps import claims_org_id, require_auth
from app.repositories.catalog_repository import CatalogRepository


def build_bi_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/bi", tags=["bi"])

    @router.get("/reports")
    def bi_reports(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> list[dict]:
        payload = CatalogRepository(db).get_dataset(claims_org_id(claims), "bi_reports")
        if not payload:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rapports BI introuvables")
        return payload.get("items") or []

    return router
