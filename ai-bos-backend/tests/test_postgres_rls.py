from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text


@pytest.mark.skipif(not os.getenv("RLS_DATABASE_URL"), reason="RLS_DATABASE_URL required for PostgreSQL integration")
def test_postgres_rls_prevents_cross_tenant_reads_and_writes() -> None:
    engine = create_engine(os.environ["RLS_DATABASE_URL"])
    with engine.begin() as connection:
        assert connection.dialect.name == "postgresql"
        connection.execute(text("INSERT INTO organizations (id, name, plan, currency, timezone, locale, created_at, updated_at) VALUES ('rls-org-1', 'RLS One', 'starter', 'EUR', 'UTC', 'fr', now(), now()), ('rls-org-2', 'RLS Two', 'starter', 'EUR', 'UTC', 'fr', now(), now()) ON CONFLICT (id) DO NOTHING"))
        connection.execute(text("SELECT set_config('app.current_org_id', 'rls-org-1', true)"))
        connection.execute(text("INSERT INTO contacts (id, org_id, first_name, last_name, email, company, status, owner_id, tags, last_activity_at, created_at, updated_at) VALUES ('rls-contact-1', 'rls-org-1', 'One', 'Tenant', 'one@example.invalid', 'One', 'active', 'system', '[]'::json, now(), now(), now()) ON CONFLICT (id) DO NOTHING"))
        org1_ids = set(connection.execute(text("SELECT id FROM contacts")).scalars())
        connection.execute(text("SELECT set_config('app.current_org_id', 'rls-org-2', true)"))
        connection.execute(text("INSERT INTO contacts (id, org_id, first_name, last_name, email, company, status, owner_id, tags, last_activity_at, created_at, updated_at) VALUES ('rls-contact-2', 'rls-org-2', 'Two', 'Tenant', 'two@example.invalid', 'Two', 'active', 'system', '[]'::json, now(), now(), now()) ON CONFLICT (id) DO NOTHING"))
        org2_ids = set(connection.execute(text("SELECT id FROM contacts")).scalars())
        assert org1_ids.isdisjoint(org2_ids)
        assert "rls-contact-1" in org1_ids and "rls-contact-2" in org2_ids
        with pytest.raises(Exception):
            connection.execute(
                text("INSERT INTO contacts (id, org_id, first_name, last_name, email, company, status, owner_id, tags, last_activity_at, created_at, updated_at) VALUES ('rls-cross-write', 'rls-org-1', 'RLS', 'Probe', 'rls@example.invalid', 'RLS Probe', 'active', 'system', '[]'::json, now(), now(), now())")
            )
