from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
from sqlalchemy.future import select
import httpx
import os
from app.schemas.competition_schema import TeamFilters, LeagueFilters, FixtureFilters, TeamCreate, LeagueCreate
from app.crud.competition_crud import store_team_in_db, store_league_in_db, Competition
app=FastAPI()

load_dotenv()

RAPIDAPI_KEY= os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")

BASE_URL = os.getenv("BASE_URL")

def get_headers():
    if not RAPIDAPI_KEY or not RAPIDAPI_HOST:
        raise RuntimeError("RAPIDAPI_KEY or RAPIDAPI_HOST not set in environment")
    return{
        "x-rapidapi-key" : RAPIDAPI_KEY,
        "x-rapidapi-host" : RAPIDAPI_HOST
    }

######### LEAGUES ########
async def get_competitions(filters: LeagueFilters):

    url = f"{BASE_URL}/leagues"

    params = filters.dict(exclude_none=True)

    async with httpx.AsyncClient() as client:
        response = await client.get(url,headers=get_headers(),params=params)
        response.raise_for_status()
        
        api_response = response.json()
        return  api_response

async def get_competition_by_id(competition_id: int):

    url = f"{BASE_URL}/leagues"

    params = {"id":competition_id}

    async with httpx.AsyncClient() as client:
        response = await client.get(url,headers=get_headers(),params=params)
        response.raise_for_status()
        
        api_response = response.json()
        return api_response
    
async def store_league_from_api(db: AsyncSession, filters: LeagueFilters):
    api_response = await get_competitions(filters)
    inserted = 0
    skipped = 0

    for league in api_response["response"]:
        league_data = LeagueCreate(
            external_id=league["league"]["id"],
            name=league["league"]["name"],
            season=league["seasons"][0]["year"],
            country=league["country"]["name"],
            type=league["league"]["type"],
            logo=league["league"]["logo"],
        )

        # ✅ Check if league already exists
        result = await db.execute(select(Competition).where(Competition.external_id == league_data.external_id))
        existing_league = result.scalar_one_or_none()

        if existing_league:
            skipped += 1
            continue  # skip duplicate

        # Otherwise, insert
        await store_league_in_db(db, league_data)
        inserted += 1

    return {
        "message": "League sync complete",
        "inserted": inserted,
        "skipped": skipped
    }

######### TEAMS ########
async def get_teams(filters: TeamFilters):

    url = f"{BASE_URL}/teams"

    params = filters.dict(exclude_none=True)

    async with httpx.AsyncClient() as client:
        response = await client.get(url,headers=get_headers(),params=params)
        
        api_response = response.json()
        return api_response

async def get_teams_by_id(team_id: int):
    url = f"{BASE_URL}/teams"

    params = {"id": team_id}

    async with httpx.AsyncClient() as client:
        response = await client.get(url,headers=get_headers(),params=params)
        response.raise_for_status()
        
        api_response = response.json()
        return api_response
    
async def store_teams_from_api(db:AsyncSession, filters:TeamFilters):
    api_response = await get_teams(filters)

    for teams in api_response["response"]:
        team_data = TeamCreate(
            external_id=teams["team"]["id"],
            name=teams["team"]["name"],
            short_name=teams["team"]["code"],
            venue_name=teams["venue"]["name"],
            venue_id=teams["venue"]["id"],
            competition_id=filters.league,
        )
        await store_team_in_db(db,team_data)
        
######### FIXTURES ########
async def get_fixtures(filters : FixtureFilters):
    url = f"{BASE_URL}/fixtures"
    params = filters.dict(exclude_none=True)

    async with httpx.AsyncClient() as client:
        response = await client.get(url,headers=get_headers(),params=params)
        response.raise_for_status()

        api_response = response.json()
        return api_response

async def get_fixtures_by_id(fixture_id: int):

    url = f"{BASE_URL}/fixtures"

    params = {"id":fixture_id}

    async with httpx.AsyncClient() as client:
        response = await client.get(url,headers=get_headers(),params=params)
        response.raise_for_status()

        api_response = response.json()
        return api_response

