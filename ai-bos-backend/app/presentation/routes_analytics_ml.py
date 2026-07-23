from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.presentation.deps import claims_org_id, require_feature, require_permission
from app.repositories.catalog_repository import CatalogRepository


def build_analytics_ml_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["analytics-ml"])

    @router.get("/analytics/kpis")
    def analytics_kpis(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("analytics.read")),
    ) -> dict:
        payload = CatalogRepository(db).get_dataset(claims_org_id(claims), "analytics_kpis")
        if not payload:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analytics introuvable")
        return payload

    @router.get("/ml/forecast")
    def ml_forecast(
        horizon: str = Query(default="7d"),
        db: Session = Depends(get_db),
        claims: dict = Depends(require_feature("ml.forecasts")),
    ) -> dict:
        if horizon not in {"7d", "30d", "90d"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="horizon doit être 7d, 30d ou 90d",
            )
        payload = CatalogRepository(db).get_dataset(claims_org_id(claims), f"forecast_{horizon}")
        if not payload:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prévision introuvable")
        return payload

    return router
