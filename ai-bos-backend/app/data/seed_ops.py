"""Rich static demo payloads for modules still served from memory (not DB tables)."""

from __future__ import annotations

from app.data.datetime_utils import days_ago, days_from_now, hours_ago
from app.data.seed_crm import COMPANIES, FIRST_NAMES, LAST_NAMES

PROJECT_DEFS = [
    ("proj-1", "Growth Strategy", "Plan de croissance Q3/Q4 et priorisation CRM/Finance.", "active", 62, "#4f46e5", 250000, 155000, 48, 30),
    ("proj-2", "Contracts & Legal", "Revue contrats, NDA, et conformité sécurité.", "on_hold", 28, "#f59e0b", 80000, 21000, 16, 4),
    ("proj-3", "Security Baseline", "Hardening, SSO, audit logs et conformité.", "active", 71, "#0d9488", 120000, 78000, 32, 22),
    ("proj-4", "Product Launch", "Lancement module Copilot + RAG.", "active", 54, "#8b5cf6", 180000, 96000, 40, 21),
    ("proj-5", "Ops Excellence", "Automatisation workflows et procurement.", "planning", 18, "#64748b", 90000, 12000, 20, 3),
    ("proj-6", "Customer Success", "Playbooks support et NPS.", "active", 44, "#ec4899", 70000, 31000, 22, 10),
    ("proj-7", "Data Platform", "Pipeline analytics / BI / forecasts.", "active", 66, "#06b6d4", 210000, 140000, 36, 24),
    ("proj-8", "Mobile App", "Application mobile AI BOS.", "on_hold", 12, "#ef4444", 150000, 18000, 28, 3),
]

DEMO_PROJECTS = [
    {
        "id": pid,
        "name": name,
        "description": desc,
        "status": status,
        "progress": progress,
        "startDate": days_ago(120 - i * 10),
        "endDate": days_from_now(60 + i * 15),
        "budget": budget,
        "spent": spent,
        "teamMembers": [
            {"id": "u-owner-1", "name": "Jean Bernard", "avatarColor": "bg-primary-100", "role": "owner"},
            {"id": "u-staff-1", "name": "Lucas Thomas", "avatarColor": "bg-slate-100", "role": "staff"},
        ][: 1 + (i % 2)],
        "taskCount": tasks,
        "completedTasks": done,
        "color": color,
    }
    for i, (pid, name, desc, status, progress, color, budget, spent, tasks, done) in enumerate(PROJECT_DEFS)
]

ORDER_STATUSES = ["draft", "sent", "accepted", "fulfilled", "invoiced", "cancelled"]

DEMO_SALES_ORDERS = []
for i in range(24):
    company = COMPANIES[i % len(COMPANIES)]
    qty = (i % 5) + 1
    unit = 2500 + i * 350
    DEMO_SALES_ORDERS.append(
        {
            "id": f"so-{i + 1}",
            "orderNumber": f"SO-{2000 + i}",
            "customerId": f"contact-{(i % 20) + 1}",
            "customerName": company,
            "status": ORDER_STATUSES[i % len(ORDER_STATUSES)],
            "amount": qty * unit,
            "currency": "EUR",
            "date": days_ago(i * 4 + 1)[:10] if isinstance(days_ago(i * 4 + 1), str) else str(days_ago(i * 4 + 1))[:10],
            "salesRepId": "u-owner-1" if i % 2 == 0 else "u-staff-1",
            "salesRepName": "Jean Bernard" if i % 2 == 0 else "Lucas Thomas",
            "lineItems": [
                {
                    "id": f"li-so-{i + 1}-1",
                    "description": ["Pack CRM + IA", "Support premium", "Licences Pro", "Formation"][i % 4],
                    "quantity": qty,
                    "unitPrice": unit,
                    "total": qty * unit,
                }
            ],
        }
    )

CAMPAIGN_TYPES = ["email", "social", "ads", "webinar", "content"]
CAMPAIGN_STATUSES = ["draft", "scheduled", "active", "paused", "completed"]

DEMO_CAMPAIGNS = []
for i in range(18):
    budget = 8000 + i * 2500
    spent = int(budget * ((i % 8) / 10))
    DEMO_CAMPAIGNS.append(
        {
            "id": f"camp-{i + 1}",
            "name": [
                "Q3 Growth — Paid Search",
                "Webinar Partner Program",
                "Newsletter Product Launch",
                "Retargeting CRM Churn",
                "LinkedIn Lead Gen",
                "Brand Awareness TV",
                "Content SEO Sprint",
                "Customer Advocacy",
            ][i % 8]
            + f" #{i + 1}",
            "type": CAMPAIGN_TYPES[i % len(CAMPAIGN_TYPES)],
            "status": CAMPAIGN_STATUSES[i % len(CAMPAIGN_STATUSES)],
            "reach": 20000 + i * 8500,
            "openRate": round(0.18 + (i % 10) * 0.02, 2),
            "clickRate": round(0.04 + (i % 8) * 0.01, 2),
            "conversions": 120 + i * 45,
            "budget": budget,
            "spent": spent,
            "startDate": days_ago(40 - i)[:10] if True else "2026-06-01",
            "endDate": days_from_now(20 + i)[:10],
        }
    )

# Normalize dates to YYYY-MM-DD strings for FE
for order in DEMO_SALES_ORDERS:
    d = order["date"]
    order["date"] = d[:10] if isinstance(d, str) else str(d)[:10]
for camp in DEMO_CAMPAIGNS:
    camp["startDate"] = str(camp["startDate"])[:10]
    if camp.get("endDate"):
        camp["endDate"] = str(camp["endDate"])[:10]

DEMO_CALENDAR_EVENTS = []
EVENT_TYPES = ["meeting", "deadline", "reminder", "call", "task"]
COLORS = ["#4f46e5", "#ef4444", "#f59e0b", "#0d9488", "#8b5cf6", "#ec4899"]
for i in range(30):
    start = days_from_now(i - 10)
    DEMO_CALENDAR_EVENTS.append(
        {
            "id": f"ev-{i + 1}",
            "title": [
                "Réunion CRM",
                "Deadline audit",
                "Relance facture",
                "Demo client",
                "Sync finance",
                "Standup produit",
                "Revue pipeline",
                "Formation équipe",
            ][i % 8]
            + f" #{i + 1}",
            "type": EVENT_TYPES[i % len(EVENT_TYPES)],
            "startDate": f"{str(start)[:10]}T{9 + (i % 8):02d}:00:00Z",
            "endDate": f"{str(start)[:10]}T{10 + (i % 8):02d}:00:00Z",
            "color": COLORS[i % len(COLORS)],
            "location": ["Room A / Zoom", "HQ", "Remote", "Room Finance"][i % 4],
            "attendees": ["Jean Bernard", "Lucas Thomas"],
            "description": "Événement démo AI BOS pour tester le calendrier.",
        }
    )

DEMO_MEETINGS = []
for i in range(16):
    DEMO_MEETINGS.append(
        {
            "id": f"mt-{i + 1}",
            "title": [
                "Monthly Finance Sync",
                "Sales Pipeline Review",
                "Product Roadmap",
                "Customer Success Sync",
                "Security Council",
                "Hiring Committee",
            ][i % 6]
            + f" #{i + 1}",
            "date": str(days_from_now(i - 5))[:10],
            "duration": 30 + (i % 4) * 15,
            "status": ["upcoming", "completed", "cancelled"][i % 3],
            "location": ["Room Finance", "Zoom", "HQ Board", "Room Sales"][i % 4],
            "attendees": [
                {"id": "u-owner-1", "name": "Jean Bernard", "avatarColor": "bg-primary-100"},
                {"id": "u-staff-1", "name": "Lucas Thomas", "avatarColor": "bg-slate-100"},
            ],
            "agenda": ["Points clés", "Décisions", "Actions"],
            "summary": "Compte-rendu démo pour tester les réunions.",
            "actionItems": [
                {"id": f"ai-{i + 1}-1", "text": "Suivre les actions ouvertes", "done": i % 2 == 0, "assignee": "Lucas Thomas"},
                {"id": f"ai-{i + 1}-2", "text": "Partager le compte-rendu", "done": True, "assignee": "Jean Bernard"},
            ],
        }
    )

DEMO_BI_REPORTS = [
    {
        "id": f"bi-{i + 1}",
        "name": name,
        "description": desc,
        "category": cat,
        "chartType": chart,
        "lastRun": hours_ago(i * 5 + 1),
        "schedule": sched,
    }
    for i, (name, desc, cat, chart, sched) in enumerate(
        [
            ("KPI Finance — vue générale", "Trésorerie, AR/AP, cashflow et alertes.", "finance", "bar", "daily 06:00"),
            ("Pipeline CRM — performance", "Taux de conversion et valeur par étape.", "crm", "line", "hourly"),
            ("Churn & rétention", "Analyse des clients à risque.", "analytics", "area", "daily 07:00"),
            ("Campagnes marketing ROI", "Coût / conversion par canal.", "marketing", "pie", "weekly Mon"),
            ("Charge support SLA", "Tickets ouverts vs SLA.", "support", "bar", "daily 08:00"),
            ("Forecast revenu 90j", "Prévisions ML vs réalisé.", "ml", "line", "daily 05:30"),
            ("Inventaire critique", "Articles sous seuil.", "ops", "bar", None),
            ("Productivité équipe", "Tâches done / sprint.", "projects", "area", "weekly Fri"),
            ("Billing MRR", "Abonnements et upgrades.", "billing", "line", "daily 06:30"),
            ("Audit sécurité", "Actions sensibles 7 jours.", "security", "bar", "daily 23:00"),
            ("HR headcount", "Effectifs et turnover.", "hr", "pie", "monthly 1"),
            ("Procurement cycle", "Délais PO / réception.", "procurement", "line", None),
        ]
    )
]

DEPARTMENTS = ["Management", "Sales", "Finance", "Engineering", "Marketing", "Operations", "HR", "Support", "Legal", "Product"]
POSITIONS = [
    "Chief Executive Officer", "Sales Manager", "Accountant", "Full-Stack Engineer",
    "Growth Marketer", "Ops Lead", "HR Business Partner", "Support Agent",
    "Legal Counsel", "Product Manager", "Data Analyst", "DevOps Engineer",
]

DEMO_EMPLOYEES = []
for i in range(36):
    first = FIRST_NAMES[i % len(FIRST_NAMES)]
    last = LAST_NAMES[(i * 2) % len(LAST_NAMES)]
    DEMO_EMPLOYEES.append(
        {
            "id": f"e-{i + 1}",
            "firstName": first,
            "lastName": last,
            "email": f"{first.lower()}.{last.lower()}{i + 1}@demo.aibos.io",
            "phone": f"+33 6 {10 + i:02d} 00 00 {i % 90:02d}",
            "position": POSITIONS[i % len(POSITIONS)],
            "department": DEPARTMENTS[i % len(DEPARTMENTS)],
            "startDate": str(days_ago(200 - i * 4))[:10],
            "status": ["active", "active", "active", "on_leave", "terminated"][i % 5],
            "avatarColor": ["bg-primary-100", "bg-slate-100", "bg-emerald-100", "bg-amber-100"][i % 4],
            "salary": 45000 + (i % 12) * 5000,
            "location": ["Paris", "Lyon", "Remote", "Bordeaux", "Nantes"][i % 5],
        }
    )

DEMO_FINANCE_OVERVIEW = {
    "cashBalance": 428400,
    "arOutstanding": 186200,
    "apOutstanding": 64200,
    "burnRate": 28400,
    "monthlyRevenue": [
        {"month": m, "revenue": 180000 + i * 12000, "expenses": 110000 + i * 6000}
        for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    ],
    "agingReceivables": [
        {"bucket": "0-30d", "amount": 68400},
        {"bucket": "31-60d", "amount": 45200},
        {"bucket": "61-90d", "amount": 32800},
        {"bucket": "90+d", "amount": 39800},
    ],
    "recentTransactions": [
        {
            "id": f"tx-{i + 1}",
            "description": desc,
            "amount": amount,
            "type": typ,
            "category": cat,
            "date": str(days_ago(i))[:10],
            "account": acc,
        }
        for i, (desc, amount, typ, cat, acc) in enumerate(
            [
                ("Paiement facture INV-2026-012", 18400, "income", "Invoices", "Main AR"),
                ("Dépense SaaS AWS", 4200, "expense", "Cloud", "Operating"),
                ("Licence OpenAI", 2900, "expense", "AI", "Operating"),
                ("Paiement facture INV-2026-008", 12600, "income", "Invoices", "Main AR"),
                ("Campagne Google Ads", 7800, "expense", "Marketing ads", "Operating"),
                ("Abonnement Stripe fees", 640, "expense", "Payments", "Operating"),
                ("Paiement facture INV-2026-003", 9200, "income", "Invoices", "Main AR"),
                ("Salaires run", 98000, "expense", "Payroll", "Payroll"),
                ("Achat matériel IT", 5400, "expense", "Inventory", "Operating"),
                ("Remboursement client", 1200, "expense", "Refunds", "Main AR"),
                ("Intérêts compte pro", 310, "income", "Other", "Treasury"),
                ("Loyer bureaux", 8500, "expense", "Facilities", "Operating"),
            ]
        )
    ],
}

DEMO_TRANSACTIONS = DEMO_FINANCE_OVERVIEW["recentTransactions"]
