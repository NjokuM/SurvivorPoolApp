# Survivor Pool Production Readiness Story

A living document to track the final backlog before launch. Items are grouped by surface area with priorities noted per user request.

---

## Backend & Platform

1. **Pool membership management (Priority)**
   - `PUT /pools/{pool_id}/leave`: allow members to exit without deleting themselves. Ensure PoolUserStats, picks, and lives adjust gracefully.
   - `DELETE /pools/{pool_id}` (creator only): soft-delete pools, cascade to stats/picks, and prevent new joins.

2. **Endpoint security & authentication hardening (Biggest Priority)**
   - Adopt robust auth (recommended approach: short-lived JWT access tokens + refresh tokens in HTTP-only cookies). Alternatives to evaluate: OAuth2 Password flow, managed auth (Auth0/Supabase), passwordless magic links.
   - Implement sliding-session logic so users remain logged in similar to major social apps (refresh rotation, silent refresh on app launch, SecureStore persistence).

3. **Rate limiting (High Priority)**
   - Introduce loose per-IP throttles: e.g., Auth routes 5 req/min, general API 60 req/min using FastAPI-Limiter + Redis or an upstream proxy.

4. **Forgot / reset / change password endpoints**
   - `POST /auth/forgot-password` issues signed reset token via email.
   - `POST /auth/reset-password` validates token and updates hash.
   - `POST /auth/change-password` (authenticated) requires old password + new hash.
   - Store reset tokens with TTL (Redis/DB) and apply rate limiting.

5. **Notifications service (Biggest backend priority)**
   - Background scheduler to emit:
     - Fixture deadline reminders (push/email) X hours before kickoff windows.
     - Match result summaries after weekly processing (wins/draws/losses, lives remaining).
   - Persist Expo push tokens per device; allow opt-in/out.

6. **Life loss when no pick submitted**
   - During weekly processing, detect PoolUserStats missing a pick for the gameweek and decrement a life + mark elimination state.

7. **Pool pagination & search support**
   - Extend `GET /pools` to accept `limit/offset` and return total count for front-end “View all” screen with search bar.

8. **README & docs updates**
   - Remove public “test credentials” section.
   - Document new endpoints (leave/delete pool, forgot/reset password, notifications, rate limiting).
   - Add security/auth architecture notes and notification setup guide.

9. **Long-term: Fixtures endpoint**
   - Provide consumable API for fixtures page (league filters, upcoming/past, cached data).

---

## Frontend & UX

1. **Terminology & copy fixes (Priority)**
   - Replace "Deadline passed" banner with "Matches started" until all fixtures conclude; only show "Deadline passed" when every match finished and the user missed a pick.
   - Change "Your Last Pick" label to "This Week's Pick".

2. **Pick availability indicator refresh**
   - Instead of greying out with a red X after max uses, show a counter (e.g., "2/2 uses"), keeping color until edit-pick feature ships.

3. **Pick history draw indicator**
   - Swap "-" with "D" to clearly represent draws.

4. **Missed pick life loss messaging**
   - Mirror backend enforcement by surfacing alerts/banners when a life is lost due to no pick.

5. **Pool list scalability**
   - Show top 3–4 pools on dashboard plus "View All Pools" CTA that opens a dedicated list with search/filter.

6. **Dynamic greeting**
   - Replace "Welcome back Player" with the actual first name/username from profile data.

7. **Pull-to-refresh affordance**
   - Add visible indicator (arrow animation, label, or Lottie) so users know the gesture is available.

8. **Login screen cleanup (Priority)**
   - Remove "test user" helper text; rely on internal documentation for demo accounts.

9. **Notifications UI**
   - Add settings surfaces for reminder toggles and push-permission prompts aligned with backend notifier.

10. **Long-term fixtures page**
    - Dedicated screen showing Premier League (plus other leagues) fixtures with filters by gameweek, kickoff status, and search.

---

## Open Questions
- Preferred notifier channel order (push vs email) and copy tone?
- Should pool deletion hard-delete historical stats or archive for analytics?
- Do we need admin tooling for rate-limit overrides or notification retries?
- Any compliance requirements for storing refresh tokens/PII?

_Last updated: Jan 3, 2026_
