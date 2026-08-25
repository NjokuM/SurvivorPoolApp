# Operations

Running notes on how this app is deployed, what needs to happen every season,
and what to check when something looks wrong. Keep this current — it's the
first place to look before debugging from scratch.

_Last updated: 2026-08-25_

---

## Environments

| Env | URL | Purpose |
|---|---|---|
| local | `http://192.168.1.168:8001` (your machine's LAN IP) | Dev-client builds and local backend testing. Update the IP in `frontend/survivorpool-mobile/src/config/environment.js` if your machine's address changes. |
| int | `https://survivorpoolapp-int.up.railway.app` | Pre-prod testing. Currently configured with the 5 major leagues only (Premier League, La Liga, Ligue 1, Bundesliga, Serie A). |
| prod | `https://survivorpoolapp-production.up.railway.app` | Real users. Has 6 extra minor leagues int doesn't (Irish First Division/Premier Division/FAI Cup/Women's President's Cup, Primeira Liga, Eredivisie) — origin unclear, likely leftover test data. |

**Deployment:** both int and prod are Railway services. It's not confirmed
whether either auto-deploys on push to `main` or requires a manual trigger —
this needs verifying in the Railway dashboard. Migrations run automatically
as part of container startup (`backend/Dockerfile`'s `/start.sh` runs
`alembic upgrade head` before starting uvicorn) — **a broken migration chain
crashes the whole container**, not just the affected feature. This already
caused a real outage once (see Incident Log below); always verify
`alembic heads` shows a single clean head before merging a migration.

**Backend env vars needed** (see `.env.example`): `DATABASE_URL`,
`SECRET_KEY`, `CRON_SECRET`, `RAPIDAPI_KEY`/`RAPIDAPI_HOST`, `BASE_URL`,
`GOOGLE_WEB_CLIENT_ID`, `APPLE_BUNDLE_ID`.

---

## Season rollover checklist

Do this once a year, ahead of each new season (European domestic leagues
typically start mid-August):

1. **Confirm the new season's data exists in the API** before syncing —
   hit `GET /external/football/leagues?id=<external_id>&season=<year>`
   against one league first. API-Football labels a season by its *start*
   year (e.g. the 2026-27 season is `season=2026`).
2. **Sync each league**, in order (fixtures depends on teams already
   existing, teams sync depends on the league row already existing):
   ```
   POST /external/football/leagues/sync?id=<external_id>&season=<year>
   POST /external/football/teams/sync?league=<external_id>&season=<year>
   POST /external/football/fixtures/sync?league=<external_id>&season=<year>
   ```
   Run this against **int first**, verify, then **prod**. Check the response
   `skipped` counts — nonzero skips on fixtures usually means teams didn't
   fully sync (check for a 500 on the teams call).
3. **Verify**: team count and fixture count per league should match reality
   (20 teams / 380 fixtures for a 20-team league, 18/306 for 18-team, etc.),
   and fixture dates should span the new season's actual window.
4. Competitions are stored one row per `(external_id, season)` — the old
   season's row is untouched by this, so don't worry about clobbering last
   season's data.
5. **Known gap:** leagues that share clubs with another competition in the
   same sync batch (e.g. a league + its associated cup) can have those
   shared teams' `competition_id` end up pointing at whichever competition
   was synced *last*, since a team can only belong to one competition at a
   time in the current schema. Only matters for leagues with genuine
   crossover (seen on prod's minor Irish leagues/cup, not the 5 majors,
   which don't share clubs with each other). See bugfixes-and-features.md.

This whole flow was broken until 2026-08 — see the Incident Log for what was
wrong and fixed.

---

## Git / branch workflow

- Feature work happens on a branch (usually via a separate `git worktree`
  rather than switching the primary checkout, so unrelated work-in-progress
  never blocks a live investigation). Merge to `main` with `--no-ff` once
  tested.
- **Delete branches once merged and deployed** — both local and remote:
  ```
  git branch -d branch-name
  git push origin --delete branch-name
  ```
  (`-D` instead of `-d` if git doesn't recognize it as merged, e.g. after a
  squash-merge.)
- Before merging anything with a new Alembic migration, confirm
  `alembic heads` shows exactly one head from a clean checkout of the
  merge result — not just from the feature branch in isolation. A migration
  chained onto a revision that only exists locally (never committed) will
  crash every real deployment; this happened once already.
- No CI/CD pipeline exists yet (no `.github/workflows`). Tests are run
  manually before merging. See bugfixes-and-features.md for the planned
  pipeline (deprioritized, not urgent).

---

## Monitoring & health checks

- No dashboard exists yet — health is checked manually via `curl` against
  `/docs` (cheap, doesn't touch the DB) and `/competitions/leagues` (touches
  the DB, so a stronger signal that things actually work end-to-end).
- **Open question, needs verifying:** is anything actually calling
  `POST /external/football/scheduler/smart-sync` on a schedule? The
  `railway.toml` comments list options (Railway Cron Service, an external
  cron like cron-job.org, a GitHub Actions scheduled workflow) but none is
  confirmed configured. If nothing is calling it, fixture results and
  missed-pick life loss will never process automatically — someone has to
  manually hit the endpoint after every gameweek. This is the single most
  important thing to confirm before relying on the app for a real pool.
- RapidAPI quota isn't being tracked anywhere. Worth checking the plan's
  daily/monthly limits before running a full season sync (5-11 leagues ×
  3 calls each), and before the smart-sync cron (if configured) starts
  making frequent calls during live gameweeks.

---

## Incident log

Keep this short — just enough to not repeat a mistake.

- **2026-08-21 — int/prod crash loop.** A migration's `down_revision`
  pointed at a revision that only existed locally (never committed to git).
  `alembic upgrade head` threw `KeyError` while resolving the revision
  graph — before any SQL ran, so no data was affected — but since migrations
  run before the server starts, the container crash-looped through all of
  Railway's retries. Fixed by re-pointing the migration at the actual last
  committed revision. **Lesson:** always double check a new migration's
  `down_revision` resolves in a fresh clone, not just your local machine
  (which has every file you've ever created, committed or not).
- **2026-08-24 — `GET /competitions/leagues` returning empty on int.**
  Bumping a filter schema's default `season` value to the new year also
  silently changed what an unfiltered "list all leagues" call returned,
  since that endpoint reuses the same filter object. No data was lost — it
  was a query filter, not a delete. **Lesson:** a shared filter schema used
  by both a "sync to this season" endpoint and a "list everything" endpoint
  needs the season field to default to unfiltered (`None`), not a hardcoded
  year.
