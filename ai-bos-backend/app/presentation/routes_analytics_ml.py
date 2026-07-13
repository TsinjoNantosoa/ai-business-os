from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.data import seed
from app.presentation.deps import require_auth, require_feature, require_permission


def build_analytics_ml_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["analytics-ml"])

    @router.get("/analytics/kpis")
    def analytics_kpis(_claims: dict = Depends(require_permission("analytics.read"))) -> dict:
        return seed.ANALYTICS_KPIS

    @router.get("/ml/forecast")
    def ml_forecast(
        horizon: str = Query(default="7d"),
        _claims: dict = Depends(require_feature("ml.forecasts")),
    ) -> dict:
        if horizon not in {"7d", "30d", "90d"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="horizon doit être 7d, 30d ou 90d",
            )
        return seed.forecast_data(horizon)

    return router
