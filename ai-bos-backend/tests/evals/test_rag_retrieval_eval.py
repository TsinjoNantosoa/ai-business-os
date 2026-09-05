from __future__ import annotations

import pytest

from app.core.database import SessionLocal
from app.repositories.kb_repository import KbRepository
from app.services.rag_ingest import ingest_product_documents
from app.services.rag_service import hits_to_sources, retrieve


QUESTIONS = [
    "Comment fonctionne OAuth ?",
    "Comment les JWT et refresh tokens sont-ils gérés ?",
    "Quelle stratégie multi-tenant utilise PostgreSQL RLS ?",
    "Comment exécuter un workflow ?",
    "Comment Stripe gère les abonnements ?",
    "Comment fonctionne la recherche RAG ?",
    "Quels rôles et permissions RBAC existent ?",
    "Comment déployer la base PostgreSQL ?",
    "Quelle est la stratégie de sauvegarde ?",
    "Comment observer les appels IA ?",
]


@pytest.mark.parametrize("question", QUESTIONS)
def test_rag_retrieval_and_citations_are_database_grounded(question: str) -> None:
    with SessionLocal() as db:
        ingest_product_documents(db)
        hits = retrieve(db, org_id="org-1", query=question, limit=5)
        assert hits, question
        documents = KbRepository(db).get_documents_map([hit.document_id for hit in hits])
        sources = hits_to_sources(hits)
        assert len(sources) == len(hits)
        for source in sources:
            document = documents[source["documentId"]]
            assert source["documentTitle"] == document.title
            assert source["chunkId"]
            assert source["relevanceScore"] > 0
