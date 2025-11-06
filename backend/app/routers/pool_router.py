from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.schemas.pool_schema import PoolCreate, PoolResponse, PoolUserStatsCreate, PoolUserStatsRead
from app.crud import pool_crud

router = APIRouter(tags=["Pool"])

# --------------------- POOLS --------------------- #

@router.get("/pools", response_model=List[PoolResponse])
async def get_pools(db: AsyncSession = Depends(get_db)):
    pools = await pool_crud.get_all_pools(db)
    return pools

@router.get("/pools/{pool_id}", response_model=PoolResponse)
async def get_pool_by_id(pool_id: int, db: AsyncSession = Depends(get_db)):
    pool = await pool_crud.get_pool_by_id(db, pool_id)
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    return pool

@router.post("/pools/create", response_model=PoolResponse, status_code=status.HTTP_201_CREATED)
async def create_pool(pool_data: PoolCreate, db: AsyncSession = Depends(get_db)):
    pool = await pool_crud.create_pool(db, pool_data)
    return pool

# --------------------- POOL USER STATS --------------------- #

@router.post("/pools/{pool_id}/join", response_model=PoolUserStatsRead, status_code=status.HTTP_201_CREATED)
async def join_pool(pool_id: int, user_stats: PoolUserStatsCreate, db: AsyncSession = Depends(get_db)):
    """Join a pool (creates a PoolUserStats record)"""
    if user_stats.pool_id != pool_id:
        raise HTTPException(status_code=400, detail="Pool ID mismatch between path and body.")

    try:
        new_stats = await pool_crud.create_pool_user_stats(db, user_stats)
        return new_stats
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pools/{pool_id}/users", response_model=List[PoolUserStatsRead])
async def get_users_in_pool(pool_id: int, db: AsyncSession = Depends(get_db)):
    """Get all users (and their stats) in a given pool"""
    users = await pool_crud.get_pool_users(db, pool_id)
    if not users:
        raise HTTPException(status_code=404, detail="No users found in this pool.")
    return users

@router.get("/users/{user_id}/pools", response_model=List[PoolUserStatsRead])
async def get_user_pools(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get all pools that a given user is in"""
    pools = await pool_crud.get_user_pools(db, user_id)
    if not pools:
        raise HTTPException(status_code=404, detail="User is not part of any pools.")
    return pools
