"""Lot D / S31 — HITL pending actions for sensitive AI tools."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "018_ai_pending_actions"
down_revision: Union[str, None] = "017_ops_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_pending_actions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("org_id", sa.String(length=64), nullable=False),
        sa.Column("conversation_id", sa.String(length=64), nullable=True),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("agent_id", sa.String(length=64), nullable=True),
        sa.Column("tool_name", sa.String(length=128), nullable=False),
        sa.Column("arguments", sa.JSON(), nullable=False),
        sa.Column("call_id", sa.String(length=64), nullable=False),
        sa.Column("user_message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("decided_by", sa.String(length=64), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_pending_actions_org_id", "ai_pending_actions", ["org_id"], unique=False)
    op.create_index("ix_ai_pending_actions_conversation_id", "ai_pending_actions", ["conversation_id"], unique=False)
    op.create_index("ix_ai_pending_actions_user_id", "ai_pending_actions", ["user_id"], unique=False)
    op.create_index("ix_ai_pending_actions_status", "ai_pending_actions", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ai_pending_actions_status", table_name="ai_pending_actions")
    op.drop_index("ix_ai_pending_actions_user_id", table_name="ai_pending_actions")
    op.drop_index("ix_ai_pending_actions_conversation_id", table_name="ai_pending_actions")
    op.drop_index("ix_ai_pending_actions_org_id", table_name="ai_pending_actions")
    op.drop_table("ai_pending_actions")
