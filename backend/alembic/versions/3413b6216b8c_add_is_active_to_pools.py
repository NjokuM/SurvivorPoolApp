"""add_is_active_to_pools

Revision ID: 3413b6216b8c
Revises: 37cb853773cd
Create Date: 2026-01-03 14:23:23.024851

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3413b6216b8c'
down_revision: Union[str, Sequence[str], None] = '37cb853773cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add is_active column with default true and backfill existing rows
    op.add_column(
        "pools",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    # Optional: drop the server default after creation if not desired for future inserts
    op.alter_column("pools", "is_active", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("pools", "is_active")
