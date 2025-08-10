from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum, UniqueConstraint, func
from sqlalchemy.orm import relationship
from app.models.base import Base
import enum

class PickResultEnum(enum.Enum):
    WIN = "WIN"
    LOSS = "LOSS"
    DRAW = "DRAW"

class Pick(Base):
    __tablename__ = "picks"

    id = Column(Integer, primary_key=True, index=True)
    pool_id = Column(Integer, ForeignKey("pools.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False)
    home_score = Column(Integer)
    away_score = Column(Integer)
    result = Column(Enum(PickResultEnum))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("pool_id", "user_id", "fixture_id", name="uq_pick"),
    )

    pool = relationship("Pool")
    user = relationship("User")
    fixture = relationship("Fixture")