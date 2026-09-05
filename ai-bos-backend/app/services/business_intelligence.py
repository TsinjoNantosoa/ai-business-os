"""Deterministic, explainable cross-module insights for the three flagship experiences."""

from __future__ import annotations

from calendar import monthrange
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.models.catalog import FinanceTransaction
from app.models.finance_invoice import FinanceInvoice
from app.models.lead import Lead
from app.models.ops import Project
from app.models.task import Task
from app.models.ticket import Ticket


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def executive_daily_brief(db: Session, org_id: str) -> dict:
    now = datetime.now(timezone.utc)
    invoices = list(db.scalars(select(FinanceInvoice).where(FinanceInvoice.org_id == org_id)).all())
    leads = list(db.scalars(select(Lead).where(Lead.org_id == org_id)).all())
    projects = list(db.scalars(select(Project).where(Project.org_id == org_id)).all())
    tasks = list(db.scalars(select(Task).where(Task.org_id == org_id)).all())
    tickets = list(db.scalars(select(Ticket).where(Ticket.org_id == org_id)).all())
    overdue = [row for row in invoices if row.status == "overdue" or (row.status not in {"paid", "cancelled"} and _aware(row.due_date) < now)]
    late_tasks = [row for row in tasks if row.status not in {"done", "completed"} and _aware(row.due_date) < now]
    over_budget = [row for row in projects if row.budget and row.spent > row.budget]
    urgent_tickets = [row for row in tickets if row.status not in {"closed", "resolved"} and (row.priority == "urgent" or _aware(row.sla_deadline) < now)]
    hot_leads = sorted([row for row in leads if row.stage not in {"won", "lost"}], key=lambda row: row.value * row.probability, reverse=True)[:3]
    priorities = []
    if overdue:
        priorities.append({"title": f"Relancer {len(overdue)} facture(s) en retard", "why": f"{sum(row.total_amount for row in overdue)} EUR exposés", "source": "finance.invoices", "action": {"label": "Voir les factures", "href": "/app/finance/invoices"}})
    if late_tasks:
        priorities.append({"title": f"Traiter {len(late_tasks)} tâche(s) échue(s)", "why": "Échéance dépassée et statut non terminé", "source": "tasks", "action": {"label": "Voir les tâches", "href": "/app/tasks"}})
    if urgent_tickets:
        priorities.append({"title": f"Résoudre {len(urgent_tickets)} ticket(s) à risque SLA", "why": "Priorité urgente ou délai SLA dépassé", "source": "support.tickets", "action": {"label": "Ouvrir le support", "href": "/app/support"}})
    risks = [{"title": project.name, "why": f"Budget dépassé de {project.spent - project.budget:.0f} EUR", "source": "projects"} for project in over_budget[:5]]
    opportunities = [{"title": lead.title, "why": f"Pipeline {lead.value} {lead.currency}, probabilité {lead.probability:.0f}%", "source": "crm.leads", "action": {"label": "Ouvrir le pipeline", "href": "/app/crm/leads"}} for lead in hot_leads]
    return {"generatedAt": now.isoformat(), "topPriorities": priorities[:5], "risks": risks, "opportunities": opportunities, "recommendedActions": [item["action"] for item in priorities + opportunities if item.get("action")][:5], "method": "Règles déterministes sur données tenant en temps réel"}


def cashflow_intelligence(db: Session, org_id: str) -> dict:
    transactions = list(db.scalars(select(FinanceTransaction).where(FinanceTransaction.org_id == org_id)).all())
    invoices = list(db.scalars(select(FinanceInvoice).where(FinanceInvoice.org_id == org_id)).all())
    leads = list(db.scalars(select(Lead).where(Lead.org_id == org_id)).all())
    inflow = sum(float(row.amount) for row in transactions if row.type.lower() in {"income", "in", "credit", "revenue"} or row.amount > 0)
    outflow = abs(sum(float(row.amount) for row in transactions if row.type.lower() in {"expense", "out", "debit"} or row.amount < 0))
    overdue = [row for row in invoices if row.status == "overdue"]
    overdue_total = sum(row.total_amount for row in overdue)
    weighted_pipeline = sum(row.value * row.probability / 100 for row in leads if row.stage not in {"won", "lost"})
    balance = inflow - outflow
    drivers = [
        {"label": "Encaissements observés", "amount": round(inflow, 2), "source": "finance.transactions"},
        {"label": "Décaissements observés", "amount": round(-outflow, 2), "source": "finance.transactions"},
        {"label": "Factures en retard", "amount": overdue_total, "source": "finance.invoices"},
        {"label": "Pipeline pondéré (non garanti)", "amount": round(weighted_pipeline, 2), "source": "crm.leads"},
    ]
    risk = "high" if balance < 0 and overdue_total > 0 else "medium" if balance < 0 or overdue_total > 0 else "low"
    return {
        "currentSituation": {"observedNetFlow": round(balance, 2), "currency": "EUR", "source": "finance.transactions"},
        "drivers": drivers,
        "risk": {"level": risk, "why": f"Flux net observé {balance:.0f} EUR; impayés {overdue_total} EUR"},
        "affectedCustomers": [{"id": row.client_id, "name": row.client_name, "amount": row.total_amount, "invoiceId": row.id, "source": "finance.invoices"} for row in overdue[:10]],
        "recommendations": [
            {"label": "Voir les factures", "href": "/app/finance/invoices"},
            {"label": "Créer une tâche de relance", "prompt": "Crée une tâche de relance des factures en retard"},
            {"label": "Préparer un rappel", "prompt": "Prépare un rappel pour les factures en retard"},
            {"label": "Ouvrir le CRM", "href": "/app/crm/contacts"},
        ],
        "limitations": "Analyse descriptive; le pipeline pondéré n'est pas une prévision garantie.",
    }


def sales_risk_intelligence(db: Session, org_id: str) -> dict:
    now = datetime.now(timezone.utc)
    month_end = now.replace(day=monthrange(now.year, now.month)[1], hour=23, minute=59, second=59)
    leads = list(db.scalars(select(Lead).where(Lead.org_id == org_id, Lead.stage.notin_(["won", "lost"]))).all())
    activities = list(db.scalars(select(Activity).where(Activity.org_id == org_id)).all())
    latest_activity = max((_aware(row.created_at) for row in activities), default=None)
    output = []
    for lead in leads:
        close = _aware(lead.expected_close_date)
        if close > month_end:
            continue
        reasons, score = [], 10
        if close < now:
            score += 35
            reasons.append("date de clôture dépassée")
        inactivity_days = (now - _aware(lead.updated_at)).days
        if inactivity_days >= 14:
            score += 25
            reasons.append(f"aucune mise à jour du deal depuis {inactivity_days} jours")
        if lead.stage in {"new", "qualified"}:
            score += 20
            reasons.append(f"étape encore précoce ({lead.stage})")
        age_days = (now - _aware(lead.created_at)).days
        if age_days >= 60:
            score += 15
            reasons.append(f"deal ouvert depuis {age_days} jours")
        if not lead.owner_id or not lead.owner_name:
            score += 15
            reasons.append("responsable manquant")
        if latest_activity is None:
            score += 10
            reasons.append("aucune activité CRM disponible pour corroborer l'engagement")
        output.append({"id": lead.id, "title": lead.title, "company": lead.company, "value": lead.value, "currency": lead.currency, "riskScore": min(score, 95), "reasons": reasons or ["risque de base lié à une clôture ce mois-ci"], "owner": lead.owner_name or None, "expectedCloseDate": close.isoformat(), "source": "crm.leads", "suggestedActions": [{"label": "Ouvrir le deal", "href": "/app/crm/leads"}, {"label": "Créer une tâche", "prompt": f"Crée une tâche de suivi pour {lead.company}"}]})
    output.sort(key=lambda item: item["riskScore"], reverse=True)
    return {"deals": output, "method": "Score heuristique explicable: retard, inactivité, étape, ancienneté, responsable", "limitations": "Aucun modèle ML; les activités ne sont pas reliées directement aux leads dans le schéma actuel."}
