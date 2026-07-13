from __future__ import annotations

import re

from app.data import seed


def _tokenize(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-zàâäéèêëïîôùûüç0-9]{3,}", text.lower())}


def search_knowledge(query: str, limit: int = 3) -> list[dict]:
    query_tokens = _tokenize(query)
    if not query_tokens:
        return seed.KNOWLEDGE_ARTICLES[:limit]

    scored: list[tuple[int, dict]] = []
    for article in seed.KNOWLEDGE_ARTICLES:
        haystack = f"{article['title']} {article.get('category', '')} {article.get('excerpt', '')}".lower()
        score = sum(2 if token in article["title"].lower() else 1 for token in query_tokens if token in haystack)
        if score > 0:
            scored.append((score, article))

    scored.sort(key=lambda item: item[0], reverse=True)
    if not scored:
        return seed.KNOWLEDGE_ARTICLES[:limit]
    return [article for _, article in scored[:limit]]


def format_rag_context(articles: list[dict]) -> str:
    if not articles:
        return "Aucun article pertinent dans la base de connaissances."
    lines = []
    for article in articles:
        lines.append(f"- [{article['category']}] {article['title']}: {article.get('excerpt', '')}")
    return "\n".join(lines)
