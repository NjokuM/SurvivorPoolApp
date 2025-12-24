from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.competition_schema import LeagueFilters, TeamFilters, FixtureFilters
from app.services.football_api import (
    get_competitions, get_competition_by_id,
    get_teams, get_teams_by_id,
    get_fixtures, get_fixtures_by_id,
    store_league_from_api, store_teams_from_api,
    store_fixtures_from_api, update_fixtures_by_league_id,
    update_fixtures_from_api
)
from app.services.scheduler import (
    smart_sync_and_process,
    weekly_schedule_refresh,
    force_process_competition_gameweek
)
from sqlalchemy.future import select
from app.models.competiton_data import Competition

router = APIRouter(
    prefix="/external/football",
    tags=["Football API Sync"]
)

# EXTERNAL LEAGUES
@router.get("/leagues")
async def fetch_leagues(filters: LeagueFilters = Depends()):
    return await get_competitions(filters)


@router.get("/leagues/{external_id}")
async def fetch_league_by_external_id(external_id: int):
    return await get_competition_by_id(external_id)


@router.post("/leagues/sync")
async def sync_leagues(filters: LeagueFilters = Depends(), db: AsyncSession = Depends(get_db)):
    result = await store_league_from_api(db, filters)
    return result


# EXTERNAL TEAMS
@router.get("/teams")
async def fetch_teams(filters: TeamFilters = Depends()):
    return await get_teams(filters)


@router.get("/teams/{external_id}")
async def fetch_team_by_external_id(external_id: int):
    return await get_teams_by_id(external_id)


@router.post("/teams/sync")
async def sync_teams(filters: TeamFilters = Depends(), db: AsyncSession = Depends(get_db)):
    await store_teams_from_api(db, filters)
    return {"message": "Teams synced successfully"}

# EXTERNAL FIXTURES
@router.get("/fixtures")
async def fetch_fixtures(filters: FixtureFilters = Depends()):
    return await get_fixtures(filters)


@router.get("/fixtures/{external_id}")
async def fetch_fixture_by_external_id(external_id: int):
    return await get_fixtures_by_id(external_id)


@router.post("/fixtures/sync")
async def sync_fixtures(filters: FixtureFilters = Depends(), db: AsyncSession = Depends(get_db)):
    result = await store_fixtures_from_api(db, filters)
    return result


# UPDATE FIXTURES
@router.put("/fixtures/update/all")
async def update_all_fixtures(db: AsyncSession = Depends(get_db)):
    # 1. Get all competitions with external_id + season
    result = await db.execute(select(Competition.external_id, Competition.season))
    leagues = result.all()

    updated_total = 0
    inserted_total = 0
    skipped_total = 0

    # 2. Loop through each league
    for external_id, season in leagues:
        filters = FixtureFilters(league=external_id, season=season)
        response = await update_fixtures_from_api(db, filters)

        updated_total += response["updated"]
        inserted_total += response["inserted"]
        skipped_total += response["skipped"]

    return {
        "message": "All leagues updated",
        "updated": updated_total,
        "inserted": inserted_total,
        "skipped": skipped_total
    }


@router.put("/fixtures/update/{league_id}")
async def update_fixtures_for_league(league_id: int, season: int, db: AsyncSession = Depends(get_db)):
    return await update_fixtures_by_league_id(db, league_id, season)


# ============================================================
# SMART SCHEDULER ENDPOINTS (for cron jobs)
# ============================================================

@router.post("/scheduler/smart-sync")
async def run_smart_sync(db: AsyncSession = Depends(get_db)):
    """
    MAIN CRON JOB - Run every 15-30 mins.
    
    Only makes API calls when games are actually finishing.
    - Checks which leagues have active pools
    - Checks if any games kicked off 90-150 mins ago (likely finishing)
    - If yes: syncs those fixtures and processes picks
    - If no: does nothing (no API cost)
    """
    result = await smart_sync_and_process(db)
    return result


@router.post("/scheduler/weekly-refresh")
async def run_weekly_refresh(db: AsyncSession = Depends(get_db)):
    """
    WEEKLY CRON JOB - Run once per week (e.g., Sunday 11pm).
    
    Refreshes fixture schedules to catch:
    - Rescheduled games (weather, TV, etc.)
    - New fixtures added
    - Kickoff time changes
    
    Only syncs leagues that have active pools.
    """
    result = await weekly_schedule_refresh(db)
    return result


@router.post("/scheduler/process-picks/{competition_id}/{gameweek}")
async def manually_process_picks(
    competition_id: int,
    gameweek: int,
    db: AsyncSession = Depends(get_db)
):
    """
    MANUAL TRIGGER - Process picks for a specific competition/gameweek.
    
    Useful for:
    - Testing
    - Catching up on missed processing
    - Re-processing after a bug fix
    """
    result = await force_process_competition_gameweek(db, competition_id, gameweek)
    return result