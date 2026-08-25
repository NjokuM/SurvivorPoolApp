"""add has_lives to pools

Revision ID: e2f6a8c4d1b9
Revises: b8d3f5a7c9e1
Create Date: 2026-08-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2f6a8c4d1b9'
down_revision: Union[str, Sequence[str], None] = 'b8d3f5a7c9e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # League-mode pools (has_lives=False) track standings purely by points -
    # no elimination. Defaults true so every existing pool keeps its current
    # survivor behavior.
    op.add_column('pools', sa.Column('has_lives', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    op.drop_column('pools', 'has_lives')
