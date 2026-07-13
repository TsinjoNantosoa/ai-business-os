from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request, status
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
from app.presentation.schemas import ChatBody
from app.repositories.contact_repository import ContactRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.lead_repository import LeadRepository
from app.services.llm_service import LLMService
from app.services.rag_service import format_rag_context, hits_to_sources, retrieve

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
        "toolsCount": agent["toolsCount"],
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

    return (
        f"{persona}\n"
        "Tu es le copilote AI BOS. Appuie-toi en priorité sur les extraits RAG fournis "
        "(documentation produit Document/*.md et FAQ). Cite les titres de documents quand c'est pertinent.\n"
        "Réponds en français, de façon concise et actionnable.\n"
        f"{context_line}\n\n"
        "Données organisation (temps réel):\n"
        f"{org_context}\n\n"
        "Extraits base de connaissances (RAG):\n"
        f"{rag_block}"
    )


def build_ai_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

    @router.get("/agents")
    def list_agents(
        _claims: dict = Depends(require_permission("ai.agent.use")),
    ) -> list[dict]:
        return [_agent_to_dict(agent) for agent in seed.AI_AGENTS]

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

        async def event_stream() -> AsyncIterator[str]:
            try:
                async for chunk in llm.stream_chat(system_prompt=system_prompt, user_message=body.message):
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done', 'provider': 'openai' if llm.is_live else 'mock', 'sources': sources}, ensure_ascii=False)}\n\n"
            except Exception as exc:
                yield f"data: {json.dumps({'type': 'error', 'message': str(exc)}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return router
