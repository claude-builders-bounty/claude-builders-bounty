# CLAUDE.md — Next.js 15 + SQLite SaaS template

An opinionated, production-ready `CLAUDE.md` for a greenfield SaaS built with
Next.js 15 (App Router) and SQLite (`better-sqlite3` locally, Turso in prod).

Every rule has a stated reason. Highlights:

- **SQLite-specific ops**: WAL mode + `busy_timeout` mandatory, `VACUUM INTO` for
  live backups, migration limits, `INTEGER` unix-ms timestamps (SQLite has no
  datetime type)
- **One auth, no hedging**: Auth.js v5 (Lucia is deprecated — the doc says so)
- **Multi-tenancy**: single DB + `org_id` on every tenant table, with a reference
  Drizzle schema sketch (`$onUpdateFn` included — `updated_at` must not go stale)
- **Corrected guidance**: Server Actions *throw* for unexpected failures
  (`error.tsx` boundaries are designed for it); `cacheLife()`/`cacheTag()` need
  `experimental.dynamicIO` on Next 15; every `actions/` file starts with `"use server"`

## Testing

- Acceptance traceability: all 9 checklist items mapped to document sections
- Simulation test: dropped the file into an empty scaffold and had an agent
  implement a `projects` feature — **0 clarifying questions asked**, all
  conventions followed (this caught one real doc gap, since fixed)
- Independent adversarial review: 1 HIGH + 4 MED + 5 LOW found and fixed
