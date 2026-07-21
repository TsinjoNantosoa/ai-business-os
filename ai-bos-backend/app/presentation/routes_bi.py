from __future__ import annotations

from fastapi import APIRouter, Depends

from app.data.seed_ops import DEMO_BI_REPORTS
from app.presentation.deps import require_auth


def build_bi_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/bi", tags=["bi"])

    @router.get("/reports")
    def reports(_claims: dict = Depends(require_auth)) -> list[dict]:
        return DEMO_BI_REPORTS

    return router
