"""Ensure demo JSON datasets + AI agents exist for an organization.

Seed data (contacts, invoices, …) lives primarily on org-1.
Registered orgs still need finance_overview / BI / forecasts / agents
or the frontend gets 404 while Neon looks “full”.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.data import seed
from app.data.seed_ops import DEMO_BI_REPORTS, DEMO_FINANCE_OVERVIEW
from app.models.catalog import AiAgent
from app.repositories.catalog_repository import CatalogRepository

DEMO_ORG_ID = "org-1"


def ensure_org_demo_datasets(session: Session, org_id: str) -> None:
    """Upsert analytics/finance/BI/forecast payloads for org_id if missing."""
    repo = CatalogRepository(session)

    def _source(key: str, fallback: dict) -> dict:
        return repo.get_dataset(DEMO_ORG_ID, key) or fallback

    if repo.get_dataset(org_id, "finance_overview") is None:
        repo.upsert_dataset(org_id, "finance_overview", _source("finance_overview", DEMO_FINANCE_OVERVIEW))
    if repo.get_dataset(org_id, "analytics_kpis") is None:
        repo.upsert_dataset(org_id, "analytics_kpis", _source("analytics_kpis", seed.ANALYTICS_KPIS))
    if repo.get_dataset(org_id, "bi_reports") is None:
        bi = repo.get_dataset(DEMO_ORG_ID, "bi_reports") or {"items": DEMO_BI_REPORTS}
        repo.upsert_dataset(org_id, "bi_reports", bi)
    for horizon in ("7d", "30d", "90d"):
        key = f"forecast_{horizon}"
        if repo.get_dataset(org_id, key) is None:
            repo.upsert_dataset(org_id, key, _source(key, seed.forecast_data(horizon)))


def ensure_org_demo_agents(session: Session, org_id: str) -> None:
    """Ensure the 11 mock AI agents exist for this org (unique ids per org)."""
    repo = CatalogRepository(session)
    if repo.count_by_org(AiAgent, org_id) > 0:
        return
    for agent in seed.AI_AGENTS:
        agent_id = agent["id"] if org_id == DEMO_ORG_ID else f"{org_id}-{agent['id']}"
        if session.get(AiAgent, agent_id):
            continue
        session.add(
            AiAgent(
                id=agent_id,
                org_id=org_id,
                slug=agent["slug"],
                name=agent["name"],
                description=agent["description"],
                status=agent["status"],
                category=agent["category"],
                icon=agent["icon"],
                tools_count=agent["toolsCount"],
                last_used=str(agent["lastUsed"])[:32] if agent.get("lastUsed") else None,
                conversations=agent["conversations"],
            )
        )


def get_dataset_for_org(session: Session, org_id: str, key: str) -> dict | None:
    """Prefer org payload; fall back to org-1 demo so dashboards never look empty."""
    repo = CatalogRepository(session)
    payload = repo.get_dataset(org_id, key)
    if payload is not None:
        return payload
    if org_id != DEMO_ORG_ID:
        payload = repo.get_dataset(DEMO_ORG_ID, key)
        if payload is not None:
            return payload
    # Auto-seed JSON dashboards for this org (registered tenants / incomplete seed).
    ensure_org_demo_datasets(session, org_id)
    session.commit()
    return repo.get_dataset(org_id, key) or (
        repo.get_dataset(DEMO_ORG_ID, key) if org_id != DEMO_ORG_ID else None
    )
