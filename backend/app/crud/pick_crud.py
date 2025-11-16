from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.models.pick import Pick
from app.schemas.pick_schema import PickCreate

# --- Create a Pick ---
async def create_pick(db: AsyncSession, pick: PickCreate,  competition_id : int):
    db_pick = Pick(
        pool_id=pick.pool_id,
        user_id=pick.user_id,
        team_id=pick.team_id,
        fixture_id=pick.fixture_id,
        competition_id=competition_id
    )

    db.add(db_pick)
    try:
        await db.commit()
        await db.refresh(db_pick)
        return db_pick
    except IntegrityError:
        await db.rollback()
        raise ValueError("Pick already exists for this pool/user/fixture combination.")


# --- Get a single Pick ---
async def get_pick(db: AsyncSession, pick_id: int):
    result = await db.execute(select(Pick).filter(Pick.id == pick_id))
    return result.scalars().first()


# --- Get all picks by user ---
async def get_user_picks(db: AsyncSession, user_id: int):
    result = await db.execute(select(Pick).filter(Pick.user_id == user_id))
    return result.scalars().all()


# --- Get all picks in a pool ---
async def get_pool_picks(db: AsyncSession, pool_id: int):
    result = await db.execute(select(Pick).filter(Pick.pool_id == pool_id))
    return result.scalars().all()

# --- Updates an existing pick in a pool ---
async def update_pick(db: AsyncSession, pick_id: int, updates: dict):
    result = await db.execute(select(Pick).filter(Pick.id == pick_id))
    pick = result.scalar_one_or_none()

    if not pick:
        return None

    for key, value in updates.items():
        setattr(pick, key, value)
    try:
        await db.commit()
        await db.refresh(pick)
        return pick
    except IntegrityError as e:
        await db.rollback()
        raise e