"""
Tests for goal difference as a leaderboard tiebreaker, and the per-pool
team leaderboard (points earned per team, plus a per-team pick breakdown).
"""
import os
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ["CRON_SECRET"] = "test-cron-secret"

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from app.models.user import User
from app.models.competiton_data import Competition, Team, Fixture
from app.models.pool import Pool, PoolUserStats
from app.models.pick import Pick, PickResultEnum
from app.utils.auth import hash_password, create_access_token
from app.services.leaderboard import get_leaderboard, pick_goal_difference
from app.services.results import process_gameweek_results


@pytest_asyncio.fixture
async def setup(db_session):
    """Pool with two players and three teams. Fixtures:
        GW1: ARS 3-0 CHE (FT)
        GW2: CHE 1-0 TOT (FT)
        GW3: TOT vs ARS (not started)
    """
    s = db_session
    comp = Competition(external_id=39, name="PL", season=2025)
    s.add(comp)
    await s.flush()

    ars = Team(external_id=1, name="Arsenal", short_name="ARS", competition_id=comp.id)
    che = Team(external_id=2, name="Chelsea", short_name="CHE", competition_id=comp.id)
    tot = Team(external_id=3, name="Tottenham", short_name="TOT", competition_id=comp.id)
    alice = User(userName="alice", email="a@x.com", password=hash_password("pw"), firstName="A", lastName="A")
    bob = User(userName="bob", email="b@x.com", password=hash_password("pw"), firstName="B", lastName="B")
    s.add_all([ars, che, tot, alice, bob])
    await s.flush()

    now = datetime.now(timezone.utc)
    f1 = Fixture(external_id=101, competition_id=comp.id, home_team_id=ars.id, away_team_id=che.id,
                 gameweek=1, kickoff_time=now - timedelta(days=14), status="FT", home_goals=3, away_goals=0)
    f2 = Fixture(external_id=102, competition_id=comp.id, home_team_id=che.id, away_team_id=tot.id,
                 gameweek=2, kickoff_time=now - timedelta(days=7), status="FT", home_goals=1, away_goals=0)
    f3 = Fixture(external_id=103, competition_id=comp.id, home_team_id=tot.id, away_team_id=ars.id,
                 gameweek=3, kickoff_time=now + timedelta(days=1), status="NS")
    pool = Pool(session_code="ABC123", name="Test", competition_id=comp.id, start_gameweek=1,
                total_lives=3, created_by=alice.id)
    s.add_all([f1, f2, f3, pool])
    await s.flush()

    s.add_all([
        PoolUserStats(pool_id=pool.id, user_id=alice.id, lives_left=3, total_points=0),
        PoolUserStats(pool_id=pool.id, user_id=bob.id, lives_left=3, total_points=0),
    ])
    await s.commit()
    return dict(comp=comp, ars=ars, che=che, tot=tot, alice=alice, bob=bob,
                f1=f1, f2=f2, f3=f3, pool=pool)


def _headers(user):
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


def _pick(setup, user, team, fixture, **kw):
    return Pick(pool_id=setup["pool"].id, user_id=user.id, team_id=team.id,
                fixture_id=fixture.id, competition_id=setup["comp"].id, **kw)


# ==================== Goal difference ====================

class TestPickGoalDifference:
    def test_home_team_perspective(self):
        assert pick_goal_difference(1, 1, 3, 0) == 3

    def test_away_team_perspective(self):
        assert pick_goal_difference(2, 1, 3, 0) == -3

    def test_draw_is_zero(self):
        assert pick_goal_difference(1, 1, 2, 2) == 0


class TestLeaderboardGoalDifference:
    @pytest.mark.asyncio
    async def test_goal_difference_breaks_points_tie(self, db_session, setup):
        """Both win once (3 pts each). Alice won 3-0 (+3), Bob won 1-0 (+1)."""
        db_session.add_all([
            _pick(setup, setup["bob"], setup["che"], setup["f2"]),
            _pick(setup, setup["alice"], setup["ars"], setup["f1"]),
        ])
        await db_session.commit()
        await process_gameweek_results(db_session, setup["comp"].id, 1)
        await process_gameweek_results(db_session, setup["comp"].id, 2)

        board = await get_leaderboard(db_session, setup["pool"].id)
        by_name = {r["username"]: r for r in board}
        assert by_name["alice"]["total_points"] == by_name["bob"]["total_points"] == 3
        assert by_name["alice"]["goal_difference"] == 3
        assert by_name["bob"]["goal_difference"] == 1
        assert [r["username"] for r in board] == ["alice", "bob"]
        assert by_name["alice"]["rank"] == 1
        assert by_name["bob"]["rank"] == 2

    @pytest.mark.asyncio
    async def test_equal_points_and_goal_difference_share_rank(self, db_session, setup):
        db_session.add_all([
            _pick(setup, setup["alice"], setup["ars"], setup["f1"]),
            _pick(setup, setup["bob"], setup["ars"], setup["f1"]),
        ])
        await db_session.commit()
        await process_gameweek_results(db_session, setup["comp"].id, 1)

        board = await get_leaderboard(db_session, setup["pool"].id)
        assert [r["rank"] for r in board] == [1, 1]
        assert all(r["goal_difference"] == 3 for r in board)

    @pytest.mark.asyncio
    async def test_losses_and_missed_picks(self, db_session, setup):
        """A loss counts negatively; a missed pick (NP) contributes nothing."""
        db_session.add(_pick(setup, setup["alice"], setup["che"], setup["f1"]))  # lost 0-3
        await db_session.commit()
        await process_gameweek_results(db_session, setup["comp"].id, 1)  # bob gets NP

        board = await get_leaderboard(db_session, setup["pool"].id)
        by_name = {r["username"]: r for r in board}
        assert by_name["alice"]["goal_difference"] == -3
        assert by_name["bob"]["goal_difference"] == 0

    @pytest.mark.asyncio
    async def test_leaderboard_endpoint_includes_goal_difference(self, client, db_session, setup):
        db_session.add(_pick(setup, setup["alice"], setup["ars"], setup["f1"]))
        await db_session.commit()
        await process_gameweek_results(db_session, setup["comp"].id, 1)

        res = await client.get(f"/pools/{setup['pool'].id}/leaderboard", headers=_headers(setup["alice"]))
        assert res.status_code == 200
        assert res.json()[0]["goal_difference"] == 3


# ==================== Team leaderboard ====================

class TestTeamLeaderboard:
    @pytest.mark.asyncio
    async def test_ranks_teams_by_points_earned(self, client, db_session, setup):
        db_session.add_all([
            _pick(setup, setup["alice"], setup["ars"], setup["f1"]),   # W 3-0
            _pick(setup, setup["bob"], setup["ars"], setup["f1"]),     # W 3-0
            _pick(setup, setup["alice"], setup["che"], setup["f2"]),   # W 1-0
            _pick(setup, setup["bob"], setup["tot"], setup["f2"]),     # L 0-1
        ])
        await db_session.commit()
        await process_gameweek_results(db_session, setup["comp"].id, 1)
        await process_gameweek_results(db_session, setup["comp"].id, 2)

        res = await client.get(f"/pools/{setup['pool'].id}/team-leaderboard", headers=_headers(setup["alice"]))
        assert res.status_code == 200
        rows = res.json()
        assert [r["team_name"] for r in rows] == ["Arsenal", "Chelsea", "Tottenham"]

        ars, che, tot = rows
        assert (ars["total_points"], ars["goal_difference"], ars["times_picked"], ars["wins"]) == (6, 6, 2, 2)
        assert (che["total_points"], che["goal_difference"], che["wins"]) == (3, 1, 1)
        assert (tot["total_points"], tot["goal_difference"], tot["losses"]) == (0, -1, 1)
        assert [r["rank"] for r in rows] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_includes_unpicked_teams_and_counts_pending_picks(self, client, db_session, setup):
        db_session.add(_pick(setup, setup["alice"], setup["tot"], setup["f3"]))  # not played yet
        await db_session.commit()

        res = await client.get(f"/pools/{setup['pool'].id}/team-leaderboard", headers=_headers(setup["alice"]))
        rows = {r["team_name"]: r for r in res.json()}
        assert set(rows) == {"Arsenal", "Chelsea", "Tottenham"}
        assert rows["Tottenham"]["times_picked"] == 1
        assert rows["Tottenham"]["total_points"] == 0
        assert rows["Arsenal"]["times_picked"] == 0

    @pytest.mark.asyncio
    async def test_requires_auth(self, client, setup):
        res = await client.get(f"/pools/{setup['pool'].id}/team-leaderboard")
        assert res.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_unknown_pool_404(self, client, setup):
        res = await client.get("/pools/9999/team-leaderboard", headers=_headers(setup["alice"]))
        assert res.status_code == 404


class TestTeamPicks:
    @pytest.mark.asyncio
    async def test_lists_each_pick_with_result_and_gameweek(self, client, db_session, setup):
        db_session.add_all([
            _pick(setup, setup["alice"], setup["che"], setup["f1"]),   # GW1 away, L 0-3
            _pick(setup, setup["bob"], setup["che"], setup["f2"]),     # GW2 home, W 1-0
        ])
        await db_session.commit()
        await process_gameweek_results(db_session, setup["comp"].id, 1)
        await process_gameweek_results(db_session, setup["comp"].id, 2)

        res = await client.get(
            f"/pools/{setup['pool'].id}/team-leaderboard/{setup['che'].id}", headers=_headers(setup["alice"])
        )
        assert res.status_code == 200
        body = res.json()
        assert body["team_name"] == "Chelsea"

        gw2, gw1 = body["picks"]  # newest first
        assert gw2["username"] == "bob"
        assert (gw2["gameweek"], gw2["is_home"], gw2["opponent_name"]) == (2, True, "Tottenham")
        assert (gw2["team_goals"], gw2["opponent_goals"], gw2["result"], gw2["points"]) == (1, 0, "WIN", 3)

        assert gw1["username"] == "alice"
        assert (gw1["gameweek"], gw1["is_home"], gw1["opponent_name"]) == (1, False, "Arsenal")
        assert (gw1["team_goals"], gw1["opponent_goals"], gw1["result"], gw1["points"]) == (0, 3, "LOSS", 0)

    @pytest.mark.asyncio
    async def test_pending_pick_has_no_result(self, client, db_session, setup):
        db_session.add(_pick(setup, setup["alice"], setup["ars"], setup["f3"]))
        await db_session.commit()

        res = await client.get(
            f"/pools/{setup['pool'].id}/team-leaderboard/{setup['ars'].id}", headers=_headers(setup["alice"])
        )
        (pick,) = res.json()["picks"]
        assert pick["result"] is None
        assert pick["team_goals"] is None
        assert pick["points"] == 0
        assert pick["is_home"] is False

    @pytest.mark.asyncio
    async def test_team_from_other_league_404(self, client, db_session, setup):
        other = Competition(external_id=140, name="La Liga", season=2025)
        db_session.add(other)
        await db_session.flush()
        rma = Team(external_id=541, name="Real Madrid", competition_id=other.id)
        db_session.add(rma)
        await db_session.commit()

        res = await client.get(
            f"/pools/{setup['pool'].id}/team-leaderboard/{rma.id}", headers=_headers(setup["alice"])
        )
        assert res.status_code == 404
