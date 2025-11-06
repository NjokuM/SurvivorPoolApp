from pydantic import BaseModel
from typing import Optional, List

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
