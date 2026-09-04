"""add source column to picks

Revision ID: 92060fa725f3
Revises: e2f6a8c4d1b9
Create Date: 2026-08-29 17:30:42.853621

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '92060fa725f3'
down_revision: Union[str, Sequence[str], None] = 'e2f6a8c4d1b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "picks",
        sa.Column("source", sa.String(), nullable=False, server_default="user"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("picks", "source")
