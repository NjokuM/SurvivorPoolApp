# Bugfixes & Features

Running backlog of known issues and planned work. Update this as things are
found or finished — check items off rather than deleting them, so there's a
record of what was actually done.

_Last updated: 2026-08-25_

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
- **Scheduler cron status unconfirmed.** See operations.md — if nothing is
  actually calling `/scheduler/smart-sync` on a timer, results processing
  and missed-pick penalties never run automatically.

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

---

## Features

### Shipped this season

- Persistent JWT login (access + refresh tokens)
- Self-service password change
- Sign in with Google
- Missed-pick life loss (see bugs — now actually works)
- 2026-27 season data for all configured leagues

### In progress

- **Sign in with Apple** — backend (`POST /auth/apple`) done and tested.
  Frontend button built. Blocked on: enabling the "Sign In with Apple"
  capability on the Apple Developer Portal App ID, an EAS dev-client build,
  and testing on a real device (can't be verified without one). This was
  prompted by App Store guideline 4.8 — offering Google Sign-In without also
  offering Apple's own equivalent is close to a guaranteed review rejection.

### Deferred (explicitly deprioritized, not urgent)

- **Forgot / reset password flow.** Needs an email-sending provider
  (Resend recommended — simple HTTP API, no SMTP port issues on Railway,
  generous free tier) before this can be built. Decision deferred by
  request.
- **CI/CD pipeline.** Feature-branch → auto-deploy-to-int →
  manual-approval-for-prod, plus feature flags and richer int test data.
  Explicitly told this isn't needed immediately. No `.github/workflows`
  exists yet.
- **Notifications** (pick deadline reminders, result summaries).
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
