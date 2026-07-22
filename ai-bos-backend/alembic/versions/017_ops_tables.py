"""Lot B tables: sales_orders, campaigns, projects, calendar_events, meetings."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "017_ops_tables"
down_revision: Union[str, None] = "016_password_reset_codes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _common_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("org_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "sales_orders",
        *_common_columns(),
        sa.Column("order_number", sa.String(length=32), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=True),
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("date", sa.String(length=32), nullable=False),
        sa.Column("sales_rep_id", sa.String(length=64), nullable=True),
        sa.Column("sales_rep_name", sa.String(length=128), nullable=True),
        sa.Column("line_items", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sales_orders_org_id", "sales_orders", ["org_id"], unique=False)

    op.create_table(
        "campaigns",
        *_common_columns(),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reach", sa.Integer(), nullable=False),
        sa.Column("open_rate", sa.Float(), nullable=False),
        sa.Column("click_rate", sa.Float(), nullable=False),
        sa.Column("conversions", sa.Integer(), nullable=False),
        sa.Column("budget", sa.Float(), nullable=False),
        sa.Column("spent", sa.Float(), nullable=False),
        sa.Column("start_date", sa.String(length=32), nullable=False),
        sa.Column("end_date", sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_campaigns_org_id", "campaigns", ["org_id"], unique=False)

    op.create_table(
        "projects",
        *_common_columns(),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.String(length=32), nullable=False),
        sa.Column("end_date", sa.String(length=32), nullable=True),
        sa.Column("budget", sa.Float(), nullable=False),
        sa.Column("spent", sa.Float(), nullable=False),
        sa.Column("team_members", sa.JSON(), nullable=False),
        sa.Column("task_count", sa.Integer(), nullable=False),
        sa.Column("completed_tasks", sa.Integer(), nullable=False),
        sa.Column("color", sa.String(length=16), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_projects_org_id", "projects", ["org_id"], unique=False)

    op.create_table(
        "calendar_events",
        *_common_columns(),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("start_date", sa.String(length=40), nullable=False),
        sa.Column("end_date", sa.String(length=40), nullable=True),
        sa.Column("color", sa.String(length=16), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("attendees", sa.JSON(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_calendar_events_org_id", "calendar_events", ["org_id"], unique=False)

    op.create_table(
        "meetings",
        *_common_columns(),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("date", sa.String(length=32), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("attendees", sa.JSON(), nullable=False),
        sa.Column("agenda", sa.JSON(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("action_items", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_meetings_org_id", "meetings", ["org_id"], unique=False)


def downgrade() -> None:
    for table in ("meetings", "calendar_events", "projects", "campaigns", "sales_orders"):
        op.drop_index(f"ix_{table}_org_id", table_name=table)
        op.drop_table(table)
