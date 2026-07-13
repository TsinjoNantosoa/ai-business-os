from __future__ import annotations

from fastapi import APIRouter, Depends

from app.data import seed
from app.presentation.deps import require_auth


def build_procurement_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/procurement", tags=["procurement"])

    @router.get("/suppliers")
    def suppliers(_claims: dict = Depends(require_auth)) -> list[dict]:
        return seed.SUPPLIERS

    @router.get("/purchase-orders")
    def purchase_orders(_claims: dict = Depends(require_auth)) -> list[dict]:
        return seed.PURCHASE_ORDERS

    return router
