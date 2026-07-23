"""Lot G — real workflow action executors (email, task, notify, CRM, API)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.repositories.lead_repository import LeadRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.services.email_service import EmailService
from app.services.notification_service import create_and_publish_notification

logger = logging.getLogger("aibos.workflow_actions")


class ActionResult:
    def __init__(self, action: str, ok: bool, detail: str) -> None:
        self.action = action
        self.ok = ok
        self.detail = detail

    def as_text(self) -> str:
        mark = "ok" if self.ok else "err"
        return f"{self.action}[{mark}]: {self.detail}"


def _default_recipient(session: Session, org_id: str, context: dict[str, Any]) -> str:
    for key in ("email", "contactEmail", "recipient"):
        val = context.get(key)
        if isinstance(val, str) and "@" in val:
            return val
    users = UserRepository(session).list_by_org(org_id)
    if users:
        return users[0].email
    return "noreply@aibos.local"


def _owner(session: Session, org_id: str) -> tuple[str, str, str]:
    users = UserRepository(session).list_by_org(org_id)
    if not users:
        return "system", "Workflow", "#6366f1"
    u = users[0]
    name = f"{u.first_name} {u.last_name}".strip() or u.email
    return u.id, name, "#6366f1"


def execute_envoyer_email(
    session: Session,
    *,
    org_id: str,
    context: dict[str, Any],
    email_service: EmailService | None,
    workflow_name: str,
) -> ActionResult:
    if email_service is None:
        return ActionResult("Envoyer email", False, "EmailService indisponible")
    recipient = _default_recipient(session, org_id, context)
    subject = f"[AI BOS] Workflow « {workflow_name} »"
    text = (
        f"Le workflow « {workflow_name} » a été déclenché.\n\n"
        f"Contexte: {context}\n"
    )
    try:
        email_service.send(recipient=recipient, subject=subject, text=text)
    except Exception as exc:
        # Soft-fail: keep workflow chain going (SMTP outages must not block events)
        logger.warning("workflow_email_failed recipient=%s err=%s", recipient, exc)
        return ActionResult("Envoyer email", False, f"échec SMTP: {exc}")
    return ActionResult("Envoyer email", True, f"envoyé à {recipient}")


def execute_creer_tache(
    session: Session,
    *,
    org_id: str,
    context: dict[str, Any],
    workflow_name: str,
) -> ActionResult:
    assignee_id, assignee_name, color = _owner(session, org_id)
    title = context.get("title") or context.get("leadTitle") or f"Suite workflow: {workflow_name}"
    if isinstance(title, str) and len(title) > 200:
        title = title[:200]
    desc = f"Créée automatiquement par le workflow « {workflow_name} ».\nPayload: {context}"
    due = datetime.now(timezone.utc) + timedelta(days=3)
    task = TaskRepository(session).create(
        org_id=org_id,
        title=str(title),
        description=desc,
        priority="medium",
        status="todo",
        assignee_id=assignee_id,
        assignee_name=assignee_name,
        assignee_avatar_color=color,
        due_date=due,
        tags=["workflow"],
    )
    return ActionResult("Créer tâche", True, f"task={task.id}")


def execute_notifier_slack(
    session: Session,
    *,
    org_id: str,
    context: dict[str, Any],
    workflow_name: str,
) -> ActionResult:
    # Slack channel not configured in MVP — mirror as in-app notification
    create_and_publish_notification(
        session,
        org_id=org_id,
        type="info",
        title=f"Workflow: {workflow_name}",
        message=f"Action Notifier Slack — {context.get('title') or context.get('leadId') or 'événement'}",
        link="/app/workflows",
    )
    return ActionResult("Notifier Slack", True, "notification in-app publiée")


def execute_mettre_a_jour_crm(
    session: Session,
    *,
    org_id: str,
    context: dict[str, Any],
    workflow_name: str,
) -> ActionResult:
    lead_id = context.get("leadId")
    if not lead_id:
        return ActionResult("Mettre à jour CRM", True, "aucun leadId — no-op")
    repo = LeadRepository(session)
    lead = repo.get_by_id(org_id, str(lead_id))
    if not lead:
        return ActionResult("Mettre à jour CRM", False, f"lead {lead_id} introuvable")
    if lead.stage == "new":
        repo.update_stage(lead, "qualified")
        return ActionResult("Mettre à jour CRM", True, f"lead {lead.id} → qualified ({workflow_name})")
    return ActionResult("Mettre à jour CRM", True, f"lead {lead.id} stage={lead.stage}")


def execute_run_ai_agent(
    session: Session,
    *,
    org_id: str,
    context: dict[str, Any],
    workflow_name: str,
) -> ActionResult:
    create_and_publish_notification(
        session,
        org_id=org_id,
        type="info",
        title=f"Agent planifié: {workflow_name}",
        message="Action Run AI agent enregistrée (exécution asynchrone agent à brancher).",
        link="/app/ai/agents",
    )
    return ActionResult("Run AI agent", True, "notification agent planifiée")


def execute_call_api(
    session: Session,
    *,
    org_id: str,
    context: dict[str, Any],
    workflow_name: str,
) -> ActionResult:
    logger.info(
        "workflow_call_api org=%s workflow=%s context_keys=%s",
        org_id,
        workflow_name,
        list(context.keys()),
    )
    return ActionResult("Call API", True, "appel journalisé (stub HTTP sortant)")


ACTION_HANDLERS: dict[str, Callable[..., ActionResult]] = {
    "Envoyer email": execute_envoyer_email,
    "Créer tâche": execute_creer_tache,
    "Notifier Slack": execute_notifier_slack,
    "Mettre à jour CRM": execute_mettre_a_jour_crm,
    "Run AI agent": execute_run_ai_agent,
    "Call API": execute_call_api,
}


def run_actions(
    session: Session,
    *,
    org_id: str,
    actions: list[str],
    context: dict[str, Any] | None,
    workflow_name: str,
    email_service: EmailService | None,
) -> list[ActionResult]:
    ctx = context or {}
    results: list[ActionResult] = []
    for action in actions:
        handler = ACTION_HANDLERS.get(action)
        if not handler:
            results.append(ActionResult(action, False, "action inconnue"))
            continue
        try:
            kwargs: dict[str, Any] = {
                "session": session,
                "org_id": org_id,
                "context": ctx,
                "workflow_name": workflow_name,
            }
            if action == "Envoyer email":
                kwargs["email_service"] = email_service
            results.append(handler(**kwargs))
        except Exception as exc:
            logger.exception("action_failed action=%s", action)
            results.append(ActionResult(action, False, str(exc)))
    return results
