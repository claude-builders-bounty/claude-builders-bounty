# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

## Stack & versions
- Next.js 15 (App Router), React 19, TypeScript strict
- SQLite via better-sqlite3 (local) or @libsql/client (Turso)
- Tailwind CSS + shadcn/ui
- Auth: Lucia or next-auth v5
- Payments: Stripe
- Node 22 LTS

## Folder structure
```
app/                 # routes, layouts, server actions
  (auth)/            # auth route group
  (dashboard)/       # protected routes
  api/               # route handlers (webhooks only)
lib/                 # db, auth, utils
  db.ts              # single SQLite connection (singleton)
  schema.sql         # source of truth for schema
components/          # UI components (no business logic)
migrations/          # numbered SQL files: 001_init.sql
```

## Dev commands
- `npm run dev` — dev server (Turbopack)
- `npm run build` — production build (must pass before PR)
- `npm run lint` — eslint + tsc --noEmit
- `npm run db:migrate` — apply pending migrations
- `npm test` — vitest

## DB / migration rules
- Schema changes ONLY via numbered migration files in `migrations/`.
- Never edit an applied migration; create a new one.
- All queries use prepared statements (`db.prepare(...).run/bind`).
- No ORM. SQL is explicit and reviewable.
- Migrations are idempotent: use `CREATE TABLE IF NOT EXISTS`.
- Foreign keys ON; enable `PRAGMA foreign_keys = ON` on connection init.

## Component patterns
- Server Components by default; `'use client'` only when needed.
- Server Actions for mutations; no API routes except webhooks.
- Forms use `useActionState` + Zod validation.
- Loading/error states via `loading.tsx` / `error.tsx`.

## What we don't do (and why)
- No ORM: hides SQL, complicates migrations, adds cold-start overhead.
- No client-side data fetching for initial load: use Server Components.
- No `useEffect` for data: fetch on server; mutations via Server Actions.
- No global state library: URL + Server Components suffice for SaaS.
- No `any`: strict TS prevents runtime surprises.

## Anti-patterns to avoid
- Creating SQLite connection per request (use singleton).
- Storing secrets in client components.
- Using `SELECT *` in production queries.
- Skipping migrations for "quick" schema tweaks.
