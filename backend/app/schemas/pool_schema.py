from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PoolBase(BaseModel):
    name: str
    description: Optional[str] = None
    competition_id: int
    start_gameweek: int
    max_picks_per_team: int = 2
    total_lives: int = 3

class PoolCreate(PoolBase):
    pass

class PoolResponse(PoolBase):
    id: int

    class Config:
        orm_mode = True  # allows returning SQLAlchemy objects directly

class PoolUserStatsBase(BaseModel):
    pool_id: int
    user_id: int
    lives_left: int
    eliminated_gameweek: Optional[int] = None

class PoolUserStatsCreate(PoolUserStatsBase):
    pass  # same fields when creating a new record

class PoolUserStatsRead(PoolUserStatsBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True