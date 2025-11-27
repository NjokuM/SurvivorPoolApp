"""Fix teams competition_id FK to point to competitions.id instead of external_id

Revision ID: 1ba7c9c48e63
Revises: 997167814348
Create Date: 2025-11-27 19:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1ba7c9c48e63'
down_revision: Union[str, Sequence[str], None] = '997167814348'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Fix FK to point to competitions.id"""
    # Drop the existing foreign key constraint
    op.drop_constraint('teams_competition_id_fkey', 'teams', type_='foreignkey')
    
    # Recreate the foreign key pointing to competitions.id instead of external_id
    op.create_foreign_key(
        'teams_competition_id_fkey',  # constraint name
        'teams',                       # source table
        'competitions',                # target table
        ['competition_id'],            # source column
        ['id']                         # target column (was external_id, now id)
    )


def downgrade() -> None:
    """Downgrade schema - Revert FK to point to competitions.external_id"""
    # Drop the fixed foreign key
    op.drop_constraint('teams_competition_id_fkey', 'teams', type_='foreignkey')
    
    # Recreate the old (incorrect) foreign key pointing to external_id
    op.create_foreign_key(
        'teams_competition_id_fkey',
        'teams',
        'competitions',
        ['competition_id'],
        ['external_id']
    )