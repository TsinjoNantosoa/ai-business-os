"""Local embedder + chunker for RAG MVP (no external vector DB required)."""
from __future__ import annotations

import hashlib
import math
import re
import logging
from collections import Counter

from app.core.config import settings


EMBED_DIM = 256
_TOKEN_RE = re.compile(r"[a-zàâäéèêëïîôùûüç0-9_]{3,}", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "")]


def chunk_markdown(text: str, *, max_chars: int = 900, overlap: int = 120) -> list[dict]:
    """Split markdown by headings then pack into overlapping windows."""
    text = (text or "").replace("\r\n", "\n").strip()
    if not text:
        return []

    sections: list[tuple[str, str]] = []
    current_heading = ""
    current_body: list[str] = []
    for line in text.split("\n"):
        if line.startswith("#"):
            if current_body:
                sections.append((current_heading, "\n".join(current_body).strip()))
            current_heading = line.lstrip("#").strip()
            current_body = [line]
        else:
            current_body.append(line)
    if current_body:
        sections.append((current_heading, "\n".join(current_body).strip()))

    chunks: list[dict] = []
    for heading, body in sections:
        if not body:
            continue
        if len(body) <= max_chars:
            chunks.append({"heading": heading, "content": body})
            continue
        start = 0
        while start < len(body):
            end = min(len(body), start + max_chars)
            piece = body[start:end].strip()
            if piece:
                chunks.append({"heading": heading, "content": piece})
            if end >= len(body):
                break
            start = max(0, end - overlap)
    return chunks


def _embed_local_hash(text: str, dim: int = EMBED_DIM) -> list[float]:
    """Deterministic hashing-trick TF embedding (cosine-friendly, offline)."""
    tokens = tokenize(text)
    if not tokens:
        return [0.0] * dim
    counts = Counter(tokens)
    vec = [0.0] * dim
    for token, count in counts.items():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "big") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        # log TF
        vec[idx] += sign * (1.0 + math.log(count))
    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def embedding_provider_name() -> str:
    if settings.embedding_provider == "openai" and settings.openai_api_key:
        return "openai"
    return "local_hash"


def embed_text(text: str, dim: int = EMBED_DIM) -> list[float]:
    """Embed through the configured provider, with deterministic local fallback."""
    if embedding_provider_name() == "openai":
        try:
            import httpx

            response = httpx.post(
                f"{settings.openai_base_url}/embeddings",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={"model": settings.openai_embedding_model, "input": text[:30_000]},
                timeout=30.0,
            )
            response.raise_for_status()
            vector = response.json()["data"][0]["embedding"]
            return [float(value) for value in vector]
        except Exception as exc:
            logging.getLogger("aibos.rag").warning("embedding_provider_fallback provider=openai error=%s", type(exc).__name__)
    return _embed_local_hash(text, dim)


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b))
