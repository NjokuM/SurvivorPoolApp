from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.competiton_data import Competition, Team, Fixture
from app.schemas.competition_schema import TeamFilters, FixtureFilters, LeagueFilters

router = APIRouter(
    prefix="/competitions",
    tags=["Competition Data (DB)"]
)

# LEAGUES
@router.get("/leagues")
async def get_leagues_in_db(filters: LeagueFilters = Depends(), db: AsyncSession = Depends(get_db)):
    stmt = select(Competition)

    if filters.name:
        stmt = stmt.where(Competition.name.ilike(f"%{filters.name}%"))
    if filters.season:
        stmt = stmt.where(Competition.season == filters.season)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/leagues/{league_id}")
async def get_league_by_id_in_db(league_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Competition).where(Competition.id == league_id))
    league = result.scalar_one_or_none()
    if not league:
        raise HTTPException(404, "League not found")
    return league


# TEAMS
@router.get("/teams")
async def get_teams_in_db(filters: TeamFilters = Depends(), db: AsyncSession = Depends(get_db)):
    stmt = select(Team)

    if filters.league:
        stmt = stmt.where(Team.competition_id == filters.league)

    if filters.name:
        stmt = stmt.where(Team.name.ilike(f"%{filters.name}%"))

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/teams/{team_id}")
async def get_team_by_id_in_db(team_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(404, "Team not found")
    return team


# FIXTURES
@router.get("/fixtures")
async def get_fixtures_in_db(filters: FixtureFilters = Depends(), db: AsyncSession = Depends(get_db)):
    stmt = select(Fixture)

    if filters.league:
        stmt = stmt.where(Fixture.competition_id == filters.league)
        
    if filters.team:
        stmt = stmt.where(
            (Fixture.home_team_id == filters.team) |
            (Fixture.away_team_id == filters.team)
        )

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/fixtures/{fixture_id}")
async def get_fixture_by_id_in_db(fixture_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Fixture).where(Fixture.id == fixture_id))
    fixture = result.scalar_one_or_none()
    if not fixture:
        raise HTTPException(404, "Fixture not found")
    return fixture