"""
Tests for double weeks: points-only pools where a member can switch on a
gameweek with two picks (different matches) and score both results.
"""
import os
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ["CRON_SECRET"] = "test-cron-secret"

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.models.user import User
from app.models.competiton_data import Competition, Team, Fixture
from app.models.pool import Pool, PoolUserStats, DoubleWeek
from app.models.pick import Pick
from app.models.notification import PushToken
from app.utils.auth import hash_password, create_access_token
from app.services import notifications as notifications_module
from app.services.double_weeks import suggested_double_weeks
from app.services.leaderboard import get_leaderboard
from app.services.results import process_gameweek_results


@pytest_asyncio.fixture
async def setup(db_session):
    """Four teams, three gameweeks:
        GW1 (finished): A 2-0 B, C 1-1 D
        GW2 (upcoming): A v C, B v D
        GW3 (upcoming): A v D, B v C
    A points pool (2 double weeks) and a lives pool, both with alice
    (creator) and bob as members.
    """
    s = db_session
    comp = Competition(external_id=39, name="PL", season=2025)
    s.add(comp)
    await s.flush()

    a, b, c, d = (Team(external_id=i, name=n, competition_id=comp.id)
                  for i, n in enumerate(["A", "B", "C", "D"], start=1))
    alice = User(userName="alice", email="alice@x.com", password=hash_password("pw"), firstName="A", lastName="A")
    bob = User(userName="bob", email="bob@x.com", password=hash_password("pw"), firstName="B", lastName="B")
    s.add_all([a, b, c, d, alice, bob])
    await s.flush()

    now = datetime.now(timezone.utc)

    def fx(ext, gw, home, away, kickoff, **kw):
        return Fixture(external_id=ext, competition_id=comp.id, home_team_id=home.id, away_team_id=away.id,
                       gameweek=gw, kickoff_time=kickoff, **kw)

    f1 = fx(101, 1, a, b, now - timedelta(days=8), status="FT", home_goals=2, away_goals=0)
    f2 = fx(102, 1, c, d, now - timedelta(days=7), status="FT", home_goals=1, away_goals=1)
    f3 = fx(103, 2, a, c, now + timedelta(days=1), status="NS")
    f4 = fx(104, 2, b, d, now + timedelta(days=2), status="NS")
    f5 = fx(105, 3, a, d, now + timedelta(days=8), status="NS")
    f6 = fx(106, 3, b, c, now + timedelta(days=9), status="NS")
    points_pool = Pool(session_code="PTS001", name="Points", competition_id=comp.id, start_gameweek=1,
                       total_lives=0, has_lives=False, double_weeks=2, created_by=alice.id)
    lives_pool = Pool(session_code="LIV001", name="Lives", competition_id=comp.id, start_gameweek=1,
                      total_lives=3, has_lives=True, created_by=alice.id)
    s.add_all([f1, f2, f3, f4, f5, f6, points_pool, lives_pool])
    await s.flush()

    for pool in (points_pool, lives_pool):
        for user in (alice, bob):
            s.add(PoolUserStats(pool_id=pool.id, user_id=user.id,
                                lives_left=pool.total_lives, total_points=0))
    await s.commit()
    return dict(comp=comp, a=a, b=b, c=c, d=d, alice=alice, bob=bob,
                f1=f1, f2=f2, f3=f3, f4=f4, f5=f5, f6=f6,
                pool=points_pool, lives_pool=lives_pool)


def _h(user):
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


async def _activate(client, setup, user, gameweek, pool=None):
    pool = pool or setup["pool"]
    return await client.post(f"/pools/{pool.id}/double-weeks", json={"gameweek": gameweek}, headers=_h(user))


async def _pick(client, setup, user, team, fixture, pool=None):
    pool = pool or setup["pool"]
    return await client.post("/picks/", headers=_h(user), json={
        "pool_id": pool.id, "user_id": user.id, "team_id": team.id, "fixture_id": fixture.id,
    })


async def _add_scored_double(db_session, setup, user):
    """bob played a double week in finished GW1: A (beat B 2-0) and C (drew D 1-1)."""
    pool = setup["pool"]
    db_session.add_all([
        DoubleWeek(pool_id=pool.id, user_id=user.id, gameweek=1),
        Pick(pool_id=pool.id, user_id=user.id, team_id=setup["a"].id, fixture_id=setup["f1"].id,
             competition_id=setup["comp"].id),
        Pick(pool_id=pool.id, user_id=user.id, team_id=setup["c"].id, fixture_id=setup["f2"].id,
             competition_id=setup["comp"].id),
    ])
    await db_session.commit()


# ==================== Suggested allowance ====================

class TestSuggestedDoubleWeeks:
    def test_premier_league_full_season(self):
        assert suggested_double_weeks(20, 2, 38, 38) == 2

    def test_eighteen_team_league(self):
        assert suggested_double_weeks(18, 2, 34, 34) == 2

    def test_mid_season_start_is_off(self):
        assert suggested_double_weeks(20, 2, 24, 38) == 0

    def test_no_teams_synced(self):
        assert suggested_double_weeks(0, 2, 38, 38) == 0


class TestPoolCreation:
    async def _create(self, client, setup, **overrides):
        body = {"name": "New", "competition_id": setup["comp"].id, "created_by": setup["alice"].id,
                "start_gameweek": 1, **overrides}
        return await client.post("/pools/create", json=body, headers=_h(setup["alice"]))

    @pytest.mark.asyncio
    async def test_points_pool_defaults_to_suggested(self, client, setup):
        # 4 teams, 3 gameweeks -> default max picks 1 -> 4*1 - 3 = 1
        res = await self._create(client, setup, has_lives=False, total_lives=0)
        assert res.status_code == 201
        assert res.json()["double_weeks"] == 1

    @pytest.mark.asyncio
    async def test_points_pool_custom_amount(self, client, setup):
        res = await self._create(client, setup, has_lives=False, total_lives=0, double_weeks=3)
        assert res.json()["double_weeks"] == 3

    @pytest.mark.asyncio
    async def test_lives_pool_always_zero(self, client, setup):
        res = await self._create(client, setup, has_lives=True, double_weeks=2)
        assert res.json()["double_weeks"] == 0

    @pytest.mark.asyncio
    async def test_too_many_rejected(self, client, setup):
        res = await self._create(client, setup, has_lives=False, total_lives=0, double_weeks=50)
        assert res.status_code == 400


# ==================== Toggle on / off ====================

class TestActivation:
    @pytest.mark.asyncio
    async def test_activate_and_status(self, client, setup):
        res = await _activate(client, setup, setup["bob"], 2)
        assert res.status_code == 200
        assert res.json() == {"allowance": 2, "used": 1, "remaining": 1, "active_gameweeks": [2]}

        status = await client.get(f"/pools/{setup['pool'].id}/double-weeks/me", headers=_h(setup["bob"]))
        assert status.json()["active_gameweeks"] == [2]

    @pytest.mark.asyncio
    async def test_lives_pool_rejected(self, client, setup):
        res = await _activate(client, setup, setup["bob"], 2, pool=setup["lives_pool"])
        assert res.status_code == 400
        status = await client.get(f"/pools/{setup['lives_pool'].id}/double-weeks/me", headers=_h(setup["bob"]))
        assert status.json()["allowance"] == 0

    @pytest.mark.asyncio
    async def test_cannot_exceed_allowance(self, client, db_session, setup):
        setup["pool"].double_weeks = 1
        db_session.add(setup["pool"])
        await db_session.commit()
        assert (await _activate(client, setup, setup["bob"], 2)).status_code == 200
        res = await _activate(client, setup, setup["bob"], 3)
        assert res.status_code == 400
        assert "no double weeks left" in res.json()["detail"]

    @pytest.mark.asyncio
    async def test_already_active_rejected(self, client, setup):
        await _activate(client, setup, setup["bob"], 2)
        assert (await _activate(client, setup, setup["bob"], 2)).status_code == 400

    @pytest.mark.asyncio
    async def test_finished_gameweek_rejected(self, client, setup):
        assert (await _activate(client, setup, setup["bob"], 1)).status_code == 400

    @pytest.mark.asyncio
    async def test_non_member_rejected(self, client, db_session, setup):
        eve = User(userName="eve", email="eve@x.com", password=hash_password("pw"), firstName="E", lastName="E")
        db_session.add(eve)
        await db_session.commit()
        assert (await _activate(client, setup, eve, 2)).status_code == 403

    @pytest.mark.asyncio
    async def test_deactivate_removes_second_pick(self, client, db_session, setup):
        bob = setup["bob"]
        await _activate(client, setup, bob, 2)
        assert (await _pick(client, setup, bob, setup["a"], setup["f3"])).status_code == 201
        assert (await _pick(client, setup, bob, setup["b"], setup["f4"])).status_code == 201

        res = await client.delete(f"/pools/{setup['pool'].id}/double-weeks/2", headers=_h(bob))
        assert res.status_code == 200
        assert res.json()["remaining"] == 2

        picks = (await db_session.execute(
            select(Pick).where(Pick.pool_id == setup["pool"].id, Pick.user_id == bob.id)
        )).scalars().all()
        assert [p.team_id for p in picks] == [setup["a"].id]  # first pick kept

    @pytest.mark.asyncio
    async def test_deactivate_after_both_kicked_off_rejected(self, client, db_session, setup):
        await _add_scored_double(db_session, setup, setup["bob"])
        res = await client.delete(f"/pools/{setup['pool'].id}/double-weeks/1", headers=_h(setup["bob"]))
        assert res.status_code == 400


# ==================== Picking ====================

class TestDoubleWeekPicks:
    @pytest.mark.asyncio
    async def test_second_pick_needs_double_week(self, client, setup):
        bob = setup["bob"]
        assert (await _pick(client, setup, bob, setup["a"], setup["f3"])).status_code == 201
        res = await _pick(client, setup, bob, setup["b"], setup["f4"])
        assert res.status_code == 400
        assert "already made a pick" in res.json()["detail"]

    @pytest.mark.asyncio
    async def test_second_pick_allowed_with_double_week(self, client, setup):
        bob = setup["bob"]
        await _activate(client, setup, bob, 2)
        assert (await _pick(client, setup, bob, setup["a"], setup["f3"])).status_code == 201
        assert (await _pick(client, setup, bob, setup["b"], setup["f4"])).status_code == 201

    @pytest.mark.asyncio
    async def test_same_match_rejected(self, client, setup):
        bob = setup["bob"]
        await _activate(client, setup, bob, 2)
        await _pick(client, setup, bob, setup["a"], setup["f3"])
        res = await _pick(client, setup, bob, setup["c"], setup["f3"])
        assert res.status_code == 400
        assert "different matches" in res.json()["detail"]

    @pytest.mark.asyncio
    async def test_third_pick_rejected(self, client, db_session, setup):
        bob = setup["bob"]
        # A third fixture in GW2 so a third pick is otherwise possible.
        extra = Fixture(external_id=107, competition_id=setup["comp"].id, home_team_id=setup["d"].id,
                        away_team_id=setup["a"].id, gameweek=2, status="NS",
                        kickoff_time=datetime.now(timezone.utc) + timedelta(days=3))
        db_session.add(extra)
        await db_session.commit()

        await _activate(client, setup, bob, 2)
        await _pick(client, setup, bob, setup["a"], setup["f3"])
        await _pick(client, setup, bob, setup["b"], setup["f4"])
        assert (await _pick(client, setup, bob, setup["d"], extra)).status_code == 400


# ==================== Scoring ====================

class TestDoubleWeekScoring:
    @pytest.mark.asyncio
    async def test_both_results_count(self, db_session, setup):
        await _add_scored_double(db_session, setup, setup["bob"])
        await process_gameweek_results(db_session, setup["comp"].id, 1)

        board = {r["username"]: r for r in await get_leaderboard(db_session, setup["pool"].id)}
        assert board["bob"]["total_points"] == 4  # win 3 + draw 1
        assert board["bob"]["goal_difference"] == 2

    @pytest.mark.asyncio
    async def test_unused_double_week_is_released(self, client, db_session, setup):
        pool, bob = setup["pool"], setup["bob"]
        db_session.add_all([
            DoubleWeek(pool_id=pool.id, user_id=bob.id, gameweek=1),
            Pick(pool_id=pool.id, user_id=bob.id, team_id=setup["a"].id, fixture_id=setup["f1"].id,
                 competition_id=setup["comp"].id),
        ])
        await db_session.commit()

        await process_gameweek_results(db_session, setup["comp"].id, 1)

        status = await client.get(f"/pools/{pool.id}/double-weeks/me", headers=_h(bob))
        assert status.json()["used"] == 0
        assert status.json()["remaining"] == 2

    @pytest.mark.asyncio
    async def test_team_picks_flag_double(self, client, db_session, setup):
        await _add_scored_double(db_session, setup, setup["bob"])
        res = await client.get(
            f"/pools/{setup['pool'].id}/team-leaderboard/{setup['a'].id}", headers=_h(setup["alice"])
        )
        assert res.json()["picks"][0]["is_double"] is True


# ==================== Admin ====================

class TestAdminAllowance:
    async def _set(self, client, setup, n, user=None, pool=None):
        pool = pool or setup["pool"]
        return await client.put(f"/pools/{pool.id}/double-weeks/allowance",
                                json={"double_weeks": n}, headers=_h(user or setup["alice"]))

    @pytest.mark.asyncio
    async def test_admin_can_change(self, client, setup):
        res = await self._set(client, setup, 3)
        assert res.status_code == 200
        assert res.json()["double_weeks"] == 3

    @pytest.mark.asyncio
    async def test_non_admin_forbidden(self, client, setup):
        assert (await self._set(client, setup, 3, user=setup["bob"])).status_code == 403

    @pytest.mark.asyncio
    async def test_lives_pool_rejected(self, client, setup):
        assert (await self._set(client, setup, 2, pool=setup["lives_pool"])).status_code == 400

    @pytest.mark.asyncio
    async def test_cannot_go_below_used_but_can_switch_off(self, client, setup):
        bob = setup["bob"]
        await _activate(client, setup, bob, 2)
        await _activate(client, setup, bob, 3)
        assert (await self._set(client, setup, 1)).status_code == 400
        assert (await self._set(client, setup, 0)).status_code == 200


class TestAdminEditPicks:
    @pytest.mark.asyncio
    async def test_admin_can_enter_double_week(self, client, db_session, setup):
        pool, bob = setup["pool"], setup["bob"]
        res = await client.put(f"/admin/pools/{pool.id}/users/{bob.id}/picks", headers=_h(setup["alice"]), json={
            "picks": [
                {"fixture_id": setup["f1"].id, "team_id": setup["a"].id},
                {"fixture_id": setup["f2"].id, "team_id": setup["c"].id},
            ],
        })
        assert res.status_code == 200
        assert res.json()["total_points"] == 4

        rows = (await db_session.execute(select(DoubleWeek).where(DoubleWeek.user_id == bob.id))).scalars().all()
        assert [r.gameweek for r in rows] == [1]

    @pytest.mark.asyncio
    async def test_editing_another_week_keeps_double_week_points(self, client, db_session, setup):
        """Regression: the reset+replay must reset *both* picks of a double week."""
        pool, bob = setup["pool"], setup["bob"]
        await _add_scored_double(db_session, setup, bob)
        await process_gameweek_results(db_session, setup["comp"].id, 1)

        res = await client.put(f"/admin/pools/{pool.id}/users/{bob.id}/picks", headers=_h(setup["alice"]), json={
            "picks": [{"fixture_id": setup["f3"].id, "team_id": setup["a"].id}],
        })
        assert res.status_code == 200
        assert res.json()["total_points"] == 4

    @pytest.mark.asyncio
    async def test_admin_double_in_lives_pool_rejected(self, client, setup):
        pool, bob = setup["lives_pool"], setup["bob"]
        res = await client.put(f"/admin/pools/{pool.id}/users/{bob.id}/picks", headers=_h(setup["alice"]), json={
            "picks": [
                {"fixture_id": setup["f1"].id, "team_id": setup["a"].id},
                {"fixture_id": setup["f2"].id, "team_id": setup["c"].id},
            ],
        })
        assert res.status_code == 400


# ==================== Notifications ====================

class TestDoubleWeekNotifications:
    @pytest.fixture
    def pushes(self, monkeypatch):
        calls = []

        async def fake_send(token, title, body, data=None):
            calls.append(body)
            return True

        monkeypatch.setattr(notifications_module, "send_push_notification", fake_send)
        return calls

    async def _scored_double(self, db_session, setup):
        await _add_scored_double(db_session, setup, setup["bob"])
        db_session.add(PushToken(user_id=setup["bob"].id, token="ExponentPushToken[bob]", platform="ios"))
        await db_session.commit()
        picks = (await db_session.execute(
            select(Pick).where(Pick.user_id == setup["bob"].id).order_by(Pick.id)
        )).scalars().all()
        for pick, (result, points) in zip(picks, [("WIN", 3), ("DRAW", 1)]):
            pick.result, pick.points = result, points
        await db_session.commit()
        return picks

    @pytest.mark.asyncio
    async def test_both_picks_combined_into_one(self, db_session, setup, pushes):
        picks = await self._scored_double(db_session, setup)
        sent = await notifications_module.notify_pick_results(db_session, picks)
        assert sent == 1
        assert "Double week" in pushes[0]
        assert "A W" in pushes[0] and "C D" in pushes[0] and "+4 pts" in pushes[0]

    @pytest.mark.asyncio
    async def test_picks_scored_separately_each_notify(self, db_session, setup, pushes):
        picks = await self._scored_double(db_session, setup)
        assert await notifications_module.notify_pick_results(db_session, [picks[0]]) == 1
        assert await notifications_module.notify_pick_results(db_session, [picks[1]]) == 1
        # ...but never the same pick twice
        assert await notifications_module.notify_pick_results(db_session, [picks[1]]) == 0


# ==================== Clean-up ====================

class TestCleanup:
    @pytest.mark.asyncio
    async def test_leave_pool_removes_double_weeks(self, client, db_session, setup):
        await _activate(client, setup, setup["bob"], 2)
        res = await client.delete(f"/pools/{setup['pool'].id}/leave", headers=_h(setup["bob"]))
        assert res.status_code == 200
        rows = (await db_session.execute(select(DoubleWeek))).scalars().all()
        assert rows == []

    @pytest.mark.asyncio
    async def test_delete_pool_with_double_weeks(self, client, db_session, setup):
        await _activate(client, setup, setup["bob"], 2)
        res = await client.delete(f"/pools/{setup['pool'].id}", headers=_h(setup["alice"]))
        assert res.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_account_with_double_weeks(self, client, setup):
        await _activate(client, setup, setup["bob"], 2)
        res = await client.delete("/users/me", headers=_h(setup["bob"]))
        assert res.status_code == 200
