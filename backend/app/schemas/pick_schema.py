from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class PickResultEnum(str, Enum):
    WIN = "WIN"
    LOSS = "LOSS"
    DRAW = "DRAW"

class PickBase(BaseModel):
    pool_id: int
    user_id: int
    team_id: int
    fixture_id: int

class PickCreate(PickBase):
    """Used when creating a new pick — only requires IDs."""
    pass

class PickRead(PickBase):
    """Returned when reading picks from DB."""
    id: int
    competition_id : int
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    result: Optional[PickResultEnum] = None
    points: int | None
    created_at: datetime

    class Config:
        orm_mode = True

class PickUpdate(BaseModel):
    team_id: Optional[int] = None
    fixture_id: Optional[int] = None


class AdminPickEntry(BaseModel):
    fixture_id: int
    team_id: int


class AdminPicksImportRequest(BaseModel):
    """Picks to add or correct for one user in one pool - existing picks for
    gameweeks not mentioned here are left untouched, and their results are
    simply recomputed identically since the underlying fixture data hasn't
    changed."""
    picks: List[AdminPickEntry]


class AdminPicksImportResponse(BaseModel):
    pool_id: int
    user_id: int
    start_gameweek: int
    lives_left: int
    total_points: int
    eliminated_gameweek: Optional[int] = None
    picks_applied: int
    gameweeks_replayed: List[int]
