from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.data import seed
from app.presentation.deps import (
    chatbot_rate_limiter,
    claims_org_id,
    claims_user_id,
    require_permission,
    verify_chatbot_token,
)
from app.presentation.schemas import ApprovalDecisionBody, ChatBody
from app.repositories.ai_pending_action_repository import AiPendingActionRepository
from app.repositories.contact_repository import ContactRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.lead_repository import LeadRepository
from app.repositories.user_repository import UserRepository
from app.services.agent_orchestrator import pending_to_dict, run_chat_orchestration
from app.services.audit_service import record_audit
from app.services.llm_service import LLMService
from app.services.rag_service import format_rag_context, hits_to_sources, retrieve
from app.services.tool_registry import ToolContext, execute_tool, get_tool, list_tools

AGENT_PERSONAS: dict[str, str] = {
    "ceo": "Tu es le CEO Agent : synthèse stratégique, KPIs, priorités direction.",
    "sales": "Tu es le Sales Agent : pipeline, deals, relances commerciales.",
    "finance": "Tu es le Finance Agent : trésorerie, factures, anomalies financières.",
    "marketing": "Tu es le Marketing Agent : campagnes, acquisition, performance marketing.",
    "hr": "Tu es le HR Agent : recrutement, onboarding, demandes RH.",
    "analyst": "Tu es le Data Analyst : insights data, tendances, prévisions.",
}


def _find_agent(agent_id: str | None) -> dict | None:
    if not agent_id:
        return seed.AI_AGENTS[0]
    for agent in seed.AI_AGENTS:
        if agent["id"] == agent_id or agent.get("slug") == agent_id:
            return agent
    return None


def _agent_to_dict(agent: dict) -> dict:
    return {
        "id": agent["id"],
        "slug": agent.get("slug"),
        "name": agent["name"],
        "description": agent["description"],
        "status": agent["status"],
        "category": agent["category"],
        "icon": agent["icon"],
        "toolsCount": len(list_tools()),
        "lastUsed": agent.get("lastUsed"),
        "conversations": agent["conversations"],
    }


def _build_org_context(db: Session, org_id: str) -> str:
    contacts = ContactRepository(db).count_by_org(org_id)
    leads = LeadRepository(db).list_by_org(org_id)
    invoices = InvoiceRepository(db).list_by_org(org_id)
    overdue = [inv for inv in invoices if inv.status == "overdue"]
    pipeline_value = sum(lead.value for lead in leads)
    overdue_amount = sum(inv.total_amount for inv in overdue)
    return (
        f"- Contacts actifs: {contacts}\n"
        f"- Leads en pipeline: {len(leads)} (valeur {pipeline_value:,} EUR)\n"
        f"- Factures en retard: {len(overdue)} (montant {overdue_amount:,} EUR)"
    ).replace(",", " ")


def _build_system_prompt(
    *,
    agent: dict,
    org_context: str,
    ui_context: str | None,
    rag_block: str,
) -> str:
    slug = agent.get("slug") or agent["id"]
    persona = AGENT_PERSONAS.get(slug, f"Tu es {agent['name']}.")
    context_line = f"Contexte UI: {ui_context}" if ui_context else "Contexte UI: Global"
    tool_names = ", ".join(t.name for t in list_tools())

    return (
        f"{persona}\n"
        "Tu es le copilote AI BOS. Appuie-toi en priorité sur les extraits RAG fournis "
        "(documentation produit Document/*.md et FAQ). Cite les titres de documents quand c'est pertinent.\n"
        "Tu peux appeler des outils métier quand l'utilisateur demande des données ou des actions "
        f"({tool_names}). Ne invente pas de résultats d'outils.\n"
        "Les outils d'écriture (création lead/tâche) nécessitent une approbation humaine (HITL).\n"
        "Réponds en français, de façon concise et actionnable.\n"
        f"{context_line}\n\n"
        "Données organisation (temps réel):\n"
        f"{org_context}\n\n"
        "Extraits base de connaissances (RAG):\n"
        f"{rag_block}"
    )


def _permissions_set(claims: dict) -> set[str]:
    return set(claims.get("permissions") or [])


def _user_display_name(db: Session, user_id: str) -> str:
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        return "Utilisateur"
    name = f"{user.first_name} {user.last_name}".strip()
    return name or user.email


def _can_decide_approval(claims: dict, pending_user_id: str) -> bool:
    perms = _permissions_set(claims)
    if "*" in perms or "ai.approval.decide" in perms:
        return True
    # Requester may self-approve while chatting in Copilot
    return claims_user_id(claims) == pending_user_id and "ai.copilot.use" in perms


def build_ai_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

    @router.get("/agents")
    def list_agents(
        _claims: dict = Depends(require_permission("ai.agent.use")),
    ) -> list[dict]:
        return [_agent_to_dict(agent) for agent in seed.AI_AGENTS]

    @router.get("/tools")
    def list_ai_tools(
        _claims: dict = Depends(require_permission("ai.copilot.use")),
    ) -> dict:
        return {
            "items": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "permissions": tool.permissions,
                    "mutating": tool.mutating,
                    "requiresApproval": tool.requires_approval,
                    "parameters": tool.parameters,
                }
                for tool in list_tools()
            ]
        }

    @router.get("/approvals")
    def list_approvals(
        status_filter: str | None = Query(default="pending", alias="status"),
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("ai.copilot.use")),
    ) -> dict:
        org_id = claims_org_id(claims)
        rows = AiPendingActionRepository(db).list_by_org(org_id, status=status_filter)
        return {"items": [pending_to_dict(row) for row in rows]}

    @router.post("/approvals/{approval_id}/decide")
    def decide_approval(
        approval_id: str,
        body: ApprovalDecisionBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("ai.copilot.use")),
    ) -> dict:
        org_id = claims_org_id(claims)
        user_id = claims_user_id(claims)
        repo = AiPendingActionRepository(db)
        row = repo.get_by_id(org_id, approval_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approbation introuvable")
        if row.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Action déjà traitée (status={row.status})",
            )
        if not _can_decide_approval(claims, row.user_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission refusée")

        decision = body.decision.strip().lower()
        now = datetime.now(timezone.utc)
        row.decided_by = user_id
        row.decided_at = now
        row.updated_at = now

        if decision == "reject":
            row.status = "rejected"
            db.commit()
            record_audit(
                db,
                claims,
                action="REJECT",
                resource="AiPendingAction",
                resource_id=row.id,
                details=row.tool_name,
                request=request,
            )
            db.commit()
            return pending_to_dict(row)

        if decision != "approve":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="decision doit être approve ou reject",
            )

        tool_ctx = ToolContext(
            db=db,
            org_id=org_id,
            user_id=row.user_id,
            user_name=_user_display_name(db, row.user_id),
            permissions=_permissions_set(claims),
        )
        # Use decider permissions (not requester) for safer execution gate
        tool_ctx.permissions = _permissions_set(claims)
        tool_ctx.user_id = user_id
        tool_ctx.user_name = _user_display_name(db, user_id)

        result = execute_tool(row.tool_name, row.arguments or {}, tool_ctx)
        tool_def = get_tool(row.tool_name)
        if result.ok:
            row.status = "executed"
            row.result = result.data if isinstance(result.data, dict) else {"data": result.data}
            row.error = None
            if tool_def and tool_def.mutating:
                record_audit(
                    db,
                    claims,
                    action="CREATE",
                    resource=f"AiTool:{row.tool_name}",
                    resource_id=row.id,
                    details=json.dumps(row.arguments, ensure_ascii=False)[:500],
                    request=request,
                )
        else:
            row.status = "failed"
            row.error = result.error
            row.result = None
        db.commit()
        return pending_to_dict(row)

    @router.post("/chat")
    async def chat_stream(
        body: ChatBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("ai.copilot.use")),
        _chatbot_token: None = Depends(verify_chatbot_token),
    ) -> StreamingResponse:
        rate_key = claims_user_id(claims) or (request.client.host if request.client else "anonymous")
        retry_after = chatbot_rate_limiter.check(rate_key)
        if retry_after is not None:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Trop de requêtes IA. Réessayez dans {retry_after}s.",
                headers={"Retry-After": str(retry_after)},
            )

        agent = _find_agent(body.agentId)
        if not agent:
            agent = seed.AI_AGENTS[0]

        org_id = claims_org_id(claims)
        user_id = claims_user_id(claims)
        hits = retrieve(db, org_id=org_id, query=body.message, limit=5)
        rag_block = format_rag_context(hits)
        sources = hits_to_sources(hits)
        system_prompt = _build_system_prompt(
            agent=agent,
            org_context=_build_org_context(db, org_id),
            ui_context=body.context,
            rag_block=rag_block,
        )
        llm = LLMService()
        tool_ctx = ToolContext(
            db=db,
            org_id=org_id,
            user_id=user_id,
            user_name=_user_display_name(db, user_id),
            permissions=_permissions_set(claims),
        )

        async def event_stream() -> AsyncIterator[str]:
            try:
                async for event in run_chat_orchestration(
                    db=db,
                    claims=claims,
                    request=request,
                    llm=llm,
                    tool_ctx=tool_ctx,
                    system_prompt=system_prompt,
                    user_message=body.message,
                    conversation_id=body.conversationId,
                    agent_id=agent.get("id") or body.agentId,
                    sources=sources,
                ):
                    yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"
            except Exception as exc:
                yield f"data: {json.dumps({'type': 'error', 'message': str(exc)}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return router
