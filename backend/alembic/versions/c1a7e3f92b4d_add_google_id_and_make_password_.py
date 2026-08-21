"""add google_id and make password nullable on users

Revision ID: c1a7e3f92b4d
Revises: 8f2c4a6d9b31
Create Date: 2026-08-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1a7e3f92b4d'
down_revision: Union[str, Sequence[str], None] = '8f2c4a6d9b31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('google_id', sa.String(), nullable=True))
    op.create_index(op.f('ix_users_google_id'), 'users', ['google_id'], unique=True)
    op.alter_column('users', 'password',
               existing_type=sa.String(),
               nullable=True)


def downgrade() -> None:
    op.alter_column('users', 'password',
               existing_type=sa.String(),
               nullable=False)
    op.drop_index(op.f('ix_users_google_id'), table_name='users')
    op.drop_column('users', 'google_id')
