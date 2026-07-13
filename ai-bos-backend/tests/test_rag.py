from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import SessionLocal
from app.main import app
from app.services.rag_ingest import ensure_rag_index, ingest_product_documents, resolve_document_dir
from app.services.rag_service import retrieve

client = TestClient(app)


def login(email: str = "ceo@demo.aibos.io") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "demo1234"})
    assert res.status_code == 200
    return res.json()["token"]


def auth_headers(email: str = "ceo@demo.aibos.io") -> dict[str, str]:
    headers = {"Authorization": f"Bearer {login(email)}"}
    if settings.chatbot_api_token:
        headers["X-Chatbot-Token"] = settings.chatbot_api_token
    return headers


def test_document_corpus_exists() -> None:
    path = resolve_document_dir()
    assert path.is_dir(), f"Document dir missing: {path}"
    assert (path / "README_09_RAG.md").exists()
    assert (path / "README_18_MultiTenant.md").exists()


def test_rag_index_bootstrapped() -> None:
    # Lifespan already indexed; re-ensure is no-op if chunks exist
    with SessionLocal() as session:
        ensure_rag_index(session)
        stats = client.get("/api/v1/knowledge/stats", headers=auth_headers()).json()
    assert stats["chunkCount"] > 50
    assert stats["documentCount"] >= 20


def test_rag_retrieves_rag_readme() -> None:
    with SessionLocal() as session:
        hits = retrieve(session, org_id="org-1", query="pipeline RAG embeddings chunking pgvector", limit=5)
    assert hits, "expected RAG hits"
    titles = " ".join(h.document_title for h in hits).lower()
    assert "rag" in titles or any("rag" in h.excerpt.lower() for h in hits)


def test_rag_retrieves_multitenant_readme() -> None:
    with SessionLocal() as session:
        hits = retrieve(session, org_id="org-1", query="isolation multi-tenant organization_id RLS", limit=5)
    assert hits
    joined = " ".join(f"{h.document_title} {h.excerpt}" for h in hits).lower()
    assert "tenant" in joined or "multi" in joined or "organisation" in joined or "organization" in joined


def test_rag_retrieves_auth_readme() -> None:
    with SessionLocal() as session:
        hits = retrieve(session, org_id="org-1", query="JWT access token refresh authentication", limit=5)
    assert hits
    joined = " ".join(f"{h.document_title} {h.excerpt}" for h in hits).lower()
    assert any(token in joined for token in ("jwt", "auth", "token", "refresh", "login"))


def test_knowledge_search_api() -> None:
    res = client.get("/api/v1/knowledge/search", headers=auth_headers(), params={"q": "feature flags admin"})
    assert res.status_code == 200
    body = res.json()
    assert body["query"]
    assert isinstance(body["items"], list)
    assert len(body["items"]) >= 1
    assert body["items"][0]["documentTitle"]
    assert body["items"][0]["excerpt"]


def test_tenant_isolation_on_seed_chunks() -> None:
    """Org-2 must not see org-1-only seed docs; platform docs remain shared."""
    with SessionLocal() as session:
        hits_org2 = retrieve(session, org_id="org-2", query="importer contacts csv seed-only-unlikely", limit=20)
        # Platform product docs may match weakly; ensure no org-1 exclusive seed leakage by checking org filter in SQL path
        from app.repositories.kb_repository import KbRepository

        chunks = KbRepository(session).list_chunks_for_search("org-2")
        assert all(c.org_id in {"org-2", "platform"} for c in chunks)
        assert hits_org2 is not None


def test_chat_sse_includes_rag_sources() -> None:
    with client.stream(
        "POST",
        "/api/v1/ai/chat",
        headers=auth_headers(),
        json={
            "message": "Explique le module RAG AI BOS selon la documentation",
            "agentId": "ceo",
            "context": "Copilot",
        },
    ) as response:
        assert response.status_code == 200
        text = ""
        sources = None
        for line in response.iter_lines():
            if not line.startswith("data: "):
                continue
            payload = json.loads(line[6:])
            if payload.get("type") == "chunk":
                text += payload.get("content") or ""
            if payload.get("type") == "done":
                sources = payload.get("sources")
        assert text.strip()
        assert sources is not None
        assert len(sources) >= 1
        assert sources[0]["documentTitle"]
        # Mock response should echo RAG documentation block
        assert "RAG" in text or "Documentation" in text or "README" in text or "base de connaissances" in text.lower()


def test_reindex_owner() -> None:
    # Force product reindex should succeed for owner
    res = client.post("/api/v1/knowledge/reindex", headers=auth_headers())
    assert res.status_code == 200, res.text
    body = res.json()
    assert "product" in body
    # After force, at least some docs re-indexed or already present
    with SessionLocal() as session:
        result = ingest_product_documents(session, force=False)
        assert result["path"]
