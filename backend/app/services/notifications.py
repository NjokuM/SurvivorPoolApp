"""
Pick-deadline reminders and pick-result notifications.

Deadline model (see results.py): a pick is valid against any not-yet-kicked-off
fixture in a gameweek, so the real deadline is the LAST fixture's kickoff, not
the first - but reminders are anchored to the FIRST kickoff, since that's the
meaningful "the week is starting" moment for a player who hasn't picked yet.

Three reminder types, each logged in NotificationLog so a ~30-min scheduler
tick never re-sends one:
- day_before:     ~24h before the gameweek's first kickoff, once.
- four_hour:       ~4h before the gameweek's first kickoff, once.
- daily_unpicked: once per calendar day the reminder window is open and the
                   user is still unpicked, skipped on any day day_before or
                   four_hour already fired (so a user isn't double-pinged the
                   same day).
"""
from datetime import datetime, timedelta, timezone, date
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, distinct
from app.models.competiton_data import Fixture, Team
from app.models.pool import Pool, PoolUserStats
from app.models.pick import Pick
from app.models.user import User
from app.models.notification import PushToken, NotificationLog
from app.services.push_notifications import send_push_notification

# Half-width of each reminder's trigger window - wide enough that a 30-min
# cron cadence can't skip past it entirely.
_WINDOW = timedelta(minutes=45)


async def _get_push_token(db: AsyncSession, user_id: int) -> "str | None":
    res = await db.execute(select(PushToken).where(PushToken.user_id == user_id))
    row = res.scalar_one_or_none()
    return row.token if row else None


async def _already_sent(
    db: AsyncSession, user_id: int, pool_id: int, gameweek: int,
    notification_type: str, sent_date: date,
) -> bool:
    res = await db.execute(
        select(NotificationLog).where(
            NotificationLog.user_id == user_id,
            NotificationLog.pool_id == pool_id,
            NotificationLog.gameweek == gameweek,
            NotificationLog.notification_type == notification_type,
            NotificationLog.sent_date == sent_date,
        )
    )
    return res.scalar_one_or_none() is not None


async def _log_sent(
    db: AsyncSession, user_id: int, pool_id: int, gameweek: int,
    notification_type: str, sent_date: date,
):
    db.add(NotificationLog(
        user_id=user_id, pool_id=pool_id, gameweek=gameweek,
        notification_type=notification_type, sent_date=sent_date,
    ))
    await db.commit()


async def _open_gameweek_windows(db: AsyncSession, pool: Pool) -> List[dict]:
    """Gameweeks for this pool whose first kickoff is within a reminder
    window of today, and whose picking deadline (last kickoff) hasn't
    passed yet."""
    now = datetime.now(timezone.utc)
    res = await db.execute(
        select(Fixture).where(Fixture.competition_id == pool.competition_id)
    )
    fixtures = res.scalars().all()

    by_gw = {}
    for f in fixtures:
        by_gw.setdefault(f.gameweek, []).append(f)

    windows = []
    for gw, gw_fixtures in by_gw.items():
        if gw < pool.start_gameweek:
            continue
        first_kickoff = min(f.kickoff_time for f in gw_fixtures)
        last_kickoff = max(f.kickoff_time for f in gw_fixtures)
        if first_kickoff.tzinfo is None:
            first_kickoff = first_kickoff.replace(tzinfo=timezone.utc)
        if last_kickoff.tzinfo is None:
            last_kickoff = last_kickoff.replace(tzinfo=timezone.utc)

        if now >= last_kickoff:
            continue  # deadline already passed, nothing to remind about
        if now < first_kickoff - timedelta(days=1) - _WINDOW:
            continue  # too early - reminder window hasn't opened yet

        windows.append({
            "gameweek": gw, "first_kickoff": first_kickoff, "last_kickoff": last_kickoff,
        })
    return windows


async def _unpicked_eligible_members(db: AsyncSession, pool: Pool, gameweek: int) -> List[PoolUserStats]:
    picked_res = await db.execute(
        select(distinct(Pick.user_id))
        .join(Fixture, Fixture.id == Pick.fixture_id)
        .where(Pick.pool_id == pool.id, Fixture.gameweek == gameweek)
    )
    already_picked = {row[0] for row in picked_res.all()}

    stats_res = await db.execute(select(PoolUserStats).where(PoolUserStats.pool_id == pool.id))
    members = stats_res.scalars().all()

    eligible = []
    for stats in members:
        if stats.user_id in already_picked:
            continue
        if pool.has_lives and stats.lives_left <= 0:
            continue  # already eliminated, nothing to remind about
        eligible.append(stats)
    return eligible


async def check_and_send_deadline_reminders(db: AsyncSession) -> dict:
    """Call on every scheduler tick (~30 min). Cheap: pure DB reads unless
    there's actually something to send, no external API calls."""
    now = datetime.now(timezone.utc)
    today = now.date()
    sent_counts = {"day_before": 0, "four_hour": 0, "daily_unpicked": 0}

    pools_res = await db.execute(select(Pool).where(Pool.is_active == True))
    pools = pools_res.scalars().all()

    for pool in pools:
        windows = await _open_gameweek_windows(db, pool)
        for w in windows:
            gw = w["gameweek"]
            first_kickoff = w["first_kickoff"]

            eligible = await _unpicked_eligible_members(db, pool, gw)
            if not eligible:
                continue

            day_before_at = first_kickoff - timedelta(hours=24)
            four_hour_at = first_kickoff - timedelta(hours=4)
            in_day_before_window = day_before_at - _WINDOW <= now <= day_before_at + _WINDOW
            in_four_hour_window = four_hour_at - _WINDOW <= now <= four_hour_at + _WINDOW
            daily_window_open = now >= day_before_at

            for stats in eligible:
                user_res = await db.execute(select(User).where(User.id == stats.user_id))
                user = user_res.scalar_one_or_none()
                if not user or not user.notifications_enabled or not user.deadline_reminders_enabled:
                    continue
                token = await _get_push_token(db, user.id)
                if not token:
                    continue

                day_before_already_logged = await _already_sent(db, user.id, pool.id, gw, "day_before", today)
                four_hour_already_logged = await _already_sent(db, user.id, pool.id, gw, "four_hour", today)

                if in_day_before_window and not day_before_already_logged:
                    ok = await send_push_notification(
                        token, "Pick reminder",
                        f"Don't forget to make your gameweek {gw} pick in {pool.name} - kickoff is in about 24 hours.",
                        data={"pool_id": pool.id, "gameweek": gw, "type": "day_before"},
                    )
                    if ok:
                        await _log_sent(db, user.id, pool.id, gw, "day_before", today)
                        sent_counts["day_before"] += 1
                        day_before_already_logged = True

                if in_four_hour_window and not four_hour_already_logged:
                    ok = await send_push_notification(
                        token, "Last chance to pick",
                        f"Gameweek {gw} kicks off in about 4 hours and you haven't picked yet in {pool.name}.",
                        data={"pool_id": pool.id, "gameweek": gw, "type": "four_hour"},
                    )
                    if ok:
                        await _log_sent(db, user.id, pool.id, gw, "four_hour", today)
                        sent_counts["four_hour"] += 1
                        four_hour_already_logged = True

                # Skip the daily nudge on any day day_before or four_hour
                # already fired for this (user, pool, gameweek) - checked
                # against the log (sent on THIS call or an earlier one
                # today), not a per-call-only flag.
                if (
                    daily_window_open
                    and not day_before_already_logged
                    and not four_hour_already_logged
                    and not await _already_sent(db, user.id, pool.id, gw, "daily_unpicked", today)
                ):
                    ok = await send_push_notification(
                        token, "Still time to pick",
                        f"You still haven't made your gameweek {gw} pick in {pool.name}.",
                        data={"pool_id": pool.id, "gameweek": gw, "type": "daily_unpicked"},
                    )
                    if ok:
                        await _log_sent(db, user.id, pool.id, gw, "daily_unpicked", today)
                        sent_counts["daily_unpicked"] += 1

    return {"checked_at": now.isoformat(), "sent": sent_counts}


async def notify_pick_results(db: AsyncSession, picks: List[Pick]) -> int:
    """Send a "your pick was processed" notification for each newly-scored
    pick (including NP/missed-pick records). Called right after
    process_gameweek_results commits its changes. Never raises - a push
    failure must not roll back or interrupt results processing."""
    sent = 0
    today = datetime.now(timezone.utc).date()

    for pick in picks:
        pool_res = await db.execute(select(Pool).where(Pool.id == pick.pool_id))
        pool = pool_res.scalar_one_or_none()
        if not pool:
            continue

        fixture_res = await db.execute(select(Fixture).where(Fixture.id == pick.fixture_id))
        fixture = fixture_res.scalar_one_or_none()
        gameweek = fixture.gameweek if fixture else None
        if gameweek is None:
            continue

        if await _already_sent(db, pick.user_id, pick.pool_id, gameweek, "pick_result", today):
            continue

        user_res = await db.execute(select(User).where(User.id == pick.user_id))
        user = user_res.scalar_one_or_none()
        if not user or not user.notifications_enabled or not user.result_notifications_enabled:
            continue
        token = await _get_push_token(db, user.id)
        if not token:
            continue

        result_value = pick.result.value if hasattr(pick.result, "value") else pick.result

        if result_value == "NP":
            body = f"You missed gameweek {gameweek} in {pool.name}"
            body += " and lost a life." if pool.has_lives else " and scored 0 points."
        else:
            team_name = None
            if pick.team_id:
                team_res = await db.execute(select(Team).where(Team.id == pick.team_id))
                team = team_res.scalar_one_or_none()
                team_name = team.name if team else None
            team_part = f"your pick ({team_name})" if team_name else "your pick"

            if result_value == "WIN":
                body = f"{team_part} won gameweek {gameweek} in {pool.name} - +{pick.points} points!"
            elif result_value == "DRAW":
                body = f"{team_part} drew in gameweek {gameweek} of {pool.name} - +{pick.points} point."
            else:  # LOSS
                body = f"{team_part} lost in gameweek {gameweek} of {pool.name}"
                body += " and you lost a life." if pool.has_lives else "."

        ok = await send_push_notification(
            token, "Pick result", body,
            data={"pool_id": pick.pool_id, "gameweek": gameweek, "type": "pick_result"},
        )
        if ok:
            await _log_sent(db, pick.user_id, pick.pool_id, gameweek, "pick_result", today)
            sent += 1

    return sent
