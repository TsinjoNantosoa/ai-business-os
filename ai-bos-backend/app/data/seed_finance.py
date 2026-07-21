"""Finance invoices and workflows seed data (rich demo volumes)."""

from __future__ import annotations

from app.data.datetime_utils import days_ago, days_from_now
from app.data.seed_crm import COMPANIES, CONTACT_COUNT

INVOICE_STATUSES = ["draft", "sent", "paid", "paid", "paid", "overdue", "cancelled", "sent", "overdue"]
INVOICE_COUNT = 45

FINANCE_INVOICES = []
for i in range(INVOICE_COUNT):
    company = COMPANIES[i % len(COMPANIES)]
    status = INVOICE_STATUSES[i % len(INVOICE_STATUSES)]
    amount = (i + 1) * 900 + (i % 5) * 650
    tax_amount = round(amount * 0.2)
    line_count = (i % 3) + 1
    line_items = []
    for j in range(line_count):
        qty = (j + 1) * (i % 3 + 1)
        unit_price = max(100, round(amount / (line_count * qty)))
        line_items.append(
            {
                "id": f"li-inv-{i + 1}-{j + 1}",
                "description": ["Consultation", "Développement", "Licence logicielle", "Formation", "Support technique"][j % 5],
                "quantity": qty,
                "unitPrice": unit_price,
                "taxRate": 20,
                "total": qty * unit_price,
            }
        )
    FINANCE_INVOICES.append(
        {
            "id": f"inv-{i + 1}",
            "org_id": "org-1",
            "invoice_number": f"INV-2026-{i + 1:03d}",
            "client_id": f"contact-{(i % CONTACT_COUNT) + 1}",
            "client_name": company,
            "amount": amount,
            "tax_amount": tax_amount,
            "total_amount": amount + tax_amount,
            "currency": "EUR",
            "status": status,
            "issue_date": days_ago(i * 3 + 2),
            "due_date": days_from_now(30 - (i % 40)),
            "paid_date": days_ago(i * 2) if status == "paid" else None,
            "line_items": line_items,
        }
    )

WORKFLOWS = [
    {
        "id": "wf-1",
        "org_id": "org-1",
        "name": "Notification nouveau lead",
        "description": "Workflow automatisé pour améliorer l'efficacité opérationnelle.",
        "status": "active",
        "trigger": "Lead créé",
        "actions": ["Envoyer email", "Créer tâche"],
        "last_run": days_ago(1),
        "run_count": 120,
        "success_rate": 94.0,
    },
    {
        "id": "wf-2",
        "org_id": "org-1",
        "name": "Relance facture impayée",
        "description": "Relance automatique des factures en retard.",
        "status": "active",
        "trigger": "Facture en retard",
        "actions": ["Envoyer email", "Notifier Slack"],
        "last_run": days_ago(2),
        "run_count": 86,
        "success_rate": 91.0,
    },
    {
        "id": "wf-3",
        "org_id": "org-1",
        "name": "Onboarding employé",
        "description": "Checklist RH pour les nouveaux arrivants.",
        "status": "inactive",
        "trigger": "Employé créé",
        "actions": ["Créer tâches", "Assigner mentor"],
        "last_run": days_ago(12),
        "run_count": 18,
        "success_rate": 88.0,
    },
    {
        "id": "wf-4",
        "org_id": "org-1",
        "name": "Escalade ticket urgent",
        "description": "Escalade support si SLA critique.",
        "status": "active",
        "trigger": "Ticket urgent",
        "actions": ["Notifier manager", "Créer tâche"],
        "last_run": days_ago(1),
        "run_count": 54,
        "success_rate": 96.0,
    },
    {
        "id": "wf-5",
        "org_id": "org-1",
        "name": "Deal gagné → facture",
        "description": "Crée un brouillon de facture quand un lead est gagné.",
        "status": "active",
        "trigger": "Lead won",
        "actions": ["Créer facture", "Notifier finance"],
        "last_run": days_ago(4),
        "run_count": 33,
        "success_rate": 92.5,
    },
    {
        "id": "wf-6",
        "org_id": "org-1",
        "name": "Rappel réunion client",
        "description": "Rappel J-1 avant meeting commercial.",
        "status": "active",
        "trigger": "Meeting demain",
        "actions": ["Envoyer email", "Notifier calendrier"],
        "last_run": days_ago(0),
        "run_count": 210,
        "success_rate": 98.0,
    },
    {
        "id": "wf-7",
        "org_id": "org-1",
        "name": "Stock bas → achat",
        "description": "Crée un PO brouillon si stock sous seuil.",
        "status": "paused",
        "trigger": "Stock bas",
        "actions": ["Créer PO", "Notifier procurement"],
        "last_run": days_ago(8),
        "run_count": 12,
        "success_rate": 85.0,
    },
    {
        "id": "wf-8",
        "org_id": "org-1",
        "name": "NPS follow-up",
        "description": "Enquête satisfaction après ticket résolu.",
        "status": "active",
        "trigger": "Ticket resolved",
        "actions": ["Envoyer email"],
        "last_run": days_ago(3),
        "run_count": 67,
        "success_rate": 90.0,
    },
]
