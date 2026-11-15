"""add pool_user_stats.double_weeks_override for per-member double weeks

Revision ID: c4e8a2d6f1b3
Revises: b7d2f4a6c8e0
Create Date: 2026-11-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4e8a2d6f1b3'
down_revision: Union[str, Sequence[str], None] = 'b7d2f4a6c8e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('pool_user_stats', sa.Column('double_weeks_override', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('pool_user_stats', 'double_weeks_override')
