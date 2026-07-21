from __future__ import annotations

from fastapi import APIRouter, Depends

from app.data.seed_ops import DEMO_CAMPAIGNS, DEMO_SALES_ORDERS
from app.presentation.deps import require_auth


def build_sales_marketing_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["sales-marketing"])

    @router.get("/sales/orders")
    def orders(_claims: dict = Depends(require_auth)) -> list[dict]:
        return DEMO_SALES_ORDERS

    @router.get("/marketing/campaigns")
    def campaigns(_claims: dict = Depends(require_auth)) -> list[dict]:
        return DEMO_CAMPAIGNS

    return router
