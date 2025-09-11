from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user_schema import UserCreate, UserOut
from app.crud import user_crud as crud_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserOut, status_code=201)
async def create_user(make_user: UserCreate, db: AsyncSession = Depends(get_db)):
    return await crud_user.create_user(make_user, db)

@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id : int, db: AsyncSession=Depends(get_db)):
    user = await crud_user.get_user_by_id(user_id,db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user
    