from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
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
async def get_pools(db: AsyncSession = Depends(get_db)):
    pools = await pool_crud.get_all_pools(db)
    
    return pools

@router.get("/pools/{pool_id}", response_model=PoolWithUsers)
async def get_pool_by_id(pool_id: int, db: AsyncSession = Depends(get_db)):
    pool = await pool_crud.get_pool_by_id(db, pool_id)
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    return pool

@router.post("/pools/create", response_model=PoolResponse, status_code=status.HTTP_201_CREATED)
async def create_pool(pool_data: PoolCreate, db: AsyncSession = Depends(get_db)):
    if not pool_data.start_gameweek:
        current_gw = await competition_crud.get_current_gameweek(db, pool_data.competition_id)
        pool_data.start_gameweek = current_gw
    
    pool = await pool_crud.create_pool(db, pool_data)
    await pool_crud.join_pool(db,pool.id,pool_data.created_by)

    return pool

# --------------------- POOL USER STATS --------------------- #

@router.post("/pools/{pool_id}/join")
async def join_pool(pool_id: int, join_request: PoolJoinRequest, db: AsyncSession = Depends(get_db)):
    """Join a pool by user ID"""
    user_id = join_request.user_id

    user_stats = await pool_crud.join_pool(db, pool_id, user_id)
    return user_stats


@router.post("/pools/join_by_code")
async def join_pool_by_code(join_request: PoolJoinByCodeRequest, db: AsyncSession = Depends(get_db)):
    """Join a pool by session code"""
    user_id = join_request.user_id
    session_code = join_request.session_code

    user_stats = await pool_crud.join_pool_by_code(db, session_code, user_id)
    return user_stats

@router.get("/pools/{pool_id}/users", response_model=List[PoolUserStatsResponse])
async def get_users_in_pool(pool_id: int, db: AsyncSession = Depends(get_db)):
    """Get all users (and their stats) in a given pool"""
    try:
        users = await pool_crud.get_pool_users(db, pool_id)
        return users
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}/pools", response_model=List[PoolUserStatsResponse])
async def get_user_pools(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get all pools that a given user is in"""
    try:
        pools = await pool_crud.get_user_pools(db, user_id)
        return pools
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --------------------- LEADERBOARD --------------------- #
@router.get("/pools/{pool_id}/leaderboard", response_model=List[LeaderboardEntry])
async def get_pool_leaderboard(pool_id: int, db: AsyncSession = Depends(get_db)):
    """Displays all users in a pool and ranks the users based on their total points and lives"""
    return await leaderboard.get_leaderboard(db, pool_id)