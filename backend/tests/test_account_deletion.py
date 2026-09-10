"""
Tests for DELETE /users/me - permanent account deletion, required by App
Store review (Guideline 5.1.1(v): apps that support account creation must
also support real deletion, not just deactivation).

Covers:
- The account and its own data are actually gone, not just deactivated.
- Pools the user created are deleted entirely, including other members'
  picks/stats/notification logs in that pool (no ownership-transfer
  mechanism, so a pool can't outlive its creator).
- Pools the user merely joined are left intact for the other members -
  only the deleted user's own membership disappears.
- Requires auth.
"""
import os
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ["CRON_SECRET"] = "test-cron-secret"

import uuid
import pytest
from datetime import date
from sqlalchemy import select
from app.models.user import User
from app.models.pool import Pool, PoolUserStats
from app.models.pick import Pick
from app.models.notification import PushToken, NotificationLog
from app.utils.auth import create_access_token, hash_password


def _auth_headers(user):
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


async def _make_user(db_session, name):
    user = User(
        userName=name, email=f"{name}@test.com",
        password=hash_password("pass12345"), firstName=name, lastName="Test",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _make_pool(db_session, competition_id, created_by):
    pool = Pool(
        session_code=uuid.uuid4().hex[:10].upper(),
        name="Test Pool", competition_id=competition_id,
        start_gameweek=1, max_picks_per_team=2, total_lives=3,
        created_by=created_by,
    )
    db_session.add(pool)
    await db_session.commit()
    await db_session.refresh(pool)
    return pool


async def _join(db_session, pool_id, user_id, lives_left=3):
    stats = PoolUserStats(pool_id=pool_id, user_id=user_id, total_points=0, lives_left=lives_left)
    db_session.add(stats)
    await db_session.commit()
    return stats


class TestDeleteAccountRequiresAuth:
    @pytest.mark.asyncio
    async def test_without_token_returns_403(self, client):
        res = await client.delete("/users/me")
        assert res.status_code == 403


class TestDeleteAccountBasics:
    @pytest.mark.asyncio
    async def test_deletes_the_user_row(self, client, db_session, test_user):
        res = await client.delete("/users/me", headers=_auth_headers(test_user))
        assert res.status_code == 200

        result = await db_session.execute(select(User).where(User.id == test_user.id))
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_token_no_longer_usable_after_deletion(self, client, test_user):
        headers = _auth_headers(test_user)
        del_res = await client.delete("/users/me", headers=headers)
        assert del_res.status_code == 200

        me_res = await client.get("/me", headers=headers)
        assert me_res.status_code == 401

    @pytest.mark.asyncio
    async def test_deletes_own_push_token_and_notification_logs(
        self, client, db_session, test_user, test_competition
    ):
        pool = await _make_pool(db_session, test_competition.id, created_by=test_user.id)
        await _join(db_session, pool.id, test_user.id)
        db_session.add(PushToken(user_id=test_user.id, token="ExpoToken[abc]", platform="ios"))
        db_session.add(NotificationLog(
            user_id=test_user.id, pool_id=pool.id, gameweek=1,
            notification_type="day_before", sent_date=date.today(),
        ))
        await db_session.commit()

        res = await client.delete("/users/me", headers=_auth_headers(test_user))
        assert res.status_code == 200, res.text

        tokens = await db_session.execute(select(PushToken).where(PushToken.user_id == test_user.id))
        assert tokens.scalar_one_or_none() is None


class TestDeleteAccountCascadesOwnedPool:
    @pytest.mark.asyncio
    async def test_owned_pool_is_deleted_entirely(self, client, db_session, test_user, test_competition):
        pool = await _make_pool(db_session, test_competition.id, created_by=test_user.id)
        await _join(db_session, pool.id, test_user.id)

        res = await client.delete("/users/me", headers=_auth_headers(test_user))
        assert res.status_code == 200

        pool_result = await db_session.execute(select(Pool).where(Pool.id == pool.id))
        assert pool_result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_other_members_data_in_owned_pool_is_also_removed(
        self, client, db_session, test_user, test_competition
    ):
        """No ownership-transfer mechanism exists, so the pool can't
        survive without its creator - deleting the creator's account takes
        the whole pool, including other members' stats/picks, with it."""
        other = await _make_user(db_session, "otheruser")
        pool = await _make_pool(db_session, test_competition.id, created_by=test_user.id)
        await _join(db_session, pool.id, test_user.id)
        await _join(db_session, pool.id, other.id)

        res = await client.delete("/users/me", headers=_auth_headers(test_user))
        assert res.status_code == 200

        stats_result = await db_session.execute(
            select(PoolUserStats).where(PoolUserStats.pool_id == pool.id)
        )
        assert stats_result.scalars().all() == []

        # The other member's own account is untouched.
        other_result = await db_session.execute(select(User).where(User.id == other.id))
        assert other_result.scalar_one_or_none() is not None


class TestDeleteAccountLeavesJoinedPoolsIntact:
    @pytest.mark.asyncio
    async def test_pool_and_other_members_survive_when_user_was_not_the_creator(
        self, client, db_session, test_user, test_competition
    ):
        creator = await _make_user(db_session, "poolcreator")
        pool = await _make_pool(db_session, test_competition.id, created_by=creator.id)
        await _join(db_session, pool.id, creator.id)
        await _join(db_session, pool.id, test_user.id)

        res = await client.delete("/users/me", headers=_auth_headers(test_user))
        assert res.status_code == 200

        pool_result = await db_session.execute(select(Pool).where(Pool.id == pool.id))
        assert pool_result.scalar_one_or_none() is not None

        remaining_stats = await db_session.execute(
            select(PoolUserStats).where(PoolUserStats.pool_id == pool.id)
        )
        remaining_user_ids = {s.user_id for s in remaining_stats.scalars().all()}
        assert remaining_user_ids == {creator.id}
