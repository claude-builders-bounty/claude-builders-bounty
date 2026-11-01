# CLAUDE.md — Next.js 15 (App Router) + SQLite SaaS

> Opinionated. Every rule below has a reason. Do not relax a rule without
> understanding why it exists.

## Stack & versions

- Next.js 15 (App Router), React 19, TypeScript 5 (strict mode).
- SQLite via `better-sqlite3` in dev, **Turso (libsql)** in prod. Same
  driver API (`@libsql/client` is a drop-in; keep SQL portable).
- Node 20 LTS. pnpm, not npm/yarn.
- Tailwind CSS v4 + shadcn/ui. No CSS modules, no styled-components.
- Auth: Lucia v3 (or Auth.js v5). Sessions in SQLite, not JWT cookies.
- No ORMs. Raw SQL with a thin typed wrapper. Prisma/Drizzle are banned.

**Why no ORM:** ORMs hide the SQL that SQLite needs tuned (indexes, FTS5,
partial indexes). We write SQL. We own the query plan.

## Folder structure

```
app/                    # App Router: routes, layouts, server components
  (auth)/               # route group, no URL segment
  (app)/                # authenticated app shell
  api/                  # route handlers (webhooks only; prefer server actions)
components/             # shared UI (shadcn primitives live in components/ui)
lib/
  db.ts                 # single DB handle + migration runner
  auth.ts               # Lucia config
  queries/              # one file per domain, typed SQL helpers
  actions/              # server actions ('use server')
  validators/           # zod schemas, shared client+server
migrations/             # numbered .sql files, append-only
scripts/                # one-off CLIs (seed, backup)
public/
```

Rules:
- `lib/db.ts` is the only place that opens a DB connection. Import the
  exported `db` singleton everywhere else.
- Server components and server actions may import `lib/db`. Client
  components never import it (build will fail — keep it that way).
- One file per domain in `lib/queries/`. No god-files.

## Dev commands

```bash
pnpm dev          # next dev --turbopack
pnpm build        # production build (must pass before any PR)
pnpm lint         # eslint + tsc --noEmit
pnpm test         # vitest
pnpm db:migrate   # apply pending migrations
pnpm db:seed      # seed dev data
```

Never run `next dev` without `--turbopack` in this repo; the webpack path
is slower and masks HMR bugs.

## SQL / migration conventions

- Migrations are numbered, zero-padded, append-only: `0001_init.sql`,
  `0002_add_users.sql`. Never edit a merged migration; add a new one.
- Every migration must be idempotent-ish and reversible where cheap.
  Include a commented `-- rollback:` block.
- All tables have `id INTEGER PRIMARY KEY` (rowid alias) unless there is a
  specific reason (e.g. a natural key). Use `TEXT` for UUIDs only at
  boundaries; store as INTEGER internally.
- Every foreign key gets an index. SQLite does not auto-index FKs.
- Money/counts: INTEGER (cents or whole units). Never REAL for money.
- Timestamps: `INTEGER` epoch seconds (`unixepoch()`), not ISO strings.
  Store UTC only.
- Soft delete via `deleted_at INTEGER` (null = alive). Hard deletes only
  in migrations or GDPR flows.
- FTS5 for search; never `LIKE '%x%'` on large tables.
- Use transactions for multi-statement writes (`db.transaction(...)`).
- Prepared statements always. String interpolation in SQL is a bug.

**Anti-patterns (do not do):**
- `SELECT *`. Name columns.
- N+1 queries in server components. Batch with `IN (...)` or a join.
- Calling `db.prepare()` inside a request loop. Prepare once at module scope.
- Storing JSON blobs in columns for queryable data. Use real columns + indexes.

## Component patterns

- Server components by default. Add `"use client"` only when you need
  state, effects, or browser APIs. Justify it in a comment.
- Server actions for mutations (`'use server'`), with zod validation at
  the boundary. Never trust client input.
- Forms: `react-hook-form` + zod resolver, or plain `<form action={...}>`
  with `useActionState`. No Formik.
- Data fetching in server components via `lib/queries/*`. No `useEffect`
  fetching. No SWR/React Query unless realtime is required (then justify).
- Loading states via `loading.tsx` / Suspense, not spinners in components.
- Error boundaries via `error.tsx`. Never swallow errors silently.

## Naming conventions

- Files: kebab-case (`user-profile.tsx`). Components: PascalCase export.
- DB columns: snake_case. TS types: PascalCase. Variables: camelCase.
- Boolean columns: `is_*` / `has_*` / `deleted_at`.
- Route segments: kebab-case, plural nouns (`/users`, `/invoices`).

## What we don't do (and why)

- **No ORMs** — see above.
- **No client-side data fetching** — server components are faster and
  simpler; waterfalls are a smell.
- **No global state (Redux/Zustand)** unless a feature genuinely needs
  cross-tree shared mutable state. URL state (searchParams) first.
- **No `any`.** Use `unknown` and narrow. `any` disables the compiler.
- **No default exports for components** except pages/layouts (Next.js
  requires them). Named exports everywhere else.
- **No `console.log` in committed code.** Use a logger; remove debug logs.
- **No secrets in client bundles.** Only `NEXT_PUBLIC_*` is public.
  Server-only env vars must never be imported in client components.
- **No premature abstraction.** Three similar lines > a helper used once.

## Testing

- Vitest + React Testing Library. Playwright for E2E on critical flows.
- Test server actions via their zod schemas + a test DB (in-memory SQLite).
- Do not mock the database in unit tests; use `:memory:` SQLite.
- Every migration has a smoke test (apply + rollback) in CI.

## Commit / PR

- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`.
- One concern per PR. Squash-merge.
- `pnpm build && pnpm lint && pnpm test` must pass locally before pushing.

---

*Generated for Claude Code. If a rule conflicts with a newer Next.js
convention, the convention wins — update this file.*
