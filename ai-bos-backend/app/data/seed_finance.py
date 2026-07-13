"""Finance invoices and workflows seed data."""

from __future__ import annotations

from app.data.datetime_utils import days_ago, days_from_now
from app.data.seed_crm import COMPANIES

INVOICE_STATUSES = ["draft", "sent", "paid", "paid", "paid", "overdue", "cancelled"]

FINANCE_INVOICES = []
for i in range(15):
    company = COMPANIES[i % len(COMPANIES)]
    status = INVOICE_STATUSES[i % len(INVOICE_STATUSES)]
    amount = (i + 1) * 1200 + (i % 5) * 800
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
            "invoice_number": f"INV-2024-{i + 1:03d}",
            "client_id": f"contact-{(i % 20) + 1}",
            "client_name": company,
            "amount": amount,
            "tax_amount": tax_amount,
            "total_amount": amount + tax_amount,
            "currency": "EUR",
            "status": status,
            "issue_date": days_ago(i * 5 + 3),
            "due_date": days_from_now(30 - i * 5),
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
        "trigger": "Employé ajouté",
        "actions": ["Créer tâche", "Mettre à jour CRM"],
        "last_run": days_ago(5),
        "run_count": 34,
        "success_rate": 88.0,
    },
    {
        "id": "wf-4",
        "org_id": "org-1",
        "name": "Rapport hebdo auto",
        "description": "Génération et envoi du rapport hebdomadaire.",
        "status": "active",
        "trigger": "Planification hebdo",
        "actions": ["Run AI agent", "Envoyer email"],
        "last_run": days_ago(0),
        "run_count": 52,
        "success_rate": 97.0,
    },
    {
        "id": "wf-5",
        "org_id": "org-1",
        "name": "Alerte stock faible",
        "description": "Alerte quand un article passe sous le seuil.",
        "status": "draft",
        "trigger": "Stock bas",
        "actions": ["Notifier Slack"],
        "last_run": None,
        "run_count": 0,
        "success_rate": 100.0,
    },
]
