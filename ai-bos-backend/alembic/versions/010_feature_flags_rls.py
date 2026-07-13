"""Feature flags catalog + tenant overrides + optional Postgres RLS helpers."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010_feature_flags_rls"
down_revision: Union[str, None] = "009_invitations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables that carry org_id and should get RLS policies on PostgreSQL.
_RLS_TABLES = (
    "contacts",
    "leads",
    "activities",
    "finance_invoices",
    "workflows",
    "workflow_executions",
    "tasks",
    "tickets",
    "documents",
    "audit_logs",
    "invitations",
    "subscriptions",
    "billing_invoices",
)


def upgrade() -> None:
    op.create_table(
        "feature_flags",
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("env", sa.String(length=32), nullable=False),
        sa.Column("default_enabled", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )

    op.create_table(
        "tenant_feature_overrides",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("org_id", sa.String(length=64), nullable=False),
        sa.Column("flag_key", sa.String(length=64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("updated_by", sa.String(length=64), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["flag_key"], ["feature_flags.key"]),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("org_id", "flag_key", name="uq_tenant_flag"),
    )
    op.create_index("ix_tenant_feature_overrides_org_id", "tenant_feature_overrides", ["org_id"], unique=False)
    op.create_index("ix_tenant_feature_overrides_flag_key", "tenant_feature_overrides", ["flag_key"], unique=False)

    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    # Application sets: SET LOCAL app.current_org_id = '<org>'
    for table in _RLS_TABLES:
        op.execute(sa.text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
        op.execute(sa.text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))
        op.execute(
            sa.text(
                f"""
                CREATE POLICY tenant_isolation_{table} ON {table}
                USING (org_id = current_setting('app.current_org_id', true))
                WITH CHECK (org_id = current_setting('app.current_org_id', true))
                """
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for table in reversed(_RLS_TABLES):
            op.execute(sa.text(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}"))
            op.execute(sa.text(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY"))

    op.drop_index("ix_tenant_feature_overrides_flag_key", table_name="tenant_feature_overrides")
    op.drop_index("ix_tenant_feature_overrides_org_id", table_name="tenant_feature_overrides")
    op.drop_table("tenant_feature_overrides")
    op.drop_table("feature_flags")
