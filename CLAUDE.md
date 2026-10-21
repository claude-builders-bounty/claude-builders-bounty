# Project guide — Next.js 15 App Router + SQLite SaaS

Opinionated defaults for a greenfield SaaS. Each rule includes why so you can follow it without asking for clarification.

## Stack & versions
- **Next.js 15 (App Router) + TypeScript strict** — App Router is the supported path; pages router patterns create dual mental models.
- **SQLite via `better-sqlite3` locally, Turso (`@libsql/client`) in prod** — same SQL dialect, zero ops locally, hosted edge later.
- **pnpm** — lockfile + workspace-friendly; avoid mixing npm/yarn in the same repo.
- **Zod at boundaries** — validate request bodies and env once; do not re-validate deep in UI.

## Folder structure
```
app/                 # routes only (layouts, pages, route handlers)
components/          # UI primitives and feature widgets (no DB imports)
lib/db/              # schema helpers, queries, migration runner
lib/auth/            # session helpers
scripts/             # one-off jobs (seed, backfill)
db/migrations/       # numbered SQL files only
```
Why: keeps “HTTP edge” (`app/`) separate from “data” (`lib/db`), so route files stay thin and testable.

## Naming
- Files/folders: `kebab-case.ts` — greppable and OS-friendly.
- React components: `PascalCase.tsx`.
- Tables: `snake_case` plural (`users`, `billing_events`).
- Route handlers: prefer `app/api/<resource>/route.ts` over catch-all monsters.

## SQL / migration rules
1. **Every schema change is a new numbered file** in `db/migrations/` (`001_init.sql`, `002_add_users_email_unique.sql`). Why: diffs stay reviewable; no “edit the old migration” rewrites after merge.
2. **Migrations are append-only and idempotent where cheap** (`CREATE TABLE IF NOT EXISTS`, guarded `ALTER`). Why: local DBs and CI can re-run without drama.
3. **No raw SQL inside React components or Server Actions that also render UI.** Put queries in `lib/db/*.ts`. Why: UI churn must not break queries, and query reuse stays obvious.
4. **Transactions for multi-row writes.** Why: billing/seat updates must not half-apply.
5. **Prefer explicit column lists** over `SELECT *` in app code. Why: migrations that add columns should not silently change payload shapes.

## Dev commands
```bash
pnpm install
pnpm db:migrate          # apply db/migrations
pnpm dev                 # next dev
pnpm lint && pnpm test   # before opening a PR
```
Why: one happy path; if a command is missing, add a `package.json` script instead of documenting ad-hoc node one-liners.

## Component & data patterns
- **Server Components by default; `"use client"` only for interactivity** (forms with local state, charts). Why: less JS shipped, secrets stay server-side.
- **Load data close to the leaf that needs it** — avoid a root layout that fetches the whole universe. Why: cache granularity and fewer waterfalls.
- **Mutations go through route handlers or server actions that call `lib/db`**, then revalidate a tagged path. Why: one write path to audit.
- **Env via `process.env` read in `lib/env.ts` (Zod-parsed) only.** Why: fail fast on boot, not mid-request.

## What we don't do (and why)
- **No ORM “magic” in route handlers** — query builders/ORMs live behind `lib/db`. Why: route files stay readable in PR review.
- **No shared `utils.ts` god file** — prefer `lib/dates.ts`, `lib/money.ts`. Why: import graphs stay honest.
- **No skipping migrations “just this once”** on a shared DB. Why: teammate machines and prod diverge silently.
- **No client components importing `better-sqlite3` / fs.** Why: those APIs are Node-only and will break the bundle.
- **No drive-by refactors in feature PRs.** Why: review focus = the bounty/feature, not formatting noise.

## Greenfield checklist
1. `pnpm create next-app` (App Router, TS, ESLint).
2. Drop this file at the repo root as `CLAUDE.md`.
3. Add `db/migrations/001_init.sql` + `pnpm db:migrate`.
4. Put first queries in `lib/db/` and first UI in `components/` / `app/`.

If a change fights these rules, update this file in the same PR with a short reason — do not invent a parallel convention.
