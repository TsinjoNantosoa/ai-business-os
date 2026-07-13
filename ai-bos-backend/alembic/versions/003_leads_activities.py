"""Leads and activities tables."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_leads_activities"
down_revision: Union[str, None] = "002_billing_contacts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "leads",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("org_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("contact_name", sa.String(length=255), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False),
        sa.Column("owner_id", sa.String(length=64), nullable=False),
        sa.Column("owner_name", sa.String(length=128), nullable=False),
        sa.Column("owner_avatar_color", sa.String(length=64), nullable=False),
        sa.Column("expected_close_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("stage_changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_leads_org_id", "leads", ["org_id"], unique=False)

    op.create_table(
        "activities",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("org_id", sa.String(length=64), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=False),
        sa.Column("contact_id", sa.String(length=64), nullable=True),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("user_name", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_activities_org_id", "activities", ["org_id"], unique=False)
    op.create_index("ix_activities_contact_id", "activities", ["contact_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_activities_contact_id", table_name="activities")
    op.drop_index("ix_activities_org_id", table_name="activities")
    op.drop_table("activities")
    op.drop_index("ix_leads_org_id", table_name="leads")
    op.drop_table("leads")
