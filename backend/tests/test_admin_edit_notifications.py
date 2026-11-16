"""Admin pick edits must not re-announce a member's old results, and a
phone's push token belongs only to the account last signed in on it."""

import pytest
from sqlalchemy import select
from app.models.notification import PushToken
import app.services.notifications as notifications_module
from app.services.results import process_gameweek_results
from tests.test_double_weeks import setup, _h  # noqa: F401 - reuse the double-weeks pool fixture


@pytest.fixture
def pushes(monkeypatch):
    calls = []

    async def fake_send(token, title, body, data=None):
        calls.append((token, body))
        return True

    monkeypatch.setattr(notifications_module, "send_push_notification", fake_send)
    return calls


class TestAdminEditIsSilent:
    @pytest.mark.asyncio
    async def test_editing_picks_sends_no_result_notifications(self, client, db_session, setup, pushes):
        pool, bob, alice = setup["pool"], setup["bob"], setup["alice"]
        db_session.add_all([
            PushToken(user_id=bob.id, token="ExponentPushToken[bob]", platform="ios"),
            PushToken(user_id=alice.id, token="ExponentPushToken[alice]", platform="ios"),
        ])
        await db_session.commit()
        # The scheduler has already scored finished GW1 (bob missed it) and
        # told everyone - that's the notification he's already had.
        await process_gameweek_results(db_session, setup["comp"].id, 1)
        assert any(token == "ExponentPushToken[bob]" for token, _ in pushes)
        pushes.clear()

        # Setting bob's GW1 pick afterwards replays GW1 for him.
        res = await client.put(f"/admin/pools/{pool.id}/users/{bob.id}/picks", headers=_h(alice), json={
            "picks": [{"fixture_id": setup["f1"].id, "team_id": setup["a"].id}],
        })
        assert res.status_code == 200
        assert res.json()["total_points"] == 3
        assert [p for p in pushes if p[0] == "ExponentPushToken[bob]"] == []


class TestPushTokenOwnership:
    @pytest.mark.asyncio
    async def test_token_moves_to_account_that_registers_it(self, client, db_session, setup):
        alice, bob = setup["alice"], setup["bob"]
        phone = {"token": "ExponentPushToken[phone]", "platform": "ios"}
        assert (await client.post("/users/me/push-token", headers=_h(bob), json=phone)).status_code == 200
        assert (await client.post("/users/me/push-token", headers=_h(alice), json=phone)).status_code == 200

        rows = (await db_session.execute(
            select(PushToken).where(PushToken.token == phone["token"])
        )).scalars().all()
        assert [r.user_id for r in rows] == [alice.id]

    @pytest.mark.asyncio
    async def test_other_devices_untouched(self, client, db_session, setup):
        alice, bob = setup["alice"], setup["bob"]
        await client.post("/users/me/push-token", headers=_h(bob), json={"token": "tok-bob"})
        await client.post("/users/me/push-token", headers=_h(alice), json={"token": "tok-alice"})

        rows = (await db_session.execute(select(PushToken).order_by(PushToken.user_id))).scalars().all()
        assert {r.user_id: r.token for r in rows} == {alice.id: "tok-alice", bob.id: "tok-bob"}
