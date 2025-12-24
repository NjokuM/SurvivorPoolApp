import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from sqlalchemy.orm import selectinload
from datetime import datetime
from app.models.pool import Pool, PoolUserStats
from app.schemas.pool_schema import PoolCreate

# --------------------------
# HELPER: Generate session code
# --------------------------
async def generate_session_code() -> str:
    random_code = secrets.token_hex(3)  # 6-char hex
    return random_code.upper() 

# --------------------------
# CREATE POOL
# --------------------------
async def create_pool(db: AsyncSession, pool_data: PoolCreate):
    from app.services.scheduler import sync_competition_if_needed

    # 1. Generate session code
    session_code = await generate_session_code()

    # 2. Create pool object
    pool_dict = pool_data.model_dump()
    pool_dict["session_code"] = session_code

    new_pool = Pool(**pool_dict)

    db.add(new_pool)
    await db.commit()
    await db.refresh(new_pool)
    
    # 3. If this is the first pool for this competition, sync fixtures
    # This handles the edge case where a user creates a pool for a league
    # that wasn't previously active (no fixtures synced recently)
    if new_pool.competition_id:
        try:
            await sync_competition_if_needed(db, new_pool.competition_id)
        except Exception as e:
            # Don't fail pool creation if fixture sync fails
            print(f"Warning: Could not sync fixtures for competition {new_pool.competition_id}: {e}")
    
    return new_pool

# --------------------------
# GET ALL POOLS
# --------------------------
async def get_all_pools(db: AsyncSession):
    result = await db.execute(select(Pool).options(selectinload(Pool.users_stats)))
    return result.scalars().all()

# --------------------------
# GET POOL BY ID
# --------------------------
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

# --------------------------
# JOIN POOL BY ID
# --------------------------
async def join_pool(db: AsyncSession, pool_id: int, user_id: int):
    pool = await get_pool_by_id(db, pool_id)

    # Check if user already joined
    result = await db.execute(
        select(PoolUserStats).filter(
            PoolUserStats.pool_id == pool_id,
            PoolUserStats.user_id == user_id
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already joined this pool")

    # Create user stats
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
        raise HTTPException(status_code=400, detail="Database error: " + str(e.orig))


# --------------------------
# JOIN POOL BY SESSION CODE
# --------------------------
async def join_pool_by_code(db: AsyncSession, session_code: str, user_id: int):
    # 1. Look up pool by session_code
    result = await db.execute(
        select(Pool).filter(Pool.session_code == session_code)
    )
    pool = result.scalar_one_or_none()

    if not pool:
        raise HTTPException(status_code=404, detail="Invalid session code")

    # 2. Reuse join_pool logic
    return await join_pool(db, pool.id, user_id)


# --------------------------
# GET POOLS FOR USER
# --------------------------
async def get_user_pools(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(PoolUserStats).where(PoolUserStats.user_id == user_id)
    )
    return result.scalars().all()


# --------------------------
# GET USERS IN POOL
# --------------------------
async def get_pool_users(db: AsyncSession, pool_id: int):
    result = await db.execute(
        select(PoolUserStats).where(PoolUserStats.pool_id == pool_id)
    )
    return result.scalars().all()


# --------------------------
# GET USER STATS IN POOL
# --------------------------
async def get_pool_user_stats(db: AsyncSession, pool_id: int, user_id: int):
    result = await db.execute(
        select(PoolUserStats).where(
            PoolUserStats.pool_id == pool_id,
            PoolUserStats.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


# --------------------------
# UPDATE USER STATS
# --------------------------
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