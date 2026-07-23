"""Lot D / S30–S31 — Multi-step tool orchestration with HITL pause."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.repositories.ai_pending_action_repository import AiPendingActionRepository
from app.services.ai_observability import AiObservabilityRepository
from app.services.audit_service import record_audit
from app.services.llm_service import LLMService
from app.services.tool_registry import (
    ToolContext,
    execute_tool,
    get_tool,
    openai_tools_schema,
    plan_mock_tool_calls,
)

MAX_TOOL_ROUNDS = 3


def _approval_message(name: str, arguments: dict[str, Any] | Any) -> str:
    args = arguments if isinstance(arguments, dict) else {}
    if name == "crm_create_lead":
        company = args.get("company") or "ce client"
        value = args.get("value")
        value_txt = f" à {value:g} €" if isinstance(value, (int, float)) else ""
        return (
            f"La création d'un lead pour {company}{value_txt} nécessite une approbation humaine. "
            "Validez ou refusez pour continuer."
        )
    return (
        f"Action sensible « {name} » en attente d'approbation. "
        "Validez ou refusez pour continuer."
    )


def summarize_tool_results(results: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for item in results:
        name = item["name"]
        if item["ok"]:
            payload = json.dumps(item["result"], ensure_ascii=False, default=str)
            if len(payload) > 4000:
                payload = payload[:4000] + "…"
            lines.append(f"- {name}: OK → {payload}")
        else:
            lines.append(f"- {name}: ERREUR → {item.get('error')}")
    return "\n".join(lines) if lines else ""


def pending_to_dict(row: Any) -> dict[str, Any]:
    return {
        "id": row.id,
        "toolName": row.tool_name,
        "arguments": row.arguments,
        "callId": row.call_id,
        "status": row.status,
        "conversationId": row.conversation_id,
        "agentId": row.agent_id,
        "userMessage": row.user_message,
        "result": row.result,
        "error": row.error,
        "createdAt": row.created_at.isoformat() if row.created_at else None,
        "decidedAt": row.decided_at.isoformat() if row.decided_at else None,
        "decidedBy": row.decided_by,
    }


async def run_chat_orchestration(
    *,
    db: Session,
    claims: dict,
    request: Request,
    llm: LLMService,
    tool_ctx: ToolContext,
    system_prompt: str,
    user_message: str,
    conversation_id: str | None,
    agent_id: str | None,
    sources: list[dict[str, Any]],
) -> AsyncIterator[dict[str, Any]]:
    """Yield SSE payloads (without the `data: ` prefix)."""
    executed: list[dict[str, Any]] = []
    used_live_llm = False
    pending_repo = AiPendingActionRepository(db)
    obs = AiObservabilityRepository(db)
    correlation_id = request.headers.get("X-Correlation-ID")
    trace = obs.start_trace(
        org_id=tool_ctx.org_id,
        user_id=tool_ctx.user_id,
        agent_id=agent_id,
        conversation_id=conversation_id,
        correlation_id=correlation_id,
        source="chat",
    )
    db.commit()

    prior_messages: list[dict[str, Any]] = [{"role": "user", "content": user_message}]
    tools_schema = openai_tools_schema()

    def _record_usage(purpose: str, usage: dict[str, Any] | None) -> None:
        if not usage:
            return
        obs.record_llm_call(
            trace=trace,
            purpose=purpose,
            provider=str(usage.get("provider") or "mock"),
            model=str(usage.get("model") or "mock"),
            input_tokens=int(usage.get("input_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or 0),
            latency_ms=int(usage.get("latency_ms") or 0),
        )
        db.commit()

    for round_idx in range(MAX_TOOL_ROUNDS):
        planned_calls: list[dict[str, Any]] = []

        if llm.is_live:
            planned = await llm.complete_with_tools(
                system_prompt=system_prompt,
                user_message=user_message,
                tools=tools_schema,
                prior_messages=prior_messages if round_idx > 0 else None,
            )
            _record_usage("plan_tools", planned.get("usage"))
            if planned.get("fallback_mock"):
                if round_idx == 0:
                    planned_calls = [
                        {
                            "id": call.call_id,
                            "name": call.name,
                            "arguments": call.arguments,
                        }
                        for call in plan_mock_tool_calls(user_message)
                    ]
                else:
                    planned_calls = []
            else:
                used_live_llm = True
                planned_calls = list(planned.get("tool_calls") or [])
                content = planned.get("content")
                if content and not planned_calls:
                    # LLM answered in prose but user asked for a gated mutation — force tool plan (HITL).
                    forced = [
                        {
                            "id": call.call_id,
                            "name": call.name,
                            "arguments": call.arguments,
                        }
                        for call in plan_mock_tool_calls(user_message)
                        if (tdef := get_tool(call.name)) and tdef.requires_approval
                    ]
                    if forced:
                        planned_calls = forced
                    else:
                        break
        else:
            if round_idx == 0:
                planned_calls = [
                    {
                        "id": call.call_id,
                        "name": call.name,
                        "arguments": call.arguments,
                    }
                    for call in plan_mock_tool_calls(user_message)
                ]
            else:
                planned_calls = []

        if not planned_calls:
            break

        yield {
            "type": "step",
            "round": round_idx + 1,
            "toolCount": len(planned_calls),
            "traceId": trace.id,
        }

        assistant_tool_msg: dict[str, Any] | None = None
        if used_live_llm:
            assistant_tool_msg = {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": call.get("id") or f"call_{i}",
                        "type": "function",
                        "function": {
                            "name": call.get("name") or "",
                            "arguments": json.dumps(call.get("arguments") or {}, ensure_ascii=False),
                        },
                    }
                    for i, call in enumerate(planned_calls)
                ],
            }
            prior_messages.append(assistant_tool_msg)

        paused_for_approval = False
        for call in planned_calls:
            name = call.get("name") or ""
            arguments = call.get("arguments") or {}
            call_id = call.get("id") or name
            tool_def = get_tool(name)

            yield {
                "type": "tool_call",
                "name": name,
                "arguments": arguments,
                "callId": call_id,
                "round": round_idx + 1,
            }

            if tool_def and tool_def.requires_approval:
                row = pending_repo.create(
                    org_id=tool_ctx.org_id,
                    user_id=tool_ctx.user_id,
                    tool_name=name,
                    arguments=arguments if isinstance(arguments, dict) else {},
                    call_id=call_id,
                    user_message=user_message,
                    conversation_id=conversation_id,
                    agent_id=agent_id,
                )
                obs.finish_trace(
                    trace,
                    status="waiting_approval",
                    tools_used=[item["name"] for item in executed],
                )
                db.commit()
                yield {
                    "type": "approval_required",
                    "approvalId": row.id,
                    "name": name,
                    "arguments": arguments,
                    "callId": call_id,
                    "message": _approval_message(name, arguments),
                }
                yield {
                    "type": "done",
                    "provider": "openai" if used_live_llm else "mock",
                    "sources": sources,
                    "toolsUsed": [item["name"] for item in executed],
                    "status": "waiting_approval",
                    "approvalId": row.id,
                    "traceId": trace.id,
                    "inputTokens": trace.input_tokens,
                    "outputTokens": trace.output_tokens,
                    "costUsd": trace.cost_usd,
                    "latencyMs": trace.latency_ms,
                }
                paused_for_approval = True
                break

            result = execute_tool(name, arguments, tool_ctx)
            if result.ok and tool_def and tool_def.mutating:
                record_audit(
                    db,
                    claims,
                    action="CREATE",
                    resource=f"AiTool:{name}",
                    resource_id=None,
                    details=json.dumps(arguments, ensure_ascii=False)[:500],
                    request=request,
                )
                db.commit()

            event = {
                "type": "tool_result",
                "name": name,
                "callId": call_id,
                "ok": result.ok,
                "result": result.data if result.ok else None,
                "error": result.error,
                "round": round_idx + 1,
            }
            executed.append(
                {
                    "name": name,
                    "ok": result.ok,
                    "result": result.data,
                    "error": result.error,
                }
            )
            yield event

            if used_live_llm:
                prior_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": json.dumps(
                            {"ok": result.ok, "result": result.data, "error": result.error},
                            ensure_ascii=False,
                            default=str,
                        ),
                    }
                )

        if paused_for_approval:
            return

        if not used_live_llm:
            break

    tool_context = summarize_tool_results(executed)
    provider = "openai" if used_live_llm else "mock"
    async for chunk in llm.stream_chat(
        system_prompt=system_prompt,
        user_message=user_message,
        tool_context=tool_context or None,
        force_mock=not used_live_llm,
    ):
        yield {"type": "chunk", "content": chunk}

    _record_usage("stream_reply", llm.last_usage)
    obs.finish_trace(
        trace,
        status="completed",
        tools_used=[item["name"] for item in executed],
    )
    db.commit()

    yield {
        "type": "done",
        "provider": provider,
        "sources": sources,
        "toolsUsed": [item["name"] for item in executed],
        "status": "completed",
        "traceId": trace.id,
        "inputTokens": trace.input_tokens,
        "outputTokens": trace.output_tokens,
        "costUsd": trace.cost_usd,
        "latencyMs": trace.latency_ms,
    }
