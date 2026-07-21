"""Support tickets seed data (rich demo volumes)."""

from __future__ import annotations

from app.data.datetime_utils import days_ago, hours_from_now
from app.data.seed_crm import COMPANIES

SUBJECTS = [
    "Problème de connexion au portail",
    "Facture incorrecte",
    "Demande de remboursement",
    "Bug dans le module CRM",
    "Question sur l'abonnement",
    "Impossible d'exporter les données",
    "Erreur 500 sur dashboard",
    "Demande de formation",
    "Problème de synchronisation",
    "Accès refusé API",
    "SLA non respecté",
    "Demande d'ajout d'utilisateur",
    "Webhook Stripe en échec",
    "Export GDPR trop lent",
    "Copilot ne cite pas de sources",
    "Pipeline drag & drop cassé",
    "Notification non reçue",
    "SSO Microsoft échoue",
    "Stock incohérent",
    "Paie : écart de montant",
    "Contrat PDF illisible",
    "Campagne email bloquée",
    "Prévision ML absente",
    "Ticket dupliqué",
    "Demande de suppression compte",
    "Latence API contacts",
    "Erreur upload document",
    "Workflow run échoué",
    "Clé API révoquée par erreur",
    "Question licence Enterprise",
]

PRIORITIES = ["low", "medium", "high", "urgent"]
STATUSES = ["open", "pending", "resolved", "closed"]
CATEGORIES = ["Technique", "Facturation", "Compte", "Produit", "Formation", "Sécurité", "Intégrations"]
AGENTS = [
    {"id": "u-owner-1", "name": "Jean Bernard"},
    {"id": "u-staff-1", "name": "Lucas Thomas"},
]

SUPPORT_TICKETS = []
for i, subject in enumerate(SUBJECTS):
    company = COMPANIES[i % len(COMPANIES)]
    agent = AGENTS[i % len(AGENTS)] if i % 3 != 0 else None
    slug = "".join(c for c in company.lower() if c.isalnum())
    ticket_id = f"ticket-{i + 1}"
    SUPPORT_TICKETS.append(
        {
            "id": ticket_id,
            "org_id": "org-1",
            "ticket_number": f"TKT-{i + 1:04d}",
            "subject": subject,
            "customer_name": company,
            "customer_email": f"support@{slug}.com",
            "priority": PRIORITIES[i % len(PRIORITIES)],
            "status": STATUSES[i % len(STATUSES)],
            "agent_id": agent["id"] if agent else None,
            "agent_name": agent["name"] if agent else None,
            "category": CATEGORIES[i % len(CATEGORIES)],
            "created_at": days_ago(i + 1),
            "updated_at": days_ago(max(0, i // 2)),
            "sla_deadline": hours_from_now(i * 3 - 8),
            "messages": [
                {
                    "id": f"tm-{i + 1}-1",
                    "org_id": "org-1",
                    "ticket_id": ticket_id,
                    "author": "Customer",
                    "content": f"Bonjour, concernant « {subject} », pouvez-vous nous aider rapidement ?",
                    "is_internal": False,
                    "created_at": days_ago(i + 1),
                },
                {
                    "id": f"tm-{i + 1}-2",
                    "org_id": "org-1",
                    "ticket_id": ticket_id,
                    "author": "Support Agent",
                    "content": "Bonjour, nous avons bien reçu votre demande et investiguons.",
                    "is_internal": False,
                    "created_at": days_ago(max(0, i)),
                },
                {
                    "id": f"tm-{i + 1}-3",
                    "org_id": "org-1",
                    "ticket_id": ticket_id,
                    "author": "Support Agent",
                    "content": "Note interne : vérifier logs corr-id et permissions tenant.",
                    "is_internal": True,
                    "created_at": days_ago(max(0, i // 2)),
                },
            ],
        }
    )
