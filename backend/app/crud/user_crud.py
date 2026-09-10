from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.models.pick import Pick
from app.models.pool import Pool, PoolUserStats
from app.models.notification import PushToken, NotificationLog
from app.schemas.user_schema import UserCreate
from datetime import datetime
from app.utils.auth import hash_password

async def create_user(make_user: UserCreate, db:AsyncSession) -> User:
    new_user = User(
        userName=make_user.userName,
        email=make_user.email,
        password=hash_password(make_user.password),
        firstName=make_user.firstName,
        lastName=make_user.lastName,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def get_user_by_id(user_id : int, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user

async def delete_user_account(db: AsyncSession, user_id: int) -> None:
    """Permanently delete a user and everything tied to them.

    There's no ownership-transfer mechanism (single-admin-per-pool model),
    so a pool can't outlive the user who created it - pools they created
    are deleted entirely, same as the existing "delete pool" flow, cascading
    to every member's picks/stats/notification logs in that pool. Pools
    they merely joined just lose their own membership, same as "leave pool".
    """
    owned_pool_ids_result = await db.execute(
        select(Pool.id).where(Pool.created_by == user_id)
    )
    owned_pool_ids = [row[0] for row in owned_pool_ids_result.all()]

    for pool_id in owned_pool_ids:
        await db.execute(delete(Pick).where(Pick.pool_id == pool_id))
        await db.execute(delete(PoolUserStats).where(PoolUserStats.pool_id == pool_id))
        await db.execute(delete(NotificationLog).where(NotificationLog.pool_id == pool_id))
        await db.execute(delete(Pool).where(Pool.id == pool_id))

    # Membership in pools they didn't create (rows for owned pools above are
    # already gone, so these are safe no-ops for that overlap).
    await db.execute(delete(Pick).where(Pick.user_id == user_id))
    await db.execute(delete(PoolUserStats).where(PoolUserStats.user_id == user_id))
    await db.execute(delete(NotificationLog).where(NotificationLog.user_id == user_id))
    await db.execute(delete(PushToken).where(PushToken.user_id == user_id))

    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()


async def generate_unique_username(email: str, db: AsyncSession) -> str:
    """Derive a username from an email's local part, disambiguating with a
    numeric suffix if it's already taken (used for Google sign-up)."""
    base = "".join(ch for ch in email.split("@")[0] if ch.isalnum()) or "user"
    candidate = base
    suffix = 1
    while True:
        result = await db.execute(select(User).where(User.userName == candidate))
        if not result.scalar_one_or_none():
            return candidate
        suffix += 1
        candidate = f"{base}{suffix}"

