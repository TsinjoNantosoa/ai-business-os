from __future__ import annotations

from app.data.datetime_utils import days_ago, days_from_now, hours_ago, hours_from_now

COMPANIES = [
    "TechSolutions SAS",
    "GreenEnergy Corp",
    "Studio Pixel",
    "Logitrans SARL",
    "Nova Retail",
]

DEPARTMENTS = ["Sales", "Finance", "HR", "Engineering", "Marketing", "Operations", "Legal", "Support"]

FIRST_NAMES = ["Jean", "Sophie", "Pierre", "Marie", "Lucas", "Emma", "Thomas", "Camille"]
LAST_NAMES = ["Bernard", "Martin", "Dubois", "Lefevre", "Thomas", "Petit", "Robert", "Richard"]

ORGANIZATIONS = [
    {
        "id": "org-1",
        "name": "Acme Corp",
        "plan": "enterprise",
        "currency": "EUR",
        "timezone": "Europe/Paris",
        "locale": "fr",
        "address": "123 rue de la Paix, 75001 Paris",
    },
    {
        "id": "org-2",
        "name": "Acme EU",
        "plan": "pro",
        "currency": "EUR",
        "timezone": "Europe/Berlin",
        "locale": "fr",
        "address": None,
    },
]

NOTIFICATIONS = [
    {
        "id": "notif-1",
        "type": "warning",
        "title": "Facture en retard",
        "message": "TechSolutions SAS n'a pas payé la facture #INV-2024-018 (45 jours de retard)",
        "read": False,
        "createdAt": hours_ago(2),
        "link": "/app/finance/invoices",
    },
    {
        "id": "notif-2",
        "type": "info",
        "title": "Nouveau lead",
        "message": 'Un nouveau lead "GreenEnergy Corp" a été ajouté au pipeline',
        "read": False,
        "createdAt": hours_ago(5),
        "link": "/app/crm/pipeline",
    },
    {
        "id": "notif-3",
        "type": "success",
        "title": "Deal gagné",
        "message": 'Le deal "Studio Pixel" a été gagné — 12 500 €',
        "read": False,
        "createdAt": hours_ago(8),
        "link": "/app/crm/pipeline",
    },
    {
        "id": "notif-4",
        "type": "warning",
        "title": "Stock faible",
        "message": 'L\'article "Ordinateur portable Pro" est en dessous du seuil de réapprovisionnement',
        "read": True,
        "createdAt": days_ago(1),
        "link": "/app/inventory",
    },
    {
        "id": "notif-5",
        "type": "error",
        "title": "Contrat expirant",
        "message": 'Le contrat avec "Logitrans SARL" expire dans 15 jours',
        "read": True,
        "createdAt": days_ago(2),
        "link": "/app/contracts",
    },
]

AUDIT_LOGS = [
    {
        "id": f"audit-{i + 1}",
        "timestamp": hours_ago(i * 3 + 1),
        "userId": f"user-{(i % 5) + 1}",
        "userName": f"{FIRST_NAMES[i % len(FIRST_NAMES)]} {LAST_NAMES[(i * 3) % len(LAST_NAMES)]}",
        "action": ["LOGIN", "LOGOUT", "CREATE", "UPDATE", "DELETE", "EXPORT", "VIEW"][i % 7],
        "resource": ["Contact", "Invoice", "Project", "Task", "Employee", "Contract", "Setting"][i % 7],
        "resourceId": f"res-{i}",
        "ip": f"192.168.{i % 255}.{(i * 7) % 255}",
        "details": "Action effectuée depuis le navigateur",
    }
    for i in range(30)
]

JOB_OPENINGS = [
    {
        "id": f"job-{i + 1}",
        "title": title,
        "department": DEPARTMENTS[i % len(DEPARTMENTS)],
        "status": (["open", "open", "open", "paused", "closed"])[i % 5],
        "applicants": (i % 15) + 3,
        "postedDate": days_ago(i * 5 + 2),
        "location": ["Paris", "Lyon", "Remote", "Bordeaux"][i % 4],
        "type": (["full_time", "full_time", "contract", "part_time", "internship"])[i % 5],
    }
    for i, title in enumerate(
        [
            "Développeur Full-Stack Senior",
            "Product Manager",
            "Data Scientist",
            "UX Designer",
            "Sales Executive",
            "Comptable Senior",
            "Responsable Marketing",
            "DevOps Engineer",
            "Business Analyst",
            "Customer Success Manager",
        ]
    )
]

CANDIDATES = [
    {
        "id": f"cand-{i + 1}",
        "name": f"{FIRST_NAMES[i % len(FIRST_NAMES)]} {LAST_NAMES[(i * 5) % len(LAST_NAMES)]}",
        "email": f"candidate{i + 1}@email.com",
        "jobId": f"job-{(i % 10) + 1}",
        "jobTitle": JOB_OPENINGS[i % 4]["title"],
        "stage": (["applied", "screening", "interview", "offer", "hired", "rejected"])[i % 6],
        "score": 60 + (i % 40),
        "avatarColor": f"bg-{(i + 3) % 8}-100",
        "appliedAt": days_ago(i * 2 + 1),
    }
    for i in range(20)
]

CONTRACTS = [
    {
        "id": f"contract-{i + 1}",
        "title": [
            "Contrat de service TechSolutions",
            "Accord de confidentialité",
            "Contrat de travail CDI",
            "Contrat fournisseur Cloud",
            "Bail commercial",
            "Contrat de maintenance",
        ][i % 6],
        "type": (["service", "nda", "employment", "vendor", "lease", "service"])[i % 6],
        "counterparty": COMPANIES[i % len(COMPANIES)],
        "value": (i + 1) * 15000,
        "currency": "EUR",
        "startDate": days_ago(i * 30 + 60),
        "endDate": days_from_now(i * 10 - 15),
        "status": (["active", "active", "active", "expiring", "expired", "draft"])[i % 6],
        "owner": ["Jean Bernard", "Sophie Martin", "Pierre Dubois"][i % 3],
    }
    for i in range(12)
]

KNOWLEDGE_ARTICLES = [
    {
        "id": f"article-{i + 1}",
        "title": title,
        "category": category,
        "excerpt": "Un guide détaillé pour vous aider à tirer le meilleur parti d'AI BOS.",
        "content": "# Article complet\n\nCet article explique en détail les meilleures pratiques et étapes à suivre.",
        "author": ["Marie Lefevre", "Jean Bernard", "Sophie Martin"][i % 3],
        "updatedAt": days_ago(i * 3 + 1),
        "views": (i + 1) * 120 + 45,
        "helpful": (i + 1) * 30 + 5,
    }
    for i, (title, category) in enumerate(
        [
            ("Comment configurer l'authentification à deux facteurs", "Sécurité"),
            ("Guide de démarrage rapide AI BOS", "Guide"),
            ("Importer des contacts depuis un fichier CSV", "CRM"),
            ("Créer et envoyer une facture", "Finance"),
            ("Configurer les workflows automatisés", "Automatisation"),
            ("Utiliser le copilote IA efficacement", "IA"),
            ("Personnaliser le tableau de bord", "Personnalisation"),
            ("Gérer les permissions et rôles", "Administration"),
            ("Intégrer AI BOS avec Slack", "Intégrations"),
            ("Exporter des rapports financiers", "Finance"),
            ("Créer une campagne marketing", "Marketing"),
            ("Comprendre les prévisions ML", "Analytics"),
        ]
    )
]

WORKFLOWS = [
    {
        "id": f"wf-{i + 1}",
        "name": name,
        "description": "Workflow automatisé pour améliorer l'efficacité opérationnelle.",
        "status": (["active", "active", "inactive", "active", "draft"])[i % 5],
        "trigger": trigger,
        "actions": ["Envoyer email", "Créer tâche", "Notifier Slack", "Mettre à jour CRM"][: (i % 3) + 1],
        "lastRun": days_ago(i + 1),
        "runCount": (i + 1) * 120 + 34,
        "successRate": 92 + (i % 7),
    }
    for i, (name, trigger) in enumerate(
        [
            ("Notification nouveau lead", "Lead créé"),
            ("Relance facture impayée", "Facture en retard"),
            ("Onboarding employé", "Employé ajouté"),
            ("Rapport hebdo auto", "Planification hebdo"),
            ("Alerte stock faible", "Stock bas"),
        ]
    )
]

AI_AGENTS = [
    {
        "id": "agent-1",
        "slug": "ceo",
        "name": "CEO Agent",
        "description": "Assistant stratégique pour la direction. Analyse KPIs, suggère des décisions.",
        "status": "active",
        "category": "Executive",
        "icon": "Crown",
        "toolsCount": 12,
        "lastUsed": days_ago(0),
        "conversations": 234,
    },
    {
        "id": "agent-2",
        "slug": "sales",
        "name": "Sales Agent",
        "description": "Optimise le pipeline commercial, analyse les deals et propose des actions.",
        "status": "active",
        "category": "Sales",
        "icon": "TrendingUp",
        "toolsCount": 8,
        "lastUsed": days_ago(1),
        "conversations": 189,
    },
    {
        "id": "agent-3",
        "slug": "finance",
        "name": "Finance Agent",
        "description": "Surveille la trésorerie, détecte les anomalies, prépare des rapports.",
        "status": "active",
        "category": "Finance",
        "icon": "Wallet",
        "toolsCount": 10,
        "lastUsed": days_ago(0),
        "conversations": 156,
    },
    {
        "id": "agent-4",
        "slug": "marketing",
        "name": "Marketing Agent",
        "description": "Crée et optimise les campagnes, analyse les performances.",
        "status": "idle",
        "category": "Marketing",
        "icon": "Megaphone",
        "toolsCount": 6,
        "lastUsed": days_ago(3),
        "conversations": 78,
    },
    {
        "id": "agent-5",
        "slug": "hr",
        "name": "HR Agent",
        "description": "Gère le recrutement, onboarding, et les demandes RH.",
        "status": "active",
        "category": "HR",
        "icon": "Users",
        "toolsCount": 9,
        "lastUsed": days_ago(1),
        "conversations": 112,
    },
    {
        "id": "agent-6",
        "slug": "analyst",
        "name": "Data Analyst",
        "description": "Interroge les données, génère des insights et des visualisations.",
        "status": "active",
        "category": "Analytics",
        "icon": "BarChart3",
        "toolsCount": 14,
        "lastUsed": days_ago(0),
        "conversations": 298,
    },
]

INVENTORY_ITEMS = [
    {
        "id": f"inv-{i + 1}",
        "sku": f"SKU-{i + 1:04d}",
        "name": name,
        "category": category,
        "quantity": qty,
        "reorderLevel": reorder,
        "warehouse": ["Paris Nord", "Lyon Sud", "Bordeaux"][i % 3],
        "unitPrice": 50 + i * 120,
        "status": "out_of_stock" if qty == 0 else ("low_stock" if qty < reorder else "in_stock"),
    }
    for i, (name, category, qty, reorder) in enumerate(
        [
            ("Ordinateur portable Pro", "IT", 0, 20),
            ("Écran 27\" 4K", "IT", 50, 20),
            ("Clavier mécanique", "Accessoires", 5, 20),
            ("Souris sans fil", "Accessoires", 80, 20),
            ("Casque audio", "Audio", 45, 20),
            ("Webcam HD", "Vidéo", 12, 20),
            ("Disque SSD 1To", "Stockage", 30, 20),
            ("Routeur WiFi 6", "Réseau", 18, 20),
            ("Imprimante laser", "Impression", 6, 20),
            ("Projecteur", "Présentation", 4, 20),
        ]
    )
]

DOCUMENTS = [
    {"id": "doc-1", "name": "Contrats", "type": "folder", "size": 0, "modifiedAt": days_ago(1), "modifiedBy": "Marie Lefevre"},
    {"id": "doc-2", "name": "Factures", "type": "folder", "size": 0, "modifiedAt": days_ago(2), "modifiedBy": "Pierre Dubois"},
    {"id": "doc-3", "name": "Rapports", "type": "folder", "size": 0, "modifiedAt": days_ago(3), "modifiedBy": "Jean Bernard"},
    {
        "id": "doc-4",
        "name": "Contrat_TechSolutions_2024.pdf",
        "type": "pdf",
        "size": 245678,
        "parentId": "doc-1",
        "modifiedAt": days_ago(1),
        "modifiedBy": "Marie Lefevre",
    },
    {
        "id": "doc-5",
        "name": "Facture_INV-2024-018.pdf",
        "type": "pdf",
        "size": 128456,
        "parentId": "doc-2",
        "modifiedAt": days_ago(2),
        "modifiedBy": "Pierre Dubois",
    },
    {
        "id": "doc-6",
        "name": "Rapport_Trimestriel_Q3.xlsx",
        "type": "xlsx",
        "size": 567890,
        "parentId": "doc-3",
        "modifiedAt": days_ago(3),
        "modifiedBy": "Jean Bernard",
        "starred": True,
    },
]

SUPPLIERS = [
    {
        "id": f"supp-{i + 1}",
        "name": company,
        "email": f"achats@{company.lower().replace(' ', '').replace('.', '')}.com",
        "phone": f"+33 1 {10 + i:02d} {20 + i:02d}",
        "rating": 3 + (i % 3) * 0.5,
        "country": ["France", "Belgique", "Suisse", "Maroc"][i % 4],
        "status": (["active", "active", "active", "paused", "blacklisted"])[i % 5],
    }
    for i, company in enumerate((COMPANIES * 3)[:14])
]

_PO_STATUSES = ["draft", "submitted", "approved", "received", "cancelled"]

PURCHASE_ORDERS = []
for i in range(22):
    supplier = SUPPLIERS[i % len(SUPPLIERS)]
    status = _PO_STATUSES[i % 5]
    PURCHASE_ORDERS.append(
        {
            "id": f"po-{i + 1}",
            "poNumber": f"PO-2024-{i + 1:04d}",
            "supplierId": supplier["id"],
            "supplierName": supplier["name"],
            "status": status,
            "totalAmount": 15000 + i * 1200 + (3000 if status == "received" else 0),
            "currency": "EUR",
            "createdAt": days_ago(i * 2 + 3),
            "expectedAt": days_ago(i + 1) if status == "received" else days_from_now(i % 10 + 7),
            "ownerName": ["Sophie Martin", "Pierre Dubois", "Jean Bernard"][i % 3],
            "itemCount": 3 + (i % 15),
        }
    )

ANALYTICS_KPIS = {
    "kpis": [
        {"label": "Revenu MTD", "value": 284500, "change": 12.5, "unit": "€"},
        {"label": "Pipeline", "value": 1240000, "change": 8.3, "unit": "€"},
        {"label": "Clients actifs", "value": 342, "change": 5.2, "unit": ""},
        {"label": "Taux de conversion", "value": 24.8, "change": -2.1, "unit": "%"},
        {"label": "Churn rate", "value": 3.2, "change": -0.8, "unit": "%"},
        {"label": "NPS", "value": 47, "change": 4, "unit": ""},
    ],
    "revenue": [
        {"month": m, "revenue": 180000 + i * 12000, "target": 200000 + i * 10000}
        for i, m in enumerate(["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."])
    ],
    "users": [
        {"month": m, "active": 200 + i * 15, "new": 20 + i * 3}
        for i, m in enumerate(["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."])
    ],
    "conversion": [
        {"stage": "Visiteurs", "value": 12000, "rate": 100},
        {"stage": "Leads", "value": 3600, "rate": 30},
        {"stage": "Qualifiés", "value": 1800, "rate": 15},
        {"stage": "Devis", "value": 720, "rate": 6},
        {"stage": "Clients", "value": 298, "rate": 2.5},
    ],
    "churn": [
        {"month": m, "rate": 4.5 - i * 0.1}
        for i, m in enumerate(["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."])
    ],
}


def _forecast_points(horizon: str) -> tuple[int, int, float, list[str]]:
    if horizon == "7d":
        return 7, 800, 94.2, [
            "Augmentation prévue du CA de 8% la semaine prochaine",
            "Pic de demande attendu jeudi — préparez les stocks",
            "La tendance haussière se confirme sur 7 jours",
        ]
    if horizon == "30d":
        return 30, 1200, 89.5, [
            "Croissance mensuelle projetée: +12%",
            "Risque de plateau la 3ème semaine — envisagez une promotion",
            "La saisonnalité montre un pic en fin de mois",
        ]
    return 90, 2000, 82.1, [
        "Tendance haussière sur le trimestre: +18%",
        "Période de croissance plus lente attendue en mois 2",
        "Investir dans la capacité pour répondre à la demande du mois 3",
    ]


def forecast_data(horizon: str) -> dict:
    days, band, confidence, recommendations = _forecast_points(horizon)
    actual_cutoff = 2 if horizon == "7d" else (5 if horizon == "30d" else 10)
    mae = 342 if horizon == "7d" else (487 if horizon == "30d" else 723)

    points = []
    for i in range(days):
        base = 9500 + i * (200 if horizon == "7d" else (150 if horizon == "30d" else 80))
        points.append(
            {
                "date": days_from_now(i)[:10],
                "actual": base if i < actual_cutoff else None,
                "forecast": round(base),
                "lower": round(base - band),
                "upper": round(base + band),
            }
        )

    return {
        "horizon": horizon,
        "data": points,
        "model": {
            "name": "Prophet v2",
            "version": "2.1.3",
            "mae": mae,
            "lastTrained": days_ago(1),
            "confidence": confidence,
        },
        "recommendations": recommendations,
    }
