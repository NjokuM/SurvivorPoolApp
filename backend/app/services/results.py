# app/services/results_processor.py

from typing import Dict, Tuple, List, Iterable
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.competiton_data import Fixture
from app.models.pick import Pick, PickResultEnum
from app.models.pool import Pool, PoolUserStats

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
async def _load_gameweek_fixtures(db: AsyncSession, competition_id: int, gameweek: int) -> List[Fixture]:
    """Load every fixture for a competition + gameweek, regardless of status."""
    res = await db.execute(
        select(Fixture).where(
            Fixture.competition_id == competition_id,
            Fixture.gameweek == gameweek,
        )
    )
    return res.scalars().all()


async def _load_active_pools(db: AsyncSession, competition_id: int) -> List[Pool]:
    """Load active pools for a competition (missed-pick penalties don't apply to deleted pools)."""
    res = await db.execute(
        select(Pool).where(
            Pool.competition_id == competition_id,
            Pool.is_active == True,
        )
    )
    return res.scalars().all()


async def _load_pool_user_stats(db: AsyncSession, pool_id: int) -> List[PoolUserStats]:
    """Load every member's stats row for a pool."""
    res = await db.execute(select(PoolUserStats).where(PoolUserStats.pool_id == pool_id))
    return res.scalars().all()


async def _load_pools_by_ids(db: AsyncSession, pool_ids: Iterable[int]) -> Dict[int, Pool]:
    """Load pools keyed by id, so callers can check has_lives without a query per row."""
    pool_ids = list(pool_ids)
    if not pool_ids:
        return {}
    res = await db.execute(select(Pool).where(Pool.id.in_(pool_ids)))
    return {p.id: p for p in res.scalars().all()}


async def _users_with_a_pick(db: AsyncSession, pool_id: int, fixture_ids: Iterable[int]) -> set:
    """User ids in this pool who already have a Pick (any result, including a
    prior NP record) tied to one of these fixtures - i.e. who aren't missing."""
    fixture_ids = list(fixture_ids)
    if not fixture_ids:
        return set()
    res = await db.execute(
        select(Pick.user_id).where(
            Pick.pool_id == pool_id,
            Pick.fixture_id.in_(fixture_ids),
        )
    )
    return {row[0] for row in res.all()}


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
# 3b. MISSED PICK DETECTION
# ------------------------------------------------------------
async def _detect_missed_picks(
    db: AsyncSession,
    competition_id: int,
    gameweek: int,
    gameweek_fixtures: List[Fixture],
) -> Dict:
    """
    Find pool members who never submitted a pick for this gameweek and
    create an NP ("No Pick") record for each - which both penalizes them
    (one life, same as a loss) and makes future runs idempotent, since the
    NP record itself counts as "has a pick" on the next pass.

    Returns an accum dict in the same shape _evaluate_picks produces, so
    _apply_stats_updates can handle real losses and missed picks uniformly.
    """
    accum = {}
    fixture_ids = [f.id for f in gameweek_fixtures]
    # Attach the NP record to the gameweek's last kickoff - callers only
    # invoke this once that kickoff has passed, since a user can pick any
    # not-yet-started fixture in the gameweek right up until then.
    representative_fixture = max(gameweek_fixtures, key=lambda f: f.kickoff_time)

    pools = await _load_active_pools(db, competition_id)
    for pool in pools:
        if pool.start_gameweek > gameweek:
            continue  # pool didn't exist yet for this gameweek

        already_picked = await _users_with_a_pick(db, pool.id, fixture_ids)
        stats_list = await _load_pool_user_stats(db, pool.id)

        for stats in stats_list:
            if stats.user_id in already_picked:
                continue
            if stats.lives_left <= 0:
                continue  # already eliminated - nothing left to penalize

            db.add(Pick(
                pool_id=pool.id,
                user_id=stats.user_id,
                team_id=None,
                fixture_id=representative_fixture.id,
                competition_id=competition_id,
                result=PickResultEnum.NP,
                points=0,
            ))

            key = (pool.id, stats.user_id)
            bucket = accum.setdefault(key, {"points": 0, "losses": 0})
            bucket["losses"] += 1

    return accum


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
    pools_by_id = await _load_pools_by_ids(db, (pool_id for pool_id, _ in accum.keys()))

    for (pool_id, user_id), data in accum.items():
        stats = await _load_pool_stats(db, pool_id, user_id)
        if not stats:
            continue

        # Add points
        stats.total_points = (stats.total_points or 0) + data["points"]

        pool = pools_by_id.get(pool_id)
        if pool is not None and not pool.has_lives:
            # League mode: points only, no elimination - a loss or missed
            # pick still costs the points, but never touches lives_left.
            continue

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

    A pick can be for any fixture in the gameweek that hasn't kicked off yet
    (not just the first one), so the two halves of this run on different
    clocks:
    - Point crediting scores each submitted pick independently, as soon as
      its own fixture is FT - no need to wait for the rest of the gameweek.
    - Missed-pick detection only runs once the gameweek's *last* fixture has
      kicked off, since only then is it certain no more picks can arrive.
    """
    summary = {"picks_processed": 0, "points_awarded": 0, "lives_deducted": 0}

    gameweek_fixtures = await _load_gameweek_fixtures(db, competition_id, gameweek)
    if not gameweek_fixtures:
        return summary

    fixtures_by_id = {f.id: f for f in gameweek_fixtures}

    # Compute results for picks that were actually submitted
    picks = await _load_unprocessed_picks(db, fixtures_by_id.keys())
    res = _evaluate_picks(picks, fixtures_by_id)
    summary["picks_processed"] = res["picks_processed"]
    summary["points_awarded"] = res["total_points"]
    accum = res["accum"]

    # Fold in anyone who never picked at all - but only once the picking
    # window has definitively closed.
    last_kickoff = max(f.kickoff_time for f in gameweek_fixtures)
    if datetime.now(timezone.utc) >= last_kickoff:
        missed_accum = await _detect_missed_picks(db, competition_id, gameweek, gameweek_fixtures)
        for key, data in missed_accum.items():
            bucket = accum.setdefault(key, {"points": 0, "losses": 0})
            bucket["points"] += data["points"]
            bucket["losses"] += data["losses"]

    if not accum:
        return summary

    # Apply writes atomically
    await db.flush()  # persist pick updates + new NP records
    summary["lives_deducted"] = await _apply_stats_updates(
        db=db,
        gameweek=gameweek,
        accum=accum,
        allow_eliminated_to_play=allow_eliminated_to_play,
        apply_decrements_for_eliminated=apply_decrements_for_eliminated
    )
    await db.commit()
    return summary