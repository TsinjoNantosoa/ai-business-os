"""S34 — pricing + persistence for AI traces / LLM calls."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import metrics
from app.core.config import settings
from app.models.ai_observability import AiLlmCall, AiTrace

# USD per 1M tokens (approximate public list prices)
_MODEL_PRICES: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-3.5-turbo": (0.50, 1.50),
}


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    # Rough heuristic: ~4 chars / token
    return max(1, len(text) // 4)


def price_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    key = (model or "").lower()
    rates = _MODEL_PRICES.get(key)
    if not rates:
        for name, pair in _MODEL_PRICES.items():
            if name in key:
                rates = pair
                break
    if not rates:
        rates = (0.15, 0.60)  # default mini-tier
    inp, out = rates
    return round((input_tokens * inp + output_tokens * out) / 1_000_000, 6)


class AiObservabilityRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def start_trace(
        self,
        *,
        org_id: str,
        user_id: str | None,
        agent_id: str | None,
        conversation_id: str | None,
        correlation_id: str | None,
        source: str = "chat",
    ) -> AiTrace:
        trace = AiTrace(
            id=f"tr-{secrets.token_hex(8)}",
            org_id=org_id,
            user_id=user_id,
            agent_id=agent_id,
            conversation_id=conversation_id,
            correlation_id=correlation_id,
            status="running",
            provider="mock",
            model=settings.openai_model if settings.openai_api_key else "mock",
            tools_used=[],
            source=source,
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(trace)
        self._session.flush()
        return trace

    def record_llm_call(
        self,
        *,
        trace: AiTrace,
        purpose: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
    ) -> AiLlmCall:
        cost = price_usd(model, input_tokens, output_tokens)
        call = AiLlmCall(
            id=f"llc-{secrets.token_hex(8)}",
            org_id=trace.org_id,
            trace_id=trace.id,
            user_id=trace.user_id,
            agent_id=trace.agent_id,
            conversation_id=trace.conversation_id,
            provider=provider,
            model=model,
            purpose=purpose,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(call)
        trace.input_tokens = int(trace.input_tokens or 0) + input_tokens
        trace.output_tokens = int(trace.output_tokens or 0) + output_tokens
        trace.cost_usd = round(float(trace.cost_usd or 0) + cost, 6)
        trace.latency_ms = int(trace.latency_ms or 0) + latency_ms
        trace.provider = provider
        trace.model = model
        metrics.inc("ai_llm_calls")
        metrics.inc("ai_llm_tokens", input_tokens + output_tokens)
        self._session.flush()
        return call

    def finish_trace(
        self,
        trace: AiTrace,
        *,
        status: str,
        tools_used: list[str] | None = None,
        error_message: str | None = None,
    ) -> AiTrace:
        trace.status = status
        if tools_used is not None:
            trace.tools_used = tools_used
        if error_message:
            trace.error_message = error_message[:1000]
        trace.finished_at = datetime.now(timezone.utc)
        self._session.flush()
        return trace

    def list_traces(self, org_id: str, *, agent_id: str | None = None, limit: int = 50) -> list[AiTrace]:
        stmt = select(AiTrace).where(AiTrace.org_id == org_id)
        if agent_id:
            stmt = stmt.where(AiTrace.agent_id == agent_id)
        stmt = stmt.order_by(AiTrace.created_at.desc()).limit(limit)
        return list(self._session.scalars(stmt).all())

    def get_trace(self, org_id: str, trace_id: str) -> AiTrace | None:
        stmt = select(AiTrace).where(AiTrace.org_id == org_id, AiTrace.id == trace_id)
        return self._session.scalars(stmt).first()

    def list_calls(self, org_id: str, trace_id: str) -> list[AiLlmCall]:
        stmt = (
            select(AiLlmCall)
            .where(AiLlmCall.org_id == org_id, AiLlmCall.trace_id == trace_id)
            .order_by(AiLlmCall.created_at.asc())
        )
        return list(self._session.scalars(stmt).all())

    def usage_summary(self, org_id: str, *, days: int = 30) -> dict[str, Any]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        traces = list(
            self._session.scalars(
                select(AiTrace).where(AiTrace.org_id == org_id, AiTrace.created_at >= since)
            ).all()
        )
        by_agent: dict[str, dict[str, Any]] = {}
        by_day: dict[str, dict[str, Any]] = {}
        total_in = total_out = 0
        total_cost = 0.0
        for t in traces:
            total_in += int(t.input_tokens or 0)
            total_out += int(t.output_tokens or 0)
            total_cost += float(t.cost_usd or 0)
            aid = t.agent_id or "unknown"
            bucket = by_agent.setdefault(
                aid, {"agentId": aid, "traces": 0, "inputTokens": 0, "outputTokens": 0, "costUsd": 0.0}
            )
            bucket["traces"] += 1
            bucket["inputTokens"] += int(t.input_tokens or 0)
            bucket["outputTokens"] += int(t.output_tokens or 0)
            bucket["costUsd"] = round(bucket["costUsd"] + float(t.cost_usd or 0), 6)
            day = t.created_at.date().isoformat()
            day_b = by_day.setdefault(
                day, {"date": day, "traces": 0, "tokens": 0, "costUsd": 0.0}
            )
            day_b["traces"] += 1
            day_b["tokens"] += int(t.input_tokens or 0) + int(t.output_tokens or 0)
            day_b["costUsd"] = round(day_b["costUsd"] + float(t.cost_usd or 0), 6)

        return {
            "periodDays": days,
            "traceCount": len(traces),
            "totalInputTokens": total_in,
            "totalOutputTokens": total_out,
            "totalTokens": total_in + total_out,
            "totalCostUsd": round(total_cost, 6),
            "byAgent": sorted(by_agent.values(), key=lambda x: x["costUsd"], reverse=True),
            "byDay": sorted(by_day.values(), key=lambda x: x["date"]),
        }


def trace_to_dict(trace: AiTrace, calls: list[AiLlmCall] | None = None) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": trace.id,
        "orgId": trace.org_id,
        "userId": trace.user_id,
        "agentId": trace.agent_id,
        "conversationId": trace.conversation_id,
        "correlationId": trace.correlation_id,
        "status": trace.status,
        "provider": trace.provider,
        "model": trace.model,
        "inputTokens": trace.input_tokens,
        "outputTokens": trace.output_tokens,
        "costUsd": trace.cost_usd,
        "latencyMs": trace.latency_ms,
        "toolsUsed": trace.tools_used or [],
        "source": trace.source,
        "errorMessage": trace.error_message,
        "createdAt": trace.created_at.isoformat() if trace.created_at else None,
        "finishedAt": trace.finished_at.isoformat() if trace.finished_at else None,
    }
    if calls is not None:
        data["llmCalls"] = [
            {
                "id": c.id,
                "purpose": c.purpose,
                "provider": c.provider,
                "model": c.model,
                "inputTokens": c.input_tokens,
                "outputTokens": c.output_tokens,
                "costUsd": c.cost_usd,
                "latencyMs": c.latency_ms,
                "createdAt": c.created_at.isoformat() if c.created_at else None,
            }
            for c in calls
        ]
    return data
