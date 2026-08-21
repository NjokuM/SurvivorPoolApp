"""make competitions unique per (external_id, season) instead of globally

Revision ID: d4e8f1a9c2b7
Revises: 45d778dcae94
Create Date: 2026-08-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e8f1a9c2b7'
down_revision: Union[str, Sequence[str], None] = '45d778dcae94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # A league (external_id) now gets one row per season, so historical
    # fixtures stay tied to the season they actually happened in instead of
    # silently following the league's row forward when it rolls over.
    op.drop_constraint('competitions_external_id_key', 'competitions', type_='unique')
    op.drop_constraint('competitions_name_key', 'competitions', type_='unique')
    op.create_unique_constraint(
        'uq_competition_external_season', 'competitions', ['external_id', 'season']
    )


def downgrade() -> None:
    op.drop_constraint('uq_competition_external_season', 'competitions', type_='unique')
    op.create_unique_constraint('competitions_name_key', 'competitions', ['name'])
    op.create_unique_constraint('competitions_external_id_key', 'competitions', ['external_id'])
