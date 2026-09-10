# CLAUDE.md — Next.js 15 + SQLite SaaS

Opinionated project context for Claude Code. Every rule exists for a reason.

## Stack & versions

- Next.js **15** (App Router only — no Pages Router)
- TypeScript **strict** (`tsconfig` `"strict": true`)
- SQLite via **better-sqlite3** (local) or **Turso** (hosted) — same driver API
- Migrations: plain SQL files in `db/migrations/NNNN_*.sql` + `db/migrate.ts`
- Auth: session cookie (httpOnly, SameSite=Lax) — no JWT in localStorage
- Validation: **zod** at every system boundary (forms, API, env)

## Commands

```bash
npm run dev          # next dev
npm run build        # next build && next start
npm run db:migrate   # apply pending migrations (idempotent)
npm run db:reset     # DEV ONLY — drop schema + re-migrate
npm test             # vitest
npm run typecheck    # tsc --noEmit
```

## Folder structure

```
app/
  (marketing)/     # public routes, no auth
  (app)/           # authenticated product; layout enforces session
  api/             # route handlers only — no business logic beyond parse/auth
src/
  db/              # connection, migrate, typed query helpers
  db/migrations/   # NNNN_description.sql — forward-only
  lib/             # pure functions, zod schemas, no React
  components/      # UI only; no direct db access
tests/             # vitest; colocate only for tiny unit tests
```

## SQL & migrations

- **Never** edit a migration that is already on `main` — add a new one.
- Every migration is **reversible by a new migration**, not by hand-editing history.
- Primary keys: `TEXT` ULID/UUID or `INTEGER` autoincrement — pick one per table and stick to it.
- Timestamps: `created_at` / `updated_at` as `TEXT` ISO-8601 UTC (`strftime('%Y-%m-%dT%H:%M:%fZ','now')`).
- Always index foreign keys you filter/join on.
- Multi-statement migrations run inside a single transaction in `migrate.ts`.

## Data access

- Use `db.prepare` / typed helpers in `src/db` — **no** raw `sqlite` calls from components or route handlers.
- Parameterize every value: `?` placeholders only. Never string-concatenate SQL.
- Prefer one connection per request (or a documented singleton) — better-sqlite3 is sync; do not block the event loop with huge scans.

## Components & app code

- Server Components by default; `"use client"` only when you need state/effects/browser APIs.
- Mutations go through **Server Actions** or route handlers + zod parse — never trust client payloads.
- Loading and error states: every route segment gets `loading.tsx` and `error.tsx`.
- No `any` in shared types; export zod-inferred types (`z.infer`).

## Env

```ts
// src/lib/env.ts — parse once, fail fast
z.object({
  DATABASE_URL: z.string().min(1),
  SESSION_SECRET: z.string().min(32),
})
```

- `.env.local` for secrets; `.env.example` committed with empty values.
- Never `process.env.FOO` outside `src/lib/env.ts`.

## What we don't do (and why)

| Anti-pattern | Why not |
|--------------|---------|
| ORM magic for schema drift | SQL files are reviewable; migrations stay explicit |
| JWT in localStorage | XSS → full account takeover; httpOnly cookie instead |
| `db.exec` with user input | Injection; use prepared statements |
| Catch-and-ignore in API routes | Swallowing errors hides prod incidents; rethrow or return typed Result |
| Client fetch to `/api` from Server Components | Double hop; call the domain function directly on the server |
| Committing `*.db` files | Local-only; schema lives in migrations |

## Review checklist for Claude

1. Does this change need a migration? If yes, new file + index notes.
2. Is every user input zod-parsed before use?
3. Are secrets only in env, never in components/logs?
4. Did `npm run typecheck` and `npm test` pass?
5. Did you avoid touching unrelated files?
