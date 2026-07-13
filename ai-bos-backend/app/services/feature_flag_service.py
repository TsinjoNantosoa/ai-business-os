from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.billing_repository import BillingRepository
from app.repositories.feature_flag_repository import FeatureFlagRepository
from app.repositories.organization_repository import OrganizationRepository

# Plan code → feature key → enabled (override catalog defaults when no tenant override).
PLAN_FEATURE_FLAGS: dict[str, dict[str, bool]] = {
    "starter": {
        "module.crm": True,
        "module.sales": False,
        "module.finance": False,
        "ai.copilot": True,
        "ai.custom_agents": False,
        "ml.forecasts": False,
        "workflow.builder": False,
        "realtime.sync": False,
        "analytics.advanced": False,
        "multi.currency": False,
        "api.v2": False,
        "audit.export": False,
    },
    "pro": {
        "module.crm": True,
        "module.sales": True,
        "module.finance": True,
        "ai.copilot": True,
        "ai.custom_agents": False,
        "ml.forecasts": True,
        "workflow.builder": True,
        "realtime.sync": False,
        "analytics.advanced": True,
        "multi.currency": False,
        "api.v2": True,
        "audit.export": True,
    },
    "enterprise": {
        "module.crm": True,
        "module.sales": True,
        "module.finance": True,
        "ai.copilot": True,
        "ai.custom_agents": True,
        "ml.forecasts": True,
        "workflow.builder": True,
        "realtime.sync": True,
        "analytics.advanced": True,
        "multi.currency": True,
        "api.v2": True,
        "audit.export": True,
    },
}

FEATURE_CATALOG: list[dict] = [
    {
        "key": "ai.copilot",
        "name": "AI Copilot",
        "description": "Activer le copilote IA",
        "env": "production",
        "default_enabled": True,
    },
    {
        "key": "ml.forecasts",
        "name": "ML Forecasts",
        "description": "Prévisions machine learning",
        "env": "beta",
        "default_enabled": False,
    },
    {
        "key": "workflow.builder",
        "name": "Workflow Builder",
        "description": "Constructeur de workflows visuel",
        "env": "production",
        "default_enabled": False,
    },
    {
        "key": "realtime.sync",
        "name": "Real-time Sync",
        "description": "Synchronisation temps réel",
        "env": "alpha",
        "default_enabled": False,
    },
    {
        "key": "analytics.advanced",
        "name": "Advanced Analytics",
        "description": "Analytics avancées avec cohortes",
        "env": "beta",
        "default_enabled": False,
    },
    {
        "key": "multi.currency",
        "name": "Multi-currency",
        "description": "Support multi-devises",
        "env": "planned",
        "default_enabled": False,
    },
    {
        "key": "ai.custom_agents",
        "name": "Custom Agents",
        "description": "Création d'agents IA personnalisés",
        "env": "alpha",
        "default_enabled": False,
    },
    {
        "key": "api.v2",
        "name": "API v2",
        "description": "Nouvelle API REST v2",
        "env": "beta",
        "default_enabled": False,
    },
    {
        "key": "module.crm",
        "name": "Module CRM",
        "description": "Contacts et leads CRM",
        "env": "production",
        "default_enabled": True,
    },
    {
        "key": "module.sales",
        "name": "Module Sales",
        "description": "Pipeline et commandes",
        "env": "production",
        "default_enabled": False,
    },
    {
        "key": "module.finance",
        "name": "Module Finance",
        "description": "Facturation et paiements",
        "env": "production",
        "default_enabled": False,
    },
    {
        "key": "audit.export",
        "name": "Audit Export",
        "description": "Export des journaux d'audit",
        "env": "production",
        "default_enabled": False,
    },
]


def resolve_plan_code(session: Session, org_id: str) -> str:
    org = OrganizationRepository(session).get_by_id(org_id)
    if org and org.plan:
        return org.plan.lower()
    sub = BillingRepository(session).get_subscription_for_org(org_id)
    if sub:
        plan = BillingRepository(session).get_plan_by_id(sub.plan_id)
        if plan:
            return plan.code.lower()
    return "starter"


def is_feature_enabled(session: Session, org_id: str, feature_key: str) -> bool:
    repo = FeatureFlagRepository(session)
    override = repo.get_override(org_id, feature_key)
    if override is not None:
        return bool(override.enabled)

    plan = resolve_plan_code(session, org_id)
    plan_flags = PLAN_FEATURE_FLAGS.get(plan, PLAN_FEATURE_FLAGS["starter"])
    if feature_key in plan_flags:
        return bool(plan_flags[feature_key])

    flag = repo.get_flag(feature_key)
    if flag is not None:
        return bool(flag.default_enabled)
    return False


def list_resolved_flags(session: Session, org_id: str) -> list[dict]:
    repo = FeatureFlagRepository(session)
    flags = repo.list_flags()
    overrides = {o.flag_key: o for o in repo.list_overrides_for_org(org_id)}
    plan = resolve_plan_code(session, org_id)
    plan_flags = PLAN_FEATURE_FLAGS.get(plan, PLAN_FEATURE_FLAGS["starter"])

    result: list[dict] = []
    for flag in flags:
        source = "default"
        if flag.key in overrides:
            enabled = bool(overrides[flag.key].enabled)
            source = "override"
        elif flag.key in plan_flags:
            enabled = bool(plan_flags[flag.key])
            source = "plan"
        else:
            enabled = bool(flag.default_enabled)

        result.append(
            {
                "key": flag.key,
                "name": flag.name,
                "description": flag.description,
                "env": flag.env,
                "enabled": enabled,
                "source": source,
                "plan": plan,
            }
        )
    return result
