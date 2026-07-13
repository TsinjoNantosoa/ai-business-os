from __future__ import annotations

from fastapi import APIRouter, Depends

from app.data import seed
from app.presentation.deps import require_auth


def build_operations_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["operations"])

    @router.get("/contracts")
    def contracts(_claims: dict = Depends(require_auth)) -> list[dict]:
        return seed.CONTRACTS

    @router.get("/inventory/items")
    def inventory_items(_claims: dict = Depends(require_auth)) -> list[dict]:
        return seed.INVENTORY_ITEMS

    return router
