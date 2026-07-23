"""022 — S34 AI traces + LLM call cost tracking."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "022_ai_observability"
down_revision: Union[str, None] = "021_domain_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_traces",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("org_id", sa.String(64), nullable=False),
        sa.Column("user_id", sa.String(64), nullable=True),
        sa.Column("agent_id", sa.String(64), nullable=True),
        sa.Column("conversation_id", sa.String(64), nullable=True),
        sa.Column("correlation_id", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("model", sa.String(64), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tools_used", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_traces_org_id", "ai_traces", ["org_id"])
    op.create_index("ix_ai_traces_agent_id", "ai_traces", ["agent_id"])
    op.create_index("ix_ai_traces_user_id", "ai_traces", ["user_id"])

    op.create_table(
        "ai_llm_calls",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("org_id", sa.String(64), nullable=False),
        sa.Column("trace_id", sa.String(64), nullable=False),
        sa.Column("user_id", sa.String(64), nullable=True),
        sa.Column("agent_id", sa.String(64), nullable=True),
        sa.Column("conversation_id", sa.String(64), nullable=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("model", sa.String(64), nullable=False),
        sa.Column("purpose", sa.String(32), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["trace_id"], ["ai_traces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_llm_calls_org_id", "ai_llm_calls", ["org_id"])
    op.create_index("ix_ai_llm_calls_trace_id", "ai_llm_calls", ["trace_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_llm_calls_trace_id", table_name="ai_llm_calls")
    op.drop_index("ix_ai_llm_calls_org_id", table_name="ai_llm_calls")
    op.drop_table("ai_llm_calls")
    op.drop_index("ix_ai_traces_user_id", table_name="ai_traces")
    op.drop_index("ix_ai_traces_agent_id", table_name="ai_traces")
    op.drop_index("ix_ai_traces_org_id", table_name="ai_traces")
    op.drop_table("ai_traces")
