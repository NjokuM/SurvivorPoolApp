from fastapi import APIRouter, Depends, Request, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.user import User
from app.utils.auth import verify_password
from app.schemas.user import UserCreate, UserLogin
from app.crud.user_crud import create_user

router = APIRouter(tags=["Auth"])

@router.post("/signup")
async def signup(
    userName: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    firstName: str = Form(...),
    lastName: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    
    credentials = UserLogin(email=email, password=password)
    
    # Check if email already exists
    result = await db.execute(select(User).filter(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already in use")

    # Check if username already exists
    result = await db.execute(select(User).filter(User.userName == userName))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already taken")

    # Prepare user data using a Pydantic model or a simple class-like structure
    make_user = UserCreate(
        userName=userName,
        email=email,
        password=password,
        firstName=firstName,
        lastName=lastName,
    )

    new_user = await create_user(make_user, db)

    return {"message": "User created successfully", "user_id": new_user.id}

@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # Get user by email
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    # Check if user exists and password matches
    if not user or not verify_password(password, user.password):
        return {"error": "Invalid credentials"}

    # Store session
    request.session["user_id"] = user.id
    return {"message": "Logged in successfully"}

@router.get("/me")
async def get_me(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return {"error": "Not logged in"}

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    return {"id": user.id, "email": user.email}

@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out"}