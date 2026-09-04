"""
Tests for push-deadline reminders and pick-result notifications.

send_push_notification is monkeypatched everywhere here - these tests
never make a real network call to Expo's push API. They verify the
*decision* logic (who gets notified, when, and exactly once) rather than
delivery itself.
"""
import os
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ["CRON_SECRET"] = "test-cron-secret"

import uuid
import pytest
from datetime import datetime, timedelta, timezone
from app.models.user import User
from app.models.pool import Pool, PoolUserStats
from app.models.pick import Pick
from app.models.competiton_data import Fixture
from app.models.notification import PushToken, NotificationLog
from app.utils.auth import hash_password, create_access_token
import app.services.notifications as notifications_module


@pytest.fixture
def sent_pushes(monkeypatch):
    """Replace the real Expo call with an in-memory recorder."""
    calls = []

    async def fake_send(token, title, body, data=None):
        calls.append({"token": token, "title": title, "body": body, "data": data})
        return True

    monkeypatch.setattr(notifications_module, "send_push_notification", fake_send)
    return calls


async def _make_user(db_session, name, **prefs):
    user = User(
        userName=name, email=f"{name}@test.com",
        password=hash_password("pass"), firstName="Test", lastName=name,
        **prefs,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def _auth_headers(user):
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


async def _register_token(db_session, user_id, token="ExponentPushToken[test]"):
    db_session.add(PushToken(user_id=user_id, token=token, platform="ios"))
    await db_session.commit()


async def _seed_pool(db_session, competition_id, *, created_by, has_lives=True, total_lives=3, start_gameweek=1):
    pool = Pool(
        session_code=uuid.uuid4().hex[:10].upper(), name="Notif Test Pool",
        competition_id=competition_id, start_gameweek=start_gameweek,
        max_picks_per_team=5, total_lives=total_lives, has_lives=has_lives,
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
    return stats


_fixture_counter = 0


async def _fixture_at(db_session, competition_id, home_id, away_id, *, gameweek, kickoff, status="NS", home_goals=None, away_goals=None):
    global _fixture_counter
    _fixture_counter += 1
    fixture = Fixture(
        external_id=200000 + _fixture_counter, competition_id=competition_id,
        home_team_id=home_id, away_team_id=away_id, gameweek=gameweek,
        kickoff_time=kickoff, status=status, home_goals=home_goals, away_goals=away_goals,
    )
    db_session.add(fixture)
    await db_session.commit()
    await db_session.refresh(fixture)
    return fixture


class TestPushTokenAndPreferencesEndpoints:
    @pytest.mark.asyncio
    async def test_register_and_reregister_token_stays_single_row(self, client, db_session, test_user):
        from sqlalchemy import select
        resp1 = await client.post("/users/me/push-token", headers=_auth_headers(test_user), json={"token": "tok-1", "platform": "ios"})
        assert resp1.status_code == 200

        resp2 = await client.post("/users/me/push-token", headers=_auth_headers(test_user), json={"token": "tok-2", "platform": "android"})
        assert resp2.status_code == 200

        rows = (await db_session.execute(select(PushToken).where(PushToken.user_id == test_user.id))).scalars().all()
        assert len(rows) == 1
        assert rows[0].token == "tok-2"

    @pytest.mark.asyncio
    async def test_requires_auth(self, client):
        resp = await client.post("/users/me/push-token", json={"token": "tok"})
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_update_and_get_preferences(self, client, test_user):
        resp = await client.put(
            "/users/me/notification-preferences",
            headers=_auth_headers(test_user),
            json={"deadline_reminders_enabled": False},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["deadline_reminders_enabled"] is False
        assert body["notifications_enabled"] is True  # untouched fields keep their default

        get_resp = await client.get("/users/me/notification-preferences", headers=_auth_headers(test_user))
        assert get_resp.json()["deadline_reminders_enabled"] is False


class TestDeadlineReminders:
    @pytest.mark.asyncio
    async def test_day_before_reminder_sent_for_unpicked_member(
        self, db_session, test_competition, test_teams, test_user, sent_pushes
    ):
        home, away = test_teams
        creator = await _make_user(db_session, "creator1")
        pool = await _seed_pool(db_session, test_competition.id, created_by=creator.id)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=3)
        await _register_token(db_session, test_user.id)

        kickoff = datetime.now(timezone.utc) + timedelta(hours=24)
        await _fixture_at(db_session, test_competition.id, home.id, away.id, gameweek=1, kickoff=kickoff)

        await notifications_module.check_and_send_deadline_reminders(db_session)

        assert len(sent_pushes) == 1
        assert sent_pushes[0]["data"]["type"] == "day_before"

    @pytest.mark.asyncio
    async def test_four_hour_reminder_sent(
        self, db_session, test_competition, test_teams, test_user, sent_pushes
    ):
        home, away = test_teams
        creator = await _make_user(db_session, "creator2")
        pool = await _seed_pool(db_session, test_competition.id, created_by=creator.id)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=3)
        await _register_token(db_session, test_user.id)

        kickoff = datetime.now(timezone.utc) + timedelta(hours=4)
        await _fixture_at(db_session, test_competition.id, home.id, away.id, gameweek=1, kickoff=kickoff)

        await notifications_module.check_and_send_deadline_reminders(db_session)

        assert len(sent_pushes) == 1
        assert sent_pushes[0]["data"]["type"] == "four_hour"

    @pytest.mark.asyncio
    async def test_no_duplicate_on_second_tick_in_same_window(
        self, db_session, test_competition, test_teams, test_user, sent_pushes
    ):
        home, away = test_teams
        creator = await _make_user(db_session, "creator3")
        pool = await _seed_pool(db_session, test_competition.id, created_by=creator.id)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=3)
        await _register_token(db_session, test_user.id)

        kickoff = datetime.now(timezone.utc) + timedelta(hours=24)
        await _fixture_at(db_session, test_competition.id, home.id, away.id, gameweek=1, kickoff=kickoff)

        await notifications_module.check_and_send_deadline_reminders(db_session)
        await notifications_module.check_and_send_deadline_reminders(db_session)  # simulates next 30-min tick

        assert len(sent_pushes) == 1

    @pytest.mark.asyncio
    async def test_no_reminder_once_user_has_picked(
        self, db_session, test_competition, test_teams, test_user, sent_pushes
    ):
        home, away = test_teams
        creator = await _make_user(db_session, "creator4")
        pool = await _seed_pool(db_session, test_competition.id, created_by=creator.id)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=3)
        await _register_token(db_session, test_user.id)

        kickoff = datetime.now(timezone.utc) + timedelta(hours=24)
        fixture = await _fixture_at(db_session, test_competition.id, home.id, away.id, gameweek=1, kickoff=kickoff)

        db_session.add(Pick(pool_id=pool.id, user_id=test_user.id, team_id=home.id, fixture_id=fixture.id, competition_id=test_competition.id))
        await db_session.commit()

        await notifications_module.check_and_send_deadline_reminders(db_session)

        assert len(sent_pushes) == 0

    @pytest.mark.asyncio
    async def test_no_reminder_for_eliminated_survivor_user(
        self, db_session, test_competition, test_teams, test_user, sent_pushes
    ):
        home, away = test_teams
        creator = await _make_user(db_session, "creator5")
        pool = await _seed_pool(db_session, test_competition.id, created_by=creator.id, has_lives=True)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=0)  # eliminated
        await _register_token(db_session, test_user.id)

        kickoff = datetime.now(timezone.utc) + timedelta(hours=24)
        await _fixture_at(db_session, test_competition.id, home.id, away.id, gameweek=1, kickoff=kickoff)

        await notifications_module.check_and_send_deadline_reminders(db_session)

        assert len(sent_pushes) == 0

    @pytest.mark.asyncio
    async def test_no_reminder_without_registered_push_token(
        self, db_session, test_competition, test_teams, test_user, sent_pushes
    ):
        home, away = test_teams
        creator = await _make_user(db_session, "creator6")
        pool = await _seed_pool(db_session, test_competition.id, created_by=creator.id)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=3)
        # no push token registered

        kickoff = datetime.now(timezone.utc) + timedelta(hours=24)
        await _fixture_at(db_session, test_competition.id, home.id, away.id, gameweek=1, kickoff=kickoff)

        await notifications_module.check_and_send_deadline_reminders(db_session)

        assert len(sent_pushes) == 0

    @pytest.mark.asyncio
    async def test_no_reminder_when_deadline_reminders_disabled(
        self, db_session, test_competition, test_teams, sent_pushes
    ):
        home, away = test_teams
        creator = await _make_user(db_session, "creator7")
        user = await _make_user(db_session, "optedout", deadline_reminders_enabled=False)
        pool = await _seed_pool(db_session, test_competition.id, created_by=creator.id)
        await _join_pool(db_session, pool.id, user.id, lives_left=3)
        await _register_token(db_session, user.id)

        kickoff = datetime.now(timezone.utc) + timedelta(hours=24)
        await _fixture_at(db_session, test_competition.id, home.id, away.id, gameweek=1, kickoff=kickoff)

        await notifications_module.check_and_send_deadline_reminders(db_session)

        assert len(sent_pushes) == 0

    @pytest.mark.asyncio
    async def test_no_reminder_after_deadline_has_passed(
        self, db_session, test_competition, test_teams, test_user, sent_pushes
    ):
        home, away = test_teams
        creator = await _make_user(db_session, "creator8")
        pool = await _seed_pool(db_session, test_competition.id, created_by=creator.id)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=3)
        await _register_token(db_session, test_user.id)

        # Last (only) fixture already kicked off - deadline passed
        kickoff = datetime.now(timezone.utc) - timedelta(hours=1)
        await _fixture_at(db_session, test_competition.id, home.id, away.id, gameweek=1, kickoff=kickoff, status="FT", home_goals=1, away_goals=0)

        await notifications_module.check_and_send_deadline_reminders(db_session)

        assert len(sent_pushes) == 0

    @pytest.mark.asyncio
    async def test_daily_reminder_skipped_same_day_as_day_before(
        self, db_session, test_competition, test_teams, test_user, sent_pushes
    ):
        """day_before and daily_unpicked windows can overlap on the same
        calendar day for a gameweek starting soon - only one should fire."""
        home, away = test_teams
        creator = await _make_user(db_session, "creator9")
        pool = await _seed_pool(db_session, test_competition.id, created_by=creator.id)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=3)
        await _register_token(db_session, test_user.id)

        kickoff = datetime.now(timezone.utc) + timedelta(hours=24)
        await _fixture_at(db_session, test_competition.id, home.id, away.id, gameweek=1, kickoff=kickoff)

        await notifications_module.check_and_send_deadline_reminders(db_session)

        day_before_sends = [c for c in sent_pushes if c["data"]["type"] == "day_before"]
        daily_sends = [c for c in sent_pushes if c["data"]["type"] == "daily_unpicked"]
        assert len(day_before_sends) == 1
        assert len(daily_sends) == 0


class TestPickResultNotifications:
    @pytest.mark.asyncio
    async def test_win_notification_sent(self, db_session, test_competition, test_teams, test_user, sent_pushes):
        home, away = test_teams
        creator = await _make_user(db_session, "creator10")
        pool = await _seed_pool(db_session, test_competition.id, created_by=creator.id)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=3)
        await _register_token(db_session, test_user.id)

        fixture = await _fixture_at(db_session, test_competition.id, home.id, away.id, gameweek=1, kickoff=datetime.now(timezone.utc) - timedelta(hours=2), status="FT", home_goals=2, away_goals=0)
        pick = Pick(
            pool_id=pool.id, user_id=test_user.id, team_id=home.id, fixture_id=fixture.id,
            competition_id=test_competition.id, result="WIN", points=3,
        )
        db_session.add(pick)
        await db_session.commit()
        await db_session.refresh(pick)

        sent = await notifications_module.notify_pick_results(db_session, [pick])

        assert sent == 1
        assert "won" in sent_pushes[0]["body"].lower()
        assert home.name in sent_pushes[0]["body"]

    @pytest.mark.asyncio
    async def test_missed_pick_notification_mentions_life_lost_in_survivor_mode(
        self, db_session, test_competition, test_teams, test_user, sent_pushes
    ):
        home, away = test_teams
        creator = await _make_user(db_session, "creator11")
        pool = await _seed_pool(db_session, test_competition.id, created_by=creator.id, has_lives=True)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=2)
        await _register_token(db_session, test_user.id)

        fixture = await _fixture_at(db_session, test_competition.id, home.id, away.id, gameweek=1, kickoff=datetime.now(timezone.utc) - timedelta(hours=2), status="FT", home_goals=2, away_goals=0)
        np_pick = Pick(
            pool_id=pool.id, user_id=test_user.id, team_id=None, fixture_id=fixture.id,
            competition_id=test_competition.id, result="NP", points=0,
        )
        db_session.add(np_pick)
        await db_session.commit()
        await db_session.refresh(np_pick)

        sent = await notifications_module.notify_pick_results(db_session, [np_pick])

        assert sent == 1
        assert "lost a life" in sent_pushes[0]["body"].lower()

    @pytest.mark.asyncio
    async def test_missed_pick_notification_no_life_mention_in_league_mode(
        self, db_session, test_competition, test_teams, test_user, sent_pushes
    ):
        home, away = test_teams
        creator = await _make_user(db_session, "creator12")
        pool = await _seed_pool(db_session, test_competition.id, created_by=creator.id, has_lives=False, total_lives=0)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=0)
        await _register_token(db_session, test_user.id)

        fixture = await _fixture_at(db_session, test_competition.id, home.id, away.id, gameweek=1, kickoff=datetime.now(timezone.utc) - timedelta(hours=2), status="FT", home_goals=2, away_goals=0)
        np_pick = Pick(
            pool_id=pool.id, user_id=test_user.id, team_id=None, fixture_id=fixture.id,
            competition_id=test_competition.id, result="NP", points=0,
        )
        db_session.add(np_pick)
        await db_session.commit()
        await db_session.refresh(np_pick)

        sent = await notifications_module.notify_pick_results(db_session, [np_pick])

        assert sent == 1
        assert "life" not in sent_pushes[0]["body"].lower()

    @pytest.mark.asyncio
    async def test_no_notification_when_result_notifications_disabled(
        self, db_session, test_competition, test_teams, sent_pushes
    ):
        home, away = test_teams
        creator = await _make_user(db_session, "creator13")
        user = await _make_user(db_session, "resultsoptout", result_notifications_enabled=False)
        pool = await _seed_pool(db_session, test_competition.id, created_by=creator.id)
        await _join_pool(db_session, pool.id, user.id, lives_left=3)
        await _register_token(db_session, user.id)

        fixture = await _fixture_at(db_session, test_competition.id, home.id, away.id, gameweek=1, kickoff=datetime.now(timezone.utc) - timedelta(hours=2), status="FT", home_goals=2, away_goals=0)
        pick = Pick(pool_id=pool.id, user_id=user.id, team_id=home.id, fixture_id=fixture.id, competition_id=test_competition.id, result="WIN", points=3)
        db_session.add(pick)
        await db_session.commit()
        await db_session.refresh(pick)

        sent = await notifications_module.notify_pick_results(db_session, [pick])

        assert sent == 0
        assert len(sent_pushes) == 0

    @pytest.mark.asyncio
    async def test_pick_result_notification_via_full_results_pipeline(
        self, db_session, test_competition, test_teams, test_user, sent_pushes
    ):
        """End-to-end: process_gameweek_results should trigger the
        notification automatically, not just the direct helper call."""
        from app.services.results import process_gameweek_results

        home, away = test_teams
        creator = await _make_user(db_session, "creator14")
        pool = await _seed_pool(db_session, test_competition.id, created_by=creator.id)
        await _join_pool(db_session, pool.id, test_user.id, lives_left=3)
        await _register_token(db_session, test_user.id)

        fixture = await _fixture_at(db_session, test_competition.id, home.id, away.id, gameweek=1, kickoff=datetime.now(timezone.utc) - timedelta(hours=2), status="FT", home_goals=1, away_goals=1)
        pick = Pick(pool_id=pool.id, user_id=test_user.id, team_id=home.id, fixture_id=fixture.id, competition_id=test_competition.id)
        db_session.add(pick)
        await db_session.commit()

        await process_gameweek_results(db_session, test_competition.id, 1)

        assert len(sent_pushes) == 1
        assert "drew" in sent_pushes[0]["body"].lower()
