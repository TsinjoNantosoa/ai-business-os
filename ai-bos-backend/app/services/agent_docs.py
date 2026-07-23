"""S36 — Client-facing agent documentation catalog + guide markdown."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.event_catalog import EVENT_CATALOG
from app.services.tool_registry import list_tools

_REPO_ROOT = Path(__file__).resolve().parents[3]
_GUIDE_PATH = _REPO_ROOT / "Document" / "GUIDE_AGENTS_CLIENT.md"

AGENT_GUIDE_CARDS: list[dict[str, str]] = [
    {
        "id": "ceo",
        "name": "CEO Agent",
        "mission": "Synthèse stratégique, KPIs, priorités direction.",
        "bestFor": "Briefings exécutifs et priorisation",
    },
    {
        "id": "sales",
        "name": "Sales Agent",
        "mission": "Pipeline, deals, relances commerciales.",
        "bestFor": "Qualification leads et suivi CRM",
    },
    {
        "id": "finance",
        "name": "Finance Agent",
        "mission": "Trésorerie, factures, anomalies financières.",
        "bestFor": "Relances factures et overview finance",
    },
    {
        "id": "marketing",
        "name": "Marketing Agent",
        "mission": "Campagnes, acquisition, performance marketing.",
        "bestFor": "Analyse campagnes et messages",
    },
    {
        "id": "hr",
        "name": "HR Agent",
        "mission": "Recrutement, onboarding, demandes RH.",
        "bestFor": "Suivi candidats et process RH",
    },
    {
        "id": "analyst",
        "name": "Data Analyst",
        "mission": "Insights data, tendances, prévisions.",
        "bestFor": "Questions analytiques et forecasts",
    },
]

WORKFLOW_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "tpl-lead-welcome",
        "name": "Bienvenue nouveau lead",
        "description": "Quand un lead est créé : envoyer un email et créer une tâche de suivi.",
        "trigger": "Lead créé",
        "actions": ["Envoyer email", "Créer tâche"],
    },
    {
        "id": "tpl-invoice-overdue",
        "name": "Relance facture en retard",
        "description": "Sur facture overdue : email + notification Slack (in-app).",
        "trigger": "Facture en retard",
        "actions": ["Envoyer email", "Notifier Slack"],
    },
    {
        "id": "tpl-webhook-intake",
        "name": "Webhook → CRM",
        "description": "Réception webhook entrant puis mise à jour CRM / notification.",
        "trigger": "Webhook entrant",
        "actions": ["Mettre à jour CRM", "Notifier Slack"],
    },
    {
        "id": "tpl-order-created",
        "name": "Commande créée",
        "description": "Nouvelle commande sales : tâche ops + email confirmation.",
        "trigger": "Commande créée",
        "actions": ["Créer tâche", "Envoyer email"],
    },
]

QUOTA_TABLE: list[dict[str, Any]] = [
    {"plan": "starter", "aiRpm": 10, "aiTokensLimit": 100_000},
    {"plan": "pro", "aiRpm": 60, "aiTokensLimit": 1_000_000},
    {"plan": "enterprise", "aiRpm": 200, "aiTokensLimit": 2_000_000},
]


def load_client_guide_markdown() -> str:
    if _GUIDE_PATH.is_file():
        return _GUIDE_PATH.read_text(encoding="utf-8")
    return "# Guide agents\n\nDocumentation indisponible sur ce déploiement.\n"


def build_agent_docs_payload() -> dict[str, Any]:
    tools = [
        {
            "name": t.name,
            "description": t.description,
            "permissions": t.permissions,
            "mutating": t.mutating,
            "requiresApproval": t.requires_approval,
            "parameters": t.parameters,
        }
        for t in list_tools()
    ]
    return {
        "version": "1.0",
        "title": "Documentation agents AI BOS",
        "guidePath": "Document/GUIDE_AGENTS_CLIENT.md",
        "sections": [
            {
                "id": "overview",
                "title": "Vue d’ensemble",
                "body": (
                    "Les agents AI BOS combinent Copilot SSE, RAG documentaire, "
                    "outils métier RBAC et workflows event-driven."
                ),
            },
            {
                "id": "hitl",
                "title": "Approbation humaine",
                "body": (
                    "Les outils mutants (création lead / tâche) demandent une validation "
                    "explicite dans le Copilot avant exécution."
                ),
            },
            {
                "id": "observability",
                "title": "Observabilité",
                "body": (
                    "Chaque chat produit une trace (tokens, coût, latence). "
                    "Consultez la page Agents et GET /api/v1/ai/usage/summary."
                ),
            },
            {
                "id": "quotas",
                "title": "Quotas plan",
                "body": (
                    "Les limites RPM et tokens mensuels sont appliquées au Copilot (HTTP 429). "
                    "Voir Paramètres → Facturation."
                ),
            },
        ],
        "agents": AGENT_GUIDE_CARDS,
        "tools": tools,
        "workflowTemplates": WORKFLOW_TEMPLATES,
        "eventCatalog": EVENT_CATALOG,
        "quotas": QUOTA_TABLE,
        "api": {
            "chat": "POST /api/v1/ai/chat",
            "tools": "GET /api/v1/ai/tools",
            "docs": "GET /api/v1/ai/docs",
            "guide": "GET /api/v1/ai/docs/guide",
            "traces": "GET /api/v1/ai/traces",
            "usage": "GET /api/v1/ai/usage/summary",
            "webhooks": "POST /api/v1/webhooks/inbound/{token}",
            "quotas": "GET /api/v1/billing/quotas",
        },
    }
