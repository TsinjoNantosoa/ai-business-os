"""Password reset by verification code: attempts counter, non-unique hash."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "016_password_reset_codes"
down_revision: Union[str, None] = "015_password_reset_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "password_reset_tokens",
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    # 6-digit codes can repeat across users: the hash can no longer be unique.
    op.drop_index("ix_password_reset_tokens_token_hash", table_name="password_reset_tokens")
    op.create_index(
        "ix_password_reset_tokens_token_hash",
        "password_reset_tokens",
        ["token_hash"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_password_reset_tokens_token_hash", table_name="password_reset_tokens")
    op.create_index(
        "ix_password_reset_tokens_token_hash",
        "password_reset_tokens",
        ["token_hash"],
        unique=True,
    )
    op.drop_column("password_reset_tokens", "attempts")
