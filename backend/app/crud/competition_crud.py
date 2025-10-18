from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.competiton_data import Team, Competition,Fixture
from app.schemas.competition_schema import TeamCreate, LeagueCreate,FixtureCreate
from datetime import datetime
# Save team to DB if not already existing
async def store_team_in_db(db: AsyncSession, team: TeamCreate) -> Team:
    # Check if the team already exists
    result = await db.execute(select(Team).where(Team.external_id == team.external_id))
    existing_team = result.scalar_one_or_none()

    if existing_team:
        return existing_team  # Avoid duplicates

    # Create new team record
    new_team = Team(
        external_id=team.external_id,
        name=team.name,
        short_name=team.short_name,
        competition_id=team.competition_id,
        venue_name=team.venue_name,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(new_team)
    await db.commit()
    await db.refresh(new_team)
    return new_team

async def store_league_in_db(db: AsyncSession, league: LeagueCreate) -> Competition:
    result = await db.execute(select(Competition).where(Competition.external_id==league.external_id))
    existing_league = result.scalar_one_or_none()

    if existing_league:
        return  existing_league

    new_league = Competition(
        external_id=league.external_id,
        name=league.name,
        season=league.season,
        country=league.country,
        type=league.type,
        logo=league.logo,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(new_league)
    await db.commit()
    await db.refresh(new_league)
    return new_league 

# Get team by internal DB id
async def get_team_by_id(db: AsyncSession, team_id: int) -> Team | None:
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()
    return team

async def store_fixture_in_db(db: AsyncSession, fixture: FixtureCreate) -> Fixture:
    result = await db.execute(select(Fixture).where(Fixture.external_id==fixture.external_id))
    existing_fixture = result.scalar_one_or_none()

    if existing_fixture:
        return  existing_fixture

    new_fixture = Fixture(
        external_id=fixture.external_id,
        competition_id=fixture.competition_id,
        home_team_id=fixture.home_team_id,
        away_team_id=fixture.away_team_id,
        gameweek=fixture.gameweek,
        kickoff_time=fixture.kickoff_time,
        status=fixture.status,
        home_goals=fixture.home_goals,
        away_goals=fixture.away_goals,
        referee=fixture.referee,
        updated_at=datetime.utcnow(),
    )

    db.add(new_fixture)
    await db.commit()
    await db.refresh(new_fixture)
    return new_fixture 