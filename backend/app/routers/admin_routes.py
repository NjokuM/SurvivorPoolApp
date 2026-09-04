from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.pool import Pool
from app.models.pick import Pick
from app.models.competiton_data import Fixture
from app.crud.pool_crud import get_pool_user_stats
from app.dependencies.admin import require_pool_admin
from app.dependencies.security import verify_cron
from app.schemas.pick_schema import AdminPicksImportRequest, AdminPicksImportResponse
from app.services.results import process_gameweek_results

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
    existing_by_gameweek: Dict[int, Pick] = {gw: pick for pick, gw in existing_res.all()}

    earliest_gameweek = pool.start_gameweek
    applied = 0

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

        earliest_gameweek = min(earliest_gameweek, fixture.gameweek)

        existing = existing_by_gameweek.get(fixture.gameweek)
        if existing:
            existing.fixture_id = fixture.id
            existing.team_id = entry.team_id
            existing.source = "admin"
        else:
            new_pick = Pick(
                pool_id=pool_id, user_id=user_id,
                team_id=entry.team_id, fixture_id=fixture.id,
                competition_id=pool.competition_id, source="admin",
            )
            db.add(new_pick)
            existing_by_gameweek[fixture.gameweek] = new_pick
        applied += 1

    # Blanket-reset every pick for this pool/user - not just the ones just
    # touched - so the replay below recomputes the user's full history
    # consistently. Anything left unchanged will simply come back to the
    # same result it already had.
    for pick in existing_by_gameweek.values():
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