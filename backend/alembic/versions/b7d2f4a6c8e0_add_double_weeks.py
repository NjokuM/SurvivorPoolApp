"""add double weeks: pools.double_weeks allowance and double_weeks activations

Revision ID: b7d2f4a6c8e0
Revises: a3c5e7f9b2d4
Create Date: 2026-11-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7d2f4a6c8e0'
down_revision: Union[str, Sequence[str], None] = 'a3c5e7f9b2d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('pools', sa.Column('double_weeks', sa.Integer(), nullable=False, server_default='0'))
    op.create_table(
        'double_weeks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pool_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('gameweek', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['pool_id'], ['pools.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pool_id', 'user_id', 'gameweek', name='uq_double_week'),
    )
    op.create_index(op.f('ix_double_weeks_id'), 'double_weeks', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_double_weeks_id'), table_name='double_weeks')
    op.drop_table('double_weeks')
    op.drop_column('pools', 'double_weeks')
