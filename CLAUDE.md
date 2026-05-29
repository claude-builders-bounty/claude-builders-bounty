# CLAUDE.md — Next.js 15 (App Router) + SQLite SaaS (Opinionated)

This file is the **operating system for contributions**. If you’re unsure, follow this over “common practice”.

## Stack + versions (assumed)
- Node.js: **20+** (LTS)
- Package manager: **pnpm** (preferred) or **npm**
- Framework: **Next.js 15** (App Router)
- UI: **React** (Server Components by default)
- DB: **SQLite**
  - Local/dev: `better-sqlite3`
  - Prod: **Turso** (SQLite over the network) is acceptable
- ORM/migrations: **Drizzle** (preferred). Raw SQL is allowed, but still must use migrations.

Why: this combo is fast to iterate, cheap to run, and has fewer moving parts than Postgres for early-stage SaaS.

## Prime directives
1) **Server-first**: do work in Server Components / route handlers / server actions first.
2) **Client code is expensive**: only mark `"use client"` when you need browser-only APIs or interactive state.
3) **No “magic” cross-layer access**: UI never imports DB code directly.
4) **Migrations are mandatory**: schema changes must be represented as migrations.
5) **Type safety is a feature**: keep types accurate; don’t `any` your way out.

## Project structure (recommended)
Use `src/` to keep imports clean.

```
src/
  app/                 # Next.js App Router (routes, layouts)
  components/          # shared UI components (mostly server components)
  db/
    client.ts          # SQLite client init (better-sqlite3 / turso)
    schema.ts          # Drizzle schema
    migrations/        # generated migration files (committed)
    migrate.ts         # migration runner used in dev/prod
  lib/
    auth/              # auth + session helpers
    billing/           # Stripe adapters (if present)
    env.ts             # env validation (zod)
    logging.ts         # structured logger wrapper
  server/
    actions/           # server actions (thin; call services)
    services/          # business logic (pure-ish; calls db)
    queries/           # read models / query helpers
  styles/
  types/
```

Why: `app/` stays focused on routing + UI composition; `server/` becomes the “backend” boundary for a monorepo-in-one.

## Naming conventions (strict)
- Files:
  - React components: `PascalCase.tsx`
  - Non-React modules: `kebab-case.ts`
  - Server actions: `*.action.ts` or `actions/*.ts` (pick one, be consistent)
- Exports:
  - Prefer **named exports** for everything except React pages/layouts.
  - One default export per file only when it’s a component matching the filename.
- Functions:
  - `verbNoun` (`createCheckoutSession`, `listInvoices`, `updateProfile`)
  - DB functions start with `db` or `query` (`queryUserById`, `dbInsertOrg`)

Why: predictable naming reduces “search time” and prevents duplicate functionality.

## Data + DB rules
### 1) DB access boundaries
- Only these layers may import `src/db/*`:
  - `src/server/services/*`
  - `src/server/queries/*`
  - `src/app/api/*` (route handlers) **only if** it calls a service/query module (no ad-hoc SQL in routes)
- UI components **never** import `db`, `schema`, or query builders.

Why: it keeps the UI refactorable and makes it possible to move to another backend later.

### 2) Migrations (Drizzle)
- All schema changes must be made via:
  1) update `src/db/schema.ts`
  2) generate migration into `src/db/migrations/`
  3) run migrations locally
- Migration files are **committed**.
- Never edit an old migration after it’s merged. Create a new migration instead.

Why: editing history breaks teammate environments and production rollout safety.

### 3) SQLite behavior gotchas (you must respect)
- SQLite is single-writer. Keep write transactions short.
- Prefer **explicit transactions** for multi-step writes.
- Add indexes intentionally; don’t guess—measure or reason from query patterns.

Why: “it worked on my laptop” breaks quickly with concurrency.

## API + validation
- Every external input is validated at the boundary:
  - Route handler input (query params, JSON body)
  - Server action input
- Use `zod` schemas in `src/lib/*` (or next to the boundary) and **parse** (not “type cast”).

Why: types don’t exist at runtime; validation prevents production corruption.

## Next.js App Router patterns
- Use Server Components by default.
- Prefer:
  - `app/(marketing)/...` and `app/(app)/...` route groups to separate concerns.
  - `loading.tsx` + `error.tsx` for UX and debuggability.
- Data fetching:
  - For authenticated user-specific data: `cache: "no-store"` or appropriate revalidate strategy.
  - Don’t call your own API routes from Server Components. Import services/queries directly.

Why: calling API routes from server code adds latency and duplicates validation/auth.

## Error handling + logging
- No silent failures.
- For server code:
  - Throw typed errors for “expected” failures (e.g., `NotFoundError`, `ForbiddenError`).
  - Log unexpected errors with context: userId/orgId/requestId where possible.

Why: SaaS dies by “mystery bugs” you can’t reproduce.

## Dev commands (expected)
Adjust to project package manager, but these commands should exist:
- Dev server: `pnpm dev`
- Typecheck: `pnpm typecheck` (or `pnpm tsc -p .`)
- Lint: `pnpm lint`
- Tests: `pnpm test` (if tests exist)
- DB migrate: `pnpm db:migrate`

Why: “one obvious way to run things” keeps velocity high.

## Anti-patterns (do not do these)
- Adding `"use client"` to “fix” an error without understanding it.
- Fetching DB data in the browser.
- Storing secrets in `NEXT_PUBLIC_*`.
- Skipping migrations (“just run this SQL manually”).
- Duplicating business rules in UI + server.
- Throwing raw strings as errors in server code.

## How to work (Claude-specific)
When you implement changes:
1) Identify the correct layer (UI vs server vs DB) before coding.
2) Make the smallest safe change that passes types/tests.
3) If you touch DB schema, include migration steps in the PR description.
4) Prefer refactors that reduce future bugs (clear boundaries, fewer side effects).
5) Ask one question only if blocked; otherwise make a reasonable assumption and proceed.

