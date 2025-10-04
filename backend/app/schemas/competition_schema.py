from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class LeagueFilters(BaseModel):
    id : Optional[int] = Field(None)
    season : int = Field(2025, description="Defaults to current season")
    country : Optional[str] = Field(None)
    type : Optional[str] = Field(None) # Type of competition (League or Cup)

class TeamFilters(BaseModel):
    league : Optional[int] = Field(None)
    season : int = Field(2025, description="Defaults to current season")
    id : Optional[int] = Field(None) # Team id
    name : Optional[str] = Field(None)
    code : Optional[str] = Field(None) # The short name of a team
    venue: Optional[int] = Field(None) 

class TeamCreate(BaseModel):
    id : int 
    name : str
    short_name : str | None = None
    competition_id : int | None = None
    venue_name : str | None = None

class FixtureFilters(BaseModel):
    league : int
    season : int = Field(2025, description="Defaults to current season")
    round: Optional[str] = Field(None) # Uses a string format e.g Regular Season - 10
    team: Optional[int] = Field(None) # Uses a team ID 
    venue: Optional[int] = Field(None) # Uses a the venues ID 

class FixtureCreate(BaseModel):
    id : int 
    competition_id : int
    home_team_id : int
    away_team_id : int
    gameweek : str
    kickoff_time : str # league.round within the football api
    pass