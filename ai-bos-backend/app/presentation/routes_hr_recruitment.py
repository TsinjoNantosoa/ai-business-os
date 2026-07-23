from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.presentation.deps import claims_org_id, require_auth, require_permission
from app.presentation.schemas import (
    CandidateCreateBody,
    CandidateUpdateBody,
    JobCreateBody,
    JobUpdateBody,
)
from app.repositories.catalog_repository import (
    CandidateRepository,
    JobOpeningRepository,
    candidate_to_dict,
    job_to_dict,
)
from app.services.audit_service import record_audit

JOB_STATUSES = {"open", "closed", "draft", "on_hold"}
JOB_TYPES = {"full_time", "part_time", "contract", "internship"}
CANDIDATE_STAGES = {"applied", "screening", "interview", "offer", "hired", "rejected"}


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def build_hr_recruitment_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/hr", tags=["hr-recruitment"])

    @router.get("/jobs")
    def jobs(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> list[dict]:
        rows = JobOpeningRepository(db).list_by_org(claims_org_id(claims))
        return [job_to_dict(j) for j in rows]

    @router.post("/jobs", status_code=status.HTTP_201_CREATED)
    def create_job(
        body: JobCreateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("hr.recruitment.write")),
    ) -> dict:
        if body.status not in JOB_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut invalide")
        if body.type not in JOB_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Type invalide")
        job = JobOpeningRepository(db).create(
            claims_org_id(claims),
            title=body.title.strip(),
            department=body.department.strip(),
            status=body.status,
            applicants=0,
            posted_date=body.postedDate or _today(),
            location=body.location.strip(),
            type=body.type,
        )
        record_audit(db, claims, action="CREATE", resource="JobOpening", resource_id=job.id, details=job.title, request=request)
        db.commit()
        db.refresh(job)
        return job_to_dict(job)

    @router.patch("/jobs/{job_id}")
    def update_job(
        job_id: str,
        body: JobUpdateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("hr.recruitment.write")),
    ) -> dict:
        if body.status is not None and body.status not in JOB_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut invalide")
        if body.type is not None and body.type not in JOB_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Type invalide")
        repo = JobOpeningRepository(db)
        job = repo.get_by_id(claims_org_id(claims), job_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offre introuvable")
        repo.update(
            job,
            title=body.title.strip() if body.title else None,
            department=body.department.strip() if body.department else None,
            status=body.status,
            location=body.location.strip() if body.location else None,
            type=body.type,
            applicants=body.applicants,
        )
        record_audit(db, claims, action="UPDATE", resource="JobOpening", resource_id=job.id, details=job.title, request=request)
        db.commit()
        db.refresh(job)
        return job_to_dict(job)

    @router.get("/candidates")
    def candidates(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> list[dict]:
        rows = CandidateRepository(db).list_by_org(claims_org_id(claims))
        return [candidate_to_dict(c) for c in rows]

    @router.post("/candidates", status_code=status.HTTP_201_CREATED)
    def create_candidate(
        body: CandidateCreateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("hr.recruitment.write")),
    ) -> dict:
        if body.stage not in CANDIDATE_STAGES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Étape invalide")
        cand = CandidateRepository(db).create(
            claims_org_id(claims),
            name=body.name.strip(),
            email=body.email.strip().lower(),
            job_id=body.jobId,
            job_title=body.jobTitle,
            stage=body.stage,
            score=body.score,
            avatar_color=body.avatarColor or "bg-primary-100",
            applied_at=body.appliedAt or _today(),
        )
        record_audit(db, claims, action="CREATE", resource="Candidate", resource_id=cand.id, details=cand.email, request=request)
        db.commit()
        db.refresh(cand)
        return candidate_to_dict(cand)

    @router.patch("/candidates/{candidate_id}")
    def update_candidate(
        candidate_id: str,
        body: CandidateUpdateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("hr.recruitment.write")),
    ) -> dict:
        if body.stage is not None and body.stage not in CANDIDATE_STAGES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Étape invalide")
        repo = CandidateRepository(db)
        cand = repo.get_by_id(claims_org_id(claims), candidate_id)
        if not cand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidat introuvable")
        repo.update(
            cand,
            name=body.name.strip() if body.name else None,
            email=body.email.strip().lower() if body.email else None,
            job_id=body.jobId,
            job_title=body.jobTitle,
            stage=body.stage,
            score=body.score,
            avatar_color=body.avatarColor,
        )
        record_audit(db, claims, action="UPDATE", resource="Candidate", resource_id=cand.id, details=cand.email, request=request)
        db.commit()
        db.refresh(cand)
        return candidate_to_dict(cand)

    return router
