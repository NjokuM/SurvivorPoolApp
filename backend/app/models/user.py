from sqlalchemy import Column, Integer, String, Boolean, DateTime,func
from app.models.base import Base

class User(Base):
    __tablename__= "users"

    id = Column(Integer, primary_key=True, index=True)
    userName = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    firstName = Column(String, nullable=False)
    lastName = Column(String, nullable=False)
    password = Column(String, nullable=True)
    google_id = Column(String, unique=True, nullable=True, index=True)
    apple_id = Column(String, unique=True, nullable=True, index=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)
    # Maps directly to the three toggles on the Notifications settings
    # screen. notifications_enabled is the master switch - the other two
    # are only meaningful when it's on.
    notifications_enabled = Column(Boolean, nullable=False, default=True, server_default="true")
    deadline_reminders_enabled = Column(Boolean, nullable=False, default=True, server_default="true")
    result_notifications_enabled = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
