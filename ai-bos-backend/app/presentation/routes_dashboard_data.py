from __future__ import annotations

from fastapi import APIRouter, Depends

from app.data.seed_ops import DEMO_EMPLOYEES, DEMO_FINANCE_OVERVIEW
from app.presentation.deps import require_auth


def build_dashboard_data_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["dashboard-data"])

    @router.get("/finance/overview")
    def finance_overview(_claims: dict = Depends(require_auth)) -> dict:
        return DEMO_FINANCE_OVERVIEW

    @router.get("/hr/employees")
    def employees(_claims: dict = Depends(require_auth)) -> list[dict]:
        return DEMO_EMPLOYEES

    return router
