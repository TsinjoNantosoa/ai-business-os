from __future__ import annotations

from fastapi import APIRouter, Depends

from app.presentation.deps import require_auth


def build_bi_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/bi", tags=["bi"])

    @router.get("/reports")
    def reports(_claims: dict = Depends(require_auth)) -> list[dict]:
        return [
            {
                "id": "bi-1",
                "name": "KPI Finance — vue générale",
                "description": "Trésorerie, AR/AP, cashflow et alertes.",
                "category": "finance",
                "chartType": "bar",
                "lastRun": "2026-07-02T10:15:00Z",
                "schedule": "daily 06:00",
            },
            {
                "id": "bi-2",
                "name": "Pipeline CRM — performance",
                "description": "Taux de conversion et valeur par étape.",
                "category": "crm",
                "chartType": "line",
                "lastRun": "2026-07-01T18:40:00Z",
            },
        ]

    return router

