import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from jose import JWTError
from google.auth.exceptions import GoogleAuthError
from app.database import get_db
from app.models.user import User
from app.utils.auth import normalize_email, hash_password, verify_password, create_access_token, create_refresh_token, decode_token, token_predates_password_change
from app.utils.google_auth import verify_google_id_token
from app.utils.apple_auth import verify_apple_id_token
from app.dependencies.security import get_current_user
from app.services.email import email_configured, send_email
from app.schemas.user_schema import (
    UserCreate, UserLogin, GoogleAuthRequest, AppleAuthRequest,
    ForgotPasswordRequest, ResetPasswordRequest,
)
from app.crud.user_crud import create_user, generate_unique_username

router = APIRouter(tags=["Auth"])

RESET_CODE_TTL = timedelta(minutes=15)
RESET_CODE_RESEND_COOLDOWN = timedelta(seconds=60)
RESET_CODE_MAX_ATTEMPTS = 5

@router.post("/signup")
async def signup(
    userName: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    firstName: str = Form(...),
    lastName: str = Form(...),
    db: AsyncSession = Depends(get_db),
):

    email = normalize_email(email)
    credentials = UserLogin(email=email, password=password)

    # Check if email already exists. Compared case-insensitively so accounts
    # created before emails were normalized still count as taken.
    result = await db.execute(select(User).filter(func.lower(User.email) == email))
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

    # Log the user straight in, matching /login, /google and /apple - there's
    # no reason to make someone who just created an account immediately
    # re-enter the same credentials on a separate screen.
    return {
        "success": True,
        "message": "User created successfully",
        "user_id": new_user.id,
        "access_token": create_access_token(new_user.id),
        "refresh_token": create_refresh_token(new_user.id),
        "user": {"id": new_user.id, "email": new_user.email},
    }

@router.post("/login")
async def login(
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # Get user by email - case-insensitive, so it also matches accounts
    # stored with mixed case before emails were normalized on signup.
    email = normalize_email(email)
    result = await db.execute(select(User).where(func.lower(User.email) == email))
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
    email = normalize_email(claims["email"])

    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalars().first()

    if not user:
        result = await db.execute(select(User).where(func.lower(User.email) == email))
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
    email = normalize_email(email) if email else None

    result = await db.execute(select(User).where(User.apple_id == apple_id))
    user = result.scalars().first()

    if not user:
        if not email:
            # Should only happen if a first-time sign-in is somehow missing
            # email from both the token and the client - nothing to create
            # an account with.
            raise HTTPException(status_code=401, detail="Apple did not provide an email for this sign-in")

        result = await db.execute(select(User).where(func.lower(User.email) == email))
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

def _as_utc(dt: datetime) -> datetime:
    # SQLite (used in tests) drops tzinfo from DateTime(timezone=True) columns.
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Email a 6-digit reset code. Always returns the same response whether
    or not the email has an account, so this can't be used to probe which
    emails are registered."""
    if not email_configured():
        # Not user-specific, so it reveals nothing - but fail loudly rather
        # than silently "send" emails that never arrive.
        raise HTTPException(status_code=503, detail="Password reset is temporarily unavailable")

    generic = {"message": "If an account exists for that email, a reset code has been sent"}
    email = normalize_email(body.email)
    user = (await db.execute(select(User).where(func.lower(User.email) == email))).scalars().first()
    if not user:
        return generic

    now = datetime.now(timezone.utc)
    if user.password_reset_expires_at is not None:
        issued_at = _as_utc(user.password_reset_expires_at) - RESET_CODE_TTL
        if now - issued_at < RESET_CODE_RESEND_COOLDOWN:
            return generic  # just sent one - don't let this be used to spam an inbox

    code = f"{secrets.randbelow(1_000_000):06d}"
    user.password_reset_code_hash = hash_password(code)
    user.password_reset_expires_at = now + RESET_CODE_TTL
    user.password_reset_attempts = 0
    await db.commit()

    try:
        await send_email(
            user.email,
            "Your Survivor Pool password reset code",
            f"Hi {user.firstName or user.userName},\n\n"
            f"Your password reset code is: {code}\n\n"
            "It expires in 15 minutes. If you didn't ask to reset your password, "
            "you can ignore this email - your password won't change.\n\n"
            "- Survivor Pool",
        )
    except Exception as e:
        print(f"Failed to send password reset email: {e}")
        raise HTTPException(status_code=503, detail="Couldn't send the reset email, please try again")

    return generic


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Set a new password using the emailed code, then log the user in."""
    invalid = HTTPException(status_code=400, detail="Invalid or expired code")
    email = normalize_email(body.email)
    user = (await db.execute(select(User).where(func.lower(User.email) == email))).scalars().first()
    if not user or not user.password_reset_code_hash or not user.password_reset_expires_at:
        raise invalid

    if (
        _as_utc(user.password_reset_expires_at) < datetime.now(timezone.utc)
        or user.password_reset_attempts >= RESET_CODE_MAX_ATTEMPTS
    ):
        raise invalid

    if not verify_password(body.code, user.password_reset_code_hash):
        # Cap guesses so a 6-digit code can't be brute-forced.
        user.password_reset_attempts += 1
        await db.commit()
        raise invalid

    user.password = hash_password(body.new_password)
    # Logs out every other device, same as a normal password change.
    user.password_changed_at = datetime.now(timezone.utc)
    user.password_reset_code_hash = None
    user.password_reset_expires_at = None
    user.password_reset_attempts = 0
    await db.commit()

    return {
        "success": True,
        "message": "Password reset successfully",
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
