from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.models.base import Base

class Pool(Base):
    __tablename__ = "pools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)
    start_gameweek = Column(Integer, nullable=False)
    max_picks_per_team = Column(Integer, nullable=False, default=2)
    total_lives = Column(Integer, nullable=False, default=3)

    competition = relationship("Competition")
    users_stats = relationship("PoolUserStats", back_populates="pool")

class PoolUserStats(Base):
    __tablename__ = "pool_user_stats"

    id = Column(Integer, primary_key=True, index=True)
    pool_id = Column(Integer, ForeignKey("pools.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lives_left = Column(Integer, nullable=False)
    eliminated_gameweek = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    pool = relationship("Pool", back_populates="users_stats")
    user = relationship("User")