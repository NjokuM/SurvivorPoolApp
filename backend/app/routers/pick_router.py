from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.schemas.pick_schema import PickCreate, PickRead
from app.crud.pick_crud import create_pick, get_user_picks, get_pool_picks
from app.crud.pool_crud import get_user_pools  # for validation
from app.database import get_db

router = APIRouter(
    prefix="/picks",
    tags=["Picks"]
)

# --- Create a Pick ---
@router.post("/", response_model=PickRead, status_code=status.HTTP_201_CREATED)
async def create_pick_route(pick: PickCreate, db: AsyncSession = Depends(get_db)):
    # 1️⃣ Validate user is in the pool
    user_pools = await get_user_pools(db, pick.user_id)
    pool_ids = [pool.pool_id for pool in user_pools]

    if pick.pool_id not in pool_ids:
        raise HTTPException(status_code=400, detail="User is not a member of this pool.")

    # 2️⃣ Create the pick
    try:
        new_pick = await create_pick(db, pick)
        return new_pick
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Get all picks by a user ---
@router.get("/user/{user_id}", response_model=List[PickRead])
async def get_user_picks_route(user_id: int, db: AsyncSession = Depends(get_db)):
    return await get_user_picks(db, user_id)


# --- Get all picks in a pool (optional, for leaderboard etc.) ---
@router.get("/pool/{pool_id}", response_model=List[PickRead])
async def get_pool_picks_route(pool_id: int, db: AsyncSession = Depends(get_db)):
    return await get_pool_picks(db, pool_id)
