from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.pool_schema import PoolCreate, PoolResponse
from app.crud import pool_crud

router = APIRouter(tags=["Pool"])

@router.get("/pools", response_model=list[PoolResponse])
async def get_pools(db: AsyncSession = Depends(get_db)):
    pools = await pool_crud.get_all_pools(db)
    return pools

@router.get("/pools/{pool_id}", response_model=PoolResponse)
async def get_pool_by_id(pool_id: int, db: AsyncSession = Depends(get_db)):
    pool = await pool_crud.get_pool_by_id(db, pool_id)
    return pool

@router.post("/pools/create", response_model=PoolResponse)
async def create_pool(pool_data: PoolCreate, db: AsyncSession = Depends(get_db)):
    pool = await pool_crud.create_pool(db, pool_data)
    return pool

@router.post("/pools/{pool_id}/join")
async def join_pool(pool_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    user_stats = await pool_crud.join_pool(db, pool_id, user_id)
    return {"message": "User joined pool successfully", "stats": user_stats}
