import os
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import JWTError
from dotenv import load_dotenv
from app.database import get_db
from app.models.user import User
from app.utils.auth import decode_token, token_predates_password_change

load_dotenv()

CRON_SECRET = os.getenv("CRON_SECRET")

async def verify_cron(request: Request):
    header = request.headers.get("x-cron-secret")
    if header != CRON_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")


bearer_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the logged-in user from a Bearer access token."""
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    result = await db.execute(select(User).where(User.id == int(payload["sub"])))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if token_predates_password_change(payload, user.password_changed_at):
        raise HTTPException(status_code=401, detail="Session expired, please log in again")

    return user
