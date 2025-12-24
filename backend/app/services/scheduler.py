# app/services/scheduler.py
"""
Smart fixture sync and pick processing scheduler.
Minimizes API calls by only checking when games are actually happening.
"""

from datetime import datetime, timedelta
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
    - Started 90-150 mins ago (likely finishing soon or just finished)
    - Haven't been processed yet (status != 'FT' in our DB)
    
    This tells us if we need to make an API call.
    """
    now = datetime.utcnow()
    # Games that kicked off 90-150 mins ago are likely finishing
    earliest_kickoff = now - timedelta(minutes=150)
    latest_kickoff = now - timedelta(minutes=75)
    
    result = await db.execute(
        select(Fixture).where(
            Fixture.competition_id.in_(competition_ids),
            Fixture.kickoff_time >= earliest_kickoff,
            Fixture.kickoff_time <= latest_kickoff,
            Fixture.status != "FT"  # Not yet marked as finished
        )
    )
    return result.scalars().all()


async def get_fixtures_in_progress(
    db: AsyncSession,
    competition_ids: List[int],
) -> List[Fixture]:
    """
    Find fixtures currently in progress (kicked off within last 2 hours, not finished).
    """
    now = datetime.utcnow()
    two_hours_ago = now - timedelta(hours=2)
    
    result = await db.execute(
        select(Fixture).where(
            Fixture.competition_id.in_(competition_ids),
            Fixture.kickoff_time >= two_hours_ago,
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
    
    Returns summary of what was done.
    """
    summary = {
        "checked_at": datetime.utcnow().isoformat(),
        "active_leagues": 0,
        "fixtures_to_check": 0,
        "api_calls_made": 0,
        "fixtures_updated": 0,
        "picks_processed": 0,
        "lives_deducted": 0,
    }
    
    # 1. Get active leagues only
    active_comp_ids = await get_active_competition_ids(db)
    summary["active_leagues"] = len(active_comp_ids)
    
    if not active_comp_ids:
        summary["message"] = "No active pools, nothing to do"
        return summary
    
    # 2. Check if any games are finishing soon
    fixtures_to_check = await get_fixtures_finishing_soon(db, active_comp_ids)
    summary["fixtures_to_check"] = len(fixtures_to_check)
    
    if not fixtures_to_check:
        summary["message"] = "No games finishing soon, skipping API call"
        return summary
    
    # 3. Group fixtures by competition to minimize API calls
    comps_to_sync = set(f.competition_id for f in fixtures_to_check)
    
    for comp_id in comps_to_sync:
        # Get competition details for API call
        comp_result = await db.execute(
            select(Competition).where(Competition.id == comp_id)
        )
        comp = comp_result.scalars().first()
        if not comp:
            continue
            
        # Sync fixtures for this competition
        filters = FixtureFilters(league=comp.external_id, season=comp.season)
        try:
            sync_result = await update_fixtures_from_api(db, filters)
            summary["api_calls_made"] += 1
            summary["fixtures_updated"] += sync_result.get("updated", 0)
        except Exception as e:
            print(f"Error syncing competition {comp_id}: {e}")
            continue
        
        # 4. Process picks for any newly finished fixtures
        # Get all gameweeks that might have finished fixtures
        gw_result = await db.execute(
            select(distinct(Fixture.gameweek)).where(
                Fixture.competition_id == comp_id,
                Fixture.status == "FT"
            )
        )
        gameweeks = [row[0] for row in gw_result.all()]
        
        for gw in gameweeks:
            try:
                pick_result = await process_gameweek_results(db, comp_id, gw)
                summary["picks_processed"] += pick_result.get("picks_processed", 0)
                summary["lives_deducted"] += pick_result.get("lives_deducted", 0)
            except Exception as e:
                print(f"Error processing picks for comp {comp_id} GW {gw}: {e}")
    
    summary["message"] = f"Synced {summary['api_calls_made']} leagues, processed {summary['picks_processed']} picks"
    return summary


# ------------------------------------------------------------
# 4. WEEKLY SCHEDULE REFRESH
# ------------------------------------------------------------
async def weekly_schedule_refresh(db: AsyncSession) -> Dict:
    """
    Run this once a week (e.g., Sunday night) to catch:
    - Rescheduled games
    - New fixtures added
    - Any changes to kickoff times
    
    Only syncs active leagues.
    """
    summary = {
        "refreshed_at": datetime.utcnow().isoformat(),
        "leagues_synced": 0,
        "fixtures_updated": 0,
        "fixtures_inserted": 0,
    }
    
    active_comp_ids = await get_active_competition_ids(db)
    
    for comp_id in active_comp_ids:
        comp_result = await db.execute(
            select(Competition).where(Competition.id == comp_id)
        )
        comp = comp_result.scalars().first()
        if not comp:
            continue
        
        filters = FixtureFilters(league=comp.external_id, season=comp.season)
        try:
            sync_result = await update_fixtures_from_api(db, filters)
            summary["leagues_synced"] += 1
            summary["fixtures_updated"] += sync_result.get("updated", 0)
            summary["fixtures_inserted"] += sync_result.get("inserted", 0)
        except Exception as e:
            print(f"Error refreshing league {comp_id}: {e}")
    
    return summary


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
