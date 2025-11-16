from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from sqlalchemy.orm import selectinload
from datetime import datetime
from app.models.pool import Pool, PoolUserStats
from app.schemas.pool_schema import PoolCreate
from app.models.pool import PoolUserStats
from app.schemas.pool_schema import PoolUserStatsBase

# Create a new pool
async def create_pool(db: AsyncSession, pool_data: PoolCreate):
    new_pool = Pool(**pool_data.model_dump())
    db.add(new_pool)
    await db.commit()
    await db.refresh(new_pool)
    return new_pool

# Get all pools
async def get_all_pools(db: AsyncSession):
    result = await db.execute(select(Pool))
    return result.scalars().all()

# Get pool by id
async def get_pool_by_id(db: AsyncSession, pool_id: int):
    stmt = (
        select(Pool)
        .options(selectinload(Pool.users_stats))
        .filter(Pool.id == pool_id)
    )

    result = await db.execute(stmt)
    pool = result.scalar_one_or_none()

    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")

    return pool

# ➕ Join a pool
async def join_pool(db: AsyncSession, pool_id: int, user_id: int):
    # Ensure pool exists
    pool = await get_pool_by_id(db, pool_id)

    # Check if user already joined
    result = await db.execute(
        select(PoolUserStats).filter(
            PoolUserStats.pool_id == pool_id, PoolUserStats.user_id == user_id
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="User already joined this pool")

    # Create stats record
    user_stats = PoolUserStats(
        pool_id=pool_id,
        user_id=user_id,
        lives_left=pool.total_lives,
        eliminated_gameweek=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(user_stats)
    try:
        await db.commit()
        await db.refresh(user_stats)
        return user_stats
    except IntegrityError as e:
        await db.rollback()
        if 'unique' in str(e.orig).lower():
            raise HTTPException(status_code=400, detail="User already joined this pool")
    raise HTTPException(status_code=400, detail="Database integrity error: " + str(e.orig))

# --- Get all pools for a user ---
async def get_user_pools(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(PoolUserStats).where(PoolUserStats.user_id == user_id)
    )
    return result.scalars().all()

# --- Get all users (and stats) in a pool ---
async def get_pool_users(db: AsyncSession, pool_id: int):
    result = await db.execute(
        select(PoolUserStats).where(PoolUserStats.pool_id == pool_id)
    )
    return result.scalars().all()

# --- Get a specific user's stats for a pool ---
async def get_pool_user_stats(db: AsyncSession, pool_id: int, user_id: int):
    result = await db.execute(
        select(PoolUserStats).where(
            PoolUserStats.pool_id == pool_id,
            PoolUserStats.user_id == user_id
        )
    )
    return result.scalar_one_or_none()

# --- Update user stats ---
async def update_pool_user_stats(
    db: AsyncSession,
    pool_id: int,
    user_id: int,
    lives_left: int = None,
    eliminated_gameweek: int = None
):
    stats = await get_pool_user_stats(db, pool_id, user_id)
    if not stats:
        return None

    if lives_left is not None:
        stats.lives_left = lives_left
    if eliminated_gameweek is not None:
        stats.eliminated_gameweek = eliminated_gameweek

    await db.commit()
    await db.refresh(stats)
    return stats
