"""
Tests for max_picks_per_team being league-format-aware.

A pool can't set max_picks_per_team so low that players run out of
distinct teams before the season ends - e.g. a 20-team league starting
from gameweek 1 has 38 gameweeks to fill, so a cap of 1 (20 picks total)
leaves 18 gameweeks with no valid team left to pick. The minimum viable
value - and the suggested default - is ceil(remaining_gameweeks / team_count).
"""
import os
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ["CRON_SECRET"] = "test-cron-secret"

import pytest
from datetime import datetime, timedelta, timezone
from app.models.competiton_data import Competition, Team, Fixture
from app.crud.competition_crud import get_pick_limits


async def _seed_league(db_session, *, team_count, total_gameweeks, current_gameweek, external_id=39):
    comp = Competition(
        external_id=external_id, name="Test League", season=2026,
        country="Testland", type="League", logo="https://example.com/l.png",
    )
    db_session.add(comp)
    await db_session.flush()

    teams = []
    for i in range(team_count):
        team = Team(
            external_id=1000 + i, name=f"Team {i}", short_name=f"T{i}",
            competition_id=comp.id, venue_name=f"Ground {i}", logo="https://example.com/t.png",
        )
        db_session.add(team)
        teams.append(team)
    await db_session.flush()

    # current_gameweek's kickoff needs a comfortable buffer into the future:
    # get_current_gameweek() re-captures "now" itself a moment after this
    # seeding runs, so a kickoff of exactly "now" can already read as past
    # by the time it queries, nondeterministically shifting the result.
    now = datetime.now(timezone.utc)
    for gw in range(1, total_gameweeks + 1):
        kickoff = now + timedelta(hours=1) + timedelta(days=7 * (gw - current_gameweek))
        fixture = Fixture(
            external_id=external_id * 10000 + gw,
            competition_id=comp.id,
            home_team_id=teams[gw % team_count].id,
            away_team_id=teams[(gw + 1) % team_count].id,
            gameweek=gw,
            kickoff_time=kickoff,
            status="NS" if kickoff >= now else "FT",
        )
        db_session.add(fixture)
    await db_session.commit()
    await db_session.refresh(comp)
    return comp


class TestGetPickLimits:
    @pytest.mark.asyncio
    async def test_full_season_from_gameweek_1_requires_2(self, db_session):
        """20 teams, 38-gameweek season, starting from GW1: 38 gameweeks to
        fill but only 20 teams (20 picks available at cap 1) - cap 1 is not
        viable, minimum/default must be 2."""
        comp = await _seed_league(db_session, team_count=20, total_gameweeks=38, current_gameweek=1)

        limits = await get_pick_limits(db_session, comp.id, start_gameweek=1)

        assert limits["team_count"] == 20
        assert limits["remaining_gameweeks"] == 38
        assert limits["min_max_picks_per_team"] == 2
        assert limits["default_max_picks_per_team"] == 2

    @pytest.mark.asyncio
    async def test_mid_season_start_allows_1(self, db_session):
        """Same 20-team/38-gameweek league, but starting from GW20: only 19
        gameweeks remain, which 20 teams comfortably cover at cap 1."""
        comp = await _seed_league(db_session, team_count=20, total_gameweeks=38, current_gameweek=20)

        limits = await get_pick_limits(db_session, comp.id, start_gameweek=20)

        assert limits["remaining_gameweeks"] == 19
        assert limits["min_max_picks_per_team"] == 1
        assert limits["default_max_picks_per_team"] == 1

    @pytest.mark.asyncio
    async def test_defaults_to_current_gameweek_when_not_specified(self, db_session):
        comp = await _seed_league(db_session, team_count=20, total_gameweeks=38, current_gameweek=20)

        limits = await get_pick_limits(db_session, comp.id)

        assert limits["start_gameweek"] == 20
        assert limits["min_max_picks_per_team"] == 1

    @pytest.mark.asyncio
    async def test_no_teams_synced_yet_falls_back_to_flat_default(self, db_session):
        """A brand-new league has no teams/fixtures until the first pool's
        background sync runs - there's nothing to compute a real minimum
        from yet, so this must not force an artificial cap of 1."""
        comp = Competition(
            external_id=999, name="Unsynced League", season=2026,
            country="Nowhere", type="League", logo="https://example.com/l.png",
        )
        db_session.add(comp)
        await db_session.commit()
        await db_session.refresh(comp)

        limits = await get_pick_limits(db_session, comp.id, start_gameweek=1)

        assert limits["team_count"] == 0
        assert limits["min_max_picks_per_team"] == 1
        assert limits["default_max_picks_per_team"] == 2

    @pytest.mark.asyncio
    async def test_no_fixtures_at_all_does_not_crash(self, db_session, test_competition):
        """A competition with zero synced fixtures has no derivable current
        gameweek at all (get_current_gameweek returns None) - this must
        fall back to a nominal start rather than raising a TypeError on
        None arithmetic."""
        limits = await get_pick_limits(db_session, test_competition.id)

        assert limits["start_gameweek"] == 1


class TestPickLimitsEndpoint:
    @pytest.mark.asyncio
    async def test_returns_expected_shape(self, client, db_session, auth_headers):
        comp = await _seed_league(db_session, team_count=20, total_gameweeks=38, current_gameweek=1)

        resp = await client.get(f"/competitions/leagues/{comp.id}/pick-limits", headers=auth_headers)

        assert resp.status_code == 200
        body = resp.json()
        assert body["min_max_picks_per_team"] == 2
        assert body["default_max_picks_per_team"] == 2
        assert body["team_count"] == 20

    @pytest.mark.asyncio
    async def test_respects_start_gameweek_query_param(self, client, db_session, auth_headers):
        comp = await _seed_league(db_session, team_count=20, total_gameweeks=38, current_gameweek=1)

        resp = await client.get(f"/competitions/leagues/{comp.id}/pick-limits?start_gameweek=20", headers=auth_headers)

        assert resp.status_code == 200
        assert resp.json()["min_max_picks_per_team"] == 1

    @pytest.mark.asyncio
    async def test_404_for_unknown_league(self, client, auth_headers):
        resp = await client.get("/competitions/leagues/999999/pick-limits", headers=auth_headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_401_without_token(self, client, db_session):
        comp = await _seed_league(db_session, team_count=20, total_gameweeks=38, current_gameweek=1)
        resp = await client.get(f"/competitions/leagues/{comp.id}/pick-limits")
        assert resp.status_code == 403


class TestPoolCreationUsesFormatAwareLimits:
    @pytest.mark.asyncio
    async def test_rejects_max_picks_per_team_below_minimum(self, client, db_session, test_user, auth_headers):
        comp = await _seed_league(db_session, team_count=20, total_gameweeks=38, current_gameweek=1)

        resp = await client.post("/pools/create", headers=auth_headers, json={
            "name": "Too Low",
            "competition_id": comp.id,
            "start_gameweek": 1,
            "max_picks_per_team": 1,
            "has_lives": False,
            "created_by": test_user.id,
        })

        assert resp.status_code == 400
        assert "max_picks_per_team must be at least 2" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_accepts_max_picks_per_team_at_minimum(self, client, db_session, test_user, auth_headers):
        comp = await _seed_league(db_session, team_count=20, total_gameweeks=38, current_gameweek=20)

        resp = await client.post("/pools/create", headers=auth_headers, json={
            "name": "At Minimum",
            "competition_id": comp.id,
            "start_gameweek": 20,
            "max_picks_per_team": 1,
            "has_lives": False,
            "created_by": test_user.id,
        })

        assert resp.status_code == 201, resp.text
        assert resp.json()["max_picks_per_team"] == 1

    @pytest.mark.asyncio
    async def test_omitted_max_picks_per_team_uses_dynamic_default(self, client, db_session, test_user, auth_headers):
        comp = await _seed_league(db_session, team_count=20, total_gameweeks=38, current_gameweek=20)

        resp = await client.post("/pools/create", headers=auth_headers, json={
            "name": "Dynamic Default",
            "competition_id": comp.id,
            "start_gameweek": 20,
            "has_lives": False,
            "created_by": test_user.id,
        })

        assert resp.status_code == 201, resp.text
        assert resp.json()["max_picks_per_team"] == 1
