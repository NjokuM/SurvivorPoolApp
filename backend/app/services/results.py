# app/services/results_processor.py

from typing import Dict, Tuple, List, Iterable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.competiton_data import Fixture
from app.models.pick import Pick
from app.models.pool import PoolUserStats

POINTS_FOR_WIN = 3
POINTS_FOR_DRAW = 1
POINTS_FOR_LOSS = 0


# ------------------------------------------------------------
# 1. PURE LOGIC — COMPUTE RESULT FOR ONE PICK
# ------------------------------------------------------------
def _compute_pick_result_and_points(pick_team_id: int, fixture: Fixture) -> Tuple[str, int]:
    """Given a user's picked team and a finished fixture, compute win/draw/loss + points."""
    if fixture.status != "FT":
        return ("PENDING", 0)

    if fixture.home_goals > fixture.away_goals:
        winning_team = fixture.home_team_id
    elif fixture.away_goals > fixture.home_goals:
        winning_team = fixture.away_team_id
    else:
        return ("DRAW", POINTS_FOR_DRAW)

    if pick_team_id == winning_team:
        return ("WIN", POINTS_FOR_WIN)
    return ("LOSS", POINTS_FOR_LOSS)


# ------------------------------------------------------------
# 2. DATA FETCH HELPERS
# ------------------------------------------------------------
async def _load_finished_fixtures(db: AsyncSession, competition_id: int, gameweek: int) -> List[Fixture]:
    """Load all finished fixtures for a competition + gameweek."""
    res = await db.execute(
        select(Fixture).where(
            Fixture.competition_id == competition_id,
            Fixture.gameweek == gameweek,
            Fixture.status == "FT"
        )
    )
    return res.scalars().all()


async def _load_unprocessed_picks(db: AsyncSession, fixture_ids: Iterable[int]) -> List[Pick]:
    """Load all picks where result is still NULL and fixture is finished."""
    if not fixture_ids:
        return []

    res = await db.execute(
        select(Pick).where(
            Pick.fixture_id.in_(fixture_ids),
            Pick.result == None
        )
    )
    return res.scalars().all()


async def _load_pool_stats(db: AsyncSession, pool_id: int, user_id: int) -> PoolUserStats:
    """Fetch a single PoolUserStats row for a given user."""
    res = await db.execute(
        select(PoolUserStats).where(
            PoolUserStats.pool_id == pool_id,
            PoolUserStats.user_id == user_id,
        )
    )
    return res.scalars().first()


# ------------------------------------------------------------
# 3. PROCESSING HELPERS (PURE DATA)
# ------------------------------------------------------------
def _evaluate_picks(picks: List[Pick], fixtures_by_id: Dict[int, Fixture]) -> Dict:
    """
    Compute pick results + build aggregation data.
    Returns:
        {
            "picks": updated pick objects,
            "accum": { (pool_id, user_id): {"points": int, "losses": int} }
        }
    """
    accum = {}
    processed_count = 0
    total_points = 0

    for pick in picks:
        fixture = fixtures_by_id[pick.fixture_id]
        result, points = _compute_pick_result_and_points(pick.team_id, fixture)

        if result == "PENDING":
            continue  # fixture not final

        # Update pick object
        pick.result = result
        pick.points = points
        pick.home_score = fixture.home_goals
        pick.away_score = fixture.away_goals

        # Aggregate per pool+user
        key = (pick.pool_id, pick.user_id)
        bucket = accum.setdefault(key, {"points": 0, "losses": 0})
        bucket["points"] += points
        if result == "LOSS":
            bucket["losses"] += 1

        processed_count += 1
        total_points += points

    return {
        "picks_processed": processed_count,
        "total_points": total_points,
        "accum": accum
    }


# ------------------------------------------------------------
# 4. APPLY DATABASE UPDATES
# ------------------------------------------------------------
async def _apply_stats_updates(
    db: AsyncSession,
    gameweek: int,
    accum: Dict,
    allow_eliminated_to_play: bool,
    apply_decrements_for_eliminated: bool
):
    """Apply aggregated stats (points + life deductions) to PoolUserStats."""
    lives_deducted = 0

    for (pool_id, user_id), data in accum.items():
        stats = await _load_pool_stats(db, pool_id, user_id)
        if not stats:
            continue

        # Add points
        stats.total_points = (stats.total_points or 0) + data["points"]

        # Handle lives
        losses = data["losses"]

        if stats.lives_left > 0:
            new_lives = max(0, stats.lives_left - losses)
            lives_deducted += stats.lives_left - new_lives
            stats.lives_left = new_lives

            if new_lives == 0 and stats.eliminated_gameweek is None:
                stats.eliminated_gameweek = gameweek

        else:
            # user already eliminated
            if apply_decrements_for_eliminated:
                new_lives = max(0, stats.lives_left - losses)
                lives_deducted += stats.lives_left - new_lives
                stats.lives_left = new_lives
            # otherwise, do nothing

    await db.flush()
    await db.commit()
    return lives_deducted


# ------------------------------------------------------------
# 5. MAIN PIPELINE
# ------------------------------------------------------------
async def process_gameweek_results(
    db: AsyncSession,
    competition_id: int,
    gameweek: int,
    *,
    allow_eliminated_to_play: bool = False,
    apply_decrements_for_eliminated: bool = False
) -> Dict[str, int]:
    """
    Clean, readable and fully idempotent results processor.
    """
    summary = {"picks_processed": 0, "points_awarded": 0, "lives_deducted": 0}

    fixtures = await _load_finished_fixtures(db, competition_id, gameweek)
    if not fixtures:
        return summary

    fixtures_by_id = {f.id: f for f in fixtures}

    picks = await _load_unprocessed_picks(db, fixtures_by_id.keys())
    if not picks:
        return summary

    # Compute results for all picks
    res = _evaluate_picks(picks, fixtures_by_id)
    summary["picks_processed"] = res["picks_processed"]
    summary["points_awarded"] = res["total_points"]

    # Apply writes atomically
    await db.flush()  # update picks
    summary["lives_deducted"] = await _apply_stats_updates(
        db=db,
        gameweek=gameweek,
        accum=res["accum"],
        allow_eliminated_to_play=allow_eliminated_to_play,
        apply_decrements_for_eliminated=apply_decrements_for_eliminated
    )
    await db.commit()
    return summary