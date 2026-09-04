"""
Tests for endpoint-level authentication/authorization, added when every
endpoint was gated behind a bearer token (or, for server-to-server
sync/cron endpoints, an x-cron-secret header).

Two distinct properties are covered per endpoint group:
1. Authentication - the endpoint rejects requests with no/invalid token.
2. Authorization - where an endpoint acts "as" a user (create a pool, make
   a pick, etc.), the acting identity comes from the verified token, not
   whatever user_id/created_by the request body claims. Before this work,
   a caller could pass any user_id they liked.
"""
import os
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ["CRON_SECRET"] = "test-cron-secret"

import uuid
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.models.user import User
from app.models.pool import Pool, PoolUserStats
from app.models.pick import Pick
from app.models.competiton_data import Fixture
from app.utils.auth import hash_password, create_access_token


async def _make_user(db_session, name):
    user = User(
        userName=name, email=f"{name}@test.com",
        password=hash_password("pass"), firstName="Test", lastName=name,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def _auth_headers(user):
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


class TestReadEndpointsRequireAuth:
    """Spot-check one endpoint per previously-open router - full coverage
    of every route lives in the router-specific test files."""

    @pytest.mark.asyncio
    async def test_competitions_leagues_requires_auth(self, client):
        resp = await client.get("/competitions/leagues")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_pools_list_requires_auth(self, client):
        resp = await client.get("/pools")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_pools_list_succeeds_with_valid_token(self, client, auth_headers):
        resp = await client.get("/pools", headers=auth_headers)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_user_requires_auth(self, client, test_user):
        resp = await client.get(f"/users/{test_user.id}")
        assert resp.status_code == 403


class TestDeadRegistrationEndpointRemoved:
    @pytest.mark.asyncio
    async def test_post_users_no_longer_exists(self, client):
        """This unauthenticated duplicate of /signup skipped uniqueness
        validation entirely and was never used by the app - removed."""
        resp = await client.post("/users/", json={
            "userName": "x", "email": "x@test.com", "password": "pw",
            "firstName": "X", "lastName": "Y",
        })
        assert resp.status_code in (404, 405)


class TestExternalSyncRequiresCronSecret:
    @pytest.mark.asyncio
    async def test_rejected_without_cron_secret(self, client):
        resp = await client.get("/external/football/leagues")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_a_valid_user_token_alone_is_not_sufficient(self, client, auth_headers):
        """These are server-to-server ops endpoints - being a logged-in app
        user must not be enough to trigger them."""
        resp = await client.get("/external/football/leagues", headers=auth_headers)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_accepted_with_cron_secret(self, client):
        resp = await client.get(
            "/external/football/leagues", headers={"x-cron-secret": "test-cron-secret"}
        )
        assert resp.status_code == 200


class TestPoolCreateIgnoresSpoofedIdentity:
    @pytest.mark.asyncio
    async def test_created_by_comes_from_token_not_body(
        self, client, db_session, test_competition, test_user
    ):
        victim = await _make_user(db_session, "victim1")

        resp = await client.post(
            "/pools/create",
            headers=_auth_headers(test_user),
            json={
                "name": "spoof-test-pool",
                "competition_id": test_competition.id,
                "has_lives": False,
                "created_by": victim.id,  # attempt to attribute the pool to someone else
            },
        )

        assert resp.status_code == 201, resp.text
        assert resp.json()["created_by"] == test_user.id


class TestPoolJoinIgnoresSpoofedIdentity:
    @pytest.mark.asyncio
    async def test_join_adds_caller_not_body_user_id(
        self, client, db_session, test_competition, test_user
    ):
        victim = await _make_user(db_session, "victim2")
        creator = await _make_user(db_session, "creator_join_test")
        pool = Pool(
            session_code=uuid.uuid4().hex[:10].upper(), name="Join Test Pool",
            competition_id=test_competition.id, start_gameweek=1,
            max_picks_per_team=2, total_lives=3, has_lives=True,
            created_by=creator.id,
        )
        db_session.add(pool)
        await db_session.commit()
        await db_session.refresh(pool)

        resp = await client.post(
            f"/pools/{pool.id}/join",
            headers=_auth_headers(test_user),
            json={"user_id": victim.id},  # attempt to enroll someone else
        )

        assert resp.status_code == 200, resp.text
        assert resp.json()["user_id"] == test_user.id

        # victim was never actually enrolled
        victim_stats = await db_session.execute(
            select(PoolUserStats).where(
                PoolUserStats.pool_id == pool.id, PoolUserStats.user_id == victim.id
            )
        )
        assert victim_stats.scalar_one_or_none() is None


class TestPoolDeleteRequiresOwnership:
    @pytest.mark.asyncio
    async def test_non_creator_cannot_delete(
        self, client, db_session, test_competition, test_user
    ):
        creator = await _make_user(db_session, "creator_delete_test")
        pool = Pool(
            session_code=uuid.uuid4().hex[:10].upper(), name="Delete Test Pool",
            competition_id=test_competition.id, start_gameweek=1,
            max_picks_per_team=2, total_lives=3, has_lives=True,
            created_by=creator.id,
        )
        db_session.add(pool)
        await db_session.commit()
        await db_session.refresh(pool)

        # test_user is authenticated but not the creator - even with a
        # (now-vestigial) user_id query param, ownership is derived from
        # the token, not from anything the caller supplies.
        resp = await client.delete(f"/pools/{pool.id}?user_id={creator.id}", headers=_auth_headers(test_user))
        assert resp.status_code == 403


class TestPickCreateIgnoresSpoofedIdentity:
    @pytest.mark.asyncio
    async def test_pick_recorded_under_caller_not_body_user_id(
        self, client, db_session, test_competition, test_teams, test_user
    ):
        home, away = test_teams
        victim = await _make_user(db_session, "victim3")
        pool = Pool(
            session_code=uuid.uuid4().hex[:10].upper(), name="Pick Spoof Pool",
            competition_id=test_competition.id, start_gameweek=1,
            max_picks_per_team=2, total_lives=3, has_lives=True,
            created_by=test_user.id,
        )
        db_session.add(pool)
        await db_session.flush()
        db_session.add(PoolUserStats(pool_id=pool.id, user_id=test_user.id, total_points=0, lives_left=3))
        fixture = Fixture(
            external_id=555555, competition_id=test_competition.id,
            home_team_id=home.id, away_team_id=away.id, gameweek=1,
            kickoff_time=datetime.now(timezone.utc) + timedelta(hours=2), status="NS",
        )
        db_session.add(fixture)
        await db_session.commit()
        await db_session.refresh(fixture)

        resp = await client.post(
            "/picks/",
            headers=_auth_headers(test_user),
            json={
                "pool_id": pool.id,
                "user_id": victim.id,  # attempt to pick on someone else's behalf
                "fixture_id": fixture.id,
                "team_id": home.id,
            },
        )

        assert resp.status_code == 201, resp.text
        assert resp.json()["user_id"] == test_user.id


class TestPickUpdateRequiresOwnership:
    @pytest.mark.asyncio
    async def test_non_owner_cannot_update_pick(
        self, client, db_session, test_competition, test_teams, test_user
    ):
        home, away = test_teams
        owner = await _make_user(db_session, "pick_owner")
        pool = Pool(
            session_code=uuid.uuid4().hex[:10].upper(), name="Pick Update Pool",
            competition_id=test_competition.id, start_gameweek=1,
            max_picks_per_team=2, total_lives=3, has_lives=True,
            created_by=owner.id,
        )
        db_session.add(pool)
        await db_session.flush()
        fixture = Fixture(
            external_id=555556, competition_id=test_competition.id,
            home_team_id=home.id, away_team_id=away.id, gameweek=1,
            kickoff_time=datetime.now(timezone.utc) + timedelta(hours=2), status="NS",
        )
        db_session.add(fixture)
        await db_session.flush()
        pick = Pick(
            pool_id=pool.id, user_id=owner.id, team_id=home.id,
            fixture_id=fixture.id, competition_id=test_competition.id,
        )
        db_session.add(pick)
        await db_session.commit()
        await db_session.refresh(pick)

        # test_user is authenticated but doesn't own this pick.
        resp = await client.put(
            f"/picks/{pick.id}",
            headers=_auth_headers(test_user),
            json={"team_id": away.id},
        )
        assert resp.status_code == 403


class TestSelfScopedEndpoints:
    @pytest.mark.asyncio
    async def test_cannot_view_another_users_pools(self, client, db_session, test_user):
        other = await _make_user(db_session, "other_pools_viewer")
        resp = await client.get(f"/users/{other.id}/pools", headers=_auth_headers(test_user))
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_cannot_view_another_users_picks(self, client, db_session, test_user):
        other = await _make_user(db_session, "other_picks_viewer")
        resp = await client.get(f"/picks/user/{other.id}", headers=_auth_headers(test_user))
        assert resp.status_code == 403
