# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated, production-ready context for Claude Code. Paste this file at the repo
> root of a greenfield Next.js 15 App Router + SQLite SaaS project. Every rule below
> exists because the alternative caused a real bug, incident, or painful refactor.

## 1. Stack & versions (pin these)

- **Next.js 15** (App Router only — no `pages/`)
- **React 19**, **TypeScript 5.x** (`strict: true`, `noUncheckedIndexedAccess: true`)
- **SQLite** via **Drizzle ORM** + `better-sqlite3` (local) or `@libsql/client` (Turso, prod)
- **Auth**: Auth.js (NextAuth v5) — credentials + OAuth
- **Validation**: `zod` at every boundary (form → route handler → DB)
- **Styling**: Tailwind CSS v4, `shadcn/ui` primitives
- **Package manager**: `pnpm` (lockfile committed)
- **Runtime**: Node 20 LTS

**Why pinned:** mixing Pages and App Router doubles the mental model and breaks RSC boundaries.
One router, one data-fetching story.

## 2. Folder structure (follow exactly)

```
app/
  (marketing)/            # public, statically optimised
  (app)/                  # authenticated shell (layout does auth check)
  api/
    webhooks/stripe/route.ts   # ONLY place that trusts a raw body
  layout.tsx  page.tsx  globals.css
lib/
  db/
    index.ts              # drizzle client singleton
    schema.ts             # ALL tables live here, nothing else
    migrations/           # generated SQL, committed
  auth.ts                 # auth config, exported handlers
  env.ts                  # zod-parsed process.env (fail fast at boot)
  validators/             # zod schemas, one file per domain
components/
  ui/                     # shadcn primitives, do not hand-edit
  <domain>/               # feature components
server/
  actions/                # 'use server' mutations
  queries/                # read helpers, always parameterised
tests/                    # vitest + playwright
```

**Rule:** colocate by feature, not by file type. `components/billing/` not `components/forms/`.

## 3. SQL & migration conventions

- **Every schema change = a committed migration.** Never `db:push` against a real DB.
- Generate with `pnpm drizzle-kit generate`, review the SQL diff, then `pnpm drizzle-kit migrate`.
- **Never use `DROP TABLE` or `TRUNCATE` in a migration that ships to prod without a backup step.**
- Tables are `snake_case`, singular (`user`, `invoice`), with `id TEXT PRIMARY KEY` (ULID) and
  `created_at`, `updated_at` (`INTEGER` epoch ms) on every table.
- **All queries parameterised.** Never string-interpolate user input into SQL. Ever.
- Foreign keys explicitly declared with `references()` and `onDelete` chosen deliberately
  (`cascade` only for true child records; `restrict` otherwise).
- Every `DELETE` has a `WHERE`. Bulk deletes are a reviewed, explicit operation, not a reflex.
- Wrap multi-statement writes in `db.transaction()`.

**Why:** migrations are the only auditable record of production schema; `db:push` has
silently dropped columns in prod before.

## 4. Data access patterns

- Reads → `server/queries/*.ts`, called from Server Components. Never fetch in a Client Component.
- Writes → `server/actions/*.ts` with `'use server'`, always `zod`-parse input first,
  always re-check authorization (never trust the client's claim of identity).
- **Auth check lives in `app/(app)/layout.tsx` AND inside every server action.** Defense in depth:
  layout protects rendering, the action guard protects the API surface.
- DB client is a **singleton** in dev (guard against HMR connection storms):
  ```ts
  const g = globalThis as { _db?: DB }
  export const db = g._db ?? createDb()
  if (process.env.NODE_ENV !== 'production') g._db = db
  ```

## 5. Component patterns

- Server Components by default. Add `'use client'` only for interactivity, and only at the leaf.
- Forms: Server Action + `useActionState`; never hand-roll `fetch` to your own API route.
- Loading states: `loading.tsx` + Suspense; errors: `error.tsx` per segment.
- Environment variables: import from `lib/env.ts`, never read `process.env` directly in components.
- Mutations return a typed `{ ok: true } | { ok: false, error: string }`; never throw across the boundary.

## 6. Anti-patterns — do NOT do these (and why)

| Don't | Why |
|---|---|
| Fetch your own `/api` route from a Server Component | Extra network hop; call the query/action directly. |
| `useEffect` + client fetch for initial data | Waterfalls, no SSR data, worse Core Web Vitals. |
| Read `process.env.X` deep in the tree | Bypasses validation; missing var fails at runtime, not boot. |
| String-concatenated SQL | SQL injection. There is no safe version. |
| `DROP TABLE` / `TRUNCATE` in a shipped migration | Irreversible data loss; requires an explicit backup + approval. |
| Secrets in `NEXT_PUBLIC_*` | They ship to the browser. |
| `any`, `@ts-ignore` | Hides real bugs; `unknown` + zod at boundaries instead. |
| Auth check only in the layout | Server actions are callable directly; guard them too. |
| `db:push` on any real database | Skips migration history; drift is silent until it breaks. |
| Global mutable module state for request data | Leaks across requests on serverless; use request scope. |

## 7. Dev commands

```bash
pnpm install
pnpm dev                 # next dev (turbopack)
pnpm lint                # eslint + tsc --noEmit
pnpm test                # vitest
pnpm test:e2e            # playwright
pnpm db:generate         # drizzle-kit generate
pnpm db:migrate          # drizzle-kit migrate
pnpm db:studio           # inspect local db
```

A task is **not done** until `pnpm lint && pnpm test` pass.

## 8. Definition of done (per task)

1. Types pass (`tsc --noEmit`), lint passes, tests pass.
2. New logic has a test; new schema has a migration.
3. No `process.env` outside `lib/env.ts`.
4. No `any`, no `@ts-ignore`, no commented-out code.
5. Server action re-validates authz even if the UI already restricts it.
