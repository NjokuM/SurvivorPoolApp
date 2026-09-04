from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.models.user import User
from app.dependencies.security import get_current_user
from app.schemas.pool_schema import (
    PoolCreate,
    PoolResponse,
    PoolWithUsers,
    PoolUserStatsResponse,
    PoolJoinRequest,
    LeaderboardEntry,
    PoolJoinByCodeRequest
)
from app.crud import pool_crud, competition_crud
from app.services import leaderboard

router = APIRouter(tags=["Pool"])

# --------------------- POOLS --------------------- #

@router.get("/pools", response_model=List[PoolResponse])
async def get_pools(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    pools = await pool_crud.get_all_pools(db)

    return pools

@router.get("/pools/{pool_id}", response_model=PoolWithUsers)
async def get_pool_by_id(pool_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    pool = await pool_crud.get_pool_by_id(db, pool_id)
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    return pool

@router.post("/pools/create", response_model=PoolResponse, status_code=status.HTTP_201_CREATED)
async def create_pool(pool_data: PoolCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # created_by is authoritative from the token, not whatever the client sent.
    pool_data.created_by = current_user.id

    # get_pick_limits already resolves "no start_gameweek given" down to a
    # real gameweek (current, or a nominal 1 if the competition has no
    # fixtures synced yet) - reuse that instead of re-deriving it here,
    # since Pool.start_gameweek is NOT NULL and can't be left unresolved.
    limits = await competition_crud.get_pick_limits(
        db, pool_data.competition_id, pool_data.start_gameweek
    )
    if not pool_data.start_gameweek:
        pool_data.start_gameweek = limits["start_gameweek"]

    if pool_data.max_picks_per_team is None:
        pool_data.max_picks_per_team = limits["default_max_picks_per_team"]
    elif pool_data.max_picks_per_team < limits["min_max_picks_per_team"]:
        raise HTTPException(
            status_code=400,
            detail=(
                f"max_picks_per_team must be at least {limits['min_max_picks_per_team']} "
                f"for this league starting from gameweek {pool_data.start_gameweek} "
                f"({limits['remaining_gameweeks']} gameweeks remaining, "
                f"{limits['team_count']} teams) - a lower value would run out of "
                "distinct teams before the season ends."
            ),
        )

    pool = await pool_crud.create_pool(db, pool_data)
    await pool_crud.join_pool(db,pool.id,pool_data.created_by)

    return pool

# --------------------- POOL USER STATS --------------------- #

@router.post("/pools/{pool_id}/join")
async def join_pool(pool_id: int, join_request: PoolJoinRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Join a pool - always joins the authenticated caller, regardless of
    what user_id the request body carries."""
    user_stats = await pool_crud.join_pool(db, pool_id, current_user.id)
    return user_stats


@router.post("/pools/join_by_code")
async def join_pool_by_code(join_request: PoolJoinByCodeRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Join a pool by session code - always joins the authenticated caller."""
    session_code = join_request.session_code

    user_stats = await pool_crud.join_pool_by_code(db, session_code, current_user.id)
    return user_stats

@router.get("/pools/{pool_id}/users", response_model=List[PoolUserStatsResponse])
async def get_users_in_pool(pool_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all users (and their stats) in a given pool"""
    try:
        users = await pool_crud.get_pool_users(db, pool_id)
        return users
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}/pools", response_model=List[PoolUserStatsResponse])
async def get_user_pools(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all pools that a given user is in - only that user themselves may view this."""
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only view your own pools")
    try:
        pools = await pool_crud.get_user_pools(db, user_id)
        return pools
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --------------------- LEADERBOARD --------------------- #
@router.get("/pools/{pool_id}/leaderboard", response_model=List[LeaderboardEntry])
async def get_pool_leaderboard(pool_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Displays all users in a pool and ranks the users based on their total points and lives"""
    return await leaderboard.get_leaderboard(db, pool_id)


# --------------------- DELETE POOL --------------------- #
@router.delete("/pools/{pool_id}", status_code=status.HTTP_200_OK)
async def delete_pool(pool_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Delete a pool. Only the pool creator can delete it.
    This will also delete all associated user stats and picks.
    """
    result = await pool_crud.delete_pool(db, pool_id, current_user.id)
    return result


# --------------------- LEAVE POOL --------------------- #
@router.delete("/pools/{pool_id}/leave", status_code=status.HTTP_200_OK)
async def leave_pool(pool_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Leave a pool. Users can leave pools they've joined.
    Pool creators cannot leave - they must delete the pool instead.
    """
    result = await pool_crud.leave_pool(db, pool_id, current_user.id)
    return result