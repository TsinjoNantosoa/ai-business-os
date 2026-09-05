"""Workflow executors with SSRF protection, retries, and explicit AI capabilities."""

from __future__ import annotations

import ipaddress
import logging
import socket
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from urllib.parse import urlparse

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.lead_repository import LeadRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.services.email_service import EmailService
from app.services.notification_service import create_and_publish_notification

logger = logging.getLogger("aibos.workflow_actions")


class ActionResult:
    def __init__(self, action: str, ok: bool, detail: str, *, attempts: int = 1) -> None:
        self.action = action
        self.ok = ok
        self.detail = detail
        self.attempts = attempts

    def as_text(self) -> str:
        mark = "ok" if self.ok else "err"
        return f"{self.action}[{mark}]: {self.detail}"


def _default_recipient(session: Session, org_id: str, context: dict[str, Any]) -> str:
    for key in ("email", "contactEmail", "recipient"):
        value = context.get(key)
        if isinstance(value, str) and "@" in value:
            return value
    users = UserRepository(session).list_by_org(org_id)
    return users[0].email if users else "noreply@aibos.local"


def _owner(session: Session, org_id: str) -> tuple[str, str, str]:
    users = UserRepository(session).list_by_org(org_id)
    if not users:
        return "system", "Workflow", "#6366f1"
    user = users[0]
    return user.id, f"{user.first_name} {user.last_name}".strip() or user.email, "#6366f1"


def execute_send_email(session: Session, *, org_id: str, context: dict[str, Any], workflow_name: str, email_service: EmailService | None) -> ActionResult:
    if email_service is None:
        return ActionResult("Envoyer email", False, "EmailService indisponible")
    recipient = _default_recipient(session, org_id, context)
    try:
        email_service.send(
            recipient=recipient,
            subject=str(context.get("subject") or f"[AI BOS] Workflow « {workflow_name} »"),
            text=str(context.get("message") or f"Workflow « {workflow_name} » déclenché.\n\nContexte: {context}"),
        )
    except Exception as exc:
        logger.warning("workflow_email_failed recipient=%s err=%s", recipient, exc)
        return ActionResult("Envoyer email", False, f"échec email: {exc}")
    return ActionResult("Envoyer email", True, f"envoyé à {recipient}")


def execute_create_task(session: Session, *, org_id: str, context: dict[str, Any], workflow_name: str) -> ActionResult:
    assignee_id, assignee_name, color = _owner(session, org_id)
    title = str(context.get("title") or context.get("leadTitle") or f"Suite workflow: {workflow_name}")[:200]
    task = TaskRepository(session).create(
        org_id=org_id,
        title=title,
        description=f"Créée automatiquement par le workflow « {workflow_name} ».\nPayload: {context}",
        priority="medium",
        status="todo",
        assignee_id=assignee_id,
        assignee_name=assignee_name,
        assignee_avatar_color=color,
        due_date=datetime.now(timezone.utc) + timedelta(days=3),
        tags=["workflow"],
    )
    return ActionResult("Créer tâche", True, f"task={task.id}")


def execute_notify(session: Session, *, org_id: str, context: dict[str, Any], workflow_name: str) -> ActionResult:
    create_and_publish_notification(
        session,
        org_id=org_id,
        type="info",
        title=f"Workflow: {workflow_name}",
        message=str(context.get("message") or context.get("title") or "Action workflow exécutée"),
        link="/app/workflows",
    )
    return ActionResult("Notifier", True, "notification in-app publiée")


def execute_update_crm(session: Session, *, org_id: str, context: dict[str, Any], workflow_name: str) -> ActionResult:
    del workflow_name
    lead_id = context.get("leadId")
    if not lead_id:
        return ActionResult("Mettre à jour CRM", True, "aucun leadId — no-op")
    repo = LeadRepository(session)
    lead = repo.get_by_id(org_id, str(lead_id))
    if not lead:
        return ActionResult("Mettre à jour CRM", False, f"lead {lead_id} introuvable")
    if lead.stage == "new":
        repo.update_stage(lead, "qualified")
    return ActionResult("Mettre à jour CRM", True, f"lead={lead.id} stage={lead.stage}")


def execute_run_ai_agent(session: Session, *, org_id: str, context: dict[str, Any], workflow_name: str) -> ActionResult:
    del workflow_name
    from app.services.tool_registry import ToolContext, execute_tool, get_tool, plan_mock_tool_calls

    prompt = str(context.get("goal") or context.get("prompt") or "").strip()
    allowed = {str(name) for name in (context.get("allowedTools") or context.get("allowed_tools") or [])}
    if not prompt or not allowed:
        return ActionResult("Run AI agent", False, "goal et allowed_tools explicites requis")
    max_steps = max(1, min(int(context.get("maxSteps") or context.get("max_steps") or 3), 5))
    tool_ctx = ToolContext(
        db=session,
        org_id=org_id,
        user_id=str(context.get("userId") or "workflow-system"),
        user_name=str(context.get("userName") or "Workflow AI"),
        permissions=set(context.get("permissions") or []),
    )
    executed: list[str] = []
    for planned in plan_mock_tool_calls(prompt)[:max_steps]:
        definition = get_tool(planned.name)
        if planned.name not in allowed:
            continue
        if definition and definition.requires_approval:
            return ActionResult("Run AI agent", False, f"approval_required:{planned.name}")
        result = execute_tool(planned.name, planned.arguments, tool_ctx)
        if not result.ok:
            return ActionResult("Run AI agent", False, f"{planned.name}: {result.error}")
        executed.append(planned.name)
    return ActionResult("Run AI agent", True, f"tools={','.join(executed) or 'none'}")


def validate_outbound_url(raw_url: str) -> str:
    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("URL HTTP(S) absolue requise")
    hostname = parsed.hostname.lower().rstrip(".")
    if hostname in settings.workflow_http_allowlist:
        return raw_url
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise ValueError("Hôte local interdit")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))}
    except socket.gaierror as exc:
        raise ValueError("Hôte introuvable") from exc
    for raw_ip in addresses:
        ip = ipaddress.ip_address(raw_ip)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
            raise ValueError("Adresse réseau privée ou réservée interdite")
    return raw_url


def execute_call_api(session: Session, *, org_id: str, context: dict[str, Any], workflow_name: str) -> ActionResult:
    del session, org_id, workflow_name
    try:
        url = validate_outbound_url(str(context.get("url") or ""))
    except ValueError as exc:
        return ActionResult("Call API", False, str(exc))
    method = str(context.get("method") or "POST").upper()
    if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
        return ActionResult("Call API", False, "méthode HTTP interdite")
    timeout = max(1.0, min(float(context.get("timeout") or 10), 30.0))
    max_attempts = max(1, min(int(context.get("maxAttempts") or 3), 5))
    last_error = ""
    for attempt in range(1, max_attempts + 1):
        try:
            with httpx.Client(timeout=timeout, follow_redirects=False) as client:
                response = client.request(
                    method,
                    url,
                    headers={str(k): str(v) for k, v in (context.get("headers") or {}).items()},
                    params=context.get("query") if isinstance(context.get("query"), dict) else None,
                    json=context.get("json") if isinstance(context.get("json"), (dict, list)) else None,
                )
            if response.status_code == 429 or response.status_code >= 500:
                last_error = f"HTTP {response.status_code}"
                if attempt < max_attempts:
                    time.sleep(min(0.1 * 2 ** (attempt - 1), 0.5))
                    continue
            if response.status_code >= 400:
                return ActionResult("Call API", False, f"HTTP {response.status_code} (non retryable)", attempts=attempt)
            return ActionResult("Call API", True, f"HTTP {response.status_code}: {response.text[:2000]}", attempts=attempt)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            last_error = type(exc).__name__
            if attempt < max_attempts:
                time.sleep(min(0.1 * 2 ** (attempt - 1), 0.5))
                continue
    return ActionResult("Call API", False, f"échec après {max_attempts} tentative(s): {last_error}", attempts=max_attempts)


ACTION_HANDLERS: dict[str, Callable[..., ActionResult]] = {
    "Envoyer email": execute_send_email,
    "Créer tâche": execute_create_task,
    "Créer tâches": execute_create_task,
    "Assigner mentor": execute_create_task,
    "Notifier Slack": execute_notify,
    "Notifier manager": execute_notify,
    "Notifier finance": execute_notify,
    "Notifier calendrier": execute_notify,
    "Notifier procurement": execute_notify,
    "Créer facture": execute_notify,
    "Créer PO": execute_notify,
    "Mettre à jour CRM": execute_update_crm,
    "Run AI agent": execute_run_ai_agent,
    "Call API": execute_call_api,
}


def run_actions(session: Session, *, org_id: str, actions: list[str], context: dict[str, Any] | None, workflow_name: str, email_service: EmailService | None) -> list[ActionResult]:
    ctx = context or {}
    results: list[ActionResult] = []
    for action in actions:
        handler = ACTION_HANDLERS.get(action)
        if not handler:
            results.append(ActionResult(action, False, "action inconnue"))
            continue
        try:
            kwargs: dict[str, Any] = {"session": session, "org_id": org_id, "context": ctx, "workflow_name": workflow_name}
            if action == "Envoyer email":
                kwargs["email_service"] = email_service
            results.append(handler(**kwargs))
        except Exception as exc:
            logger.exception("workflow_action_failed action=%s", action)
            results.append(ActionResult(action, False, str(exc)))
    return results
