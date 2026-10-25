# app/services/leaderboard.py

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.pool import Pool, PoolUserStats
from app.models.user import User
from app.models.pick import Pick, PickResultEnum
from app.models.competiton_data import Fixture, Team

SCORED_RESULTS = (PickResultEnum.WIN, PickResultEnum.DRAW, PickResultEnum.LOSS)


def pick_goal_difference(team_id: int, home_team_id: int, home_score: int, away_score: int) -> int:
    """Goal difference of a single pick, from the picked team's side."""
    if team_id == home_team_id:
        return home_score - away_score
    return away_score - home_score


async def get_goal_differences(db: AsyncSession, pool_id: int) -> Dict[int, int]:
    """
    Sum each member's goal difference across their scored picks.

    Derived from the picks themselves rather than stored on PoolUserStats,
    so it can never drift from the pick history - including after an admin
    reset+replay. Missed picks (NP) and unscored picks contribute nothing.
    """
    res = await db.execute(
        select(Pick.user_id, Pick.team_id, Pick.home_score, Pick.away_score, Fixture.home_team_id)
        .join(Fixture, Fixture.id == Pick.fixture_id)
        .where(
            Pick.pool_id == pool_id,
            Pick.result.in_(SCORED_RESULTS),
            Pick.home_score.is_not(None),
            Pick.away_score.is_not(None),
        )
    )
    totals: Dict[int, int] = {}
    for user_id, team_id, home_score, away_score, home_team_id in res.all():
        totals[user_id] = totals.get(user_id, 0) + pick_goal_difference(
            team_id, home_team_id, home_score, away_score
        )
    return totals


async def get_leaderboard(db: AsyncSession, pool_id: int) -> List[Dict[str, Any]]:
    """
    Returns the leaderboard for a pool, sorted by:
        1. lives_left (desc)
        2. total_points (desc)
        3. goal_difference (desc) - tiebreaker for equal points
        4. eliminated_gameweek (NULL first)
        5. user_id (asc)

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

    goal_differences = await get_goal_differences(db, pool_id)

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
            "goal_difference": goal_differences.get(stats.user_id, 0),
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
            -x["goal_difference"],               # then best goal difference
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

        # same lives, points & goal difference = same rank
        if (
            row["lives_left"] == prev["lives_left"] and
            row["total_points"] == prev["total_points"] and
            row["goal_difference"] == prev["goal_difference"]
        ):
            row["rank"] = prev["rank"]
        else:
            row["rank"] = i + 1

    return data

async def get_team_leaderboard(db: AsyncSession, pool: Pool) -> List[Dict[str, Any]]:
    """
    Rank every team in the pool's competition by the points this pool's
    players have earned picking them, sorted by:
        1. total_points (desc)
        2. goal_difference (desc)
        3. times_picked (desc)
        4. team name (asc)

    Teams nobody has picked yet are included with zeroes, so the list
    always covers the whole league.
    """
    teams_res = await db.execute(select(Team).where(Team.competition_id == pool.competition_id))
    data: Dict[int, Dict[str, Any]] = {
        team.id: {
            "team_id": team.id,
            "team_name": team.name,
            "short_name": team.short_name,
            "logo": team.logo,
            "total_points": 0,
            "goal_difference": 0,
            "times_picked": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
        }
        for team in teams_res.scalars().all()
    }

    picks_res = await db.execute(
        select(Pick.team_id, Pick.result, Pick.points, Pick.home_score, Pick.away_score, Fixture.home_team_id)
        .join(Fixture, Fixture.id == Pick.fixture_id)
        .where(Pick.pool_id == pool.id, Pick.team_id.is_not(None))
    )
    for team_id, result, points, home_score, away_score, home_team_id in picks_res.all():
        row = data.get(team_id)
        if row is None:
            continue
        row["times_picked"] += 1
        if result not in SCORED_RESULTS:
            continue  # still pending - counts as a pick, but nothing earned yet
        row["total_points"] += points or 0
        if home_score is not None and away_score is not None:
            row["goal_difference"] += pick_goal_difference(team_id, home_team_id, home_score, away_score)
        if result == PickResultEnum.WIN:
            row["wins"] += 1
        elif result == PickResultEnum.DRAW:
            row["draws"] += 1
        else:
            row["losses"] += 1

    rows = sorted(
        data.values(),
        key=lambda x: (-x["total_points"], -x["goal_difference"], -x["times_picked"], x["team_name"]),
    )

    # ASSIGN RANKS (ties on points + goal difference share a rank)
    for i, row in enumerate(rows):
        prev = rows[i - 1] if i else None
        if prev and (row["total_points"], row["goal_difference"]) == (prev["total_points"], prev["goal_difference"]):
            row["rank"] = prev["rank"]
        else:
            row["rank"] = i + 1

    return rows


async def get_team_picks(db: AsyncSession, pool: Pool, team: Team) -> List[Dict[str, Any]]:
    """Every pick of `team` in this pool - who picked it, which gameweek,
    the opponent and score, and the points it earned. Newest first."""
    res = await db.execute(
        select(Pick, Fixture, User.userName)
        .join(Fixture, Fixture.id == Pick.fixture_id)
        .join(User, User.id == Pick.user_id)
        .options(selectinload(Fixture.home_team), selectinload(Fixture.away_team))
        .where(Pick.pool_id == pool.id, Pick.team_id == team.id)
    )

    picks = []
    for pick, fixture, username in res.all():
        is_home = fixture.home_team_id == team.id
        opponent = fixture.away_team if is_home else fixture.home_team
        scored = pick.result in SCORED_RESULTS
        # Prefer the score frozen on the pick when it was scored; fall back to
        # the fixture's live score for picks that haven't been processed yet.
        home_goals = pick.home_score if scored else fixture.home_goals
        away_goals = pick.away_score if scored else fixture.away_goals
        has_score = home_goals is not None and away_goals is not None
        picks.append({
            "pick_id": pick.id,
            "user_id": pick.user_id,
            "username": username,
            "gameweek": fixture.gameweek,
            "kickoff_time": fixture.kickoff_time,
            "is_home": is_home,
            "opponent_id": opponent.id if opponent else None,
            "opponent_name": opponent.name if opponent else None,
            "opponent_logo": opponent.logo if opponent else None,
            "team_goals": (home_goals if is_home else away_goals) if has_score else None,
            "opponent_goals": (away_goals if is_home else home_goals) if has_score else None,
            "result": pick.result.value if scored else None,
            "points": (pick.points or 0) if scored else 0,
        })

    picks.sort(key=lambda p: (-p["gameweek"], p["username"].lower()))
    return picks
