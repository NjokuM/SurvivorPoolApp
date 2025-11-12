from pydantic import BaseModel
from typing import Optional
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
