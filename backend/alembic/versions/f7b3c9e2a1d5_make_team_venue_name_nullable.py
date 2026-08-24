"""make team venue_name nullable

Revision ID: f7b3c9e2a1d5
Revises: d4e8f1a9c2b7
Create Date: 2026-08-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7b3c9e2a1d5'
down_revision: Union[str, Sequence[str], None] = 'd4e8f1a9c2b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Smaller/lower-tier clubs don't always have venue data in the API -
    # syncing them crashed on this NOT NULL constraint (e.g. Kerry FC in the
    # Irish First Division).
    op.alter_column('teams', 'venue_name',
               existing_type=sa.String(),
               nullable=True)


def downgrade() -> None:
    op.alter_column('teams', 'venue_name',
               existing_type=sa.String(),
               nullable=False)
