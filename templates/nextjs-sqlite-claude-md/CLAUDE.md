# CLAUDE.md — Next.js 15 (App Router) + SQLite SaaS

> Paste this file at the root of a greenfield Next.js 15 + SQLite project.
> It teaches Claude Code (and any LLM agent) the project's hardcoded opinions
> so it stops asking clarifying questions and just builds.

---

## Stack & Versions (do not drift)

| Concern        | Choice                    | Why                                              |
|----------------|---------------------------|--------------------------------------------------|
| Framework      | Next.js 15 (App Router)   | Server Components by default; single deploy unit |
| Language       | TypeScript (strict)       | Catch shape mismatches at build, not in prod     |
| DB             | SQLite via `better-sqlite3` (local) or Turso (`@libsql/client`) in prod | Zero-ops, file/edge scale, no connection pool needed |
| ORM/Query      | **Raw SQL + a thin query module** | SQLite is fast enough that an ORM adds latency and hides the query plan |
| Auth           | Auth.js (NextAuth) v5, credentials + GitHub provider | Stable, framework-native, no external service for MVP |
| Styling        | Tailwind CSS v4           | Utility classes keep JSX readable; no CSS sprawl |
| Validation     | Zod                       | Single source of truth shared by route + form    |
| Tests          | Vitest + `node:test`      | Fast, no browser needed for unit/integration     |

Pin these in `package.json`. Do not silently upgrade major versions in a feature PR.

---

## Folder Structure

```
src/
  app/
    (marketing)/          # public pages: /, /pricing, /blog
    (auth)/               # /login, /signup — grouped, no URL prefix
    (app)/                # authenticated shell: /dashboard, /settings
      layout.tsx          # fetches session, redirects if null
    api/                  # route handlers (see "API rules")
  components/             # presentational, no data fetching
  lib/
    db.ts                 # single sqlite connection + migration runner
    queries/              # one file per domain: users.ts, invoices.ts
    auth.ts               # session helpers, getCurrentUser()
    validation.ts         # zod schemas
  migrations/
    0001_init.sql
    0002_add_invoices.sql # never edit a closed migration
  types/                  # generated or hand-written shared types
```

Rule: **a component never imports `lib/db` directly.** Only `lib/queries/*` and route handlers touch the database. This keeps data access auditable.

---

## SQL / Migration Conventions

- Every table has `id INTEGER PRIMARY KEY AUTOINCREMENT`, `created_at TEXT NOT NULL DEFAULT (datetime('now'))`, `updated_at TEXT NOT NULL DEFAULT (datetime('now'))`.
- Use `TEXT` for timestamps stored as ISO-8601 (`datetime('now')`), never Unix ints — SQLite has no native date type and this stays sortable and human-readable.
- **Migrations are append-only.** To change a table, write a new `NNNN_description.sql`. Never edit or renumber an existing migration. The runner applies only un-applied files in lexical order.
- Wrap multi-statement writes in `db.transaction(() => { ... })`. better-sqlite3 is synchronous; a transaction is one disk flush.
- Parameterize every query: `db.prepare('SELECT * FROM users WHERE email = ?').get(email)`. No template-string SQL — ever. (Prevents the #1 SQLite injection footgun.)
- One query per function in `lib/queries`. Name it by intent: `getUserById`, `listActiveInvoices`, not `query1`.

---

## Component Patterns

- Server Components fetch data and pass plain serializable props to Client Components. Client Components (`'use client'`) are for interactivity only (forms, dialogs, live state).
- A Client Component must never receive a `better-sqlite3` handle or a DB row with secrets. Pass only the fields the UI needs.
- Forms: validate with the shared Zod schema on the client for UX, then **re-validate on the server** in the route handler. Never trust client validation.
- Loading & error states use `loading.tsx` / `error.tsx` per route segment — do not hand-roll spinners inside page components.

---

## API / Route Handler Rules

- Route handlers live under `src/app/api/**/route.ts`. Export named `GET`/`POST`/etc.
- Every handler: parse → validate (Zod) → authorize (`getCurrentUser()`) → query (`lib/queries`) → return `Response.json({...}, {status})`.
- Return `401` before any DB call if unauthenticated. Return `404` for "not found by owner" (don't leak existence).
- Wrap handlers in `try/catch`; return `500` with `{error: 'internal'}` — never stack traces to the client.

---

## Dev Commands

```bash
npm run dev        # next dev on :3000
npm run db:migrate # node src/lib/run-migrations.ts
npm run db:reset   # delete dev.db, re-run all migrations (DEV ONLY)
npm run typecheck  # tsc --noEmit
npm run test       # vitest run
npm run lint       # next lint
```

`README.md` must list these exactly. If you add a command, add it here and to README in the same PR.

---

## What We Don't Do (and why)

- **No ORM** — raw SQL keeps the query plan visible; SQLite doesn't need one.
- **No global `prisma`/Drizzle client in components** — data access only via `lib/queries`.
- **No `any`** — strict mode is on; if a type is hard, define it in `src/types`.
- **No secrets in `.env` committed** — `.env.local` is gitignored; `.env.example` lists keys only.
- **No client-side SQL** — the browser never sees the DB. All access is server-side.
- **No editing closed migrations** — append-only, or you desync every other dev's DB.
- **No floating major-version bumps in feature PRs** — pin and discuss upgrades separately.
- **No `console.log` in production paths** — use the `lib/logger` if you need observability.

---

## Agent Ground Rules

- Before writing a query, check `src/lib/queries/` — reuse before adding.
- Before adding a column, check `src/migrations/` for the latest number.
- If a task needs a schema change, you MUST add a migration file AND update any affected Zod schema + query function in the same PR.
- Run `npm run typecheck && npm run test` before declaring done. A PR that fails CI is not done.
