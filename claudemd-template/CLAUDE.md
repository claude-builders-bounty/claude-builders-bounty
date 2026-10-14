# CLAUDE.md

This file guides Claude Code when working in this repository. It is opinionated
on purpose: every rule below exists because the alternative has a specific
failure mode in a small-team SaaS. Follow these unless the user explicitly
overrides them.

## Stack & versions

- **Next.js 15** (App Router only — no `pages/`), React 19, TypeScript 5.7 (strict)
- **SQLite via better-sqlite3** 11.x — synchronous, embedded, zero-infra
- **Tailwind CSS 4** for styling — no other CSS approach
- **Vitest** for tests; `vitest run` must pass before any commit
- **Node 20 LTS**, npm for packages

Why better-sqlite3 over an ORM: at SaaS scale (<10k writes/day) the ORM's
abstraction costs more than it saves — migrations drift from the ORM schema,
N+1 queries hide behind pretty method calls, and the type layer lies about
nullability. Raw SQL + a thin typed wrapper keeps the query you wrote the
query that runs.

## Folder structure

```
app/                  # routes — App Router only
  (marketing)/        # public pages, no auth
  (app)/              # authenticated pages; layout enforces the session
  api/                # route handlers — thin: parse, call lib/, respond
db/
  migrations/         # 0001_name.sql, 0002_name.sql, ... (never edited once applied)
  index.ts            # the single better-sqlite3 Database instance
lib/
  queries/            # one module per domain: users.ts, invoices.ts, ...
  auth.ts             # session helpers
components/
  ui/                 # primitives (Button, Input, Card)
  <feature>/          # feature components, colocated with their route when single-use
```

New code goes in `lib/` or `components/`, never directly in `app/` route files
beyond composition — route files should stay under ~40 lines.

## SQL / migration conventions

1. Migrations are plain `.sql` files named `NNNN_snake_case.sql`, applied in
   numeric order. Never edit or delete an applied migration — write a new one.
2. Every migration runs inside a transaction (BEGIN/COMMIT in the file).
3. Every table has `id TEXT PRIMARY KEY` (ULID/UUIDv7), `created_at TEXT NOT
   NULL DEFAULT (datetime('now'))`, and `updated_at TEXT NOT NULL DEFAULT
   (datetime('now'))`.
4. Foreign keys: `user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE`
   unless a reason exists. `PRAGMA foreign_keys = ON` runs at connection open.
5. Queries live in `lib/queries/<domain>.ts` as exported functions with
   TypeScript input/output types. No SQL string building from user input —
   always bound parameters (`db.prepare('... WHERE id = ?').get(id)`).
6. Schema changes require a migration in the same change — never mutate schema
   from application code.

## Component patterns

- Server Components by default. Add `'use client'` only for components that
  use state, effects, or event handlers — and push it to the smallest leaf
  component, not the page.
- Data fetching happens in Server Components or route handlers, never in
  `useEffect`. Mutations go through Server Actions or `app/api/` handlers.
- One component per file, named exports (exception: Next.js pages/layouts use
  the required default export).
- Shared primitives in `components/ui/`; anything used once lives next to its
  route.

## Naming conventions

- Files: `kebab-case.tsx`. Components: `PascalCase`. Functions/variables:
  `camelCase`. DB tables/columns: `snake_case`, tables plural.
- Booleans: `is/has/can` prefix. Dates in the DB are ISO-8601 TEXT strings;
  convert to `Date` at the boundary, not in queries.

## Dev commands

```bash
npm run dev            # next dev
npm run db:migrate     # apply pending migrations (scripts/migrate.ts)
npm run db:new -- name # scaffold db/migrations/NNNN_name.sql
npm test               # vitest run
npm run lint           # next lint
```

## What we don't do (and why)

- **No Prisma/Drizzle/Kysely** — see the stack note above; raw SQL is the
  contract.
- **No `pages/` directory** — App Router only; mixing both doubles the mental
  model.
- **No `fetch()` in Client Components for initial data** — it forces
  loading-state UI for data the server already has.
- **No CSS-in-JS or CSS Modules** — Tailwind only; one styling system keeps
  the design tokens authoritative.
- **No barrel `index.ts` re-export files** — they create import cycles and
  slow cold builds.
- **No `any`** — `unknown` + narrowing. A type assertion is a code smell worth
  a comment explaining why it's safe.
- **No secrets in code** — `.env.local` (git-ignored); `NEXT_PUBLIC_` prefix
  means public — never put a secret behind it.

## When the user asks you to...

- **"add a feature"** — create the migration first (if schema changes), then
  the query module, then the route, then the component. In that order.
- **"fix a bug"** — write the failing test first, then fix.
- **"refactor"** — behavior must be identical; no drive-by renames.
