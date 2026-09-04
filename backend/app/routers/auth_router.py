from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import JWTError
from google.auth.exceptions import GoogleAuthError
from app.database import get_db
from app.models.user import User
from app.utils.auth import verify_password, create_access_token, create_refresh_token, decode_token, token_predates_password_change
from app.utils.google_auth import verify_google_id_token
from app.utils.apple_auth import verify_apple_id_token
from app.dependencies.security import get_current_user
from app.schemas.user_schema import UserCreate, UserLogin, GoogleAuthRequest, AppleAuthRequest
from app.crud.user_crud import create_user, generate_unique_username

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
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # Get user by email
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    # Check if user exists and password matches (Google-only accounts have
    # no local password, so they can't log in this way).
    if not user or not user.password or not verify_password(password, user.password):
        return {"success": False, "message": "Invalid credentials"}

    # Issue a short-lived access token plus a season-long refresh token so
    # the app can keep users signed in without re-prompting for credentials.
    return {
        "success": True,
        "message": "Logged in successfully",
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "user": {"id": user.id, "email": user.email},
    }

@router.post("/google")
async def google_login(
    body: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        claims = verify_google_id_token(body.id_token)
    except (ValueError, GoogleAuthError):
        raise HTTPException(status_code=401, detail="Invalid Google token")

    if not claims.get("email_verified"):
        raise HTTPException(status_code=401, detail="Google email is not verified")

    google_id = claims["sub"]
    email = claims["email"]

    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalars().first()

    if not user:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        if user:
            # Existing local account signing in with Google for the first time.
            user.google_id = google_id
        else:
            username = await generate_unique_username(email, db)
            user = User(
                userName=username,
                email=email,
                password=None,
                firstName=claims.get("given_name") or username,
                lastName=claims.get("family_name") or "",
                google_id=google_id,
            )
            db.add(user)
        await db.commit()
        await db.refresh(user)

    return {
        "success": True,
        "message": "Logged in successfully",
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "user": {"id": user.id, "email": user.email},
    }

@router.post("/apple")
async def apple_login(
    body: AppleAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        claims = await verify_apple_id_token(body.identity_token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Apple token")

    # Apple sometimes sends this as the string "true"/"false" rather than a
    # real boolean, depending on token version.
    if str(claims.get("email_verified", "")).lower() != "true":
        raise HTTPException(status_code=401, detail="Apple email is not verified")

    apple_id = claims["sub"]
    # Only present on the user's very first authorization ever - every
    # later sign-in omits it from both the token and the client result, so
    # fall back to whatever the client sent (also only ever set on first auth).
    email = claims.get("email") or body.email

    result = await db.execute(select(User).where(User.apple_id == apple_id))
    user = result.scalars().first()

    if not user:
        if not email:
            # Should only happen if a first-time sign-in is somehow missing
            # email from both the token and the client - nothing to create
            # an account with.
            raise HTTPException(status_code=401, detail="Apple did not provide an email for this sign-in")

        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        if user:
            # Existing local account signing in with Apple for the first time.
            user.apple_id = apple_id
        else:
            username = await generate_unique_username(email, db)
            user = User(
                userName=username,
                email=email,
                password=None,
                firstName=body.given_name or username,
                lastName=body.family_name or "",
                apple_id=apple_id,
            )
            db.add(user)
        await db.commit()
        await db.refresh(user)

    return {
        "success": True,
        "message": "Logged in successfully",
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "user": {"id": user.id, "email": user.email},
    }

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email}

@router.post("/refresh")
async def refresh(
    refresh_token: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    result = await db.execute(select(User).where(User.id == int(payload["sub"])))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if token_predates_password_change(payload, user.password_changed_at):
        raise HTTPException(status_code=401, detail="Session expired, please log in again")

    # Rotate both tokens on refresh.
    return {
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
    }

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # Tokens are stateless JWTs, so logging out is just the client discarding
    # them locally. This endpoint exists for a consistent API contract.
    return {"message": "Logged out"}
