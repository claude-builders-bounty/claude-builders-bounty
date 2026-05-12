# Sample Review 2: Larger PR Refactoring Authentication Logic

> This is a sample output from `claude-review` reviewing a PR that refactors the authentication system from a custom JWT implementation to use a session-based auth library.

---

## PR Review: Refactor authentication to use next-auth with session-based flow

**PR**: #512 | **Author**: securityteam | **Branch**: `refactor/auth-next-auth` -> `main`
**Changes**: +1,847/-923 across 34 files

### Summary

This PR replaces the custom JWT-based authentication system with NextAuth.js (v5), migrating from manually signed JWTs stored in cookies to server-side sessions backed by a PostgreSQL session store. The change touches the entire auth surface: login/logout flows, middleware-based route protection, API route authentication, the user context provider, and all 12 protected pages. A new database migration adds a `sessions` table, and the existing `users` table gains OAuth provider columns for future social login support.

### Risk Assessment

| Risk | Severity | Details |
|------|----------|---------|
| Session secret fallback to hardcoded value | Critical | `src/lib/auth.config.ts:18` — The `NEXTAUTH_SECRET` falls back to `"development-secret-do-not-use"` when the env var is missing. If the production environment fails to set this variable, sessions would be signed with a known secret, allowing session forgery. Remove the fallback entirely and fail fast if the secret is not set. |
| Incomplete session invalidation on password change | High | `src/app/api/auth/change-password/route.ts:45` — After a successful password change, only the current session is invalidated. Other active sessions for the same user remain valid. An attacker who has compromised a session could retain access even after the user changes their password. Invalidate all sessions for the user. |
| Race condition in session cleanup cron | High | `src/jobs/cleanExpiredSessions.ts:12-28` — The cleanup job deletes expired sessions in a `SELECT` then `DELETE` loop without a transaction. If a session is renewed between the SELECT and DELETE, the active session gets deleted, logging out the user unexpectedly. Use a single `DELETE WHERE expires_at < NOW()` statement instead. |
| Missing CSRF protection on logout | Medium | `src/app/api/auth/logout/route.ts` — The logout endpoint accepts `GET` requests, making it vulnerable to CSRF via image tags or link prefetching. An attacker could log users out by embedding `<img src="/api/auth/logout">` on any page. Change to `POST`-only with CSRF token validation. |
| Migration rollback not tested | Medium | `migrations/20240115_add_sessions.sql` — The migration adds columns and a table but the down migration (`migrations/20240115_add_sessions.down.sql`) only drops the `sessions` table without removing the added columns from `users` (`provider`, `provider_id`, `provider_email`). A rollback would leave orphaned columns. |
| Cookie attributes not explicitly set | Medium | `src/lib/auth.config.ts:32` — The session cookie configuration does not explicitly set `SameSite`, `Secure`, or `HttpOnly` flags. While NextAuth sets reasonable defaults, explicitly configuring these prevents surprises if defaults change in a library update. |
| Stale user context after session expiry | Low | `src/providers/AuthProvider.tsx:24` — The client-side user context polls `getSession()` every 5 minutes but does not handle the case where the session has expired between polls. The user sees stale UI (appears logged in) until the next poll. Consider using NextAuth's `onSessionExpired` callback. |

### Suggestions

1. **Remove the hardcoded secret fallback** (`src/lib/auth.config.ts:18`)
   This is the highest priority fix. Fail fast if the secret is not configured:
   ```ts
   if (!process.env.NEXTAUTH_SECRET) {
     throw new Error('NEXTAUTH_SECRET environment variable is required');
   }
   ```

2. **Invalidate all user sessions on password change** (`src/app/api/auth/change-password/route.ts:45`)
   After verifying the password change, delete all sessions for the user:
   ```ts
   await db.query('DELETE FROM sessions WHERE user_id = $1', [userId]);
   ```

3. **Simplify the session cleanup job** (`src/jobs/cleanExpiredSessions.ts`)
   Replace the SELECT-then-DELETE loop with a single atomic query:
   ```ts
   await db.query('DELETE FROM sessions WHERE expires_at < NOW()');
   ```

4. **Make logout POST-only with CSRF validation** (`src/app/api/auth/logout/route.ts`)
   Remove the `GET` export and ensure the `POST` handler validates the CSRF token from NextAuth.

5. **Fix the down migration** (`migrations/20240115_add_sessions.down.sql`)
   Add the missing column drops:
   ```sql
   ALTER TABLE users DROP COLUMN IF EXISTS provider;
   ALTER TABLE users DROP COLUMN IF EXISTS provider_id;
   ALTER TABLE users DROP COLUMN IF EXISTS provider_email;
   DROP TABLE IF EXISTS sessions;
   ```

6. **Set cookie attributes explicitly** (`src/lib/auth.config.ts:32`)
   ```ts
   cookies: {
     sessionToken: {
       name: '__Secure-next-auth.session-token',
       options: { httpOnly: true, sameSite: 'lax', secure: true, path: '/' },
     },
   },
   ```

7. **Add integration tests for auth flows** (missing)
   The PR removes 8 test files for the old JWT system but only adds 3 new test files. Critical flows missing test coverage:
   - Session persistence across requests
   - Session invalidation on password change (all sessions)
   - Concurrent session handling
   - Token refresh/rotation
   - Middleware redirect behavior for expired sessions

8. **Document the migration plan** (missing)
   This is a breaking change for active user sessions. All existing users will be logged out when this deploys because their JWT cookies will no longer be valid and no sessions exist yet. Consider:
   - Adding a transitional period that accepts both JWT and session auth
   - Scheduling deployment during low-traffic hours
   - Notifying users about the expected re-login

### What Looks Good

- The migration from custom JWT to NextAuth is a sound architectural decision that reduces the auth attack surface and eliminates the need to maintain custom token signing, rotation, and validation logic.
- The middleware-based route protection (`src/middleware.ts`) is clean and correctly uses NextAuth's `auth()` wrapper with proper redirect handling.
- Database session store choice over JWT sessions is appropriate for this use case since the app needs server-side session invalidation (e.g., on password change, admin-initiated logout).
- The new `AuthProvider` correctly wraps `SessionProvider` and avoids the common mistake of fetching the session in every component — it uses React context properly.
- The PR removes ~900 lines of custom crypto and token handling code, which is a meaningful reduction in security-sensitive code surface.

### Confidence

**Medium**

While the auth changes are clearly structured and the diff is readable, the large scope (34 files, 1,847 additions) and the security-critical nature of authentication mean that some risks may only be visible with runtime testing or with knowledge of the deployment environment. The missing integration tests for critical flows further reduce confidence. The critical session secret fallback issue and the race condition in session cleanup are high-confidence findings visible directly in the diff.

---
