from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from app.schemas.competition_schema import TeamFilters , LeagueFilters, FixtureFilters
from app.services.football_api import get_competitions, get_competition_by_id, get_teams,get_teams_by_id, store_teams_from_api, get_fixtures, get_fixtures_by_id,store_league_from_api
from app.database import get_db
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



