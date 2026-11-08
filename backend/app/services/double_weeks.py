# app/services/double_weeks.py
"""
Double weeks: in a points-only pool, each member gets a small allowance of
gameweeks where they may pick two teams (from different fixtures) and score
both results.

Why it exists: a double round-robin league with N teams has 2(N-1)
gameweeks, but picking every team exactly twice takes 2N picks - two short.
Two double weeks close that gap, so every team can be used exactly twice.

A member switches one on per gameweek (a DoubleWeek row). The row is the
only thing that permits a second pick that week. If the week closes with
fewer than two picks the row is removed again, so it isn't used up.
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.competiton_data import Fixture
from app.models.pick import Pick
from app.models.pool import Pool, DoubleWeek

MAX_DOUBLE_WEEKS = 5


def suggested_double_weeks(team_count: int, max_picks_per_team: int,
                           remaining_gameweeks: int, total_gameweeks: int) -> int:
    """How many double weeks let every team be picked exactly max_picks
    times. Only meaningful for a pool covering the whole season - a pool
    starting mid-season already has more team slots than gameweeks, so
    double weeks would just be bonus picks and default to off."""
    if team_count <= 0 or remaining_gameweeks < total_gameweeks:
        return 0
    gap = team_count * max_picks_per_team - remaining_gameweeks
    return gap if 0 < gap <= MAX_DOUBLE_WEEKS else 0


def as_utc(dt: datetime) -> datetime:
    # SQLite (used in tests) drops tzinfo from DateTime(timezone=True) columns.
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


async def gameweek_last_kickoff(db: AsyncSession, competition_id: int, gameweek: int) -> Optional[datetime]:
    res = await db.execute(
        select(func.max(Fixture.kickoff_time)).where(
            Fixture.competition_id == competition_id,
            Fixture.gameweek == gameweek,
        )
    )
    last = res.scalar_one_or_none()
    return as_utc(last) if last else None


async def is_active(db: AsyncSession, pool_id: int, user_id: int, gameweek: int) -> bool:
    res = await db.execute(
        select(DoubleWeek.id).where(
            DoubleWeek.pool_id == pool_id,
            DoubleWeek.user_id == user_id,
            DoubleWeek.gameweek == gameweek,
        )
    )
    return res.first() is not None


async def active_gameweeks(db: AsyncSession, pool_id: int, user_id: int) -> List[int]:
    res = await db.execute(
        select(DoubleWeek.gameweek)
        .where(DoubleWeek.pool_id == pool_id, DoubleWeek.user_id == user_id)
        .order_by(DoubleWeek.gameweek)
    )
    return [row[0] for row in res.all()]


async def max_used_in_pool(db: AsyncSession, pool_id: int) -> int:
    """The most double weeks any single member of this pool has used."""
    res = await db.execute(
        select(func.count(DoubleWeek.id))
        .where(DoubleWeek.pool_id == pool_id)
        .group_by(DoubleWeek.user_id)
    )
    counts = [row[0] for row in res.all()]
    return max(counts, default=0)


async def gameweek_picks(db: AsyncSession, pool_id: int, user_id: int, gameweek: int) -> List[Tuple[Pick, Fixture]]:
    """A member's picks for one gameweek in a pool, oldest first."""
    res = await db.execute(
        select(Pick, Fixture)
        .join(Fixture, Fixture.id == Pick.fixture_id)
        .where(Pick.pool_id == pool_id, Pick.user_id == user_id, Fixture.gameweek == gameweek)
        .order_by(Pick.created_at, Pick.id)
    )
    return list(res.all())


async def double_pick_keys(db: AsyncSession, pool_id: int) -> set:
    """(user_id, gameweek) pairs in this pool where a double week was played."""
    res = await db.execute(select(DoubleWeek.user_id, DoubleWeek.gameweek).where(DoubleWeek.pool_id == pool_id))
    return {(u, gw) for u, gw in res.all()}


async def release_unused(db: AsyncSession, competition_id: int, gameweek: int) -> int:
    """Once a gameweek's picking window has closed, give back any double
    week that ended up with fewer than two picks - switching one on and
    then only picking once shouldn't cost the member their double week."""
    res = await db.execute(
        select(DoubleWeek)
        .join(Pool, Pool.id == DoubleWeek.pool_id)
        .where(Pool.competition_id == competition_id, DoubleWeek.gameweek == gameweek)
    )
    released = 0
    for dw in res.scalars().all():
        if len(await gameweek_picks(db, dw.pool_id, dw.user_id, gameweek)) < 2:
            await db.delete(dw)
            released += 1
    return released
