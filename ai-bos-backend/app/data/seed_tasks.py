"""Tasks seed data (rich demo volumes)."""

from __future__ import annotations

from app.data.datetime_utils import days_ago, days_from_now

TASK_TITLES = [
    "Préparer présentation Q4",
    "Réviser contrat TechSolutions",
    "Formation équipe CRM",
    "Audit sécurité mensuel",
    "Configurer environnement staging",
    "Réviser pull request #142",
    "Créer maquettes Figma",
    "Écrire tests E2E",
    "Documenter API publique",
    "Optimiser requêtes SQL",
    "Préparer démo client",
    "Mettre à jour dépendances",
    "Corriger bug authentification",
    "Implémenter dark mode",
    "Refactorer composants UI",
    "Setup monitoring",
    "Relance clients impayés",
    "Planifier sprint suivant",
    "Revue budget marketing",
    "Onboarding nouveau collaborateur",
    "Préparer board meeting",
    "Analyser churn clients",
    "Mettre à jour playbook sales",
    "Configurer SSO Google",
    "Migrer données CRM",
    "Écrire cas d'usage IA",
    "Revue accessibilité WCAG",
    "Optimiser temps de build",
    "Créer dashboard BI finance",
    "Tester backup/restore",
    "Mettre à jour runbook staging",
    "Qualifier pipeline Q3",
    "Relancer leads froids",
    "Préparer webinar partenaires",
    "Audit licences SaaS",
    "Mettre en place alertes SLA",
    "Revue performance agents IA",
    "Synchroniser inventaire",
    "Valider paie mensuelle",
    "Préparer export GDPR client",
    "Créer templates email",
    "Mettre à jour org chart",
    "Revue contrats fournisseurs",
    "Planifier campagne ads",
    "Corriger export CSV",
    "Intégrer webhook Stripe",
    "Documenter RBAC",
    "Tester isolation multi-tenant",
    "Préparer roadmap produit",
    "Revue coûts cloud",
]

TASK_STATUSES = ["todo", "in_progress", "review", "done"]
TASK_PRIORITIES = ["low", "medium", "high", "urgent"]
PROJECTS = [
    ("proj-1", "Growth Strategy"),
    ("proj-2", "Contracts & Legal"),
    ("proj-3", "Security Baseline"),
    ("proj-4", "Product Launch"),
    ("proj-5", "Ops Excellence"),
    ("proj-6", "Customer Success"),
    ("proj-7", "Data Platform"),
    ("proj-8", "Mobile App"),
]
ASSIGNEES = [
    {"id": "u-owner-1", "name": "Jean Bernard", "color": "bg-primary-100"},
    {"id": "u-staff-1", "name": "Lucas Thomas", "color": "bg-slate-100"},
]
TAG_SETS = [["frontend"], ["backend"], ["design"], ["devops"], ["urgent"], ["review"], ["finance"], ["crm"]]

TASKS = []
for i, title in enumerate(TASK_TITLES):
    assignee = ASSIGNEES[i % len(ASSIGNEES)]
    project_id, project_name = PROJECTS[i % len(PROJECTS)]
    TASKS.append(
        {
            "id": f"task-{i + 1}",
            "org_id": "org-1",
            "title": title,
            "description": f"Tâche démo #{i + 1} — {title}. Priorité opérationnelle pour la démo AI BOS.",
            "status": TASK_STATUSES[i % len(TASK_STATUSES)],
            "priority": TASK_PRIORITIES[i % len(TASK_PRIORITIES)],
            "assignee_id": assignee["id"],
            "assignee_name": assignee["name"],
            "assignee_avatar_color": assignee["color"],
            "project_id": project_id,
            "project_name": project_name,
            "due_date": days_from_now((i % 21) + 1),
            "tags": TAG_SETS[i % len(TAG_SETS)],
            "created_at": days_ago(i + 1),
        }
    )
