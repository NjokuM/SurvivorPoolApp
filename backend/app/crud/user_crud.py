from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.schemas.user_schema import UserCreate
from datetime import datetime
from app.utils.auth import hash_password

async def create_user(make_user: UserCreate, db:AsyncSession) -> User:
    new_user = User(
        userName=make_user.userName,
        email=make_user.email,
        password=hash_password(make_user.password),
        firstName=make_user.firstName,
        lastName=make_user.lastName,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def get_user_by_id(user_id : int, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user

async def generate_unique_username(email: str, db: AsyncSession) -> str:
    """Derive a username from an email's local part, disambiguating with a
    numeric suffix if it's already taken (used for Google sign-up)."""
    base = "".join(ch for ch in email.split("@")[0] if ch.isalnum()) or "user"
    candidate = base
    suffix = 1
    while True:
        result = await db.execute(select(User).where(User.userName == candidate))
        if not result.scalar_one_or_none():
            return candidate
        suffix += 1
        candidate = f"{base}{suffix}"

