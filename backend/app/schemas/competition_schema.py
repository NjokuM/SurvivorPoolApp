from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class LeagueFilters(BaseModel):
    id : Optional[int] = Field(None)
    name : Optional[str] = Field(None)
    # Optional and unfiltered by default: GET /competitions/leagues uses this
    # same schema to list DB rows, and a competition now spans multiple
    # season rows per league - a hardcoded default season here would silently
    # hide every other season's data from that endpoint (as happened before
    # this was made Optional). Pass season explicitly when calling the sync
    # endpoint for a specific season.
    season : Optional[int] = Field(None, description="Filter to a specific season; omit for all seasons")
    country : Optional[str] = Field(None)
    type : Optional[str] = Field(None) # Type of competition (League or Cup)

class LeagueCreate(BaseModel):
    external_id: int
    name: str
    season: int
    country: str
    type: Optional[str] = None
    logo: str

class TeamFilters(BaseModel):
    league : Optional[int] = Field(None)
    season : int = Field(2026, description="Defaults to current season")
    id : Optional[int] = Field(None) # Team id
    name : Optional[str] = Field(None)
    code : Optional[str] = Field(None) # The short name of a team

class TeamCreate(BaseModel):
    external_id : int 
    name : str
    short_name : str | None = None
    competition_id : int | None = None
    venue_name : str | None = None
    venue_id: int | None = None
    logo : str | None = None

class FixtureFilters(BaseModel):
    league : int
    season : int = Field(2026, description="Defaults to current season")
    round: Optional[str] = Field(None) # Uses a string format e.g Regular Season - 10
    team: Optional[int] = Field(None) # Uses a team ID 
    venue: Optional[int] = Field(None) # Uses a the venues ID 

class FixtureCreate(BaseModel):
    competition_id: int
    external_id: int
    home_team_id: int
    away_team_id: int
    gameweek: int
    kickoff_time: datetime # league.round within the football api
    status: Optional[str] = None
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None
    referee: Optional[str] = None

class FixtureUpdate(BaseModel):
    external_id: int
    kickoff_time: Optional[datetime] = None
    status: Optional[str] = None
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None
    referee: Optional[str] = None