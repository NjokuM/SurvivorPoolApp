"""add apple_id to users

Revision ID: b8d3f5a7c9e1
Revises: f7b3c9e2a1d5
Create Date: 2026-08-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8d3f5a7c9e1'
down_revision: Union[str, Sequence[str], None] = 'f7b3c9e2a1d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('apple_id', sa.String(), nullable=True))
    op.create_index(op.f('ix_users_apple_id'), 'users', ['apple_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_apple_id'), table_name='users')
    op.drop_column('users', 'apple_id')
