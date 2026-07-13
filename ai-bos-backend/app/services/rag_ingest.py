"""Ingest Document/*.md + seed articles into kb_* tables (README_09)."""
from __future__ import annotations

import hashlib
import logging
import re
import secrets
from pathlib import Path

from sqlalchemy.orm import Session

from app.data import seed
from app.models.kb import KbChunk, KbDocument
from app.repositories.kb_repository import KbRepository
from app.services.rag_embedder import chunk_markdown, embed_text, tokenize

logger = logging.getLogger("aibos.rag")

PLATFORM_ORG = "platform"


def resolve_document_dir() -> Path:
    """Locate ai-bos/Document next to ai-bos-backend."""
    backend_root = Path(__file__).resolve().parents[2]
    candidates = [
        backend_root.parent / "Document",
        backend_root / "Document",
        Path(__file__).resolve().parents[3] / "Document",
    ]
    for path in candidates:
        if path.is_dir():
            return path
    return candidates[0]


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _topics_from_name(name: str, heading: str, content: str) -> list[str]:
    base = re.sub(r"[_\-.]+", " ", name.replace(".md", ""))
    topics = set(tokenize(f"{base} {heading}"))
    # Boost common product terms present in chunk
    for token in tokenize(content[:400]):
        if token in {
            "rag",
            "oauth",
            "jwt",
            "tenant",
            "multi",
            "rbac",
            "billing",
            "stripe",
            "workflow",
            "agent",
            "postgres",
            "fastapi",
            "react",
            "gdpr",
            "backup",
            "staging",
            "sse",
            "notification",
            "crm",
            "facture",
            "invoice",
        }:
            topics.add(token)
    return sorted(topics)[:40]


def _upsert_markdown_document(
    repo: KbRepository,
    *,
    org_id: str,
    title: str,
    source_type: str,
    source_uri: str | None,
    text: str,
    language: str = "fr",
    extra_meta: dict | None = None,
) -> int:
    digest = _content_hash(text)
    existing = repo.get_document_by_hash(org_id, digest)
    if existing and existing.status == "indexed":
        return 0

    if existing:
        repo.delete_document_cascade(existing.id)

    doc_id = f"kbd-{secrets.token_hex(8)}"
    now = repo.now()
    doc = KbDocument(
        id=doc_id,
        org_id=org_id,
        title=title,
        source_type=source_type,
        source_uri=source_uri,
        mime_type="text/markdown",
        content_hash=digest,
        status="indexed",
        language=language,
        metadata_json=repo.dumps(extra_meta or {}),
        created_at=now,
        updated_at=now,
    )
    repo.add_document(doc)

    pieces = chunk_markdown(text)
    for index, piece in enumerate(pieces):
        content = piece["content"]
        heading = piece.get("heading") or title
        topics = _topics_from_name(title, heading, content)
        embedding = embed_text(f"{title}\n{heading}\n{content}")
        chunk = KbChunk(
            id=f"kbc-{secrets.token_hex(8)}",
            org_id=org_id,
            document_id=doc_id,
            chunk_index=index,
            content=content,
            token_count=len(tokenize(content)),
            topics_json=repo.dumps(topics),
            embedding_json=repo.dumps(embedding),
            metadata_json=repo.dumps({"heading": heading, "title": title}),
            created_at=now,
        )
        repo.add_chunk(chunk)
    return len(pieces)


def ingest_product_documents(db: Session, *, force: bool = False) -> dict:
    repo = KbRepository(db)
    doc_dir = resolve_document_dir()
    if not doc_dir.is_dir():
        logger.warning("document_dir_missing path=%s", doc_dir)
        return {"indexedDocs": 0, "chunks": 0, "path": str(doc_dir), "error": "Document dir missing"}

    if force:
        repo.wipe_source_type(PLATFORM_ORG, "product_docs")

    indexed_docs = 0
    chunks = 0
    for path in sorted(doc_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        n = _upsert_markdown_document(
            repo,
            org_id=PLATFORM_ORG,
            title=path.stem,
            source_type="product_docs",
            source_uri=str(path),
            text=text,
            extra_meta={"filename": path.name},
        )
        if n:
            indexed_docs += 1
            chunks += n

    db.commit()
    return {"indexedDocs": indexed_docs, "chunks": chunks, "path": str(doc_dir)}


def ingest_seed_articles(db: Session, org_id: str = "org-1") -> dict:
    repo = KbRepository(db)
    indexed = 0
    chunks = 0
    for article in seed.KNOWLEDGE_ARTICLES:
        body = (
            f"# {article['title']}\n\n"
            f"Catégorie: {article.get('category', '')}\n\n"
            f"{article.get('excerpt', '')}\n\n"
            f"{article.get('content', '')}"
        )
        n = _upsert_markdown_document(
            repo,
            org_id=org_id,
            title=article["title"],
            source_type="seed",
            source_uri=article["id"],
            text=body,
            extra_meta={"category": article.get("category"), "seedId": article["id"]},
        )
        if n:
            indexed += 1
            chunks += n
    db.commit()
    return {"indexedDocs": indexed, "chunks": chunks}


def ensure_rag_index(db: Session) -> None:
    """Bootstrap hook: index product docs + seed FAQ if KB empty."""
    repo = KbRepository(db)
    if repo.count_chunks() > 0:
        return
    ingest_product_documents(db)
    ingest_seed_articles(db, org_id="org-1")
    ingest_seed_articles(db, org_id="org-2")
