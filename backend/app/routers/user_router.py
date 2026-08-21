from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.schemas.user_schema import UserCreate, UserOut, ChangePasswordRequest
from app.crud import user_crud as crud_user
from app.dependencies.security import get_current_user
from app.utils.auth import verify_password, hash_password, create_access_token, create_refresh_token

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

@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.password:
        raise HTTPException(
            status_code=400,
            detail="This account signed up with Google and has no password set",
        )
    if not verify_password(body.current_password, current_user.password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.password = hash_password(body.new_password)
    current_user.password_changed_at = datetime.now(timezone.utc)
    await db.commit()

    # Issue this device a fresh token pair so it stays logged in; every other
    # device's existing tokens were issued before password_changed_at and
    # will be rejected on their next request (see get_current_user).
    return {
        "message": "Password changed successfully",
        "access_token": create_access_token(current_user.id),
        "refresh_token": create_refresh_token(current_user.id),
    }
    