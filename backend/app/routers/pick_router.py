from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import timezone, datetime
from sqlalchemy import select
from app.models.competiton_data import Fixture
from app.models.pick import Pick
from app.models.pool import Pool
from app.schemas.pick_schema import PickCreate, PickRead
from app.crud.pick_crud import create_pick, get_user_picks, get_pool_picks
from app.crud.pool_crud import get_pool_user_stats, get_user_pools  # for validation
from app.database import get_db

router = APIRouter(
    prefix="/picks",
    tags=["Picks"]
)

# --- Create a Pick ---
@router.post("/", response_model=PickRead, status_code=status.HTTP_201_CREATED)
async def create_pick_route(pick: PickCreate, db: AsyncSession = Depends(get_db)):

    # 1️⃣ Validate user is part of the pool
    user_pools = await get_user_pools(db, pick.user_id)
    pool_ids = [pool.pool_id for pool in user_pools]
    if pick.pool_id not in pool_ids:
        raise HTTPException(status_code=400, detail="User is not a member of this pool.")

    # 2️⃣ Fetch fixture
    fixture_result = await db.execute(select(Fixture).filter(Fixture.id == pick.fixture_id))
    fixture = fixture_result.scalar_one_or_none()
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")

    # 3️⃣ Fetch pool
    pool_result = await db.execute(select(Pool).filter(Pool.id == pick.pool_id))
    pool = pool_result.scalar_one_or_none()
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")

    # 4️⃣ Validate fixture belongs to the same competition as pool
    if fixture.competition_id != pool.competition_id:
        raise HTTPException(
            status_code=400,
            detail="Fixture competition does not match the pool competition."
        )
    # Use pool.competition_id for the Pick
    competition_id = pool.competition_id

    # 5️⃣ Fixture timing validation
    if fixture.kickoff_time <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Cannot pick for a fixture that has already started")

    # 6️⃣ Team validation
    if pick.team_id not in [fixture.home_team_id, fixture.away_team_id]:
        raise HTTPException(status_code=400, detail="Invalid team for this fixture")

    # 7️⃣ Ensure user has not already made a pick this gameweek in this pool
    existing_gameweek_pick_result = await db.execute(
    select(Pick)
    .join(Fixture, Fixture.id == Pick.fixture_id)
    .filter(
        Pick.pool_id == pick.pool_id,
        Pick.user_id == pick.user_id,
        Fixture.gameweek == fixture.gameweek
    ))

    existing_gameweek_pick = existing_gameweek_pick_result.scalars().first()

    if existing_gameweek_pick:
        raise HTTPException(
            status_code=400,
            detail=f"You've already made a pick for gameweek {fixture.gameweek}."
        )

    # 8️⃣ Check if user still has lives
    user_stats = await get_pool_user_stats(db, pick.pool_id, pick.user_id)
    if user_stats and user_stats.lives_left <= 0:
        raise HTTPException(status_code=400, detail="User has no lives left in this pool")

    # 9️⃣ Ensure team hasn’t been picked more than allowed
    previous_team_picks = (await db.execute(
        select(Pick).filter(
            Pick.pool_id == pick.pool_id,
            Pick.user_id == pick.user_id,
            Pick.team_id == pick.team_id
        )
    )).scalars().all()

    if len(previous_team_picks) >= pool.max_picks_per_team:
        raise HTTPException(
            status_code=400,
            detail=f"You've already picked this team the maximum of {pool.max_picks_per_team} times in this pool."
        )

    # 🔟 Save pick
    try:
        new_pick = await create_pick(db, pick,competition_id=pool.competition_id)
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
