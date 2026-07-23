"""021 — Lot F / S33 domain events + inbound webhooks + execution provenance."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "021_domain_events"
down_revision: Union[str, None] = "020_catalog_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "domain_events",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("org_id", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("triggered_workflow_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_domain_events_org_id", "domain_events", ["org_id"])
    op.create_index("ix_domain_events_event_type", "domain_events", ["event_type"])

    op.create_table(
        "webhook_endpoints",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("org_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("token", sa.String(64), nullable=False),
        sa.Column("secret", sa.String(128), nullable=True),
        sa.Column("event_types", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("description", sa.String(512), nullable=False),
        sa.Column("last_received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("receive_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index("ix_webhook_endpoints_org_id", "webhook_endpoints", ["org_id"])
    op.create_index("ix_webhook_endpoints_token", "webhook_endpoints", ["token"])

    with op.batch_alter_table("workflow_executions") as batch:
        batch.add_column(sa.Column("event_id", sa.String(64), nullable=True))
        batch.add_column(sa.Column("trigger_source", sa.String(64), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("workflow_executions") as batch:
        batch.drop_column("trigger_source")
        batch.drop_column("event_id")
    op.drop_index("ix_webhook_endpoints_token", table_name="webhook_endpoints")
    op.drop_index("ix_webhook_endpoints_org_id", table_name="webhook_endpoints")
    op.drop_table("webhook_endpoints")
    op.drop_index("ix_domain_events_event_type", table_name="domain_events")
    op.drop_index("ix_domain_events_org_id", table_name="domain_events")
    op.drop_table("domain_events")
