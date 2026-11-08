from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.pool import Pool, DoubleWeek
from app.models.user import User
from app.crud.pool_crud import get_pool_user_stats
from app.dependencies.admin import require_pool_admin
from app.dependencies.security import get_current_user
from app.schemas.pool_schema import DoubleWeekStatus, DoubleWeekActivate, DoubleWeekAllowanceUpdate
from app.services import double_weeks as dw

router = APIRouter(tags=["Double Weeks"])


async def _load_member_pool(db: AsyncSession, pool_id: int, user_id: int) -> Pool:
    pool = (await db.execute(select(Pool).where(Pool.id == pool_id))).scalar_one_or_none()
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    if not await get_pool_user_stats(db, pool_id, user_id):
        raise HTTPException(status_code=403, detail="You are not a member of this pool")
    return pool


async def _status(db: AsyncSession, pool: Pool, user_id: int) -> DoubleWeekStatus:
    active = await dw.active_gameweeks(db, pool.id, user_id)
    allowance = 0 if pool.has_lives else pool.double_weeks
    return DoubleWeekStatus(
        allowance=allowance,
        used=len(active),
        remaining=max(0, allowance - len(active)),
        active_gameweeks=active,
    )


@router.get("/pools/{pool_id}/double-weeks/me", response_model=DoubleWeekStatus)
async def get_my_double_weeks(pool_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    pool = await _load_member_pool(db, pool_id, current_user.id)
    return await _status(db, pool, current_user.id)


@router.post("/pools/{pool_id}/double-weeks", response_model=DoubleWeekStatus)
async def activate_double_week(
    pool_id: int,
    body: DoubleWeekActivate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Switch on a double week for a gameweek, allowing a second pick that week."""
    pool = await _load_member_pool(db, pool_id, current_user.id)
    if pool.has_lives:
        raise HTTPException(status_code=400, detail="Double weeks are only available in points-only pools")

    status = await _status(db, pool, current_user.id)
    if body.gameweek in status.active_gameweeks:
        raise HTTPException(status_code=400, detail=f"Double week is already on for gameweek {body.gameweek}")
    if status.remaining <= 0:
        raise HTTPException(status_code=400, detail="You have no double weeks left in this pool")
    if body.gameweek < pool.start_gameweek:
        raise HTTPException(status_code=400, detail="That gameweek is before this pool started")

    last_kickoff = await dw.gameweek_last_kickoff(db, pool.competition_id, body.gameweek)
    if last_kickoff is None:
        raise HTTPException(status_code=404, detail=f"No fixtures found for gameweek {body.gameweek}")
    if last_kickoff <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail=f"Gameweek {body.gameweek} has already finished picking")

    db.add(DoubleWeek(pool_id=pool.id, user_id=current_user.id, gameweek=body.gameweek))
    await db.commit()
    return await _status(db, pool, current_user.id)


@router.delete("/pools/{pool_id}/double-weeks/{gameweek}", response_model=DoubleWeekStatus)
async def deactivate_double_week(
    pool_id: int,
    gameweek: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Switch a double week back off. If a second pick was already made, it's
    removed - which is only possible while that pick hasn't kicked off."""
    pool = await _load_member_pool(db, pool_id, current_user.id)
    row = (await db.execute(
        select(DoubleWeek).where(
            DoubleWeek.pool_id == pool.id,
            DoubleWeek.user_id == current_user.id,
            DoubleWeek.gameweek == gameweek,
        )
    )).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail=f"Double week isn't on for gameweek {gameweek}")

    picks = await dw.gameweek_picks(db, pool.id, current_user.id, gameweek)
    if len(picks) >= 2:
        now = datetime.now(timezone.utc)
        # Remove the most recent pick that hasn't started yet.
        removable = [p for p, f in reversed(picks) if dw.as_utc(f.kickoff_time) > now]
        if not removable:
            raise HTTPException(status_code=400, detail="Both of this week's picks have already kicked off")
        await db.delete(removable[0])

    await db.delete(row)
    await db.commit()
    return await _status(db, pool, current_user.id)


@router.put("/pools/{pool_id}/double-weeks/allowance")
async def set_double_week_allowance(
    pool_id: int,
    body: DoubleWeekAllowanceUpdate,
    pool: Pool = Depends(require_pool_admin),
    db: AsyncSession = Depends(get_db),
):
    """Pool admin: set how many double weeks each member gets (0 switches
    the feature off for future weeks - weeks already played stay scored)."""
    if pool.has_lives:
        raise HTTPException(status_code=400, detail="Double weeks are only available in points-only pools")
    if body.double_weeks > dw.MAX_DOUBLE_WEEKS:
        raise HTTPException(status_code=400, detail=f"A pool can have at most {dw.MAX_DOUBLE_WEEKS} double weeks")
    used = await dw.max_used_in_pool(db, pool.id)
    if 0 < body.double_weeks < used:
        raise HTTPException(
            status_code=400,
            detail=f"A member has already used {used} double weeks - set at least {used}, or 0 to switch them off",
        )
    pool.double_weeks = body.double_weeks
    await db.commit()
    return {"pool_id": pool.id, "double_weeks": pool.double_weeks}
