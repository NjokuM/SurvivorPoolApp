# Bugfixes & Features

Running backlog of known issues and planned work. Update this as things are
found or finished — check items off rather than deleting them, so there's a
record of what was actually done.

_Last updated: 2026-09-04_

---

## Known bugs

### Open

- **Team↔Competition can't represent a team in two competitions at once.**
  `Team.competition_id` is a single foreign key. Leagues that share clubs
  with another competition in the same season (e.g. a domestic cup drawing
  entrants from multiple divisions) fight over who "owns" a shared team —
  whichever competition was synced last wins, and the loser's "teams in this
  competition" listing comes back empty (fixtures are unaffected, since they
  reference `Team.id` directly). Only observed on prod's minor Irish
  leagues/cup so far — doesn't affect the 5 major leagues, which don't share
  clubs. Real fix needs a proper many-to-many Team↔Competition membership
  table; not started.
- **"Forgot password?" on the login screen does nothing.** Dead button
  (`onPress={() => {}}`). Either hide it or wire up a real flow — see
  Deferred features below.
- **`test_decode_tampered_token_raises` is flaky.** Pre-existing test (not
  something introduced this session) that flips the *last* character of a
  JWT signature to simulate tampering — but for a 256-bit HMAC signature,
  that character's low bits are padding discarded on decode, so occasionally
  the "tampered" token decodes to the exact same bytes as the original and
  the test fails. Not a real security issue (the actual verification logic
  is correct), just a bad choice of which character to flip. Quick fix:
  flip a character from the middle of the signature instead.
- **Scheduler cron status unconfirmed - now more urgent.** See operations.md
  — if nothing is actually calling `/scheduler/smart-sync` on a timer,
  results processing and missed-pick penalties never run automatically.
  As of the endpoint-security pass (2026-08-29), that endpoint (and every
  other `/external/football/*` and `/admin/process-results/*` route) now
  *requires* an `x-cron-secret` header matching the `CRON_SECRET` env var —
  previously these had no auth at all. **Action needed:** confirm
  `CRON_SECRET` is set in Railway for int/prod, and that whatever calls
  these endpoints (cron job, Railway scheduled service, or a manual ops
  script) sends that header - otherwise those calls will start failing
  with 401 after this deploys, silently breaking automation that may have
  been working (however unauthenticated) before.

### Fixed this session (2026-08)

- Persistent login was broken — users had to log in every time they
  reopened the app. Root cause: cookie-based sessions don't persist well on
  React Native. Replaced with JWT access + refresh tokens (refresh token
  lasts a full season).
- Changing your password didn't actually invalidate sessions on other
  devices, despite the UI claiming it would.
- Users who never submitted a pick for a gameweek never lost a life for it,
  no matter how long the gameweek had been over — the results processor only
  ever looked at existing `Pick` rows, so a missing pick was invisible to it.
- A migration chain break crashed both int and prod (see operations.md
  incident log).
- `GET /competitions/leagues` silently returning nothing on int (see
  operations.md incident log).
- `store_league_in_db` didn't handle season rollover — re-syncing an
  already-known league for a new season just silently no-opped, so a new
  season could never actually get synced. Competitions now get one row per
  `(external_id, season)`.
- Team sync crashed on clubs the API doesn't supply venue data for
  (smaller/lower-tier clubs) — `venue_name` is now nullable.
- Pool creation showed duplicate league entries (one per season) once
  competitions became season-scoped. Now dedupes to the latest season per
  league client-side.
- Pool creation used a hardcoded country-flag emoji instead of the league's
  real logo from the API.
- `max_picks_per_team` was a flat value (default 2, UI range 1-5) with no
  regard for the league's actual format. A limit of 1 was selectable even
  when the season had more remaining gameweeks than teams (guaranteed to
  run out of valid picks before the season ended), and the default of 2 was
  wrong for shorter/mid-season pools. Now computed per-league as
  `ceil(remaining_gameweeks / team_count)`: this is both the minimum
  selectable value (lower values are hidden/rejected as infeasible) and the
  suggested default, so a freshly created pool is always playable to
  completion. New `GET /competitions/leagues/{id}/pick-limits` endpoint
  backs the frontend counter; `POST /pools/create` rejects an
  under-provisioned value server-side too. Applies identically to league
  and survivor mode (the per-team cap was never gated by `has_lives`).
- `get_pick_limits` (and pool creation itself) crashed for the very first
  pool ever created on a competition with zero fixtures synced yet -
  `get_current_gameweek` returns `None` with nothing to derive a gameweek
  from, which then hit `None` arithmetic in `get_pick_limits` and a
  `NOT NULL` constraint violation on `Pool.start_gameweek` in
  `create_pool`. Both now fall back to a nominal gameweek 1. Surfaced by
  the new endpoint-security tests, not something previously reported.

---

## Features

### Shipped this season

- Persistent JWT login (access + refresh tokens)
- Self-service password change
- Sign in with Google
- Missed-pick life loss (see bugs — now actually works)
- 2026-27 season data for all configured leagues
- League-only pool mode — `Pool.has_lives = false`: points-only standings,
  no elimination, no `lives_left`/`eliminated_gameweek` tracking. Toggle
  lives in the "Pool Mode" selector on pool creation.
- Format-aware `max_picks_per_team` (see bugs above) — applies to both
  survivor and league mode.
- League-mode pick creation was blocked entirely by an unconditional
  "no lives left" check (league pools store `total_lives=0` by design,
  since they never track lives) — no league-mode user could ever make a
  pick. Fixed at `pick_router.py` step 8️⃣: the lives gate now only applies
  when `pool.has_lives`.
- **Admin pick editing.** `PUT /admin/pools/{pool_id}/users/{user_id}/picks`
  — only the pool's creator (verified via JWT, not a client-supplied flag)
  can add or correct another user's picks, for migrating a pool's pre-app
  history or fixing a mistake. Design: picks for gameweeks not mentioned in
  the request are left alone; every pick for that user in that pool is then
  replayed gameweek-by-gameweek through the normal results pipeline
  (`process_gameweek_results`), so lives/points/elimination come out
  exactly as if it had all happened live - untouched weeks just recompute
  to the same result, and any gameweek left without a pick correctly
  becomes a missed pick. This avoids ever hand-reversing a
  previously-applied points/life delta, which is error-prone once
  elimination is involved. `pool.start_gameweek` is pulled back
  automatically to cover the earliest imported gameweek. `Pick.source`
  ("user" vs "admin") records which picks were entered this way. The old
  unauthenticated `force=true` bypass on `POST /picks/` (skipped the
  fixture-deadline check, no auth at all) has been removed - this endpoint
  is its replacement.
- **Every endpoint now requires authentication.** Previously most endpoints
  trusted a client-supplied `user_id`/`created_by` with no verification at
  all - any caller could act as anyone. Now:
  - User-facing endpoints require a valid JWT (`Authorization: Bearer ...`),
    resolved via the existing `get_current_user` dependency. The frontend
    already attached this to every request (see `api.js`'s interceptor),
    so no frontend changes were needed.
  - Endpoints that act "as" a user (create/join/leave/delete a pool, create/
    update a pick) now derive that identity from the token, not the request
    body - a spoofed `user_id` in the body is silently ignored/overridden.
  - "View my own X" endpoints (`GET /users/{id}/pools`, `GET /picks/user/{id}`)
    now 403 if the caller isn't that user.
  - `PUT /picks/{pick_id}` previously had no ownership check at all - now
    requires the caller to own the pick.
  - Server-to-server sync/cron endpoints (`/external/football/*`,
    `/admin/process-results/*`) require the `x-cron-secret` header instead
    of a user token - a logged-in app user's token alone isn't sufficient
    for these. **See the cron-status bug above - this needs a Railway
    `CRON_SECRET` check before/after deploy.**
  - Removed `POST /users/`, a fully unauthenticated duplicate of `/signup`
    that skipped its email/username uniqueness checks and wasn't used by
    the app.
  - 19 new tests in `test_endpoint_security.py` plus updates across the
    existing router test files cover both the auth requirement and the
    identity-spoofing scenarios directly.

### In progress

- **Sign in with Apple** — backend (`POST /auth/apple`) done and tested.
  Frontend button built. Blocked on: enabling the "Sign In with Apple"
  capability on the Apple Developer Portal App ID, an EAS dev-client build,
  and testing on a real device (can't be verified without one). This was
  prompted by App Store guideline 4.8 — offering Google Sign-In without also
  offering Apple's own equivalent is close to a guaranteed review rejection.
- **Notifications** — backend done and tested, frontend wired, **blocked on
  a new EAS dev-client build + real-device testing** (same situation as
  Apple Sign-In: `expo-notifications` is a native module, won't work in the
  currently-installed build). Shipped:
  - `day_before` / `four_hour` reminders anchored to the gameweek's first
    kickoff, plus a `daily_unpicked` nudge for any day in between (skipped
    on a day the other two already fired, so no double-ping). All check
    against the *last* fixture's kickoff for the actual deadline, matching
    the pick model (a pick is valid against any not-yet-started fixture in
    the gameweek). Idempotent per (user, pool, gameweek, type, day) via
    `NotificationLog` - safe to call on every scheduler tick.
  - `pick_result` notification fires automatically at the end of
    `process_gameweek_results` for every newly-scored pick, including NP
    (missed pick) - copy differs for league vs. survivor mode (mentions
    losing a life only where that's real).
  - Reminder check folded into the existing `POST
    /external/football/scheduler/smart-sync` tick (every ~30 min) rather
    than needing its own cron job - pure DB reads plus at most a few pushes,
    no extra football-API cost.
  - `PushToken` (one per user, most recent device wins) and
    `NotificationLog` tables; three preference columns on `User`
    (`notifications_enabled`, `deadline_reminders_enabled`,
    `result_notifications_enabled`) wired to the three toggles already on
    the Profile screen's Notifications section - those were previously
    local-only UI state with no backend behind them.
  - Sends via Expo's push API directly over `httpx` (no SDK dependency) -
    `POST /users/me/push-token`, `GET`/`PUT
    /users/me/notification-preferences`.
  - **Still needed before this actually works on a phone:** `expo-notifications`
    + `expo-device` installed and `expo-notifications` added to
    `app.json`'s plugins, but that's a native module change - requires a
    fresh interactive EAS build (`eas build --profile development
    --platform ios`, same as Apple Sign-In needed) before push tokens can
    even be generated on-device. iOS also needs the "Push Notifications"
    capability, which EAS Build typically provisions automatically for an
    interactive build (same mechanism that picked up Sign In with Apple's
    entitlement once run interactively) - not confirmed since it can't be
    without a real build.

### Deferred (explicitly deprioritized, not urgent)

- **Forgot / reset password flow.** Needs an email-sending provider
  (Resend recommended — simple HTTP API, no SMTP port issues on Railway,
  generous free tier) before this can be built. Decision deferred by
  request.
- **CI/CD pipeline.** Feature-branch → auto-deploy-to-int →
  manual-approval-for-prod, plus feature flags and richer int test data.
  Explicitly told this isn't needed immediately. No `.github/workflows`
  exists yet.
- **Live in-game score updates.**
- **Rate limiting.** Low risk right now with a small, known user base.

### App Store readiness (not started beyond Apple Sign-In)

Apple Sign-In was the biggest blocker, but a few other things stand between
"works for friends on a dev build" and an actual submission:

- Fresh **production**-profile build incorporating everything built this
  season (last one was built in January, before any of it existed).
- Privacy policy URL (required — the app collects email/name and does
  OAuth).
- App Store Connect's "App Privacy" data-collection disclosure.
- Version/build number bump (still at 1.0.1 / build 2).
- Manual QA pass on an actual production-style build, not just dev-client.
