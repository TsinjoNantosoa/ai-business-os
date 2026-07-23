"""023 — S35 plan AI RPM hard limits."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "023_plan_ai_rpm"
down_revision: Union[str, None] = "022_ai_observability"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("billing_plans") as batch:
        batch.add_column(sa.Column("ai_rpm", sa.Integer(), nullable=False, server_default="20"))

    # Plan-specific RPM (README_20 style)
    op.execute("UPDATE billing_plans SET ai_rpm = 10 WHERE code = 'starter'")
    op.execute("UPDATE billing_plans SET ai_rpm = 60 WHERE code = 'pro'")
    op.execute("UPDATE billing_plans SET ai_rpm = 200 WHERE code = 'enterprise'")


def downgrade() -> None:
    with op.batch_alter_table("billing_plans") as batch:
        batch.drop_column("ai_rpm")
