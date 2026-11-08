from collections import defaultdict
from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from app.database import get_db
from app.models.pool import Pool, DoubleWeek
from app.models.pick import Pick
from app.models.competiton_data import Fixture
from app.crud.pool_crud import get_pool_user_stats
from app.dependencies.admin import require_pool_admin
from app.dependencies.security import verify_cron
from app.schemas.pick_schema import AdminPicksImportRequest, AdminPicksImportResponse
from app.services.results import process_gameweek_results, recompute_all_pool_statuses
from app.services import double_weeks

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/process-results/{competition_id}/{gameweek}", dependencies=[Depends(verify_cron)])
async def process_results(
    competition_id: int,
    gameweek: int,
    db: AsyncSession = Depends(get_db)
):
    summary = await process_gameweek_results(
        db=db,
        competition_id=competition_id,
        gameweek=gameweek,
        allow_eliminated_to_play=True,
        apply_decrements_for_eliminated=False
    )
    return summary


@router.post("/recompute-pool-status", dependencies=[Depends(verify_cron)])
async def recompute_pool_status(db: AsyncSession = Depends(get_db)):
    """One-off/backfill trigger: re-check every active pool against the
    archiving criteria (season concluded, or a lives pool already decided).
    Normally this happens automatically as each gameweek is processed -
    this exists to catch pools whose season concluded before that logic
    existed, or where a gameweek had nothing to process and the automatic
    check never ran."""
    archived = await recompute_all_pool_statuses(db)
    return {"pools_archived": archived}


@router.put("/pools/{pool_id}/users/{user_id}/picks", response_model=AdminPicksImportResponse)
async def admin_set_user_picks(
    pool_id: int,
    user_id: int,
    body: AdminPicksImportRequest,
    pool: Pool = Depends(require_pool_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Add or correct a user's picks for this pool - the intended path for
    migrating a pool's pre-app history, or fixing a mistake in an
    already-scored pick. Only the pool's creator (verified via JWT) can
    call this.

    Picks for gameweeks not included in `body.picks` are left as-is. Every
    pick belonging to this user in this pool - touched or not - is then
    replayed gameweek-by-gameweek through the normal results pipeline, so
    lives/points/elimination come out exactly as if it had all happened
    live: untouched weeks recompute to the same result they already had
    (the underlying fixture data hasn't changed), and any gameweek left
    with no pick at all correctly becomes a missed pick. This avoids ever
    having to hand-reverse a previously-applied points/life delta, which is
    error-prone once elimination is involved.
    """
    stats = await get_pool_user_stats(db, pool_id, user_id)
    if not stats:
        raise HTTPException(status_code=400, detail="User is not a member of this pool")

    existing_res = await db.execute(
        select(Pick, Fixture.gameweek)
        .join(Fixture, Fixture.id == Pick.fixture_id)
        .where(Pick.pool_id == pool_id, Pick.user_id == user_id)
    )
    # A gameweek can hold two picks if a double week was played.
    existing_by_gameweek: Dict[int, List[Pick]] = defaultdict(list)
    for pick, gw in existing_res.all():
        existing_by_gameweek[gw].append(pick)

    # Validate every entry first, grouped by gameweek.
    entries_by_gameweek: Dict[int, List] = defaultdict(list)
    for entry in body.picks:
        fixture_res = await db.execute(select(Fixture).where(Fixture.id == entry.fixture_id))
        fixture = fixture_res.scalar_one_or_none()
        if not fixture:
            raise HTTPException(status_code=404, detail=f"Fixture {entry.fixture_id} not found")
        if fixture.competition_id != pool.competition_id:
            raise HTTPException(
                status_code=400,
                detail=f"Fixture {entry.fixture_id} does not belong to this pool's competition",
            )
        if entry.team_id not in (fixture.home_team_id, fixture.away_team_id):
            raise HTTPException(
                status_code=400,
                detail=f"Team {entry.team_id} is not playing in fixture {entry.fixture_id}",
            )
        entries_by_gameweek[fixture.gameweek].append((entry, fixture))

    active_double_weeks = set(await double_weeks.active_gameweeks(db, pool_id, user_id))
    for gw, entries in entries_by_gameweek.items():
        if len(entries) > 2:
            raise HTTPException(status_code=400, detail=f"Gameweek {gw} can have at most two picks")
        if len(entries) == 2:
            if pool.has_lives:
                raise HTTPException(status_code=400, detail="Double weeks are only available in points-only pools")
            if entries[0][1].id == entries[1][1].id:
                raise HTTPException(status_code=400, detail=f"Gameweek {gw}'s two picks must be from different matches")
            if gw not in active_double_weeks:
                if len(active_double_weeks) >= pool.double_weeks:
                    raise HTTPException(status_code=400, detail="This member has no double weeks left")
                active_double_weeks.add(gw)

    earliest_gameweek = pool.start_gameweek
    applied = 0

    # Each gameweek mentioned is replaced wholesale with the given picks.
    for gw, entries in entries_by_gameweek.items():
        earliest_gameweek = min(earliest_gameweek, gw)
        for old in existing_by_gameweek.pop(gw, []):
            await db.delete(old)
        await db.flush()  # free the (pool, user, fixture) slot before re-adding

        await db.execute(delete(DoubleWeek).where(
            DoubleWeek.pool_id == pool_id, DoubleWeek.user_id == user_id, DoubleWeek.gameweek == gw,
        ))
        if len(entries) == 2:
            db.add(DoubleWeek(pool_id=pool_id, user_id=user_id, gameweek=gw))

        for entry, fixture in entries:
            db.add(Pick(
                pool_id=pool_id, user_id=user_id,
                team_id=entry.team_id, fixture_id=fixture.id,
                competition_id=pool.competition_id, source="admin",
            ))
            applied += 1

    # Blanket-reset every other pick for this pool/user - not just the ones
    # just touched - so the replay below recomputes the user's full history
    # consistently. Anything left unchanged will simply come back to the
    # same result it already had.
    for gw_picks in existing_by_gameweek.values():
        for pick in gw_picks:
            pick.result = None
            pick.points = 0
            pick.home_score = None
            pick.away_score = None

    stats.lives_left = pool.total_lives
    stats.total_points = 0
    stats.eliminated_gameweek = None

    if earliest_gameweek < pool.start_gameweek:
        pool.start_gameweek = earliest_gameweek

    await db.commit()

    max_gw_res = await db.execute(
        select(func.max(Fixture.gameweek)).where(
            Fixture.competition_id == pool.competition_id,
            Fixture.status == "FT",
        )
    )
    max_finished_gameweek = max_gw_res.scalar_one()

    gameweeks_replayed: List[int] = []
    if max_finished_gameweek is not None:
        for gw in range(pool.start_gameweek, max_finished_gameweek + 1):
            await process_gameweek_results(db, pool.competition_id, gw)
            gameweeks_replayed.append(gw)

    await db.refresh(stats)
    return AdminPicksImportResponse(
        pool_id=pool_id,
        user_id=user_id,
        start_gameweek=pool.start_gameweek,
        lives_left=stats.lives_left,
        total_points=stats.total_points,
        eliminated_gameweek=stats.eliminated_gameweek,
        picks_applied=applied,
        gameweeks_replayed=gameweeks_replayed,
    )