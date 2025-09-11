from fastapi import APIRouter, Depends
from app.schemas.competition_schema import TeamFilters , LeagueFilters, FixtureFilters
from app.services.football_api import get_fixtures, get_teams, get_competitions, get_teams_by_id, get_competition_by_id, get_fixtures_by_id
router = APIRouter(prefix="/competitons", tags=["Competitons"])

######### LEAGUES ########
@router.get("/")
async def get_leagues(filters: LeagueFilters=Depends()):
    data = await get_competitions(filters)
    return data

@router.get("/{competition_id}")
async def get_leagues_by_id(competition_id):
    data = await get_competition_by_id(competition_id)
    return data

######### TEAMS ########
@router.get("/teams")
async def fetch_teams(filters: TeamFilters=Depends()):
    data = await get_teams(filters)
    return data

@router.get("/teams/{team_id}")
async def get_team_by_id(team_id: int):
    data = await get_teams_by_id(team_id)
    return data

######### FIXTURES ########
@router.get("/fixtures")
async def fetch_fixtures(filters: FixtureFilters=Depends()):
    data = await get_fixtures(filters)
    return data

@router.get("/fixtures/{fixture_id}")
async def fetch_fixtures(fixture_id: int):
    data = await get_fixtures_by_id(fixture_id)
    return data



