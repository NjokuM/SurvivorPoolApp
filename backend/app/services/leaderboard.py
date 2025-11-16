# app/services/leaderboard.py

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.pool import PoolUserStats
from app.models.user import User


async def get_leaderboard(db: AsyncSession, pool_id: int) -> List[Dict[str, Any]]:
    """
    Returns the leaderboard for a pool, sorted by:
        1. lives_left (desc)
        2. total_points (desc)
        3. eliminated_gameweek (NULL first)
        4. user_id (asc)

    Also returns rank numbers *with ties skipping ranks*.
    """

    # BUILD THE SQL QUERY 
    stmt = (
        select(
            PoolUserStats,
            User.userName,
            User.firstName,
            User.lastName
        )
        .join(User, User.id == PoolUserStats.user_id)
        .where(PoolUserStats.pool_id == pool_id)
    )

    # EXECUTE QUERY
    res = await db.execute(stmt)
    rows = res.all()  # List of (PoolUserStats, firstname, lastname)

    # CONVERT ROWS → PYTHON DICTIONARIES
    data = []
    for stats, username, firstName, lastName in rows:
        data.append({
            "user_id": stats.user_id,
            "username": username,
            "firstname": firstName,
            "lastname": lastName,
            "lives_left": stats.lives_left,
            "total_points": stats.total_points,
            "eliminated_gameweek": stats.eliminated_gameweek,
            "is_eliminated": (
                stats.lives_left == 0 and stats.eliminated_gameweek is not None
            )
        })

    # SORT LEADERBOARD
    data.sort(
        key=lambda x: (
            -x["lives_left"],                    # highest lives first
            -x["total_points"],                  # then highest points
            x["eliminated_gameweek"]
            if x["eliminated_gameweek"] is not None
            else -9999,                          # alive players sort before eliminated
            x["user_id"]                         # stable ordering
        )
    )

    # ASSIGN RANKS (ties skip)
    for i, row in enumerate(data):
        if i == 0:
            row["rank"] = 1
            continue

        prev = data[i - 1]

        # same lives & points = same rank
        if (
            row["lives_left"] == prev["lives_left"] and
            row["total_points"] == prev["total_points"]
        ):
            row["rank"] = prev["rank"]
        else:
            row["rank"] = i + 1

    return data