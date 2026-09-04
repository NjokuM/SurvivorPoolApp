"""add notification tables and user preferences

Revision ID: 77fa5b7d2dcb
Revises: 92060fa725f3
Create Date: 2026-09-04 15:17:54.073708

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77fa5b7d2dcb'
down_revision: Union[str, Sequence[str], None] = '92060fa725f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("notifications_enabled", sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("users", sa.Column("deadline_reminders_enabled", sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("users", sa.Column("result_notifications_enabled", sa.Boolean(), nullable=False, server_default="true"))

    op.create_table(
        "push_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("platform", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "notification_logs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("pool_id", sa.Integer(), sa.ForeignKey("pools.id"), nullable=False),
        sa.Column("gameweek", sa.Integer(), nullable=False),
        sa.Column("notification_type", sa.String(), nullable=False),
        sa.Column("sent_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "user_id", "pool_id", "gameweek", "notification_type", "sent_date",
            name="uq_notification_log_slot",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("notification_logs")
    op.drop_table("push_tokens")
    op.drop_column("users", "result_notifications_enabled")
    op.drop_column("users", "deadline_reminders_enabled")
    op.drop_column("users", "notifications_enabled")
