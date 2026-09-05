"""Track RAG document versions and embedding provenance."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "026_rag_provider_metadata"
down_revision: Union[str, None] = "025_workflow_step_history"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("kb_documents") as batch:
        batch.add_column(sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    with op.batch_alter_table("kb_chunks") as batch:
        batch.add_column(sa.Column("embedding_provider", sa.String(length=64), nullable=False, server_default="local_hash"))
        batch.add_column(sa.Column("embedding_model", sa.String(length=128), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("kb_chunks") as batch:
        batch.drop_column("embedding_model")
        batch.drop_column("embedding_provider")
    with op.batch_alter_table("kb_documents") as batch:
        batch.drop_column("version")
