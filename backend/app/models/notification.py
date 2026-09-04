from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship
from app.models.base import Base


class PushToken(Base):
    """One Expo push token per user - the most recently registered device
    wins. Fine for a casual friend-group app; not trying to fan out to
    every device a user has ever logged in on."""
    __tablename__ = "push_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    token = Column(String, nullable=False)
    platform = Column(String, nullable=True)  # 'ios' | 'android'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")


class NotificationLog(Base):
    """Records a notification as sent so the scheduler (ticking every ~30
    min) never sends the same one twice.

    sent_date is a plain calendar Date (not a timestamp) so daily_unpicked
    can fire once per day: the app only ever inserts one row per
    (user, pool, gameweek, type) for day_before/four_hour/pick_result, but
    inserts a fresh row each day for daily_unpicked - the unique constraint
    is a safety net against a double-insert race either way.
    """
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pool_id = Column(Integer, ForeignKey("pools.id"), nullable=False)
    gameweek = Column(Integer, nullable=False)
    notification_type = Column(String, nullable=False)  # day_before | four_hour | daily_unpicked | pick_result
    sent_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "user_id", "pool_id", "gameweek", "notification_type", "sent_date",
            name="uq_notification_log_slot",
        ),
    )
