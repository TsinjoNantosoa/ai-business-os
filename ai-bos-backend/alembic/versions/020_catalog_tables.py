"""020 — Persist remaining seed modules into SQL tables (Postgres-ready)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "020_catalog_tables"
down_revision: Union[str, None] = "019_workflow_definition"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "employees",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("org_id", sa.String(64), nullable=False),
        sa.Column("first_name", sa.String(128), nullable=False),
        sa.Column("last_name", sa.String(128), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("position", sa.String(128), nullable=False),
        sa.Column("department", sa.String(128), nullable=False),
        sa.Column("start_date", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("avatar_color", sa.String(64), nullable=True),
        sa.Column("salary", sa.Float(), nullable=True),
        sa.Column("location", sa.String(128), nullable=True),
        sa.Column("manager_id", sa.String(64), nullable=True),
        *_ts(),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_employees_org_id", "employees", ["org_id"])

    op.create_table(
        "job_openings",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("org_id", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("department", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("applicants", sa.Integer(), nullable=False),
        sa.Column("posted_date", sa.String(32), nullable=False),
        sa.Column("location", sa.String(128), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        *_ts(),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_openings_org_id", "job_openings", ["org_id"])

    op.create_table(
        "candidates",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("org_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("job_id", sa.String(64), nullable=True),
        sa.Column("job_title", sa.String(255), nullable=True),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("avatar_color", sa.String(64), nullable=True),
        sa.Column("applied_at", sa.String(32), nullable=False),
        *_ts(),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_candidates_org_id", "candidates", ["org_id"])

    op.create_table(
        "suppliers",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("org_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("rating", sa.Float(), nullable=False),
        sa.Column("country", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        *_ts(),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_suppliers_org_id", "suppliers", ["org_id"])

    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("org_id", sa.String(64), nullable=False),
        sa.Column("po_number", sa.String(32), nullable=False),
        sa.Column("supplier_id", sa.String(64), nullable=True),
        sa.Column("supplier_name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False),
        sa.Column("created_at_iso", sa.String(32), nullable=False),
        sa.Column("expected_at", sa.String(32), nullable=False),
        sa.Column("owner_name", sa.String(128), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False),
        *_ts(),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_purchase_orders_org_id", "purchase_orders", ["org_id"])

    op.create_table(
        "contracts",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("org_id", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("counterparty", sa.String(255), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False),
        sa.Column("start_date", sa.String(32), nullable=False),
        sa.Column("end_date", sa.String(32), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("owner", sa.String(128), nullable=False),
        *_ts(),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contracts_org_id", "contracts", ["org_id"])

    op.create_table(
        "inventory_items",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("org_id", sa.String(64), nullable=False),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(128), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("reorder_level", sa.Integer(), nullable=False),
        sa.Column("warehouse", sa.String(128), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        *_ts(),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inventory_items_org_id", "inventory_items", ["org_id"])

    op.create_table(
        "finance_transactions",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("org_id", sa.String(64), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("type", sa.String(16), nullable=False),
        sa.Column("category", sa.String(128), nullable=False),
        sa.Column("date", sa.String(32), nullable=False),
        sa.Column("account", sa.String(128), nullable=False),
        *_ts(),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_finance_transactions_org_id", "finance_transactions", ["org_id"])

    op.create_table(
        "knowledge_articles",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("org_id", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("category", sa.String(128), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("author", sa.String(128), nullable=False),
        sa.Column("updated_at_iso", sa.String(32), nullable=False),
        sa.Column("views", sa.Integer(), nullable=False),
        sa.Column("helpful", sa.Integer(), nullable=False),
        *_ts(),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_articles_org_id", "knowledge_articles", ["org_id"])

    op.create_table(
        "ai_agents",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("org_id", sa.String(64), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("icon", sa.String(64), nullable=False),
        sa.Column("tools_count", sa.Integer(), nullable=False),
        sa.Column("last_used", sa.String(32), nullable=True),
        sa.Column("conversations", sa.Integer(), nullable=False),
        *_ts(),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_agents_org_id", "ai_agents", ["org_id"])

    op.create_table(
        "org_datasets",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("org_id", sa.String(64), nullable=False),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        *_ts(),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("org_id", "key", name="uq_org_datasets_org_key"),
    )
    op.create_index("ix_org_datasets_org_id", "org_datasets", ["org_id"])


def downgrade() -> None:
    for table in [
        "org_datasets",
        "ai_agents",
        "knowledge_articles",
        "finance_transactions",
        "inventory_items",
        "contracts",
        "purchase_orders",
        "suppliers",
        "candidates",
        "job_openings",
        "employees",
    ]:
        op.drop_table(table)
