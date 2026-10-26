# CLAUDE.md — Next.js 15 (App Router) + SQLite

> Opinionated, production-ready guidance for a SaaS built with **Next.js 15 App
> Router** and **SQLite** (better-sqlite3 locally, Turso in production). Paste
> this into a greenfield project; every rule has a reason.

## Stack & versions
- **Next.js 15** (App Router, React 19, RSC by default)
- **TypeScript** strict mode, **ESLint** + **Prettier**
- **SQLite**: `better-sqlite3` for local/dev, **Turso** (`@libsql/client`) for prod
- **Drizzle ORM** for migrations and typed queries
- **Zod** for runtime validation at every boundary

*Why these:* App Router gives streaming + server components (less client JS);
SQLite has zero ops overhead for an early-stage SaaS; Drizzle is type-safe and
migration-first, avoiding stringly-typed SQL drift.

## Folder structure
```
src/
  app/                 # routes only (no business logic)
    (auth)/            # route groups for shared layouts
    api/               # route handlers (thin; delegate to services)
  server/
    db/                # schema.ts, migrations/, client.ts
    services/          # business logic, one file per domain
    auth/              # session + RBAC
  lib/                 # framework-agnostic helpers
  components/          # presentational + client components
```
*Why:* routes stay declarative; all logic lives in `server/` so it is testable
without the framework. Route handlers must be ≤30 lines and call a service.

## SQL / migration conventions
- **Migrations are the source of truth.** Never edit a past migration; add a new
  one. Run `drizzle-kit generate` then `drizzle-kit migrate`.
- Every table has `id` (text uuid), `created_at`, `updated_at`.
- **All queries go through Drizzle**, never raw `db.exec` except inside a
  migration file.
- Always `SELECT` explicit columns, never `SELECT *`, to keep payloads small and
  avoid over-fetching.
- Wrap multi-statement writes in a transaction; SQLite writes are serial, so
  keep transactions short.
- *Why:* migration-first prevents schema drift between local and prod; explicit
  columns protect against accidental PII leakage and bundle bloat.

## Component patterns
- Server Components by default. Add `"use client"` only for interactivity
  (forms, hooks). Justification required in PR if a client component fetches data.
- Data fetching happens in Server Components or Route Handlers, never in client
  components via `fetch` to your own API (call the service directly on the server).
- Validate every external input with **Zod** at the edge; never trust
  `req.json()` without a schema.
- *Why:* keeps the client bundle minimal and moves trust boundaries server-side.

## Dev commands
```bash
npm run dev        # next dev
npm run db:gen     # drizzle-kit generate
npm run db:migrate # apply migrations (better-sqlite3)
npm run typecheck  # tsc --noEmit
npm run lint       # eslint + prettier
npm test           # vitest
```

## What we do NOT do (and why)
- **No ORM raw SQL string concatenation** — SQL injection risk; use Drizzle.
- **No `any`** — defeats the type system we rely on for safety.
- **No client-side secrets** — SQLite file path, Turso URL, and tokens stay
  server-only (never `NEXT_PUBLIC_` for them).
- **No `SELECT *` in production queries** — see SQL conventions.
- **No mutations in Server Component render** — render must be pure; do writes in
  actions / route handlers.
- **No floating promises** — `await` or explicitly `void` them; unhandled
  rejections crash the serverless function.

## Session / auth
- Sessions via httpOnly, SameSite=Lax cookies; never store them in localStorage.
- RBAC enforced in the **service layer**, not the UI (UI hides buttons, services
  deny).
