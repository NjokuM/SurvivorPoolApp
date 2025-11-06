from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.models.pool import Pool, PoolUserStats
from app.schemas.pool_schema import PoolCreate
from app.models.pool import PoolUserStats
from app.schemas.pool_schema import PoolUserStatsCreate

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
    result = await db.execute(select(Pool).filter(Pool.id == pool_id))
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
        pool_id=pool_id, user_id=user_id, lives_left=pool.total_lives
    )
    db.add(user_stats)
    await db.commit()
    await db.refresh(user_stats)
    return user_stats

# --- Create ---
async def create_pool_user_stats(db: AsyncSession, stats: PoolUserStatsCreate):
    db_stats = PoolUserStats(
        pool_id=stats.pool_id,
        user_id=stats.user_id,
        lives_left=stats.lives_left,
        eliminated_gameweek=stats.eliminated_gameweek
    )

    db.add(db_stats)
    try:
        await db.commit()
        await db.refresh(db_stats)
        return db_stats
    except IntegrityError:
        await db.rollback()
        raise ValueError("User already has stats for this pool.")

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
