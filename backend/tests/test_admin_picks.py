"""
Tests for the admin picks endpoint (PUT /admin/pools/{pool_id}/users/{user_id}/picks).

Only a pool's creator - resolved from their verified JWT, never a
client-supplied flag - can add or correct another user's picks. Touched and
untouched picks are all replayed through the normal results pipeline
(process_gameweek_results) so lives/points/elimination come out correctly
without ever having to hand-reverse a previously-applied delta.
"""
import os
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ["CRON_SECRET"] = "test-cron-secret"

import uuid
import pytest
from datetime import datetime, timedelta, timezone
from app.models.user import User
from app.models.pool import Pool, PoolUserStats
from app.models.competiton_data import Fixture
from app.models.pick import Pick
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


async def _seed_pool(db_session, competition_id, *, created_by, has_lives=True, total_lives=3, start_gameweek=1):
    pool = Pool(
        session_code=uuid.uuid4().hex[:10].upper(),
        name="Test Pool",
        competition_id=competition_id,
        start_gameweek=start_gameweek,
        max_picks_per_team=5,
        total_lives=total_lives,
        has_lives=has_lives,
        created_by=created_by,
    )
    db_session.add(pool)
    await db_session.commit()
    await db_session.refresh(pool)
    return pool


async def _join_pool(db_session, pool_id, user_id, lives_left):
    stats = PoolUserStats(pool_id=pool_id, user_id=user_id, total_points=0, lives_left=lives_left)
    db_session.add(stats)
    await db_session.commit()
    await db_session.refresh(stats)
    return stats


_fixture_counter = 0


async def _finished_fixture(db_session, competition_id, home_id, away_id, *, gameweek, home_goals, away_goals):
    """A past, finished (FT) fixture - kickoff further in the past for
    higher gameweeks so max(gameweek) queries behave sensibly."""
    global _fixture_counter
    _fixture_counter += 1
    fixture = Fixture(
        external_id=100000 + _fixture_counter,
        competition_id=competition_id,
        home_team_id=home_id, away_team_id=away_id,
        gameweek=gameweek,
        kickoff_time=datetime.now(timezone.utc) - timedelta(days=30 - gameweek),
        status="FT", home_goals=home_goals, away_goals=away_goals,
    )
    db_session.add(fixture)
    await db_session.commit()
    await db_session.refresh(fixture)
    return fixture


class TestAdminAuthorization:
    @pytest.mark.asyncio
    async def test_non_creator_gets_403(self, client, db_session, test_competition, test_user):
        creator = await _make_user(db_session, "creator1")
        pool = await _seed_pool(db_session, test_competition.id, created_by=creator.id)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=3)

        resp = await client.put(
            f"/admin/pools/{pool.id}/users/{test_user.id}/picks",
            headers=_auth_headers(test_user),  # test_user is NOT the pool creator
            json={"picks": []},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_no_auth_header_rejected(self, client, db_session, test_competition, test_user):
        creator = await _make_user(db_session, "creator2")
        pool = await _seed_pool(db_session, test_competition.id, created_by=creator.id)

        resp = await client.put(
            f"/admin/pools/{pool.id}/users/{test_user.id}/picks",
            json={"picks": []},
        )
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_target_user_must_be_pool_member(self, client, db_session, test_competition, test_user):
        creator = await _make_user(db_session, "creator3")
        pool = await _seed_pool(db_session, test_competition.id, created_by=creator.id)
        # test_user never joined this pool

        resp = await client.put(
            f"/admin/pools/{pool.id}/users/{test_user.id}/picks",
            headers=_auth_headers(creator),
            json={"picks": []},
        )
        assert resp.status_code == 400


class TestAdminPicksReplay:
    @pytest.mark.asyncio
    async def test_correcting_a_finished_losing_pick_to_a_win_reverses_life_loss(
        self, client, db_session, test_competition, test_teams, test_user
    ):
        """User originally picked the losing team for GW1 (already scored,
        1 life lost). Admin corrects it to the winning team - the user's
        life should come back and points should reflect a win."""
        home, away = test_teams
        creator = await _make_user(db_session, "creator4")
        pool = await _seed_pool(db_session, test_competition.id, created_by=creator.id, total_lives=3)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=2)  # already lost 1 life

        fixture = await _finished_fixture(
            db_session, test_competition.id, home.id, away.id,
            gameweek=1, home_goals=2, away_goals=0,  # home wins
        )
        # Original (wrong) pick: away team, already scored as a loss
        bad_pick = Pick(
            pool_id=pool.id, user_id=test_user.id, team_id=away.id,
            fixture_id=fixture.id, competition_id=test_competition.id,
            result="LOSS", points=0, source="user",
        )
        db_session.add(bad_pick)
        await db_session.commit()

        resp = await client.put(
            f"/admin/pools/{pool.id}/users/{test_user.id}/picks",
            headers=_auth_headers(creator),
            json={"picks": [{"fixture_id": fixture.id, "team_id": home.id}]},
        )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["lives_left"] == 3  # full reversal via full replay
        assert body["total_points"] == 3  # win = 3 points
        assert body["picks_applied"] == 1

        await db_session.refresh(bad_pick)
        assert bad_pick.team_id == home.id
        assert bad_pick.source == "admin"
        assert bad_pick.result == "WIN" or bad_pick.result.value == "WIN"

    @pytest.mark.asyncio
    async def test_filling_in_a_missing_historical_pick_avoids_missed_pick_penalty(
        self, client, db_session, test_competition, test_teams, test_user
    ):
        home, away = test_teams
        creator = await _make_user(db_session, "creator5")
        pool = await _seed_pool(db_session, test_competition.id, created_by=creator.id, total_lives=3, start_gameweek=1)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=3)

        fixture = await _finished_fixture(
            db_session, test_competition.id, home.id, away.id,
            gameweek=1, home_goals=1, away_goals=1,  # draw
        )
        # No pick was ever submitted for GW1 - importing one now should
        # avoid the missed-pick penalty entirely.
        resp = await client.put(
            f"/admin/pools/{pool.id}/users/{test_user.id}/picks",
            headers=_auth_headers(creator),
            json={"picks": [{"fixture_id": fixture.id, "team_id": home.id}]},
        )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["lives_left"] == 3  # no life lost
        assert body["total_points"] == 1  # draw = 1 point

    @pytest.mark.asyncio
    async def test_untouched_gameweek_recomputes_to_same_result(
        self, client, db_session, test_competition, test_teams, test_user
    ):
        """Importing GW2 shouldn't disturb an already-correct GW1 pick."""
        home, away = test_teams
        creator = await _make_user(db_session, "creator6")
        pool = await _seed_pool(db_session, test_competition.id, created_by=creator.id, total_lives=3, start_gameweek=1)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=3)

        gw1_fixture = await _finished_fixture(
            db_session, test_competition.id, home.id, away.id,
            gameweek=1, home_goals=3, away_goals=0,
        )
        gw1_pick = Pick(
            pool_id=pool.id, user_id=test_user.id, team_id=home.id,
            fixture_id=gw1_fixture.id, competition_id=test_competition.id,
            result="WIN", points=3, source="user",
        )
        db_session.add(gw1_pick)
        await db_session.commit()

        gw2_fixture = await _finished_fixture(
            db_session, test_competition.id, home.id, away.id,
            gameweek=2, home_goals=0, away_goals=2,  # away wins
        )

        resp = await client.put(
            f"/admin/pools/{pool.id}/users/{test_user.id}/picks",
            headers=_auth_headers(creator),
            json={"picks": [{"fixture_id": gw2_fixture.id, "team_id": away.id}]},
        )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        # GW1 win (3) + GW2 win (3) = 6, GW1's result untouched by the import
        assert body["total_points"] == 6
        assert body["lives_left"] == 3

        await db_session.refresh(gw1_pick)
        assert gw1_pick.source == "user"  # not touched/relabeled
        assert gw1_pick.team_id == home.id

    @pytest.mark.asyncio
    async def test_start_gameweek_lowered_to_cover_earliest_import(
        self, client, db_session, test_competition, test_teams, test_user
    ):
        home, away = test_teams
        creator = await _make_user(db_session, "creator7")
        pool = await _seed_pool(db_session, test_competition.id, created_by=creator.id, start_gameweek=10)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=3)

        fixture = await _finished_fixture(
            db_session, test_competition.id, home.id, away.id,
            gameweek=3, home_goals=1, away_goals=0,
        )

        resp = await client.put(
            f"/admin/pools/{pool.id}/users/{test_user.id}/picks",
            headers=_auth_headers(creator),
            json={"picks": [{"fixture_id": fixture.id, "team_id": home.id}]},
        )

        assert resp.status_code == 200, resp.text
        assert resp.json()["start_gameweek"] == 3

        await db_session.refresh(pool)
        assert pool.start_gameweek == 3


class TestAdminPicksValidation:
    @pytest.mark.asyncio
    async def test_rejects_fixture_from_different_competition(
        self, client, db_session, test_competition, test_teams, test_user
    ):
        from app.models.competiton_data import Competition
        home, away = test_teams
        creator = await _make_user(db_session, "creator8")
        pool = await _seed_pool(db_session, test_competition.id, created_by=creator.id)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=3)

        other_comp = Competition(
            external_id=999, name="Other League", season=2026,
            country="Other", type="League", logo="l",
        )
        db_session.add(other_comp)
        await db_session.commit()
        await db_session.refresh(other_comp)

        fixture = await _finished_fixture(
            db_session, other_comp.id, home.id, away.id,
            gameweek=1, home_goals=1, away_goals=0,
        )

        resp = await client.put(
            f"/admin/pools/{pool.id}/users/{test_user.id}/picks",
            headers=_auth_headers(creator),
            json={"picks": [{"fixture_id": fixture.id, "team_id": home.id}]},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_rejects_team_not_in_fixture(
        self, client, db_session, test_competition, test_teams, test_user
    ):
        home, away = test_teams
        creator = await _make_user(db_session, "creator9")
        pool = await _seed_pool(db_session, test_competition.id, created_by=creator.id)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=3)

        fixture = await _finished_fixture(
            db_session, test_competition.id, home.id, away.id,
            gameweek=1, home_goals=1, away_goals=0,
        )

        resp = await client.put(
            f"/admin/pools/{pool.id}/users/{test_user.id}/picks",
            headers=_auth_headers(creator),
            json={"picks": [{"fixture_id": fixture.id, "team_id": 999999}]},
        )
        assert resp.status_code == 400
