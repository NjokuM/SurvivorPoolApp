from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.dependencies.security import get_current_user
from app.models.user import User
from app.models.pool import Pool


async def require_pool_admin(
    pool_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Pool:
    """A pool's only admin is its creator - resolved from the caller's
    verified JWT, never from a client-supplied flag."""
    result = await db.execute(select(Pool).where(Pool.id == pool_id))
    pool = result.scalar_one_or_none()
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    if pool.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only the pool creator can perform this action")
    return pool
