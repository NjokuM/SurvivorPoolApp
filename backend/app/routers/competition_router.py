from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.future import select
from app.models.competiton_data import Competition
from app.schemas.competition_schema import TeamFilters , LeagueFilters, FixtureFilters, FixtureUpdate
from app.services.football_api import get_competitions, get_competition_by_id, get_teams,get_teams_by_id, store_teams_from_api, store_fixtures_from_api, get_fixtures, get_fixtures_by_id,store_league_from_api, update_fixtures_by_league_id,update_fixtures_from_api
from app.database import get_db
from typing import List
router = APIRouter(prefix="/competitions", tags=["Competitions"])

######### LEAGUES ########
@router.get("/leagues")
async def get_leagues(filters: LeagueFilters=Depends()):
    data = await get_competitions(filters)
    return data

@router.get("/leagues/{competition_id}")
async def get_leagues_by_id(competition_id):
    data = await get_competition_by_id(competition_id)
    return data

@router.post("/leagues/sync")
async def sync_leagues(filters: LeagueFilters = Depends(), db: AsyncSession = Depends(get_db)):
    """This route fetches leagues from the external API and stores them in the database."""

    try:
        result = await store_league_from_api(db, filters)
        inserted = result["inserted"]
        skipped = result["skipped"]

        if inserted > 0:
            # ✅ New leagues added
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={"message": "League sync complete", "inserted": inserted, "skipped": skipped}
            )

        else:
            # ⚠️ No new leagues added
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": "All leagues already exist", "inserted": inserted, "skipped": skipped}
            )

    except Exception as e:
        # ❌ Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error syncing leagues: {str(e)}"
        )
    
@router.put("/fixtures/update/all")
async def update_all_fixtures(db: AsyncSession = Depends(get_db)):
    # Fetch all competitions' external IDs and their seasons
    result = await db.execute(select(Competition.external_id, Competition.season))
    leagues = result.all()

    updated_count = 0
    skipped_count = 0

    # Loop through all leagues using the API's external_id
    for external_id, season in leagues:
        filters = FixtureFilters(league=external_id, season=season)
        try:
            result = await store_fixtures_from_api(db, filters)
            updated_count += result.get("inserted", 0)
            skipped_count += result.get("skipped", 0)
        except Exception as e:
            print(f"⚠️ Skipped league {external_id} due to error: {e}")

    return {
        "message": "Fixture updates complete for all leagues",
        "inserted": updated_count,
        "skipped": skipped_count
    }

@router.put("/fixtures/update/{league_id}")
async def update_league_fixtures(league_id: int, season: int, db: AsyncSession = Depends(get_db)):
    """
    Updates fixtures for a specific league (by league_id).
    """
    result = await update_fixtures_by_league_id(db, league_id, season)
    return result

######### TEAMS ########
@router.get("/teams")
async def fetch_teams(filters: TeamFilters=Depends()):
    data = await get_teams(filters)
    return data

@router.get("/teams/{team_id}")
async def get_team_by_id(team_id: int):
    data = await get_teams_by_id(team_id)
    return data

@router.post("/teams/sync")
async def sync_teams(filters: TeamFilters=Depends(), db:AsyncSession=Depends(get_db)):
    """ This route fetches teams from the external api and stores them within the database."""

    await store_teams_from_api(db,filters)
    return{"message": "Teams synced successfully"}

######### FIXTURES ########
@router.get("/fixtures")
async def fetch_fixtures(filters: FixtureFilters=Depends()):
    data = await get_fixtures(filters)
    return data

@router.get("/fixtures/{fixture_id}")
async def fetch_fixtures(fixture_id: int):
    data = await get_fixtures_by_id(fixture_id)
    return data

@router.post("/fixtures/sync")
async def sync_fixtures(filters: FixtureFilters = Depends(), db: AsyncSession = Depends(get_db)):
    """This route fetches fixtures from the external API and stores them in the database."""

    try:
        result = await store_fixtures_from_api(db, filters)
        inserted = result["inserted"]
        skipped = result["skipped"]

        if inserted > 0:
            # New fixture added
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={"message": "Fixture sync complete", "inserted": inserted, "skipped": skipped}
            )

        else:
            # No new fixures added
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": "All fixtures already exist", "inserted": inserted, "skipped": skipped}
            )

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error syncing fixtures: {str(e)}"
        )