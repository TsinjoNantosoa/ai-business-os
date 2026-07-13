from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.data import seed
from app.presentation.deps import claims_org_id, require_auth, require_permission
from app.repositories.kb_repository import KbRepository
from app.services.rag_ingest import ingest_product_documents, ingest_seed_articles
from app.services.rag_service import hits_to_sources, retrieve


def build_knowledge_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])

    @router.get("/articles")
    def knowledge_articles(_claims: dict = Depends(require_auth)) -> list[dict]:
        return seed.KNOWLEDGE_ARTICLES

    @router.get("/search")
    def knowledge_search(
        q: str = Query(..., min_length=2),
        limit: int = Query(5, ge=1, le=20),
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> dict:
        org_id = claims_org_id(claims)
        hits = retrieve(db, org_id=org_id, query=q, limit=limit)
        return {"query": q, "items": hits_to_sources(hits)}

    @router.get("/stats")
    def knowledge_stats(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> dict:
        org_id = claims_org_id(claims)
        repo = KbRepository(db)
        return {
            "chunkCount": repo.count_chunks(org_id),
            "documentCount": len(repo.list_documents(org_id)),
        }

    @router.post("/reindex")
    def knowledge_reindex(
        db: Session = Depends(get_db),
        _claims: dict = Depends(require_permission("admin.audit")),
    ) -> dict:
        product = ingest_product_documents(db, force=True)
        seed1 = ingest_seed_articles(db, org_id="org-1")
        seed2 = ingest_seed_articles(db, org_id="org-2")
        return {"product": product, "seedOrg1": seed1, "seedOrg2": seed2}

    return router
