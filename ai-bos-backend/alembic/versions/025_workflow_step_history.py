"""Durable workflow step history and idempotency keys."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "025_workflow_step_history"
down_revision: Union[str, None] = "024_tenant_security_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workflow_step_executions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("org_id", sa.String(length=64), nullable=False),
        sa.Column("workflow_id", sa.String(length=64), nullable=False),
        sa.Column("execution_id", sa.String(length=64), nullable=False),
        sa.Column("step_key", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("input_data", sa.JSON(), nullable=False),
        sa.Column("output_data", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["execution_id"], ["workflow_executions.id"]),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("execution_id", "step_key", name="uq_workflow_step_once"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index("ix_workflow_step_executions_org_id", "workflow_step_executions", ["org_id"])
    op.create_index("ix_workflow_step_executions_workflow_id", "workflow_step_executions", ["workflow_id"])
    op.create_index("ix_workflow_step_executions_execution_id", "workflow_step_executions", ["execution_id"])

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(sa.text("ALTER TABLE workflow_step_executions ENABLE ROW LEVEL SECURITY"))
        op.execute(sa.text("ALTER TABLE workflow_step_executions FORCE ROW LEVEL SECURITY"))
        op.execute(sa.text("""
            CREATE POLICY tenant_isolation_workflow_step_executions ON workflow_step_executions
            USING (org_id = current_setting('app.current_org_id', true))
            WITH CHECK (org_id = current_setting('app.current_org_id', true))
        """))


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(sa.text("DROP POLICY IF EXISTS tenant_isolation_workflow_step_executions ON workflow_step_executions"))
        op.execute(sa.text("ALTER TABLE workflow_step_executions DISABLE ROW LEVEL SECURITY"))
    op.drop_index("ix_workflow_step_executions_execution_id", table_name="workflow_step_executions")
    op.drop_index("ix_workflow_step_executions_workflow_id", table_name="workflow_step_executions")
    op.drop_index("ix_workflow_step_executions_org_id", table_name="workflow_step_executions")
    op.drop_table("workflow_step_executions")
