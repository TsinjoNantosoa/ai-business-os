from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator
from typing import Any

from app.core.config import settings
from app.services.ai_observability import estimate_tokens, price_usd


def _format_tool_context_for_user(tool_context: str) -> str | None:
    """Turn orchestrator tool summary lines into a short French answer (no raw JSON dump)."""
    lines_out: list[str] = []
    for raw in tool_context.splitlines():
        line = raw.strip()
        if not line.startswith("- "):
            continue
        # "- name: OK → {json}" or "- name: ERREUR → ..."
        try:
            head, payload = line[2:].split(":", 1)
        except ValueError:
            continue
        name = head.strip()
        payload = payload.strip()
        if payload.startswith("ERREUR"):
            lines_out.append(f"**{name}** : échec — {payload.replace('ERREUR →', '').strip()}")
            continue
        if "OK →" not in payload:
            lines_out.append(f"**{name}** : {payload}")
            continue
        json_part = payload.split("OK →", 1)[1].strip()
        try:
            data = json.loads(json_part.rstrip("…"))
        except json.JSONDecodeError:
            # Truncated JSON from summarize_tool_results — still avoid dumping it
            if name == "crm_search_contacts":
                lines_out.append("Voici une sélection de contacts CRM (résultats outil).")
            elif name == "projects_list":
                lines_out.append("Voici les projets récupérés via l'outil projets.")
            elif name == "finance_list_invoices":
                lines_out.append("Voici les factures récupérées.")
            else:
                lines_out.append(f"**{name}** : résultats disponibles.")
            continue

        if name == "executive_daily_brief":
            lines_out.append("### Priorités du jour")
            for item in data.get("topPriorities", [])[:5]:
                lines_out.append(f"- **{item.get('title')}** — {item.get('why')} · Source: `{item.get('source')}`")
            lines_out.append("\n### Risques")
            for item in data.get("risks", [])[:5]:
                lines_out.append(f"- **{item.get('title')}** — {item.get('why')} · Source: `{item.get('source')}`")
            lines_out.append("\n### Opportunités")
            for item in data.get("opportunities", [])[:5]:
                lines_out.append(f"- **{item.get('title')}** — {item.get('why')} · Source: `{item.get('source')}`")
        elif name == "cashflow_intelligence":
            situation = data.get("currentSituation") or {}
            risk = data.get("risk") or {}
            lines_out.append(f"### Situation actuelle\nFlux net observé: **{situation.get('observedNetFlow', 0)} {situation.get('currency', 'EUR')}**.")
            lines_out.append(f"\n### Risque\n**{str(risk.get('level', 'unknown')).upper()}** — {risk.get('why', '')}")
            lines_out.append("\n### Facteurs")
            for item in data.get("drivers", []):
                lines_out.append(f"- {item.get('label')}: {item.get('amount')} · Source: `{item.get('source')}`")
            lines_out.append(f"\n_Limite: {data.get('limitations', '')}_")
        elif name == "sales_deal_risk":
            lines_out.append("### Deals à risque")
            for deal in data.get("deals", [])[:8]:
                reasons = "; ".join(deal.get("reasons") or [])
                lines_out.append(f"- **{deal.get('title')}** ({deal.get('company')}) — risque **{deal.get('riskScore')}%** · {reasons} · Source: `{deal.get('source')}`")
            lines_out.append(f"\n_Méthode: {data.get('method', '')}. {data.get('limitations', '')}_")
        elif name == "crm_search_contacts":
            contacts = data.get("contacts") or []
            lines_out.append(f"Voici {len(contacts)} contact(s) CRM :\n")
            for c in contacts[:8]:
                lines_out.append(
                    f"- **{c.get('firstName', '')} {c.get('lastName', '')}** — "
                    f"{c.get('company') or '—'} · {c.get('email') or '—'}"
                    + (f" · {c.get('phone')}" if c.get("phone") else "")
                )
        elif name == "projects_list":
            projects = data.get("projects") or []
            active = [p for p in projects if (p.get("status") or "").lower() == "active"]
            show = active or projects
            lines_out.append(f"Voici {len(show)} projet(s) :\n")
            for p in show[:8]:
                lines_out.append(
                    f"- **{p.get('name')}** — {p.get('status')} · progrès {p.get('progress', 0)}% "
                    f"· budget {p.get('budget', 0)} {('EUR')}"
                )
        elif name == "finance_list_invoices":
            invoices = data.get("invoices") or data.get("items") or []
            if isinstance(data, dict) and not invoices and "count" in data:
                # handler may nest differently
                invoices = data.get("invoices") or []
            lines_out.append(f"Voici {len(invoices)} facture(s) :\n")
            for inv in invoices[:8]:
                lines_out.append(
                    f"- **{inv.get('invoiceNumber') or inv.get('id')}** — "
                    f"{inv.get('clientName') or '—'} · {inv.get('status')} · "
                    f"{inv.get('totalAmount', inv.get('amount', '—'))}"
                )
        elif name == "crm_create_lead":
            lead = data if isinstance(data, dict) else {}
            lines_out.append(
                f"Lead créé : **{lead.get('title') or 'OK'}** "
                f"({lead.get('company') or ''}) — valeur {lead.get('value', '—')}."
            )
        elif name == "tasks_create":
            task = data if isinstance(data, dict) else {}
            lines_out.append(f"Tâche créée : **{task.get('title') or 'OK'}**.")
        else:
            lines_out.append(f"**{name}** : opération réussie.")

    if not lines_out:
        return None
    return "\n".join(lines_out).strip() + "\n\nSouhaitez-vous affiner le filtre ou lancer une action ?"


class LLMService:
    """LLM streaming with OpenAI when configured, otherwise deterministic mock."""

    def __init__(self) -> None:
        self.last_usage: dict[str, Any] | None = None

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
        self.last_usage = None
        if settings.openai_api_key and not force_mock:
            produced = False
            try:
                async for chunk in self._stream_openai(system_prompt, user_message, tool_context=tool_context):
                    produced = True
                    yield chunk
                return
            except Exception:
                # Never append mock after a partial/full OpenAI answer (was duplicating replies).
                if produced:
                    return

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
        """Returns content, tool_calls, and usage {input_tokens, output_tokens, cost_usd, latency_ms, provider, model}."""
        empty_usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
            "latency_ms": 0,
            "provider": "mock",
            "model": "mock",
        }
        if not settings.openai_api_key:
            return {"content": None, "tool_calls": [], "usage": empty_usage}

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

        started = time.perf_counter()
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
            return {"content": None, "tool_calls": [], "fallback_mock": True, "usage": empty_usage}

        latency_ms = max(1, int((time.perf_counter() - started) * 1000))
        usage_raw = body.get("usage") or {}
        in_tok = int(usage_raw.get("prompt_tokens") or 0)
        out_tok = int(usage_raw.get("completion_tokens") or 0)
        if in_tok == 0 and out_tok == 0:
            in_tok = estimate_tokens(json.dumps(messages, ensure_ascii=False))
            out_tok = estimate_tokens(str(body.get("choices", [{}])[0].get("message", {}).get("content") or ""))
        model = body.get("model") or settings.openai_model
        usage = {
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "cost_usd": price_usd(model, in_tok, out_tok),
            "latency_ms": latency_ms,
            "provider": "openai",
            "model": model,
        }
        self.last_usage = usage

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
        return {"content": message.get("content"), "tool_calls": tool_calls, "usage": usage}

    async def _stream_mock(
        self,
        user_message: str,
        system_prompt: str,
        *,
        tool_context: str | None = None,
    ) -> AsyncIterator[str]:
        started = time.perf_counter()
        response = self._build_mock_response(user_message, system_prompt, tool_context=tool_context)
        tokens = response.split(" ")
        for index, token in enumerate(tokens):
            yield token + (" " if index < len(tokens) - 1 else "")
            await asyncio.sleep(0.02)
        in_tok = estimate_tokens(system_prompt + user_message + (tool_context or ""))
        out_tok = estimate_tokens(response)
        self.last_usage = {
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "cost_usd": 0.0,
            "latency_ms": max(1, int((time.perf_counter() - started) * 1000)),
            "provider": "mock",
            "model": "mock",
        }

    def _build_mock_response(
        self,
        user_message: str,
        system_prompt: str,
        *,
        tool_context: str | None = None,
    ) -> str:
        # Prefer a clean tool-based answer when tools already ran (no JSON dump / generic RAG fluff).
        if tool_context and tool_context.strip():
            formatted = _format_tool_context_for_user(tool_context)
            if formatted:
                return formatted

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
                if len(rag_lines) >= 4:
                    break
        rag_block = "\n".join(rag_lines) if rag_lines else "- Consultez la documentation AI BOS."

        return (
            f"Voici mon analyse concernant « {user_message} » :\n\n"
            f"**Contexte organisation**\n{stats_line or '- Données métier disponibles via AI BOS.'}\n\n"
            f"**Documentation pertinente (RAG)**\n{rag_block}\n\n"
            "**Recommandations**\n"
            "1. S'appuyer sur les sources citées\n"
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
            "stream_options": {"include_usage": True},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        }

        started = time.perf_counter()
        collected = ""
        usage_raw: dict[str, Any] = {}
        model = settings.openai_model

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
                    if parsed.get("model"):
                        model = parsed["model"]
                    if parsed.get("usage"):
                        usage_raw = parsed["usage"]
                    delta = parsed.get("choices", [{}])[0].get("delta", {}).get("content")
                    if delta:
                        collected += delta
                        yield delta

        try:
            in_tok = int(usage_raw.get("prompt_tokens") or 0)
            out_tok = int(usage_raw.get("completion_tokens") or 0)
            if in_tok == 0 and out_tok == 0:
                in_tok = estimate_tokens(system_prompt + user_content)
                out_tok = estimate_tokens(collected)
            self.last_usage = {
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "cost_usd": price_usd(model, in_tok, out_tok),
                "latency_ms": max(1, int((time.perf_counter() - started) * 1000)),
                "provider": "openai",
                "model": model,
            }
        except Exception:
            # Never fail the stream after content was already yielded.
            self.last_usage = None
