"""Tenant-wide RLS coverage and persistent refresh sessions."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "024_tenant_security_sessions"
down_revision: Union[str, None] = "023_plan_ai_rpm"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_NEW_RLS_TABLES = (
    "users",
    "tenant_feature_overrides",
    "oauth_identities",
    "kb_documents",
    "kb_chunks",
    "sales_orders",
    "campaigns",
    "projects",
    "calendar_events",
    "meetings",
    "ticket_messages",
    "employees",
    "job_openings",
    "candidates",
    "suppliers",
    "purchase_orders",
    "contracts",
    "inventory_items",
    "finance_transactions",
    "knowledge_articles",
    "ai_agents",
    "org_datasets",
    "ai_pending_actions",
    "domain_events",
    "webhook_endpoints",
    "ai_traces",
    "ai_llm_calls",
    "refresh_sessions",
)


def _tenant_policy(table: str) -> None:
    op.execute(sa.text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))
    op.execute(sa.text(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}"))
    op.execute(
        sa.text(
            f"""
            CREATE POLICY tenant_isolation_{table} ON {table}
            USING (org_id = current_setting('app.current_org_id', true))
            WITH CHECK (org_id = current_setting('app.current_org_id', true))
            """
        )
    )


def upgrade() -> None:
    op.create_table(
        "stripe_webhook_events",
        sa.Column("event_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("ix_stripe_webhook_events_event_type", "stripe_webhook_events", ["event_type"])
    op.create_table(
        "refresh_sessions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("org_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("family_id", sa.String(length=64), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by_id", sa.String(length=64), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_refresh_sessions_org_id", "refresh_sessions", ["org_id"])
    op.create_index("ix_refresh_sessions_user_id", "refresh_sessions", ["user_id"])
    op.create_index("ix_refresh_sessions_family_id", "refresh_sessions", ["family_id"])
    op.create_index("ix_refresh_sessions_expires_at", "refresh_sessions", ["expires_at"])

    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for table in _NEW_RLS_TABLES:
        _tenant_policy(table)

    for table in ("kb_documents", "kb_chunks"):
        op.execute(sa.text(f"DROP POLICY tenant_isolation_{table} ON {table}"))
        op.execute(sa.text(f"""
            CREATE POLICY tenant_isolation_{table} ON {table}
            USING (org_id = current_setting('app.current_org_id', true) OR org_id = 'platform')
            WITH CHECK (org_id = current_setting('app.current_org_id', true))
        """))

    # Narrow bootstrap policies: each pre-auth lookup must first set the exact
    # opaque credential it is attempting to resolve. They do not permit scans.
    op.execute(sa.text("""
        CREATE POLICY auth_lookup_api_keys ON api_keys FOR SELECT
        USING (key_hash = current_setting('app.auth_api_key_hash', true))
    """))
    op.execute(sa.text("""
        CREATE POLICY auth_lookup_refresh_sessions ON refresh_sessions FOR SELECT
        USING (id = current_setting('app.auth_refresh_sid', true))
    """))
    op.execute(sa.text("""
        CREATE POLICY auth_lookup_users_email ON users FOR SELECT
        USING (lower(email) = lower(current_setting('app.auth_email', true)))
    """))
    op.execute(sa.text("""
        CREATE POLICY auth_lookup_users_id ON users FOR SELECT
        USING (id = current_setting('app.auth_user_id', true))
    """))
    op.execute(sa.text("""
        CREATE POLICY auth_lookup_oauth_identity ON oauth_identities FOR SELECT
        USING ((provider || ':' || provider_subject) = current_setting('app.auth_oauth_subject', true))
    """))
    op.execute(sa.text("""
        CREATE POLICY auth_lookup_invitations_email ON invitations FOR SELECT
        USING (lower(email) = lower(current_setting('app.auth_email', true)))
    """))
    op.execute(sa.text("""
        CREATE POLICY stripe_lookup_subscriptions ON subscriptions
        USING (stripe_subscription_id = current_setting('app.stripe_subscription_id', true))
        WITH CHECK (stripe_subscription_id = current_setting('app.stripe_subscription_id', true))
    """))
    op.execute(sa.text("""
        CREATE POLICY stripe_lookup_billing_invoices ON billing_invoices
        USING (stripe_invoice_id = current_setting('app.stripe_invoice_id', true))
        WITH CHECK (stripe_invoice_id = current_setting('app.stripe_invoice_id', true))
    """))


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(sa.text("DROP POLICY IF EXISTS stripe_lookup_billing_invoices ON billing_invoices"))
        op.execute(sa.text("DROP POLICY IF EXISTS stripe_lookup_subscriptions ON subscriptions"))
        op.execute(sa.text("DROP POLICY IF EXISTS auth_lookup_invitations_email ON invitations"))
        op.execute(sa.text("DROP POLICY IF EXISTS auth_lookup_oauth_identity ON oauth_identities"))
        op.execute(sa.text("DROP POLICY IF EXISTS auth_lookup_users_id ON users"))
        op.execute(sa.text("DROP POLICY IF EXISTS auth_lookup_users_email ON users"))
        op.execute(sa.text("DROP POLICY IF EXISTS auth_lookup_refresh_sessions ON refresh_sessions"))
        op.execute(sa.text("DROP POLICY IF EXISTS auth_lookup_api_keys ON api_keys"))
        for table in reversed(_NEW_RLS_TABLES):
            op.execute(sa.text(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}"))
            op.execute(sa.text(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY"))
    op.drop_index("ix_refresh_sessions_expires_at", table_name="refresh_sessions")
    op.drop_index("ix_refresh_sessions_family_id", table_name="refresh_sessions")
    op.drop_index("ix_refresh_sessions_user_id", table_name="refresh_sessions")
    op.drop_index("ix_refresh_sessions_org_id", table_name="refresh_sessions")
    op.drop_table("refresh_sessions")
    op.drop_index("ix_stripe_webhook_events_event_type", table_name="stripe_webhook_events")
    op.drop_table("stripe_webhook_events")
