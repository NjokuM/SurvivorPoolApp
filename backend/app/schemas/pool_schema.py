from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PoolBase(BaseModel):
    name: str = Field(example = "Premier League Pool")
    description: Optional[str] = Field(None,example="Weekly survivor challenge")
    competition_id: int
    # Optional fields handled automatically by the backend if not provided
    start_gameweek: Optional[int] = None
    max_picks_per_team: Optional[int] = 2
    total_lives: Optional[int] = 3

class PoolCreate(PoolBase):
    created_by: int

class PoolResponse(PoolBase):
    id: int
    participant_count: int

    class Config:
        orm_mode = True  # allows returning SQLAlchemy objects directly

class PoolUserStatsBase(BaseModel):
    pool_id: int
    user_id: int

class PoolJoinRequest(BaseModel):
    user_id: int

class PoolJoinByCodeRequest(BaseModel):
    user_id: int
    session_code: str
    
class PoolUserStatsResponse(PoolUserStatsBase):
    id: int
    pool_id : int
    user_id : int
    lives_left: int
    eliminated_gameweek: Optional[int] = None
    created_at: datetime
    updated_at : datetime

    class Config:
        orm_mode = True

class PoolWithUsers(PoolResponse):
    users_stats: List[PoolUserStatsResponse] = []

class LeaderboardEntry(BaseModel):
    user_id: int
    username: str
    lives_left: int
    total_points: int
    eliminated_gameweek: Optional[int]
    is_eliminated: bool
    rank: int

    class Config:
        from_attributes = True