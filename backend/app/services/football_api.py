from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
from sqlalchemy.future import select
import httpx
import os
import re
from app.schemas.competition_schema import TeamFilters, LeagueFilters, FixtureFilters, TeamCreate, LeagueCreate,FixtureCreate
from app.crud.competition_crud import store_team_in_db, store_league_in_db, store_fixture_in_db,update_fixture_in_db, Competition, Fixture, Team
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
    
def extract_gameweek(round_str: str) -> int:
    """
    Extracts the matchweek number from a round string like
    "Regular Season - 1" or "Playoffs - 2" and returns it as an integer.
    """
    if not round_str:
        return 0  # fallback if string is missing
    match = re.search(r'(\d+)$', round_str)
    if match:
        return int(match.group(1))
    return 0  # fallback if no number found

async def store_fixtures_from_api(db: AsyncSession, filters: FixtureFilters):
    api_response = await get_fixtures(filters)
    inserted = 0
    skipped = 0

    for fixture in api_response["response"]:
        # --- Competition FK ---
        result = await db.execute(select(Competition).where(Competition.external_id == fixture["league"]["id"]))
        competition = result.scalar_one_or_none()
        if not competition:
            skipped += 1
            continue
        competition_id = competition.id

        # --- Home team FK ---
        result = await db.execute(select(Team).where(Team.external_id == fixture["teams"]["home"]["id"]))
        home_team = result.scalar_one_or_none()
        if not home_team:
            skipped += 1
            continue
        home_team_id = home_team.id

        # --- Away team FK ---
        result = await db.execute(select(Team).where(Team.external_id == fixture["teams"]["away"]["id"]))
        away_team = result.scalar_one_or_none()
        if not away_team:
            skipped += 1
            continue
        away_team_id = away_team.id

        # --- Create Fixture object ---
        fixture_data = FixtureCreate(
            external_id=fixture["fixture"]["id"],
            competition_id=competition_id,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            gameweek=extract_gameweek(fixture["league"]["round"]),
            kickoff_time=fixture["fixture"]["date"],  # handle tz-aware if needed
            status=fixture["fixture"]["status"]["short"],
            home_goals=fixture["goals"]["home"],
            away_goals=fixture["goals"]["away"],
            referee=fixture["fixture"]["referee"],
        )

        # --- Check duplicates ---
        result = await db.execute(select(Fixture).where(Fixture.external_id == fixture_data.external_id))
        existing_fixture = result.scalar_one_or_none()
        if existing_fixture:
            skipped += 1
            continue

        # --- Insert ---
        await store_fixture_in_db(db, fixture_data)
        inserted += 1

    return {
        "message": "Fixture sync complete",
        "inserted": inserted,
        "skipped": skipped
    }

async def update_fixtures_from_api(db: AsyncSession, filters: FixtureFilters):
    """Fetches and updates all fixtures across leagues from the external API."""
    api_response = await get_fixtures(filters)
    updated = 0
    skipped = 0
    inserted = 0

    for fixture in api_response["response"]:
        # --- Match Competition ---
        result = await db.execute(select(Competition).where(Competition.external_id == fixture["league"]["id"]))
        competition = result.scalar_one_or_none()
        if not competition:
            skipped += 1
            continue
        competition_id = competition.id

        # --- Match Home Team ---
        result = await db.execute(select(Team).where(Team.external_id == fixture["teams"]["home"]["id"]))
        home_team = result.scalar_one_or_none()
        if not home_team:
            skipped += 1
            continue
        home_team_id = home_team.id

        # --- Match Away Team ---
        result = await db.execute(select(Team).where(Team.external_id == fixture["teams"]["away"]["id"]))
        away_team = result.scalar_one_or_none()
        if not away_team:
            skipped += 1
            continue
        away_team_id = away_team.id

        # --- Build FixtureCreate object ---
        fixture_data = FixtureCreate(
            external_id=fixture["fixture"]["id"],
            competition_id=competition_id,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            gameweek=extract_gameweek(fixture["league"]["round"]),
            kickoff_time=fixture["fixture"]["date"],
            status=fixture["fixture"]["status"]["short"],
            home_goals=fixture["goals"]["home"],
            away_goals=fixture["goals"]["away"],
            referee=fixture["fixture"]["referee"],
        )

        # --- Update or insert ---
        result = await db.execute(select(Fixture).where(Fixture.external_id == fixture_data.external_id))
        existing_fixture = result.scalar_one_or_none()

        if existing_fixture:
            await update_fixture_in_db(db, fixture_data)
            updated += 1
        else:
            await store_fixture_in_db(db, fixture_data)
            inserted += 1

    return {
        "message": "Fixture update complete",
        "updated": updated,
        "inserted": inserted,
        "skipped": skipped
    }

async def update_fixtures_by_league_id(db: AsyncSession, league_id: int, season: int):
    """Fetches and updates fixtures for a specific league and season."""
    filters = FixtureFilters(league=league_id, season=season)
    api_response = await get_fixtures(filters)
    updated = 0
    skipped = 0
    inserted = 0

    for fixture in api_response["response"]:
        # --- Match Competition ---
        result = await db.execute(select(Competition).where(Competition.external_id == fixture["league"]["id"]))
        competition = result.scalar_one_or_none()
        if not competition:
            skipped += 1
            continue
        competition_id = competition.id

        # --- Match Home & Away Teams ---
        result = await db.execute(select(Team).where(Team.external_id == fixture["teams"]["home"]["id"]))
        home_team = result.scalar_one_or_none()
        if not home_team:
            skipped += 1
            continue
        result = await db.execute(select(Team).where(Team.external_id == fixture["teams"]["away"]["id"]))
        away_team = result.scalar_one_or_none()
        if not away_team:
            skipped += 1
            continue

        # --- Build Fixture Data ---
        fixture_data = FixtureCreate(
            external_id=fixture["fixture"]["id"],
            competition_id=competition_id,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            gameweek=extract_gameweek(fixture["league"]["round"]),
            kickoff_time=fixture["fixture"]["date"],
            status=fixture["fixture"]["status"]["short"],
            home_goals=fixture["goals"]["home"],
            away_goals=fixture["goals"]["away"],
            referee=fixture["fixture"]["referee"],
        )

        # --- Update or insert ---
        result = await db.execute(select(Fixture).where(Fixture.external_id == fixture_data.external_id))
        existing_fixture = result.scalar_one_or_none()

        if existing_fixture:
            await update_fixture_in_db(db, fixture_data)
            updated += 1
        else:
            await store_fixture_in_db(db, fixture_data)
            inserted += 1

    return {
        "message": f"Fixture update complete for league {league_id}",
        "updated": updated,
        "inserted": inserted,
        "skipped": skipped
    }