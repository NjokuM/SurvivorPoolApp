"""
Tests for the lives/results processing pipeline.
Covers: correct picks, incorrect picks, draws, missed picks (no pick made),
elimination, idempotency, and already-eliminated users.
"""
import os
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ["CRON_SECRET"] = "test-cron-secret"

import pytest
from datetime import datetime, timedelta, timezone
from app.models.user import User
from app.models.competiton_data import Competition, Team, Fixture
from app.models.pool import Pool, PoolUserStats
from app.models.pick import Pick
from app.utils.auth import hash_password
from app.services.results import (
    _compute_pick_result_and_points,
    process_gameweek_results,
    POINTS_FOR_WIN,
    POINTS_FOR_DRAW,
    POINTS_FOR_LOSS,
)


# ==================== Unit Tests: _compute_pick_result_and_points ====================

class TestComputePickResult:
    """Pure logic tests — no DB needed."""

    def _make_fixture(self, home_goals, away_goals, home_team_id=1, away_team_id=2, status="FT"):
        """Create a minimal fixture-like object for testing (avoids SQLAlchemy instrumentation)."""
        from types import SimpleNamespace
        return SimpleNamespace(
            home_goals=home_goals, away_goals=away_goals,
            home_team_id=home_team_id, away_team_id=away_team_id,
            status=status,
        )

    def test_pick_home_team_wins(self):
        fixture = self._make_fixture(home_goals=2, away_goals=0)
        result, points = _compute_pick_result_and_points(1, fixture)
        assert result == "WIN"
        assert points == POINTS_FOR_WIN

    def test_pick_away_team_wins(self):
        fixture = self._make_fixture(home_goals=0, away_goals=3)
        result, points = _compute_pick_result_and_points(2, fixture)
        assert result == "WIN"
        assert points == POINTS_FOR_WIN

    def test_pick_home_team_loses(self):
        fixture = self._make_fixture(home_goals=0, away_goals=1)
        result, points = _compute_pick_result_and_points(1, fixture)
        assert result == "LOSS"
        assert points == POINTS_FOR_LOSS

    def test_pick_away_team_loses(self):
        fixture = self._make_fixture(home_goals=2, away_goals=1)
        result, points = _compute_pick_result_and_points(2, fixture)
        assert result == "LOSS"
        assert points == POINTS_FOR_LOSS

    def test_draw_gives_draw_result(self):
        fixture = self._make_fixture(home_goals=1, away_goals=1)
        result, points = _compute_pick_result_and_points(1, fixture)
        assert result == "DRAW"
        assert points == POINTS_FOR_DRAW

    def test_draw_same_for_either_team(self):
        fixture = self._make_fixture(home_goals=0, away_goals=0)
        r1, p1 = _compute_pick_result_and_points(1, fixture)
        r2, p2 = _compute_pick_result_and_points(2, fixture)
        assert r1 == r2 == "DRAW"
        assert p1 == p2 == POINTS_FOR_DRAW

    def test_pending_fixture_returns_pending(self):
        fixture = self._make_fixture(home_goals=0, away_goals=0, status="NS")
        result, points = _compute_pick_result_and_points(1, fixture)
        assert result == "PENDING"
        assert points == 0

    def test_in_progress_fixture_returns_pending(self):
        fixture = self._make_fixture(home_goals=1, away_goals=0, status="1H")
        result, points = _compute_pick_result_and_points(1, fixture)
        assert result == "PENDING"
        assert points == 0

    def test_high_scoring_draw(self):
        fixture = self._make_fixture(home_goals=4, away_goals=4)
        result, points = _compute_pick_result_and_points(1, fixture)
        assert result == "DRAW"
        assert points == POINTS_FOR_DRAW


# ==================== Integration Tests: process_gameweek_results ====================

# Helper to seed a full scenario into the test DB
async def _seed_scenario(db, *, num_users=1, lives=3, home_goals=2, away_goals=0,
                         fixture_status="FT", make_picks=True, pick_team="home",
                         start_gameweek=1, gameweek=10):
    """
    Seeds: 1 competition, 2 teams, 1 fixture, 1 pool, N users with stats,
    and optionally picks for each user.
    Returns dict with all created objects.
    """
    comp = Competition(
        external_id=39, name="Premier League", season=2025,
        country="England", type="League", logo="https://example.com/pl.png",
    )
    db.add(comp)
    await db.flush()

    home_team = Team(
        external_id=33, name="Manchester United", short_name="MUN",
        competition_id=comp.id, venue_name="Old Trafford", logo="https://example.com/mun.png",
    )
    away_team = Team(
        external_id=40, name="Liverpool", short_name="LIV",
        competition_id=comp.id, venue_name="Anfield", logo="https://example.com/liv.png",
    )
    db.add_all([home_team, away_team])
    await db.flush()

    kickoff = datetime.now(timezone.utc) - timedelta(hours=3)
    fixture = Fixture(
        external_id=1001, competition_id=comp.id,
        home_team_id=home_team.id, away_team_id=away_team.id,
        gameweek=gameweek, kickoff_time=kickoff,
        status=fixture_status, home_goals=home_goals, away_goals=away_goals,
    )
    db.add(fixture)
    await db.flush()

    pool = Pool(
        session_code="TEST123", name="Test Pool",
        competition_id=comp.id, start_gameweek=start_gameweek,
        max_picks_per_team=2, total_lives=3, is_active=True,
    )
    db.add(pool)
    await db.flush()

    users = []
    stats_list = []
    picks = []

    for i in range(num_users):
        user = User(
            userName=f"user{i}", email=f"user{i}@test.com",
            password=hash_password("pass"), firstName="Test", lastName=f"User{i}",
        )
        db.add(user)
        await db.flush()

        stat = PoolUserStats(
            pool_id=pool.id, user_id=user.id,
            total_points=0, lives_left=lives,
        )
        db.add(stat)
        await db.flush()

        if make_picks:
            picked_team = home_team if pick_team == "home" else away_team
            pick = Pick(
                pool_id=pool.id, user_id=user.id,
                team_id=picked_team.id, fixture_id=fixture.id,
                competition_id=comp.id,
            )
            db.add(pick)
            await db.flush()
            picks.append(pick)

        users.append(user)
        stats_list.append(stat)

    await db.commit()

    return {
        "comp": comp, "home_team": home_team, "away_team": away_team,
        "fixture": fixture, "pool": pool, "users": users,
        "stats": stats_list, "picks": picks,
    }


class TestProcessGameweekResults:

    @pytest.mark.asyncio
    async def test_winning_pick_awards_points_no_life_lost(self, db_session):
        """User picks home team, home team wins -> 3 points, no life lost."""
        data = await _seed_scenario(db_session, home_goals=2, away_goals=0, pick_team="home")

        result = await process_gameweek_results(db_session, data["comp"].id, 10)

        assert result["picks_processed"] == 1
        assert result["points_awarded"] == POINTS_FOR_WIN
        assert result["lives_deducted"] == 0

        await db_session.refresh(data["stats"][0])
        assert data["stats"][0].lives_left == 3
        assert data["stats"][0].total_points == POINTS_FOR_WIN

    @pytest.mark.asyncio
    async def test_losing_pick_deducts_life(self, db_session):
        """User picks home team, away team wins -> 0 points, 1 life lost."""
        data = await _seed_scenario(db_session, home_goals=0, away_goals=1, pick_team="home")

        result = await process_gameweek_results(db_session, data["comp"].id, 10)

        assert result["picks_processed"] == 1
        assert result["points_awarded"] == POINTS_FOR_LOSS
        assert result["lives_deducted"] == 1

        await db_session.refresh(data["stats"][0])
        assert data["stats"][0].lives_left == 2
        assert data["stats"][0].total_points == POINTS_FOR_LOSS

    @pytest.mark.asyncio
    async def test_draw_awards_1_point_no_life_lost(self, db_session):
        """User picks home team, match draws -> 1 point, no life lost."""
        data = await _seed_scenario(db_session, home_goals=1, away_goals=1, pick_team="home")

        result = await process_gameweek_results(db_session, data["comp"].id, 10)

        assert result["picks_processed"] == 1
        assert result["points_awarded"] == POINTS_FOR_DRAW
        assert result["lives_deducted"] == 0

        await db_session.refresh(data["stats"][0])
        assert data["stats"][0].lives_left == 3
        assert data["stats"][0].total_points == POINTS_FOR_DRAW

    @pytest.mark.asyncio
    async def test_loss_with_1_life_eliminates_user(self, db_session):
        """User on last life loses -> eliminated, eliminated_gameweek set."""
        data = await _seed_scenario(db_session, lives=1, home_goals=0, away_goals=2, pick_team="home")

        result = await process_gameweek_results(db_session, data["comp"].id, 10)

        assert result["lives_deducted"] == 1

        await db_session.refresh(data["stats"][0])
        assert data["stats"][0].lives_left == 0
        assert data["stats"][0].eliminated_gameweek == 10

    @pytest.mark.asyncio
    async def test_already_eliminated_user_not_deducted_further(self, db_session):
        """User already at 0 lives should not go negative."""
        data = await _seed_scenario(db_session, lives=0, home_goals=0, away_goals=1, pick_team="home")
        # Manually set eliminated_gameweek
        data["stats"][0].eliminated_gameweek = 8
        await db_session.commit()

        result = await process_gameweek_results(db_session, data["comp"].id, 10)

        await db_session.refresh(data["stats"][0])
        assert data["stats"][0].lives_left == 0
        assert data["stats"][0].eliminated_gameweek == 8  # unchanged

    @pytest.mark.asyncio
    async def test_no_finished_fixtures_returns_zero(self, db_session):
        """If no fixtures are FT, nothing should be processed."""
        data = await _seed_scenario(db_session, fixture_status="NS", pick_team="home")

        result = await process_gameweek_results(db_session, data["comp"].id, 10)

        assert result["picks_processed"] == 0
        assert result["points_awarded"] == 0
        assert result["lives_deducted"] == 0

    @pytest.mark.asyncio
    async def test_idempotent_second_run_does_nothing(self, db_session):
        """Running process twice should not double-count picks."""
        data = await _seed_scenario(db_session, home_goals=2, away_goals=0, pick_team="home")

        result1 = await process_gameweek_results(db_session, data["comp"].id, 10)
        assert result1["picks_processed"] == 1

        result2 = await process_gameweek_results(db_session, data["comp"].id, 10)
        assert result2["picks_processed"] == 0

        await db_session.refresh(data["stats"][0])
        assert data["stats"][0].total_points == POINTS_FOR_WIN  # not doubled

    @pytest.mark.asyncio
    async def test_multiple_users_processed_correctly(self, db_session):
        """Two users in same pool, both pick home team which wins."""
        data = await _seed_scenario(db_session, num_users=2, home_goals=3, away_goals=1, pick_team="home")

        result = await process_gameweek_results(db_session, data["comp"].id, 10)

        assert result["picks_processed"] == 2
        assert result["points_awarded"] == POINTS_FOR_WIN * 2

        for stat in data["stats"]:
            await db_session.refresh(stat)
            assert stat.lives_left == 3
            assert stat.total_points == POINTS_FOR_WIN


# ==================== BUG: Missed Pick (no pick made) ====================

class TestMissedPick:
    """
    Tests for the known bug: users who don't make a pick for a gameweek
    should lose a life, but currently they don't because no Pick row exists.
    These tests document the EXPECTED behavior and expose the current bug.
    """

    @pytest.mark.asyncio
    async def test_missed_pick_loses_a_life(self, db_session):
        """
        EXPECTED: User makes no pick for a gameweek that has finished fixtures.
        They should lose 1 life as a penalty.
        """
        data = await _seed_scenario(db_session, make_picks=False, home_goals=2, away_goals=0)

        result = await process_gameweek_results(db_session, data["comp"].id, 10)

        assert result["lives_deducted"] == 1

        await db_session.refresh(data["stats"][0])
        assert data["stats"][0].lives_left == 2

    @pytest.mark.asyncio
    async def test_missed_pick_with_1_life_eliminates_user(self, db_session):
        """User on last life who misses a pick should be eliminated."""
        data = await _seed_scenario(db_session, make_picks=False, lives=1, home_goals=2, away_goals=0)

        result = await process_gameweek_results(db_session, data["comp"].id, 10)

        assert result["lives_deducted"] == 1

        await db_session.refresh(data["stats"][0])
        assert data["stats"][0].lives_left == 0
        assert data["stats"][0].eliminated_gameweek == 10

    @pytest.mark.asyncio
    async def test_missed_pick_mixed_scenario(self, db_session):
        """
        Two users in a pool: user0 makes a winning pick, user1 makes no pick.
        User0 should get points. User1 should lose a life.
        """
        data = await _seed_scenario(
            db_session, num_users=2, make_picks=False,
            home_goals=2, away_goals=0,
        )

        # Manually add a pick only for user0
        pick = Pick(
            pool_id=data["pool"].id, user_id=data["users"][0].id,
            team_id=data["home_team"].id, fixture_id=data["fixture"].id,
            competition_id=data["comp"].id,
        )
        db_session.add(pick)
        await db_session.commit()

        result = await process_gameweek_results(db_session, data["comp"].id, 10)

        # User0's pick is processed — won, no life lost
        assert result["picks_processed"] == 1
        await db_session.refresh(data["stats"][0])
        assert data["stats"][0].total_points == POINTS_FOR_WIN
        assert data["stats"][0].lives_left == 3

        # User1 made no pick — should lose 1 life
        await db_session.refresh(data["stats"][1])
        assert data["stats"][1].lives_left == 2
        assert data["stats"][1].total_points == 0

    @pytest.mark.asyncio
    async def test_missed_pick_already_eliminated_not_penalized(self, db_session):
        """User already eliminated (0 lives) who misses a pick should not be penalized further."""
        data = await _seed_scenario(db_session, make_picks=False, lives=0, home_goals=2, away_goals=0)
        data["stats"][0].eliminated_gameweek = 8
        await db_session.commit()

        result = await process_gameweek_results(db_session, data["comp"].id, 10)

        await db_session.refresh(data["stats"][0])
        assert data["stats"][0].lives_left == 0
        assert data["stats"][0].eliminated_gameweek == 8  # unchanged


# ==================== BUG REGRESSION: start_gameweek guard + idempotency ====================

class TestMissedPickStartGameweekGuard:
    """Regression tests for the bug where missed-pick penalties were applied
    retroactively to gameweeks before the pool's start_gameweek."""

    @pytest.mark.asyncio
    async def test_no_penalty_before_pool_start_gameweek(self, db_session):
        """
        Pool starts at GW25. Processing GW10 should NOT penalize anyone
        for missing a pick, because the pool didn't exist yet.
        """
        data = await _seed_scenario(
            db_session, make_picks=False, home_goals=2, away_goals=0,
            start_gameweek=25, gameweek=10,
        )

        result = await process_gameweek_results(db_session, data["comp"].id, 10)

        assert result["lives_deducted"] == 0
        await db_session.refresh(data["stats"][0])
        assert data["stats"][0].lives_left == 3  # untouched

    @pytest.mark.asyncio
    async def test_penalty_applied_at_pool_start_gameweek(self, db_session):
        """
        Pool starts at GW10. Processing GW10 SHOULD penalize a user
        who missed their pick.
        """
        data = await _seed_scenario(
            db_session, make_picks=False, home_goals=2, away_goals=0,
            start_gameweek=10, gameweek=10,
        )

        result = await process_gameweek_results(db_session, data["comp"].id, 10)

        assert result["lives_deducted"] == 1
        await db_session.refresh(data["stats"][0])
        assert data["stats"][0].lives_left == 2

    @pytest.mark.asyncio
    async def test_penalty_applied_after_pool_start_gameweek(self, db_session):
        """
        Pool starts at GW5. Processing GW10 SHOULD penalize a user
        who missed their pick.
        """
        data = await _seed_scenario(
            db_session, make_picks=False, home_goals=2, away_goals=0,
            start_gameweek=5, gameweek=10,
        )

        result = await process_gameweek_results(db_session, data["comp"].id, 10)

        assert result["lives_deducted"] == 1
        await db_session.refresh(data["stats"][0])
        assert data["stats"][0].lives_left == 2


class TestMissedPickIdempotency:
    """Regression tests for the bug where re-running process_gameweek_results
    would re-deduct lives for missed picks."""

    @pytest.mark.asyncio
    async def test_missed_pick_penalty_idempotent_on_rerun(self, db_session):
        """
        Running process_gameweek_results twice for the same gameweek
        should only deduct 1 life total, not 2.
        """
        data = await _seed_scenario(
            db_session, make_picks=False, home_goals=2, away_goals=0,
            start_gameweek=1, gameweek=10,
        )

        result1 = await process_gameweek_results(db_session, data["comp"].id, 10)
        assert result1["lives_deducted"] == 1

        await db_session.refresh(data["stats"][0])
        assert data["stats"][0].lives_left == 2

        result2 = await process_gameweek_results(db_session, data["comp"].id, 10)
        # Second run should NOT deduct again
        assert result2["lives_deducted"] == 0

        await db_session.refresh(data["stats"][0])
        assert data["stats"][0].lives_left == 2  # still 2, not 1

    @pytest.mark.asyncio
    async def test_missed_pick_elimination_idempotent(self, db_session):
        """
        User on last life misses a pick -> eliminated.
        Re-running should not change anything.
        """
        data = await _seed_scenario(
            db_session, make_picks=False, lives=1, home_goals=2, away_goals=0,
            start_gameweek=1, gameweek=10,
        )

        result1 = await process_gameweek_results(db_session, data["comp"].id, 10)
        assert result1["lives_deducted"] == 1

        await db_session.refresh(data["stats"][0])
        assert data["stats"][0].lives_left == 0
        assert data["stats"][0].eliminated_gameweek == 10

        result2 = await process_gameweek_results(db_session, data["comp"].id, 10)
        assert result2["lives_deducted"] == 0

        await db_session.refresh(data["stats"][0])
        assert data["stats"][0].lives_left == 0
        assert data["stats"][0].eliminated_gameweek == 10  # unchanged


# ==================== NP (No Pick) Record Tests ====================

class TestNPPickRecord:
    """
    TDD tests for the NP approach: when a user misses a pick, a Pick record
    should be created with result='NP' and team_id=None. This provides:
    - Audit trail (user can see why they lost a life in history)
    - Built-in idempotency (Pick row exists, so re-run won't double-penalize)
    """

    @pytest.mark.asyncio
    async def test_missed_pick_creates_np_record(self, db_session):
        """
        When a user misses a pick, an NP Pick record should be created
        with result='NP', team_id=None, and points=0.
        """
        data = await _seed_scenario(
            db_session, make_picks=False, home_goals=2, away_goals=0,
            start_gameweek=1, gameweek=10,
        )

        await process_gameweek_results(db_session, data["comp"].id, 10)

        # Check that an NP pick was created
        from sqlalchemy import select as sa_select
        np_res = await db_session.execute(
            sa_select(Pick).where(
                Pick.pool_id == data["pool"].id,
                Pick.user_id == data["users"][0].id,
            )
        )
        np_pick = np_res.scalars().first()

        assert np_pick is not None, "NP Pick record should be created"
        assert np_pick.result.value == "NP"
        assert np_pick.team_id is None
        assert np_pick.points == 0
        assert np_pick.fixture_id == data["fixture"].id
        assert np_pick.competition_id == data["comp"].id

    @pytest.mark.asyncio
    async def test_np_record_provides_idempotency(self, db_session):
        """
        Running process_gameweek_results twice should only create one NP record
        and only deduct 1 life total — the NP Pick row prevents double-penalty.
        """
        data = await _seed_scenario(
            db_session, make_picks=False, home_goals=2, away_goals=0,
            start_gameweek=1, gameweek=10,
        )

        result1 = await process_gameweek_results(db_session, data["comp"].id, 10)
        assert result1["lives_deducted"] == 1

        result2 = await process_gameweek_results(db_session, data["comp"].id, 10)
        assert result2["lives_deducted"] == 0

        await db_session.refresh(data["stats"][0])
        assert data["stats"][0].lives_left == 2  # only deducted once

        # Verify only ONE NP pick exists
        from sqlalchemy import select as sa_select
        np_res = await db_session.execute(
            sa_select(Pick).where(
                Pick.pool_id == data["pool"].id,
                Pick.user_id == data["users"][0].id,
            )
        )
        np_picks = np_res.scalars().all()
        assert len(np_picks) == 1

    @pytest.mark.asyncio
    async def test_np_record_mixed_scenario(self, db_session):
        """
        Two users: user0 makes a winning pick, user1 misses.
        User0 gets points + no NP record. User1 gets NP record + loses a life.
        """
        data = await _seed_scenario(
            db_session, num_users=2, make_picks=False,
            home_goals=2, away_goals=0, start_gameweek=1, gameweek=10,
        )

        # Manually add a pick only for user0
        pick = Pick(
            pool_id=data["pool"].id, user_id=data["users"][0].id,
            team_id=data["home_team"].id, fixture_id=data["fixture"].id,
            competition_id=data["comp"].id,
        )
        db_session.add(pick)
        await db_session.commit()

        await process_gameweek_results(db_session, data["comp"].id, 10)

        # User0: winning pick processed, no NP
        await db_session.refresh(data["stats"][0])
        assert data["stats"][0].lives_left == 3
        assert data["stats"][0].total_points == POINTS_FOR_WIN

        # User1: NP record created, lost a life
        await db_session.refresh(data["stats"][1])
        assert data["stats"][1].lives_left == 2

        from sqlalchemy import select as sa_select
        np_res = await db_session.execute(
            sa_select(Pick).where(
                Pick.pool_id == data["pool"].id,
                Pick.user_id == data["users"][1].id,
            )
        )
        np_pick = np_res.scalars().first()
        assert np_pick is not None
        assert np_pick.result.value == "NP"
        assert np_pick.team_id is None

    @pytest.mark.asyncio
    async def test_np_record_not_created_before_pool_start(self, db_session):
        """
        Pool starts at GW25. Processing GW10 should NOT create any NP records.
        """
        data = await _seed_scenario(
            db_session, make_picks=False, home_goals=2, away_goals=0,
            start_gameweek=25, gameweek=10,
        )

        await process_gameweek_results(db_session, data["comp"].id, 10)

        from sqlalchemy import select as sa_select
        np_res = await db_session.execute(
            sa_select(Pick).where(
                Pick.pool_id == data["pool"].id,
                Pick.user_id == data["users"][0].id,
            )
        )
        np_picks = np_res.scalars().all()
        assert len(np_picks) == 0, "No NP record should be created before pool start"

        await db_session.refresh(data["stats"][0])
        assert data["stats"][0].lives_left == 3  # untouched

    @pytest.mark.asyncio
    async def test_np_record_on_last_life_eliminates(self, db_session):
        """
        User on last life misses a pick -> NP record created, eliminated.
        """
        data = await _seed_scenario(
            db_session, make_picks=False, lives=1, home_goals=2, away_goals=0,
            start_gameweek=1, gameweek=10,
        )

        await process_gameweek_results(db_session, data["comp"].id, 10)

        await db_session.refresh(data["stats"][0])
        assert data["stats"][0].lives_left == 0
        assert data["stats"][0].eliminated_gameweek == 10

        from sqlalchemy import select as sa_select
        np_res = await db_session.execute(
            sa_select(Pick).where(
                Pick.pool_id == data["pool"].id,
                Pick.user_id == data["users"][0].id,
            )
        )
        np_pick = np_res.scalars().first()
        assert np_pick is not None
        assert np_pick.result.value == "NP"

    @pytest.mark.asyncio
    async def test_np_not_created_for_already_eliminated_user(self, db_session):
        """
        User already eliminated (0 lives) should NOT get an NP record.
        """
        data = await _seed_scenario(
            db_session, make_picks=False, lives=0, home_goals=2, away_goals=0,
            start_gameweek=1, gameweek=10,
        )
        data["stats"][0].eliminated_gameweek = 8
        await db_session.commit()

        await process_gameweek_results(db_session, data["comp"].id, 10)

        from sqlalchemy import select as sa_select
        np_res = await db_session.execute(
            sa_select(Pick).where(
                Pick.pool_id == data["pool"].id,
                Pick.user_id == data["users"][0].id,
            )
        )
        np_picks = np_res.scalars().all()
        assert len(np_picks) == 0, "No NP record for already eliminated user"


# ==================== Pool Archiving Tests ====================

class TestPoolArchiving:
    """A pool is archived (is_active flips to False) once there's nothing
    left to play for: a lives pool with at most one survivor, or any pool
    once its competition's final gameweek has fully finished."""

    async def _seed_two_user_lives_pool(self, db, *, gameweek=10, total_gameweeks=None):
        """Two users, one fixture each user picks a different team for, so
        one wins and one loses - lets us control exactly who survives."""
        comp = Competition(
            external_id=39, name="Premier League", season=2025,
            country="England", type="League", logo="https://example.com/pl.png",
        )
        db.add(comp)
        await db.flush()

        home_team = Team(
            external_id=33, name="Man United", short_name="MUN",
            competition_id=comp.id, venue_name="Old Trafford", logo="x",
        )
        away_team = Team(
            external_id=40, name="Liverpool", short_name="LIV",
            competition_id=comp.id, venue_name="Anfield", logo="x",
        )
        db.add_all([home_team, away_team])
        await db.flush()

        kickoff = datetime.now(timezone.utc) - timedelta(hours=3)
        fixture = Fixture(
            external_id=1001, competition_id=comp.id,
            home_team_id=home_team.id, away_team_id=away_team.id,
            gameweek=gameweek, kickoff_time=kickoff,
            status="FT", home_goals=2, away_goals=0,  # home wins
        )
        db.add(fixture)
        await db.flush()

        if total_gameweeks and total_gameweeks != gameweek:
            # A fixture in a later, not-yet-played gameweek, so this isn't
            # actually the final gameweek of the competition.
            db.add(Fixture(
                external_id=1002, competition_id=comp.id,
                home_team_id=home_team.id, away_team_id=away_team.id,
                gameweek=total_gameweeks,
                kickoff_time=datetime.now(timezone.utc) + timedelta(days=7),
                status="NS",
            ))
            await db.flush()

        pool = Pool(
            session_code="ARCH01", name="Archive Test Pool",
            competition_id=comp.id, start_gameweek=1,
            max_picks_per_team=2, total_lives=1, has_lives=True, is_active=True,
        )
        db.add(pool)
        await db.flush()

        winner = User(userName="winner", email="winner@test.com", password=hash_password("pass"), firstName="W", lastName="Survivor")
        loser = User(userName="loser", email="loser@test.com", password=hash_password("pass"), firstName="L", lastName="Eliminated")
        db.add_all([winner, loser])
        await db.flush()

        winner_stats = PoolUserStats(pool_id=pool.id, user_id=winner.id, total_points=0, lives_left=1)
        loser_stats = PoolUserStats(pool_id=pool.id, user_id=loser.id, total_points=0, lives_left=1)
        db.add_all([winner_stats, loser_stats])
        await db.flush()

        db.add(Pick(pool_id=pool.id, user_id=winner.id, team_id=home_team.id, fixture_id=fixture.id, competition_id=comp.id))
        db.add(Pick(pool_id=pool.id, user_id=loser.id, team_id=away_team.id, fixture_id=fixture.id, competition_id=comp.id))
        await db.commit()

        return {
            "comp": comp, "pool": pool, "fixture": fixture,
            "winner": winner, "winner_stats": winner_stats,
            "loser": loser, "loser_stats": loser_stats,
        }

    @pytest.mark.asyncio
    async def test_lives_pool_archived_once_one_survivor_remains(self, db_session):
        # total_gameweeks=20 keeps this mid-season, isolating the
        # lives-decided path from the separate season-concluded path.
        data = await self._seed_two_user_lives_pool(db_session, gameweek=10, total_gameweeks=20)

        await process_gameweek_results(db_session, data["comp"].id, 10)

        await db_session.refresh(data["pool"])
        assert data["pool"].is_active is False

    @pytest.mark.asyncio
    async def test_lives_pool_stays_active_with_two_survivors(self, db_session):
        """Both users on 2 lives - the loser drops to 1 life but is still
        a survivor, so there's still a contest. total_gameweeks=20 keeps
        this mid-season, isolating from the season-concluded path."""
        data = await self._seed_two_user_lives_pool(db_session, gameweek=10, total_gameweeks=20)
        data["winner_stats"].lives_left = 2
        data["loser_stats"].lives_left = 2
        await db_session.commit()

        await process_gameweek_results(db_session, data["comp"].id, 10)

        await db_session.refresh(data["pool"])
        assert data["pool"].is_active is True

    @pytest.mark.asyncio
    async def test_league_pool_not_archived_by_elimination_logic(self, db_session):
        """League mode has no elimination at all, so the "decided" check
        must never apply to it - only a concluded season archives it."""
        data = await self._seed_two_user_lives_pool(
            db_session, gameweek=10, total_gameweeks=20,
        )
        data["pool"].has_lives = False
        await db_session.commit()

        await process_gameweek_results(db_session, data["comp"].id, 10)

        await db_session.refresh(data["pool"])
        assert data["pool"].is_active is True

    @pytest.mark.asyncio
    async def test_season_concluded_archives_pool_regardless_of_mode(self, db_session):
        """Final gameweek of the competition finishing archives the pool
        even with multiple survivors still in it."""
        data = await self._seed_two_user_lives_pool(db_session, gameweek=10)
        data["winner_stats"].lives_left = 2
        data["loser_stats"].lives_left = 2
        await db_session.commit()
        # gameweek 10 is the only (and therefore final) gameweek seeded.

        await process_gameweek_results(db_session, data["comp"].id, 10)

        await db_session.refresh(data["pool"])
        assert data["pool"].is_active is False

    @pytest.mark.asyncio
    async def test_not_archived_when_processing_a_non_final_gameweek(self, db_session):
        """A later gameweek's fixture already exists (not yet played), so
        gameweek 10 finishing isn't the end of the season."""
        data = await self._seed_two_user_lives_pool(
            db_session, gameweek=10, total_gameweeks=20,
        )
        data["winner_stats"].lives_left = 2
        data["loser_stats"].lives_left = 2
        await db_session.commit()

        await process_gameweek_results(db_session, data["comp"].id, 10)

        await db_session.refresh(data["pool"])
        assert data["pool"].is_active is True

    @pytest.mark.asyncio
    async def test_already_inactive_pool_is_left_alone(self, db_session):
        """A pool archived some other way shouldn't be touched again (no
        crash, no reactivation) just because a gameweek gets reprocessed."""
        data = await self._seed_two_user_lives_pool(db_session, gameweek=10)
        data["pool"].is_active = False
        await db_session.commit()

        await process_gameweek_results(db_session, data["comp"].id, 10)

        await db_session.refresh(data["pool"])
        assert data["pool"].is_active is False


class TestRecomputeAllPoolStatuses:
    """The one-off backfill used to catch pools that were already decided
    or already past their final gameweek before this feature existed."""

    @pytest.mark.asyncio
    async def test_archives_an_already_decided_pool_without_reprocessing(self, db_session):
        from app.services.results import recompute_all_pool_statuses

        comp = Competition(
            external_id=39, name="Premier League", season=2025,
            country="England", type="League", logo="x",
        )
        db_session.add(comp)
        await db_session.flush()

        pool = Pool(
            session_code="BACKFIL1", name="Old Pool", competition_id=comp.id,
            start_gameweek=1, max_picks_per_team=2, total_lives=3,
            has_lives=True, is_active=True,
        )
        db_session.add(pool)
        await db_session.flush()

        winner = User(userName="oldwinner", email="oldwinner@test.com", password=hash_password("pass"), firstName="W", lastName="Old")
        loser = User(userName="oldloser", email="oldloser@test.com", password=hash_password("pass"), firstName="L", lastName="Old")
        db_session.add_all([winner, loser])
        await db_session.flush()

        db_session.add(PoolUserStats(pool_id=pool.id, user_id=winner.id, total_points=10, lives_left=1))
        db_session.add(PoolUserStats(pool_id=pool.id, user_id=loser.id, total_points=5, lives_left=0))
        await db_session.commit()

        archived = await recompute_all_pool_statuses(db_session)

        assert archived == 1
        await db_session.refresh(pool)
        assert pool.is_active is False

    @pytest.mark.asyncio
    async def test_leaves_an_undecided_pool_active(self, db_session):
        from app.services.results import recompute_all_pool_statuses

        comp = Competition(
            external_id=39, name="Premier League", season=2025,
            country="England", type="League", logo="x",
        )
        db_session.add(comp)
        await db_session.flush()

        pool = Pool(
            session_code="BACKFIL2", name="Ongoing Pool", competition_id=comp.id,
            start_gameweek=1, max_picks_per_team=2, total_lives=3,
            has_lives=True, is_active=True,
        )
        db_session.add(pool)
        await db_session.flush()

        p1 = User(userName="p1", email="p1@test.com", password=hash_password("pass"), firstName="P", lastName="One")
        p2 = User(userName="p2", email="p2@test.com", password=hash_password("pass"), firstName="P", lastName="Two")
        db_session.add_all([p1, p2])
        await db_session.flush()

        db_session.add(PoolUserStats(pool_id=pool.id, user_id=p1.id, total_points=10, lives_left=2))
        db_session.add(PoolUserStats(pool_id=pool.id, user_id=p2.id, total_points=5, lives_left=1))
        await db_session.commit()

        archived = await recompute_all_pool_statuses(db_session)

        assert archived == 0
        await db_session.refresh(pool)
        assert pool.is_active is True
