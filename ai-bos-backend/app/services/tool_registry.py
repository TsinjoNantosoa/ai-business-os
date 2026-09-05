"""Lot C / S29 — Tool registry for AI Copilot agents.

In-process registry: each tool has a JSON schema, required permissions,
and a handler that talks to existing repositories (never HTTP-to-self).
"""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.presentation.serializers import (
    contact_to_dict,
    finance_invoice_to_dict,
    lead_to_dict,
    project_to_dict,
    task_to_dict,
)
from app.repositories.contact_repository import ContactRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.lead_repository import LeadRepository
from app.repositories.ops_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.services.business_intelligence import (
    cashflow_intelligence,
    executive_daily_brief,
    sales_risk_intelligence,
)


@dataclass
class ToolContext:
    db: Session
    org_id: str
    user_id: str
    user_name: str
    permissions: set[str]


@dataclass
class ToolResult:
    ok: bool
    data: Any = None
    error: str | None = None


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]
    permissions: list[str]
    handler: Callable[[ToolContext, dict[str, Any]], ToolResult]
    mutating: bool = False
    requires_approval: bool = False
    risk_level: str = "LOW"
    read_only: bool = True
    tenant_scoped: bool = True


def _clamp_limit(value: Any, default: int = 10, max_limit: int = 25) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, min(limit, max_limit))


def _has_permission(ctx: ToolContext, required: list[str]) -> bool:
    if "*" in ctx.permissions:
        return True
    return all(perm in ctx.permissions for perm in required)


def _tool_executive_brief(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    del args
    return ToolResult(ok=True, data=executive_daily_brief(ctx.db, ctx.org_id))


def _tool_cashflow_intelligence(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    del args
    return ToolResult(ok=True, data=cashflow_intelligence(ctx.db, ctx.org_id))


def _tool_sales_risk(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    del args
    return ToolResult(ok=True, data=sales_risk_intelligence(ctx.db, ctx.org_id))


def _tool_search_contacts(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    q = str(args.get("q") or "").strip().lower()
    limit = _clamp_limit(args.get("limit"), default=8)
    contacts = ContactRepository(ctx.db).list_by_org(ctx.org_id)
    if q:
        contacts = [
            c
            for c in contacts
            if q in (c.first_name or "").lower()
            or q in (c.last_name or "").lower()
            or q in (c.email or "").lower()
            or q in (c.company or "").lower()
        ]
    items = [contact_to_dict(c) for c in contacts[:limit]]
    return ToolResult(ok=True, data={"count": len(items), "contacts": items})


def _tool_create_lead(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    title = str(args.get("title") or "").strip()
    company = str(args.get("company") or "").strip()
    contact_name = str(args.get("contactName") or args.get("contact_name") or "").strip()
    if not title or not company or not contact_name:
        return ToolResult(ok=False, error="title, company et contactName sont requis")
    try:
        value = int(args.get("value") or 0)
    except (TypeError, ValueError):
        return ToolResult(ok=False, error="value doit être un entier")
    if value < 0:
        return ToolResult(ok=False, error="value doit être >= 0")

    close_days = 30
    try:
        close_days = max(1, int(args.get("closeInDays") or 30))
    except (TypeError, ValueError):
        pass

    lead = LeadRepository(ctx.db).create(
        org_id=ctx.org_id,
        title=title,
        company=company,
        contact_name=contact_name,
        value=value,
        owner_id=ctx.user_id,
        owner_name=ctx.user_name,
        expected_close_date=datetime.now(timezone.utc) + timedelta(days=close_days),
    )
    ctx.db.commit()
    ctx.db.refresh(lead)
    return ToolResult(ok=True, data=lead_to_dict(lead))


def _tool_list_invoices(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    status_filter = str(args.get("status") or "").strip().lower() or None
    limit = _clamp_limit(args.get("limit"), default=10)
    invoices = InvoiceRepository(ctx.db).list_by_org(ctx.org_id)
    if status_filter:
        invoices = [inv for inv in invoices if inv.status == status_filter]
    items = [finance_invoice_to_dict(inv) for inv in invoices[:limit]]
    total = sum(inv.total_amount for inv in invoices[:limit])
    return ToolResult(
        ok=True,
        data={"count": len(items), "totalAmount": total, "invoices": items},
    )


def _tool_create_task(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    title = str(args.get("title") or "").strip()
    if not title:
        return ToolResult(ok=False, error="title est requis")
    priority = str(args.get("priority") or "medium").strip().lower()
    if priority not in {"urgent", "high", "medium", "low"}:
        priority = "medium"
    due_raw = args.get("dueDate") or args.get("due_date")
    if due_raw:
        due = datetime.fromisoformat(str(due_raw).replace("Z", "+00:00"))
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
    else:
        due = datetime.now(timezone.utc) + timedelta(days=7)

    task = TaskRepository(ctx.db).create(
        org_id=ctx.org_id,
        title=title,
        description=(str(args.get("description") or "").strip() or None),
        priority=priority,
        status="todo",
        assignee_id=ctx.user_id,
        assignee_name=ctx.user_name,
        assignee_avatar_color="bg-primary-100",
        due_date=due,
    )
    ctx.db.commit()
    ctx.db.refresh(task)
    return ToolResult(ok=True, data=task_to_dict(task))


def _tool_list_projects(ctx: ToolContext, args: dict[str, Any]) -> ToolResult:
    limit = _clamp_limit(args.get("limit"), default=8)
    projects = ProjectRepository(ctx.db).list_by_org(ctx.org_id)[:limit]
    items = [project_to_dict(p) for p in projects]
    return ToolResult(ok=True, data={"count": len(items), "projects": items})


# OpenAI requires tool names matching ^[a-zA-Z0-9_-]+$ (no dots).
_TOOLS: list[ToolDefinition] = [
    ToolDefinition(
        name="executive_daily_brief",
        description="Agrège les priorités, risques et opportunités Finance, CRM, Projets, Tâches et Support.",
        parameters={"type": "object", "properties": {}},
        permissions=["dashboard.read"],
        handler=_tool_executive_brief,
    ),
    ToolDefinition(
        name="cashflow_intelligence",
        description="Explique les facteurs de trésorerie à partir des transactions, factures et du pipeline.",
        parameters={"type": "object", "properties": {}},
        permissions=["finance.invoice.read"],
        handler=_tool_cashflow_intelligence,
    ),
    ToolDefinition(
        name="sales_deal_risk",
        description="Score les deals à risque avec des raisons heuristiques explicites.",
        parameters={"type": "object", "properties": {}},
        permissions=["crm.lead.read"],
        handler=_tool_sales_risk,
    ),
    ToolDefinition(
        name="crm_search_contacts",
        description="Recherche des contacts CRM de l'organisation (nom, email, société).",
        parameters={
            "type": "object",
            "properties": {
                "q": {"type": "string", "description": "Texte de recherche (optionnel)"},
                "limit": {"type": "integer", "description": "Nombre max de résultats (défaut 8)"},
            },
        },
        permissions=["crm.contact.read"],
        handler=_tool_search_contacts,
    ),
    ToolDefinition(
        name="crm_create_lead",
        description="Crée un lead commercial dans le pipeline CRM.",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "company": {"type": "string"},
                "contactName": {"type": "string"},
                "value": {"type": "integer", "description": "Valeur estimée en EUR"},
                "closeInDays": {"type": "integer", "description": "Jours avant close estimée"},
            },
            "required": ["title", "company", "contactName", "value"],
        },
        permissions=["crm.lead.write"],
        handler=_tool_create_lead,
        mutating=True,
        requires_approval=True,
        risk_level="MEDIUM",
        read_only=False,
    ),
    ToolDefinition(
        name="finance_list_invoices",
        description="Liste les factures finance (filtrable par statut: draft, sent, paid, overdue).",
        parameters={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "limit": {"type": "integer"},
            },
        },
        permissions=["finance.invoice.read"],
        handler=_tool_list_invoices,
    ),
    ToolDefinition(
        name="tasks_create",
        description="Crée une tâche assignée à l'utilisateur courant.",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "priority": {"type": "string", "enum": ["urgent", "high", "medium", "low"]},
                "dueDate": {"type": "string", "description": "ISO date YYYY-MM-DD"},
            },
            "required": ["title"],
        },
        permissions=["task.write"],
        handler=_tool_create_task,
        mutating=True,
        requires_approval=True,
        risk_level="MEDIUM",
        read_only=False,
    ),
    ToolDefinition(
        name="projects_list",
        description="Liste les projets de l'organisation avec progression et budget.",
        parameters={
            "type": "object",
            "properties": {
                "limit": {"type": "integer"},
            },
        },
        permissions=["project.read"],
        handler=_tool_list_projects,
    ),
]

_REGISTRY: dict[str, ToolDefinition] = {tool.name: tool for tool in _TOOLS}


def list_tools() -> list[ToolDefinition]:
    return list(_TOOLS)


def get_tool(name: str) -> ToolDefinition | None:
    return _REGISTRY.get(name)


def openai_tools_schema() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            },
        }
        for tool in _TOOLS
    ]


def execute_tool(name: str, arguments: dict[str, Any] | None, ctx: ToolContext) -> ToolResult:
    tool = _REGISTRY.get(name)
    if not tool:
        return ToolResult(ok=False, error=f"Outil inconnu: {name}")
    if not _has_permission(ctx, tool.permissions):
        needed = ", ".join(tool.permissions)
        return ToolResult(ok=False, error=f"Permission refusée (requis: {needed})")
    try:
        return tool.handler(ctx, arguments or {})
    except Exception as exc:  # noqa: BLE001 — surfaced to SSE as tool_result
        return ToolResult(ok=False, error=str(exc))


# --- Mock intent detection (CI / no OpenAI key) ---

@dataclass
class PlannedToolCall:
    name: str
    arguments: dict[str, Any]
    call_id: str = field(default_factory=lambda: f"call_{secrets.token_hex(4)}")


def plan_mock_tool_calls(user_message: str) -> list[PlannedToolCall]:
    """Heuristic tool planner used when OpenAI is not configured.

    Collects multiple intents in one pass (S30 multi-step) instead of
    exclusive elif — e.g. « contacts et factures » → 2 tools.
    """
    text = user_message.lower()
    planned: list[PlannedToolCall] = []

    if re.search(r"surveiller aujourd|priorit[eÃé]s? (du jour|aujourd)|daily brief", text):
        planned.append(PlannedToolCall(name="executive_daily_brief", arguments={}))
    if re.search(r"tr[eÃé]sorerie.*(baisser|baisse|risque)|cash.?flow", text):
        planned.append(PlannedToolCall(name="cashflow_intelligence", arguments={}))
    if re.search(r"deals?.*(risque|fermer|cl[oÃô]turer)|risque.*deals?", text):
        planned.append(PlannedToolCall(name="sales_deal_risk", arguments={}))

    if re.search(r"cr[eé]e[rz]?\s+(un\s+)?lead|nouveau lead|create lead", text):
        company = "Client Demo"
        value = 5000.0
        m = re.search(r"chez\s+([A-Za-z0-9 &\-]+)", user_message, re.I)
        if m:
            company = m.group(1).strip()
        else:
            m2 = re.search(
                r"lead\s+([A-Za-z][A-Za-z0-9 &\-]{1,40}?)(?:\s+à|\s+de|\s+pour|\s*$)",
                user_message,
                re.I,
            )
            if m2:
                company = m2.group(1).strip(" .,")
        mv = re.search(r"(\d[\d\s]*[.,]?\d*)\s*€", user_message)
        if not mv:
            mv = re.search(r"(?:à|de|valeur|value)\s+(\d[\d\s]*[.,]?\d*)", user_message, re.I)
        if mv:
            raw = mv.group(1).replace(" ", "").replace(",", ".")
            try:
                value = float(raw)
            except ValueError:
                pass
        planned.append(
            PlannedToolCall(
                name="crm_create_lead",
                arguments={
                    "title": f"Lead {company}",
                    "company": company,
                    "contactName": "Contact Copilot",
                    "value": value,
                },
            )
        )

    if re.search(r"cr[eé]e[rz]?\s+(une\s+)?t[aâ]che|nouvelle t[aâ]che|create task", text):
        title = "Tâche Copilot"
        m = re.search(r"t[aâ]che\s+[«\"]?(.+?)[»\"]?\s*$", user_message, re.I)
        if m:
            title = m.group(1).strip()[:120] or title
        planned.append(
            PlannedToolCall(
                name="tasks_create",
                arguments={"title": title, "priority": "medium"},
            )
        )

    if re.search(r"facture|invoice|impay|overdue", text):
        status = "overdue" if re.search(r"retard|impay|overdue", text) else None
        args: dict[str, Any] = {"limit": 8}
        if status:
            args["status"] = status
        planned.append(PlannedToolCall(name="finance_list_invoices", arguments=args))

    if re.search(r"projet", text):
        planned.append(PlannedToolCall(name="projects_list", arguments={"limit": 8}))

    if re.search(r"contact", text):
        q = ""
        m = re.search(
            r"contact[s]?\s+(?:nomm[eé]s?|appel[eé]s?)\s+[«\"]?([A-Za-zÀ-ÿ\- ]{2,40})",
            user_message,
            re.I,
        )
        if m:
            q = m.group(1).strip()
        planned.append(PlannedToolCall(name="crm_search_contacts", arguments={"q": q, "limit": 8}))

    return planned
