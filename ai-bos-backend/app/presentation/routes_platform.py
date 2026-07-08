from __future__ import annotations

from fastapi import APIRouter, Depends

from app.presentation.deps import require_auth


def build_platform_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/platform", tags=["platform"])

    @router.get("/organizations")
    def organizations(_claims: dict = Depends(require_auth)) -> list[dict]:
        return [
            {
                "id": "org-demo-1",
                "name": "AI BOS Demo Org",
                "plan": "starter",
                "currency": "EUR",
                "timezone": "UTC",
                "locale": "fr",
            }
        ]

    @router.get("/notifications")
    def notifications(_claims: dict = Depends(require_auth)) -> list[dict]:
        return []

    return router

