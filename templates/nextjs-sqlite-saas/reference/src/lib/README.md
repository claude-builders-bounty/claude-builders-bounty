# `src/lib/` — shared server utilities

| Module | Purpose |
|--------|---------|
| `env.ts` | Zod-validated `process.env` — fail fast on missing `DATABASE_URL` / `SESSION_SECRET` |
| `db.ts` | Singleton DB connection — **only** module that imports the SQLite driver |
| `auth.ts` | Session read/write and `requireOrgMember(orgSlug)` |
| `utils.ts` | Pure helpers (`cn`, `formatCurrency`) — no DB imports |

**Security:** Secrets are read here from `process.env`, never hardcoded. `SESSION_SECRET` must be at least 32 characters.
