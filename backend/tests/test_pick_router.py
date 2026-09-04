"""
Tests for pick creation (POST /picks/).

Covers the "no lives" gate specifically: a league-mode pool (has_lives=False)
stores total_lives/lives_left=0 by design since it never tracks lives, but
the pick-creation route was checking lives_left <= 0 unconditionally - which
meant no league-mode user could ever make a pick. Regression-tested here
alongside the survivor-mode behavior it must not have broken.
"""
import os
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ["CRON_SECRET"] = "test-cron-secret"

import uuid
import pytest
from datetime import datetime, timedelta, timezone
from app.models.pool import Pool, PoolUserStats
from app.models.competiton_data import Fixture
from app.utils.auth import create_access_token


def _auth_headers(user):
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


async def _seed_pool(db_session, competition_id, *, has_lives, total_lives, max_picks_per_team=2, start_gameweek=1):
    pool = Pool(
        session_code=uuid.uuid4().hex[:10].upper(),
        name="Test Pool",
        competition_id=competition_id,
        start_gameweek=start_gameweek,
        max_picks_per_team=max_picks_per_team,
        total_lives=total_lives,
        has_lives=has_lives,
    )
    db_session.add(pool)
    await db_session.commit()
    await db_session.refresh(pool)
    return pool


async def _join_pool(db_session, pool_id, user_id, lives_left):
    stats = PoolUserStats(pool_id=pool_id, user_id=user_id, total_points=0, lives_left=lives_left)
    db_session.add(stats)
    await db_session.commit()
    return stats


async def _future_fixture(db_session, competition_id, home_team_id, away_team_id, gameweek=1):
    fixture = Fixture(
        external_id=uuid.uuid4().int >> 96,  # cheap unique int
        competition_id=competition_id,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        gameweek=gameweek,
        kickoff_time=datetime.now(timezone.utc) + timedelta(hours=2),
        status="NS",
    )
    db_session.add(fixture)
    await db_session.commit()
    await db_session.refresh(fixture)
    return fixture


class TestNoLivesGate:
    @pytest.mark.asyncio
    async def test_league_mode_pick_succeeds_with_zero_lives(
        self, client, db_session, test_user, test_competition, test_teams
    ):
        """League-mode pools have total_lives=0 by design (they never track
        lives) - a pick must still be allowed."""
        home, away = test_teams
        pool = await _seed_pool(db_session, test_competition.id, has_lives=False, total_lives=0)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=0)
        fixture = await _future_fixture(db_session, test_competition.id, home.id, away.id)

        resp = await client.post("/picks/", headers=_auth_headers(test_user), json={
            "pool_id": pool.id,
            "user_id": test_user.id,
            "fixture_id": fixture.id,
            "team_id": home.id,
        })

        assert resp.status_code == 201, resp.text

    @pytest.mark.asyncio
    async def test_survivor_mode_pick_blocked_with_zero_lives(
        self, client, db_session, test_user, test_competition, test_teams
    ):
        """Survivor mode must still reject picks once a user is eliminated."""
        home, away = test_teams
        pool = await _seed_pool(db_session, test_competition.id, has_lives=True, total_lives=3)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=0)
        fixture = await _future_fixture(db_session, test_competition.id, home.id, away.id)

        resp = await client.post("/picks/", headers=_auth_headers(test_user), json={
            "pool_id": pool.id,
            "user_id": test_user.id,
            "fixture_id": fixture.id,
            "team_id": home.id,
        })

        assert resp.status_code == 400
        assert "no lives left" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_survivor_mode_pick_succeeds_with_lives_remaining(
        self, client, db_session, test_user, test_competition, test_teams
    ):
        home, away = test_teams
        pool = await _seed_pool(db_session, test_competition.id, has_lives=True, total_lives=3)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=3)
        fixture = await _future_fixture(db_session, test_competition.id, home.id, away.id)

        resp = await client.post("/picks/", headers=_auth_headers(test_user), json={
            "pool_id": pool.id,
            "user_id": test_user.id,
            "fixture_id": fixture.id,
            "team_id": home.id,
        })

        assert resp.status_code == 201, resp.text


class TestMaxPicksPerTeam:
    @pytest.mark.asyncio
    async def test_enforced_in_survivor_mode(
        self, client, db_session, test_user, test_competition, test_teams
    ):
        home, away = test_teams
        pool = await _seed_pool(db_session, test_competition.id, has_lives=True, total_lives=3, max_picks_per_team=1)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=3)

        fixture1 = await _future_fixture(db_session, test_competition.id, home.id, away.id, gameweek=1)
        resp1 = await client.post("/picks/", headers=_auth_headers(test_user), json={
            "pool_id": pool.id, "user_id": test_user.id,
            "fixture_id": fixture1.id, "team_id": home.id,
        })
        assert resp1.status_code == 201, resp1.text

        fixture2 = await _future_fixture(db_session, test_competition.id, home.id, away.id, gameweek=2)
        resp2 = await client.post("/picks/", headers=_auth_headers(test_user), json={
            "pool_id": pool.id, "user_id": test_user.id,
            "fixture_id": fixture2.id, "team_id": home.id,
        })
        assert resp2.status_code == 400
        assert "already picked this team" in resp2.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_enforced_in_league_mode(
        self, client, db_session, test_user, test_competition, test_teams
    ):
        """The per-team cap isn't gated by has_lives - league mode must
        enforce it identically to survivor mode."""
        home, away = test_teams
        pool = await _seed_pool(db_session, test_competition.id, has_lives=False, total_lives=0, max_picks_per_team=1)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=0)

        fixture1 = await _future_fixture(db_session, test_competition.id, home.id, away.id, gameweek=1)
        resp1 = await client.post("/picks/", headers=_auth_headers(test_user), json={
            "pool_id": pool.id, "user_id": test_user.id,
            "fixture_id": fixture1.id, "team_id": home.id,
        })
        assert resp1.status_code == 201, resp1.text

        fixture2 = await _future_fixture(db_session, test_competition.id, home.id, away.id, gameweek=2)
        resp2 = await client.post("/picks/", headers=_auth_headers(test_user), json={
            "pool_id": pool.id, "user_id": test_user.id,
            "fixture_id": fixture2.id, "team_id": home.id,
        })
        assert resp2.status_code == 400
        assert "already picked this team" in resp2.json()["detail"].lower()
