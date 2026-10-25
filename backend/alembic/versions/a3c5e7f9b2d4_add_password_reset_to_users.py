"""add password reset code columns to users

Revision ID: a3c5e7f9b2d4
Revises: 77fa5b7d2dcb
Create Date: 2026-10-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3c5e7f9b2d4'
down_revision: Union[str, Sequence[str], None] = '77fa5b7d2dcb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('password_reset_code_hash', sa.String(), nullable=True))
    op.add_column('users', sa.Column('password_reset_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('password_reset_attempts', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('users', 'password_reset_attempts')
    op.drop_column('users', 'password_reset_expires_at')
    op.drop_column('users', 'password_reset_code_hash')
