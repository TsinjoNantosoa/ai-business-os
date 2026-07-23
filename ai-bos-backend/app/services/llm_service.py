from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from app.core.config import settings


class LLMService:
    """LLM streaming with OpenAI when configured, otherwise deterministic mock."""

    @property
    def is_live(self) -> bool:
        return bool(settings.openai_api_key)

    async def stream_chat(
        self,
        *,
        system_prompt: str,
        user_message: str,
        tool_context: str | None = None,
        force_mock: bool = False,
    ) -> AsyncIterator[str]:
        if settings.openai_api_key and not force_mock:
            try:
                async for chunk in self._stream_openai(system_prompt, user_message, tool_context=tool_context):
                    yield chunk
                return
            except Exception:
                # Bad key / API error → continue with deterministic mock
                pass

        async for chunk in self._stream_mock(user_message, system_prompt, tool_context=tool_context):
            yield chunk

    async def complete_with_tools(
        self,
        *,
        system_prompt: str,
        user_message: str,
        tools: list[dict[str, Any]],
        prior_messages: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Non-streaming turn that may return tool_calls or final content.

        Returns: {"content": str|None, "tool_calls": list[{id,name,arguments}]}
        Falls back to empty tool_calls if OpenAI is unavailable/misconfigured.

        When prior_messages is set (multi-step), it should include the user turn
        and any assistant/tool messages from previous rounds.
        """
        if not settings.openai_api_key:
            return {"content": None, "tool_calls": []}

        try:
            import httpx
        except ImportError as exc:
            raise RuntimeError("httpx requis pour OpenAI (pip install httpx)") from exc

        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        if prior_messages:
            messages.extend(prior_messages)
        else:
            messages.append({"role": "user", "content": user_message})

        payload: dict[str, Any] = {
            "model": settings.openai_model,
            "stream": False,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
        }

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    f"{settings.openai_base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                body = response.json()
        except Exception:
            # Invalid key / quota / network → let caller use mock planner
            return {"content": None, "tool_calls": [], "fallback_mock": True}

        message = body.get("choices", [{}])[0].get("message", {})
        raw_calls = message.get("tool_calls") or []
        tool_calls: list[dict[str, Any]] = []
        for call in raw_calls:
            fn = call.get("function") or {}
            args_raw = fn.get("arguments") or "{}"
            try:
                arguments = json.loads(args_raw) if isinstance(args_raw, str) else (args_raw or {})
            except json.JSONDecodeError:
                arguments = {}
            tool_calls.append(
                {
                    "id": call.get("id") or f"call_{len(tool_calls)}",
                    "name": fn.get("name") or "",
                    "arguments": arguments if isinstance(arguments, dict) else {},
                }
            )
        return {"content": message.get("content"), "tool_calls": tool_calls}

    async def _stream_mock(
        self,
        user_message: str,
        system_prompt: str,
        *,
        tool_context: str | None = None,
    ) -> AsyncIterator[str]:
        response = self._build_mock_response(user_message, system_prompt, tool_context=tool_context)
        tokens = response.split(" ")
        for index, token in enumerate(tokens):
            yield token + (" " if index < len(tokens) - 1 else "")
            await asyncio.sleep(0.02)

    def _build_mock_response(
        self,
        user_message: str,
        system_prompt: str,
        *,
        tool_context: str | None = None,
    ) -> str:
        stats_line = ""
        for line in system_prompt.splitlines():
            if line.startswith("- Contacts actifs:"):
                stats_line = line
                break

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

        tools_block = ""
        if tool_context:
            tools_block = f"\n\n**Résultats outils**\n{tool_context}\n"

        return (
            f"Voici mon analyse concernant « {user_message} » :\n\n"
            f"**Contexte organisation**\n{stats_line or '- Données métier disponibles via AI BOS.'}\n"
            f"{tools_block}\n"
            f"**Documentation pertinente (RAG)**\n{rag_block}\n\n"
            "**Recommandations**\n"
            "1. S'appuyer sur les sources citées et les résultats d'outils ci-dessus\n"
            "2. Prioriser les actions à fort impact sur les 7 prochains jours\n"
            "3. Automatiser le suivi via un workflow si applicable\n\n"
            "Souhaitez-vous un plan d'action détaillé ?"
        )

    async def _stream_openai(
        self,
        system_prompt: str,
        user_message: str,
        *,
        tool_context: str | None = None,
    ) -> AsyncIterator[str]:
        try:
            import httpx
        except ImportError as exc:
            raise RuntimeError("httpx requis pour OpenAI (pip install httpx)") from exc

        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        user_content = user_message
        if tool_context:
            user_content = (
                f"{user_message}\n\n"
                "[Résultats des outils métier déjà exécutés — utilise-les pour répondre]\n"
                f"{tool_context}"
            )
        payload = {
            "model": settings.openai_model,
            "stream": True,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
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
