from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PoolBase(BaseModel):
    name: str = Field(example = "Premier League Pool")
    description: Optional[str] = Field(None,example="Weekly survivor challenge")
    competition_id: int
    # Optional fields handled automatically by the backend if not provided
    start_gameweek: Optional[int] = None
    # None means "use the format-aware default" - computed at creation time
    # from how many gameweeks remain and how many teams are in the league,
    # since a flat default (e.g. always 2) can be too low to finish a full
    # season or unnecessarily high for a pool starting mid-season.
    max_picks_per_team: Optional[int] = None
    total_lives: Optional[int] = 3
    has_lives: Optional[bool] = Field(True, description="False for a league-style pool with no elimination - standings are points only")
    is_active: Optional[bool] = True

class PoolCreate(PoolBase):
    created_by: int

class PoolResponse(PoolBase):
    id: int
    session_code: str
    participant_count: int
    created_by: Optional[int] = None

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
    total_points: int = 0
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