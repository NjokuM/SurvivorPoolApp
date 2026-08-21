"""add NP to pick result enum and make team_id nullable

Revision ID: 45d778dcae94
Revises: c1a7e3f92b4d
Create Date: 2026-02-21 17:19:01.116237

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '45d778dcae94'
down_revision: Union[str, Sequence[str], None] = 'c1a7e3f92b4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE pickresultenum ADD VALUE IF NOT EXISTS 'NP'")
    op.alter_column('picks', 'team_id',
               existing_type=sa.INTEGER(),
               nullable=True)


def downgrade() -> None:
    op.alter_column('picks', 'team_id',
               existing_type=sa.INTEGER(),
               nullable=False)
