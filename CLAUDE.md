# SurvivorPool

Survivor / points pool app for European football. iOS app in `frontend/survivorpool-mobile` (Expo / React Native), backend in `backend` (FastAPI, async SQLAlchemy, Alembic, Postgres). Environments, deploys and incidents are in `internal-docs/operations.md`; the backlog is `internal-docs/bugfixes-and-features.md`.

## Commands

- Backend tests: `backend/venv/bin/python -m pytest -q` (SQLite in memory, ~2 min)
- Migration heads: `cd backend && venv/bin/alembic heads` (must be exactly one)
- App files have no test runner yet - syntax-check changed files with `@babel/core` + `@babel/preset-react`.

## Workflow

- `/ship` - test, review, commit, merge to main, confirm the deploy, delete the branch
- `/phone-build` - put the current branch on the iPhone for testing
- `/release` - publish a new version to the App Store
- `backend-change-reviewer` agent - run before merging backend changes
- `project-manager` agent - status, risks and what to work on next

## Rules for this project

- **Merging to `main` deploys int and prod together.** Migrations run on container start, so a broken migration takes the whole backend down. New non-null columns need a `server_default`.
- **Never break the app already on people's phones.** Older app versions keep calling the backend for weeks after a release. Only add endpoints and fields - don't rename or remove anything `src/api/apiService.js` uses, or make an existing request field required. If a change has to break the old shape, keep the old one working until the app version that stops using it has shipped.
- **Hide UI behind a feature flag rather than deleting it.** Flags live in `frontend/survivorpool-mobile/src/config/features.js` (e.g. `historyTab`). They ship inside the app, so changing one needs a new build.
- **Replays and backfills must never notify anyone.** Anything that re-runs `process_gameweek_results` over past gameweeks (admin edits, recomputes, data fixes) passes `silent_member` or otherwise suppresses notifications for results that were already announced.
- **New tables linked to users or pools** must be cleaned up in `delete_pool`, `leave_pool` and `delete_user_account`.
- **Pool admin** is `pool.created_by`, checked from the JWT via `require_pool_admin` - never trust a flag sent by the client.
- **Double weeks** are for points-only pools only, never lives pools.
- The user keeps unrelated local edits in `frontend/survivorpool-mobile/eas.json` and `.gitignore` - leave them out of commits.
