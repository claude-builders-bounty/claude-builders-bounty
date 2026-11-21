# CLAUDE.md

Opinionated project rules for this codebase. Follow them literally —
each rule exists because a past incident, convention debt, or production
bug made it necessary.

## Stack & versions

- Next.js 15, App Router only. **No `pages/` directory, ever.** Mixing
  routers causes subtle routing/priority bugs that CI won't catch.
- React 19, Server Components by default. `use client` is an opt-in
  boundary, never a default.
- TypeScript strict. `any` requires a `// why:` comment explaining why
  the type can't be known.
- SQLite via `better-sqlite3` for app data, `drizzle-orm` for typed
  queries. **Never raw string-concatenated SQL** — parameterized
  queries only (`stmt.get(?, ?)` or Drizzle builders).
- Node 20+. pnpm only — the lockfile is `pnpm-lock.yaml`; do not
  generate `package-lock.json` or `yarn.lock`.

## Commands

- `pnpm dev` — dev server (port 3000)
- `pnpm build` — production build; must pass before committing
- `pnpm lint` — eslint + typecheck; zero warnings tolerated
- `pnpm db:migrate` — apply pending migrations
- `pnpm db:generate` — create a new migration from schema changes
- `pnpm test` — vitest

## Folder structure

```
app/                    # routes only: page.tsx, layout.tsx, route.ts
  (marketing)/          # route group: public pages
  (app)/                # route group: authed pages, enforces session in layout
  api/                  # route handlers; thin controllers only
components/             # dumb UI: props in, events out, no fetching
lib/                    # all business logic and data access
  db/schema.ts          # Drizzle schema — single source of truth
  db/migrations/        # generated SQL, committed, never hand-edited
  auth.ts               # session helpers
  actions.ts            # server actions, thin wrappers over lib/
tests/                  # mirrors lib/ layout
```

Why: fetching and rules live in `lib/` so components stay swappable
and testable; route files stay thin enough to review at a glance.

## Naming

- Files: `kebab-case.tsx` / `kebab-case.ts`. Components export PascalCase.
- DB: `snake_case` tables and columns, plural table names (`users`,
  `order_items`). Enums are `TEXT` with a `CHECK` constraint, declared
  in the schema — the DB must reject invalid states, not the UI.
- Env vars: `SCREAMING_SNAKE`, defined in `.env.example` with a comment
  per var; code reads them only through `lib/env.ts` (validated with
  zod at boot — a typo'd env fails fast, not at 3am).
- Routes: lowercase slugs; REST handlers named `route.ts`.

## SQL & migrations — non-negotiable rules

1. **Every schema change = a migration file.** Never mutate
   `schema.ts` without `pnpm db:generate`; a schema/migration drift
   silently corrupts prod data.
2. Migrations are committed and **never edited after merge** — write a
   new migration instead; edited migrations don't rerun on prod.
3. No destructive ops (`DROP`, `ALTER ... DROP COLUMN`) in a migration
   that ships the same day as the code removal — two-phase: deploy code
   that stops using the column, drop it a release later.
4. All queries parameterized. `db.exec("... " + userInput)` is a
   rejected PR, not a discussion.
5. Indexes declared in `schema.ts` for every column used in `WHERE`
   or `JOIN` — SQLite won't warn you about table scans.
6. `created_at`/`updated_at` are `INTEGER` (unixepoch), never `TEXT`
   timestamps — text dates can't be compared or indexed sanely.

## Patterns to follow

- **Data fetching in Server Components or `lib/` functions.** No
  `useEffect` fetching — waterfalls and flash-of-empty-state bugs.
- Mutations go through **Server Actions** in `app/.../actions.ts` or
  `route.ts` handlers, which call into `lib/`. Action bodies validate
  input with zod before touching the DB.
- Errors: throw `AppError` subclasses from `lib/errors.ts`; route
  handlers translate them to status codes. UI renders `error.tsx`
  boundaries — no `.catch(() => null)` that swallows failures.
- Auth: check session inside each `(app)` layout AND inside each
  server action — layouts alone leak on direct action calls.
- Transactions via `db.transaction(() => ...)` for any multi-statement
  write; partial writes are how accounts get double-charged.

## Anti-patterns (instant review blockers)

- `useEffect` + `fetch` for initial page data.
- `'use client'` at the top of a file that doesn't use hooks/events.
- Business logic inside `page.tsx`, `layout.tsx`, or JSX callbacks.
- `JSON.parse` / `JSON.stringify` on columns to fake relations — add a
  real table instead; unindexable blobs become unmigratable debt.
- `Date.now()` comparisons against `TEXT` timestamps.
- Secrets or DB files committed to git (`*.db`, `.env*` — see
  `.gitignore`).
- `console.log` left in committed code — use `lib/logger.ts`.
- Editing generated migration files by hand.

## Gotchas specific to this stack

- `better-sqlite3` is sync and runs on the **server only** — importing
  `lib/db` from a client component bundle fails the build.
- Next.js caches `fetch` and route handlers aggressively; mutating
  endpoints must opt out (`export const dynamic = 'force-dynamic'` or
  `revalidatePath` after writes) or users see stale data.
- SQLite is single-writer: long-running transactions during build or
  seed scripts will lock the DB — keep them short.
- RSC payloads are serializable only: no `Date`, `Map`, or class
  instances across the server→client boundary; convert at the edge.

## Definition of done

A change is done when: `pnpm lint` and `pnpm build` pass clean, new
behavior is covered by a vitest case, and any schema change ships with
its generated migration committed.
