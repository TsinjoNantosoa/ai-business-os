"""Lot E / S32 — persist React Flow graph on workflows."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "019_workflow_definition"
down_revision: Union[str, None] = "018_ai_pending_actions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("workflows") as batch:
        batch.add_column(sa.Column("definition", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("workflows") as batch:
        batch.drop_column("definition")
