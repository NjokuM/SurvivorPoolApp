"""
Shared test fixtures for the SurvivorPool backend test suite.
Uses an in-memory SQLite database so tests are fast and isolated.
"""
import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient, ASGITransport

# Set a deterministic secret key for tests before any app imports
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ["CRON_SECRET"] = "test-cron-secret"

from app.models.base import Base
from app.models import User, Competition, Team, Fixture, Pool, PoolUserStats, Pick
from app.database import get_db
from app.main import app
from app.utils.auth import hash_password, create_access_token, create_refresh_token


# --------------- Database fixtures ---------------

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    async_session_factory = sessionmaker(
        db_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with async_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_engine):
    """
    Provides an httpx AsyncClient wired to the FastAPI app,
    with the DB dependency overridden to use the test database.
    """
    async_session_factory = sessionmaker(
        db_engine, expire_on_commit=False, class_=AsyncSession
    )

    async def override_get_db():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# --------------- Helper fixtures ---------------

@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a test user in the DB and return it."""
    user = User(
        userName="testuser",
        email="test@example.com",
        password=hash_password("password123"),
        firstName="Test",
        lastName="User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_tokens(test_user):
    """Return a dict with access_token and refresh_token for the test user."""
    return {
        "access_token": create_access_token(test_user.id),
        "refresh_token": create_refresh_token(test_user.id),
    }


@pytest_asyncio.fixture
async def auth_headers(auth_tokens):
    """Return Authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {auth_tokens['access_token']}"}


@pytest_asyncio.fixture
async def test_competition(db_session):
    """Create a test competition."""
    comp = Competition(
        external_id=39,
        name="Premier League",
        season=2025,
        country="England",
        type="League",
        logo="https://example.com/pl.png",
    )
    db_session.add(comp)
    await db_session.commit()
    await db_session.refresh(comp)
    return comp


@pytest_asyncio.fixture
async def test_teams(db_session, test_competition):
    """Create two test teams."""
    home = Team(
        external_id=33,
        name="Manchester United",
        short_name="MUN",
        competition_id=test_competition.id,
        venue_name="Old Trafford",
        logo="https://example.com/mun.png",
    )
    away = Team(
        external_id=40,
        name="Liverpool",
        short_name="LIV",
        competition_id=test_competition.id,
        venue_name="Anfield",
        logo="https://example.com/liv.png",
    )
    db_session.add_all([home, away])
    await db_session.commit()
    await db_session.refresh(home)
    await db_session.refresh(away)
    return home, away
