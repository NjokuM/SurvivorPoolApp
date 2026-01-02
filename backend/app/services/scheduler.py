# app/services/scheduler.py
"""
Smart fixture sync and pick processing scheduler.
Minimizes API calls by only checking when games are actually happening.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, distinct
from app.models.competiton_data import Fixture, Competition
from app.models.pool import Pool
from app.services.results import process_gameweek_results
from app.services.football_api import update_fixtures_from_api
from app.schemas.competition_schema import FixtureFilters


# ------------------------------------------------------------
# 1. GET ACTIVE LEAGUES (only leagues with pools)
# ------------------------------------------------------------
async def get_active_competition_ids(db: AsyncSession) -> List[int]:
    """
    Returns competition IDs that have at least one active pool.
    This ensures we only sync leagues that users actually care about.
    """
    result = await db.execute(
        select(distinct(Pool.competition_id)).where(Pool.competition_id.isnot(None))
    )
    return [row[0] for row in result.all()]


# ------------------------------------------------------------
# 2. CHECK IF ANY GAMES ARE FINISHING SOON
# ------------------------------------------------------------
async def get_fixtures_finishing_soon(
    db: AsyncSession,
    competition_ids: List[int],
    window_hours: int = 2
) -> List[Fixture]:
    """
    Find fixtures that:
    - Belong to active competitions
    - Started within the last 3 hours (covers kickoff to full-time + buffer)
    - Haven't been processed yet (status != 'FT' in our DB)
    
    This tells us if we need to make an API call.
    """
    # Use timezone-aware datetime to match DB kickoff_time format
    now = datetime.now(timezone.utc)
    # Check games that kicked off in the last 3 hours (covers full match + extra time)
    earliest_kickoff = now - timedelta(hours=3)
    
    result = await db.execute(
        select(Fixture).where(
            Fixture.competition_id.in_(competition_ids),
            Fixture.kickoff_time >= earliest_kickoff,
            Fixture.kickoff_time <= now,
            Fixture.status != "FT"  # Not yet marked as finished
        )
    )
    return result.scalars().all()


async def get_fixtures_in_progress(
    db: AsyncSession,
    competition_ids: List[int],
) -> List[Fixture]:
    """
    Find fixtures currently in progress (kicked off within last 3 hours, not finished).
    """
    now = datetime.now(timezone.utc)
    three_hours_ago = now - timedelta(hours=3)
    
    result = await db.execute(
        select(Fixture).where(
            Fixture.competition_id.in_(competition_ids),
            Fixture.kickoff_time >= three_hours_ago,
            Fixture.kickoff_time <= now,
            Fixture.status.notin_(["FT", "PST", "CANC", "ABD"])
        )
    )
    return result.scalars().all()


# ------------------------------------------------------------
# 3. SMART SYNC - Only sync when needed
# ------------------------------------------------------------
async def smart_sync_and_process(db: AsyncSession) -> Dict:
    """
    Main scheduler function. Call this every 15-30 mins.
    It will only make API calls when games are actually finishing.
    
    Returns immediately and processes in background if games are found.
    """
    import asyncio
    from app.database import async_session
    
    # 1. Get active leagues only
    active_comp_ids = await get_active_competition_ids(db)
    
    if not active_comp_ids:
        return {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "active_leagues": 0,
            "fixtures_to_check": 0,
            "status": "skipped",
            "message": "No active pools, nothing to do"
        }
    
    # 2. Check if any games are in progress or finishing soon
    fixtures_to_check = await get_fixtures_finishing_soon(db, active_comp_ids)
    
    if not fixtures_to_check:
        return {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "active_leagues": len(active_comp_ids),
            "fixtures_to_check": 0,
            "status": "skipped",
            "message": "No games in progress, skipping API call"
        }
    
    # 3. Group fixtures by competition
    comps_to_sync = list(set(f.competition_id for f in fixtures_to_check))
    
    # Background task for sync and processing
    async def background_sync_and_process():
        async with async_session() as bg_db:
            for comp_id in comps_to_sync:
                comp_result = await bg_db.execute(
                    select(Competition).where(Competition.id == comp_id)
                )
                comp = comp_result.scalars().first()
                if not comp:
                    continue
                    
                # Sync fixtures for this competition
                filters = FixtureFilters(league=comp.external_id, season=comp.season)
                try:
                    await update_fixtures_from_api(bg_db, filters)
                    print(f"Synced fixtures for {comp.name}")
                except Exception as e:
                    print(f"Error syncing competition {comp_id}: {e}")
                    continue
                
                # Process picks for finished fixtures
                gw_result = await bg_db.execute(
                    select(distinct(Fixture.gameweek)).where(
                        Fixture.competition_id == comp_id,
                        Fixture.status == "FT"
                    )
                )
                gameweeks = [row[0] for row in gw_result.all()]
                
                for gw in gameweeks:
                    try:
                        await process_gameweek_results(bg_db, comp_id, gw)
                        print(f"Processed picks for {comp.name} GW{gw}")
                    except Exception as e:
                        print(f"Error processing picks for comp {comp_id} GW {gw}: {e}")
    
    # Fire and forget
    asyncio.create_task(background_sync_and_process())
    
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "active_leagues": len(active_comp_ids),
        "fixtures_to_check": len(fixtures_to_check),
        "competitions_queued": len(comps_to_sync),
        "status": "started",
        "message": f"Background sync started for {len(comps_to_sync)} competitions with {len(fixtures_to_check)} fixtures"
    }


# ------------------------------------------------------------
# 4. WEEKLY SCHEDULE REFRESH
# ------------------------------------------------------------
async def weekly_schedule_refresh(db: AsyncSession) -> Dict:
    """
    Run this once a week (e.g., Sunday night) to catch:
    - Rescheduled games
    - New fixtures added
    - Any changes to kickoff times
    
    Only syncs active leagues. Returns immediately and runs in background.
    """
    import asyncio
    from app.database import async_session
    
    # Get active competitions before spawning background task
    active_comp_ids = await get_active_competition_ids(db)
    
    if not active_comp_ids:
        return {
            "status": "skipped",
            "message": "No active competitions to refresh",
            "triggered_at": datetime.now(timezone.utc).isoformat(),
        }
    
    # Background task that runs independently
    async def background_refresh():
        leagues_synced = 0
        fixtures_updated = 0
        fixtures_inserted = 0
        errors = []
        
        async with async_session() as bg_db:
            for comp_id in active_comp_ids:
                comp_result = await bg_db.execute(
                    select(Competition).where(Competition.id == comp_id)
                )
                comp = comp_result.scalars().first()
                if not comp:
                    continue
                
                filters = FixtureFilters(league=comp.external_id, season=comp.season)
                try:
                    result = await update_fixtures_from_api(bg_db, filters)
                    leagues_synced += 1
                    fixtures_updated += result.get("updated", 0)
                    fixtures_inserted += result.get("inserted", 0)
                    print(f"✓ Refreshed {comp.name}: {result.get('updated', 0)} updated, {result.get('inserted', 0)} inserted")
                except Exception as e:
                    errors.append(f"{comp.name}: {str(e)}")
                    print(f"✗ Error refreshing {comp.name}: {e}")
        
        # Log completion summary
        print(f"\n{'='*50}")
        print(f"WEEKLY REFRESH COMPLETED")
        print(f"{'='*50}")
        print(f"Leagues synced: {leagues_synced}/{len(active_comp_ids)}")
        print(f"Fixtures updated: {fixtures_updated}")
        print(f"Fixtures inserted: {fixtures_inserted}")
        if errors:
            print(f"Errors: {len(errors)}")
            for err in errors:
                print(f"  - {err}")
        print(f"{'='*50}\n")
    
    # Fire and forget - don't await
    asyncio.create_task(background_refresh())
    
    return {
        "status": "started",
        "message": f"Background refresh started for {len(active_comp_ids)} leagues",
        "triggered_at": datetime.now(timezone.utc).isoformat(),
        "leagues_queued": len(active_comp_ids),
    }


# ------------------------------------------------------------
# 5. MANUAL TRIGGER ENDPOINTS (for testing/admin)
# ------------------------------------------------------------
async def force_process_competition_gameweek(
    db: AsyncSession,
    competition_id: int,
    gameweek: int
) -> Dict:
    """
    Manually trigger pick processing for a specific competition/gameweek.
    Useful for testing or catching up on missed processing.
    """
    return await process_gameweek_results(db, competition_id, gameweek)


# ------------------------------------------------------------
# 6. ON-DEMAND SYNC FOR NEW POOLS
# ------------------------------------------------------------
async def sync_competition_if_needed(
    db: AsyncSession,
    competition_id: int
) -> Optional[Dict]:
    """
    Called when a new pool is created.
    
    Checks if this competition already had pools (fixtures likely synced).
    If this is the FIRST pool for this competition, sync fixtures immediately.
    
    This handles the edge case where:
    - La Liga had no pools
    - User creates La Liga pool on Tuesday
    - Weekly refresh already ran Sunday
    - Without this, pool would have no/outdated fixtures
    """
    from app.models.pool import Pool
    
    # Check if there are OTHER pools for this competition
    result = await db.execute(
        select(Pool).where(Pool.competition_id == competition_id)
    )
    existing_pools = result.scalars().all()
    
    # If this is the first pool (or only 1 exists - the one just created), sync fixtures
    if len(existing_pools) <= 1:
        # Get competition details
        comp_result = await db.execute(
            select(Competition).where(Competition.id == competition_id)
        )
        comp = comp_result.scalars().first()
        
        if not comp:
            return {"message": "Competition not found", "synced": False}
        
        # Sync fixtures for this competition
        filters = FixtureFilters(league=comp.external_id, season=comp.season)
        try:
            sync_result = await update_fixtures_from_api(db, filters)
            return {
                "message": f"Synced fixtures for new competition {comp.name}",
                "synced": True,
                "updated": sync_result.get("updated", 0),
                "inserted": sync_result.get("inserted", 0),
            }
        except Exception as e:
            return {"message": f"Failed to sync: {str(e)}", "synced": False}
    
    return {"message": "Competition already has pools, fixtures likely up to date", "synced": False}
