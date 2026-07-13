from __future__ import annotations

from fastapi import APIRouter, Depends

from app.data import seed
from app.presentation.deps import require_auth


def build_hr_recruitment_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/hr", tags=["hr"])

    @router.get("/jobs")
    def job_openings(_claims: dict = Depends(require_auth)) -> list[dict]:
        return seed.JOB_OPENINGS

    @router.get("/candidates")
    def candidates(_claims: dict = Depends(require_auth)) -> list[dict]:
        return seed.CANDIDATES

    return router
