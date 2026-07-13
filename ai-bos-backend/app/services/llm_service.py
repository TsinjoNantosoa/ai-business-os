from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from app.core.config import settings


class LLMService:
    """LLM streaming with OpenAI when configured, otherwise deterministic mock."""

    @property
    def is_live(self) -> bool:
        return bool(settings.openai_api_key)

    async def stream_chat(self, *, system_prompt: str, user_message: str) -> AsyncIterator[str]:
        if settings.openai_api_key:
            async for chunk in self._stream_openai(system_prompt, user_message):
                yield chunk
            return

        async for chunk in self._stream_mock(user_message, system_prompt):
            yield chunk

    async def _stream_mock(self, user_message: str, system_prompt: str) -> AsyncIterator[str]:
        response = self._build_mock_response(user_message, system_prompt)
        tokens = response.split(" ")
        for index, token in enumerate(tokens):
            yield token + (" " if index < len(tokens) - 1 else "")
            await asyncio.sleep(0.02)

    def _build_mock_response(self, user_message: str, system_prompt: str) -> str:
        stats_line = ""
        for line in system_prompt.splitlines():
            if line.startswith("- Contacts actifs:"):
                stats_line = line
                break

        # Prefer first numbered RAG excerpts from system prompt
        rag_lines: list[str] = []
        capture = False
        for line in system_prompt.splitlines():
            if "Extraits base de connaissances" in line:
                capture = True
                continue
            if capture:
                if not line.strip():
                    if rag_lines:
                        break
                    continue
                rag_lines.append(line.strip())
                if len(rag_lines) >= 6:
                    break
        rag_block = "\n".join(rag_lines) if rag_lines else "- Consultez la documentation AI BOS (Document/*.md)."

        return (
            f"Voici mon analyse concernant « {user_message} » :\n\n"
            f"**Contexte organisation**\n{stats_line or '- Données métier disponibles via AI BOS.'}\n\n"
            f"**Documentation pertinente (RAG)**\n{rag_block}\n\n"
            "**Recommandations**\n"
            "1. S'appuyer sur les sources citées ci-dessus (README produit)\n"
            "2. Prioriser les actions à fort impact sur les 7 prochains jours\n"
            "3. Automatiser le suivi via un workflow si applicable\n\n"
            "Souhaitez-vous un plan d'action détaillé ?"
        )

    async def _stream_openai(self, system_prompt: str, user_message: str) -> AsyncIterator[str]:
        try:
            import httpx
        except ImportError as exc:
            raise RuntimeError("httpx requis pour OpenAI (pip install httpx)") from exc

        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.openai_model,
            "stream": True,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            async with client.stream(
                "POST",
                f"{settings.openai_base_url}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[6:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        parsed = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    delta = parsed.get("choices", [{}])[0].get("delta", {}).get("content")
                    if delta:
                        yield delta
