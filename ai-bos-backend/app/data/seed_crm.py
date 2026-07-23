"""Initial billing plans and CRM contacts seed data (rich demo volumes)."""

from __future__ import annotations

from app.data.datetime_utils import days_ago, days_from_now, hours_ago

BILLING_PLANS = [
    {
        "id": "plan-starter",
        "code": "starter",
        "name": "Starter",
        "price_monthly": 49,
        "currency": "EUR",
        "seats_limit": 5,
        "ai_tokens_limit": 100_000,
        "ai_rpm": 10,
        "storage_gb_limit": 10,
        "stripe_price_id": None,
    },
    {
        "id": "plan-pro",
        "code": "pro",
        "name": "Pro",
        "price_monthly": 299,
        "currency": "EUR",
        "seats_limit": 25,
        "ai_tokens_limit": 1_000_000,
        "ai_rpm": 60,
        "storage_gb_limit": 50,
        "stripe_price_id": None,
    },
    {
        "id": "plan-enterprise",
        "code": "enterprise",
        "name": "Enterprise",
        "price_monthly": 1200,
        "currency": "EUR",
        "seats_limit": 50,
        "ai_tokens_limit": 2_000_000,
        "ai_rpm": 200,
        "storage_gb_limit": 100,
        "stripe_price_id": None,
    },
]

COMPANIES = [
    "TechSolutions SAS",
    "GreenEnergy Corp",
    "Studio Pixel",
    "Logitrans SARL",
    "Nova Retail",
    "MediCare Plus",
    "Finova Bank",
    "AgriSense",
    "CloudNest",
    "Urban Mobility",
    "BlueOcean Logistics",
    "Helix Biotech",
    "Summit Hotels",
    "Atlas Education",
    "Prime Legal",
]

FIRST_NAMES = [
    "Jean", "Sophie", "Pierre", "Marie", "Lucas", "Emma", "Thomas", "Camille",
    "Hugo", "Léa", "Antoine", "Chloe", "Nicolas", "Julie", "Alexandre", "Sarah",
]
LAST_NAMES = [
    "Bernard", "Martin", "Dubois", "Lefevre", "Thomas", "Petit", "Robert", "Richard",
    "Moreau", "Simon", "Laurent", "Michel", "Garcia", "David", "Bertrand", "Roux",
]
TAGS = ["VIP", "Hot Lead", "Newsletter", "Partner", "Enterprise", "SMB", "Referral", "Cold", "Upsell", "Churn Risk"]
STATUSES = ["active", "active", "active", "lead", "lead", "inactive", "archived"]
POSITIONS = [
    "CEO", "CTO", "Manager", "Director", "VP Sales", "Head of Ops",
    "Procurement", "Marketing Lead", "CFO", "HR Manager", "Product Owner", "Analyst",
]
AVATAR_COLORS = [
    "bg-primary-100",
    "bg-emerald-100",
    "bg-amber-100",
    "bg-pink-100",
    "bg-sky-100",
    "bg-violet-100",
]

CONTACT_COUNT = 80
LEAD_COUNT = 45
ACTIVITY_COUNT = 60

CRM_CONTACTS = [
    {
        "id": f"contact-{i + 1}",
        "org_id": "org-1",
        "first_name": FIRST_NAMES[i % len(FIRST_NAMES)],
        "last_name": LAST_NAMES[(i * 3) % len(LAST_NAMES)],
        "email": f"{FIRST_NAMES[i % len(FIRST_NAMES)].lower()}.{LAST_NAMES[(i * 3) % len(LAST_NAMES)].lower()}{i + 1}@example.com",
        "phone": f"+33 6 {10 + (i % 80):02d} {20 + (i % 70):02d} {30 + (i % 60):02d} {40 + (i % 50):02d}",
        "company": COMPANIES[i % len(COMPANIES)],
        "position": POSITIONS[i % len(POSITIONS)],
        "status": STATUSES[i % len(STATUSES)],
        "owner_id": "u-owner-1" if i % 3 else "u-staff-1",
        "owner_name": "Jean Bernard" if i % 3 else "Lucas Thomas",
        "tags": [TAGS[i % len(TAGS)], TAGS[(i + 2) % len(TAGS)]],
        "avatar_color": AVATAR_COLORS[i % len(AVATAR_COLORS)],
        "last_activity_at": hours_ago(i * 7 + 3),
        "created_at": days_ago(i * 2 + 5),
    }
    for i in range(CONTACT_COUNT)
]

LEAD_STAGES = ["new", "qualified", "proposal", "negotiation", "won", "lost"]
LEAD_TITLES = [
    "Refonte site web",
    "Migration cloud",
    "Audit sécurité",
    "Implementation CRM",
    "Campagne marketing",
    "Consultation juridique",
    "Formation équipe",
    "Maintenance applicative",
    "Developpement mobile",
    "Stratégie digitale",
    "Optimisation SEO",
    "Analyse données",
    "Licence Enterprise",
    "Support Premium",
    "Intégration ERP",
]

CRM_LEADS = [
    {
        "id": f"lead-{i + 1}",
        "org_id": "org-1",
        "title": f"{LEAD_TITLES[i % len(LEAD_TITLES)]} — {COMPANIES[i % len(COMPANIES)]}",
        "company": COMPANIES[i % len(COMPANIES)],
        "contact_name": f"{FIRST_NAMES[i % len(FIRST_NAMES)]} {LAST_NAMES[(i * 5) % len(LAST_NAMES)]}",
        "value": (i + 1) * 2500 + (i % 7) * 1200,
        "currency": "EUR",
        "stage": LEAD_STAGES[i % len(LEAD_STAGES)],
        "probability": (
            100
            if LEAD_STAGES[i % len(LEAD_STAGES)] == "won"
            else 0
            if LEAD_STAGES[i % len(LEAD_STAGES)] == "lost"
            else 75
            if LEAD_STAGES[i % len(LEAD_STAGES)] == "negotiation"
            else 50
            if LEAD_STAGES[i % len(LEAD_STAGES)] == "proposal"
            else 30
            if LEAD_STAGES[i % len(LEAD_STAGES)] == "qualified"
            else 10
        ),
        "owner_id": "u-owner-1" if i % 2 == 0 else "u-staff-1",
        "owner_name": "Jean Bernard" if i % 2 == 0 else "Lucas Thomas",
        "owner_avatar_color": AVATAR_COLORS[i % len(AVATAR_COLORS)],
        "expected_close_date": days_from_now(i * 3 + 7),
        "stage_changed_at": days_ago(i % 20 + 1),
        "created_at": days_ago(i * 2 + 5),
    }
    for i in range(LEAD_COUNT)
]

ACTIVITY_TYPES = ["call", "email", "meeting", "note", "task"]
ACTIVITY_DESCRIPTIONS = [
    "Appel de découverte avec le client",
    "Email de suivi envoyé",
    "Réunion de démonstration produit",
    "Note interne ajoutée",
    "Tâche de suivi créée",
    "Proposition commerciale envoyée",
    "Négociation tarifaire",
    "Qualification BANT réalisée",
]

CRM_ACTIVITIES = [
    {
        "id": f"activity-{i + 1}",
        "org_id": "org-1",
        "type": ACTIVITY_TYPES[i % len(ACTIVITY_TYPES)],
        "description": ACTIVITY_DESCRIPTIONS[i % len(ACTIVITY_DESCRIPTIONS)],
        "contact_id": f"contact-{(i % CONTACT_COUNT) + 1}",
        "user_id": "u-owner-1" if i % 2 == 0 else "u-staff-1",
        "user_name": "Jean Bernard" if i % 2 == 0 else "Lucas Thomas",
        "created_at": hours_ago(i * 8 + 2),
    }
    for i in range(ACTIVITY_COUNT)
]
