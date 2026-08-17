import os
import bcrypt
from datetime import datetime, timedelta, timezone
from jose import jwt

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# Short-lived access token: limits exposure if a token leaks.
ACCESS_TOKEN_EXPIRE_MINUTES = 30
# Long-lived refresh token: covers a full season so users aren't forced to
# log in again mid-season. The app silently exchanges this for a fresh
# access token (see /refresh) whenever the access token expires.
REFRESH_TOKEN_EXPIRE_DAYS = 180


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def _create_token(user_id: int, token_type: str, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {"sub": str(user_id), "type": token_type, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(user_id: int) -> str:
    return _create_token(user_id, "access", timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(user_id: int) -> str:
    return _create_token(user_id, "refresh", timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))


def decode_token(token: str) -> dict:
    """Decode and verify a JWT, raising jose.JWTError if invalid/expired/tampered."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
