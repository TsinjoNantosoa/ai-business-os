"""Hybrid RAG retrieval (lexical + local embeddings) — README_09."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.repositories.kb_repository import KbRepository
from app.services.rag_embedder import cosine, embed_text, tokenize


@dataclass(frozen=True)
class RagHit:
    chunk_id: str
    document_id: str
    document_title: str
    source_uri: str | None
    content: str
    score: float
    excerpt: str
    topics: list[str]


def _lexical_score(query_tokens: set[str], content: str, topics: list[str], title: str) -> float:
    if not query_tokens:
        return 0.0
    content_tokens = set(tokenize(content))
    title_tokens = set(tokenize(title))
    topic_set = {t.lower() for t in topics}
    score = 0.0
    for token in query_tokens:
        if token in title_tokens:
            score += 3.0
        if token in topic_set:
            score += 2.5
        if token in content_tokens:
            score += 1.0
        # substring boost for compound queries
        if token in content.lower():
            score += 0.25
    return score


def retrieve(
    db: Session,
    *,
    org_id: str,
    query: str,
    limit: int = 5,
) -> list[RagHit]:
    repo = KbRepository(db)
    chunks = repo.list_chunks_for_search(org_id)
    if not chunks:
        return []

    query_tokens = set(tokenize(query))
    query_vec = embed_text(query)
    docs = repo.get_documents_map([c.document_id for c in chunks])

    scored: list[tuple[float, RagHit]] = []
    for chunk in chunks:
        doc = docs.get(chunk.document_id)
        title = doc.title if doc else "Document"
        topics = repo.loads(chunk.topics_json, []) or []
        lex = _lexical_score(query_tokens, chunk.content, topics, title)
        emb = repo.loads(chunk.embedding_json, []) or []
        sem = cosine(query_vec, emb) if emb else 0.0
        # Hybrid: lexical dominates for exact product terms; semantic helps paraphrases
        score = (0.65 * lex) + (0.35 * (sem * 10.0))
        if score <= 0:
            continue
        excerpt = chunk.content.strip().replace("\n", " ")
        if len(excerpt) > 280:
            excerpt = excerpt[:277] + "..."
        hit = RagHit(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            document_title=title,
            source_uri=doc.source_uri if doc else None,
            content=chunk.content,
            score=round(score, 4),
            excerpt=excerpt,
            topics=list(topics),
        )
        scored.append((score, hit))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [hit for _, hit in scored[:limit]]


def format_rag_context(hits: list[RagHit]) -> str:
    if not hits:
        return "Aucun extrait pertinent dans la base de connaissances."
    lines: list[str] = []
    for index, hit in enumerate(hits, start=1):
        lines.append(
            f"{index}. [{hit.document_title}] (score={hit.score})\n"
            f"   {hit.excerpt}"
        )
    return "\n".join(lines)


def hits_to_sources(hits: list[RagHit]) -> list[dict]:
    return [
        {
            "documentId": hit.document_id,
            "documentTitle": hit.document_title,
            "chunkId": hit.chunk_id,
            "relevanceScore": hit.score,
            "excerpt": hit.excerpt,
            "sourceUri": hit.source_uri,
        }
        for hit in hits
    ]


# Back-compat helpers used by older call sites
def search_knowledge(query: str, limit: int = 3) -> list[dict]:
    """Deprecated in-memory fallback — prefer retrieve(db, ...)."""
    from app.data import seed

    query_tokens = set(tokenize(query))
    if not query_tokens:
        return seed.KNOWLEDGE_ARTICLES[:limit]
    scored: list[tuple[float, dict]] = []
    for article in seed.KNOWLEDGE_ARTICLES:
        haystack = f"{article['title']} {article.get('category', '')} {article.get('excerpt', '')}".lower()
        score = sum(2 if token in article["title"].lower() else 1 for token in query_tokens if token in haystack)
        if score > 0:
            scored.append((float(score), article))
    scored.sort(key=lambda item: item[0], reverse=True)
    if not scored:
        return seed.KNOWLEDGE_ARTICLES[:limit]
    return [article for _, article in scored[:limit]]
