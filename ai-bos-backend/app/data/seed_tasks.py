"""Tasks seed data."""

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
]

TASK_STATUSES = ["todo", "in_progress", "review", "done"]
TASK_PRIORITIES = ["low", "medium", "high", "urgent"]
ASSIGNEES = [
    {"id": "u-owner-1", "name": "Jean Bernard", "color": "bg-primary-100"},
    {"id": "u-staff-1", "name": "Lucas Thomas", "color": "bg-slate-100"},
]

TASKS = []
for i, title in enumerate(TASK_TITLES):
    assignee = ASSIGNEES[i % len(ASSIGNEES)]
    TASKS.append(
        {
            "id": f"task-{i + 1}",
            "org_id": "org-1",
            "title": title,
            "description": "Tâche importante pour le bon déroulement du projet.",
            "status": TASK_STATUSES[i % len(TASK_STATUSES)],
            "priority": TASK_PRIORITIES[i % len(TASK_PRIORITIES)],
            "assignee_id": assignee["id"],
            "assignee_name": assignee["name"],
            "assignee_avatar_color": assignee["color"],
            "project_id": f"proj-{(i % 5) + 1}",
            "project_name": ["Growth Strategy", "Contracts & Legal", "Security Baseline", "Product Launch", "Ops Excellence"][i % 5],
            "due_date": days_from_now((i % 14) + 1),
            "tags": [["frontend"], ["backend"], ["design"], ["devops"], ["urgent"], ["review"]][i % 6],
            "created_at": days_ago(i + 1),
        }
    )
