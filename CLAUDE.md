# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

> Opinionated project guide for Claude Code (and human teammates) working on a
> Next.js 15 (App Router) + SQLite SaaS codebase.
> Every rule here exists because it saves real pain — not for decoration.

## Stack & Versions

- **Next.js 15** (App Router, Server Components by default), React 19
- **SQLite** via [better-sqlite3](https://github.com/WiseLibs/better-sqlite3) (local dev) — swap to Turso/libSQL in prod only when you actually need horizontal reads
- **TypeScript strict mode** — no `any` unless the boundary truly is untyped (JSON.parse, third-party SDKs)
- **Tailwind CSS** for styling; no CSS-in-JS libraries (they add a runtime cost to RSC payloads)
- **Zod** for every schema boundary: forms, API routes, DB writes
- **Node 20+** (>= 20.9, current LTS line)

## Folder Structure

```
app/
  (auth)/            # login/signup — group routes by concern, not by file type
  (dashboard)/       # authenticated app shell
  api/               # route handlers ONLY (thin: parse → validate → call service)
lib/
  db/                # db.ts (client singleton) + migrations/ + queries.ts
  services/          # business logic — no req/res types in here, ever
  validations/       # zod schemas (mirror the names of your domain objects)
components/
  ui/                # presentational (button, input, table) — no data fetching
  features/          # feature components — fetch data, compose ui components
public/
migrations/          # .sql files, numbered: 001_init.sql, 002_xxx.sql
```

Rule: **`app/` never contains business logic** — only routing + data wiring.
If a route handler grows past ~30 lines, move the logic to `lib/services`.

## SQL / Migration Conventions

- One migration file per change, strictly append-only: `migrations/001_…sql`, `002_…sql`
- Every migration runs exactly once, in order — never edit a migration after it's applied
- All tables get `id INTEGER PRIMARY KEY AUTOINCREMENT` (better-sqlite3)
- Timestamps are `TEXT` stored as ISO-8601 UTC (SQLite has no native datetime; don't fake one)
- Foreign keys must be enabled per connection: `PRAGMA foreign_keys = ON`
- **Never** use `DROP TABLE`/`ALTER TABLE ... RENAME` in a migration meant for production
  (SQLite ALTER support is limited — plan columns up front)
- Queries go in `lib/db/queries.ts` as small named functions; **no raw SQL scattered through components**

## Component Patterns

- Server Components by default; `"use client"` only when you need state/effects/events
- Client components are **leaf-first**: keep them small and push data fetching up to the server
- Forms: React Hook Form + Zod (`zodResolver`) — never hand-rolled validation
- Never fetch inside `useEffect` for initial data — do it in a Server Component or route handler
- `'use server'` actions for mutations that need auth; keep them one-layer-thin, call `lib/services`

## What We Don't Do (and why)

- **No `any`** — it silently turns type errors into runtime errors at the worst moment (checkout, billing)
- **No ORM for SQLite** — better-sqlite3 is synchronous and fast; an ORM hides the schema and makes migrations lie to you
- **No `N+1` queries in lists** — batch with `IN (...)`; SQLite is local, so this is cheap to do right
- **No server-side state in client components** — stale data bugs come from duplicating state; fetch at the boundary
- **No deleting user data hard** — soft-delete (`deleted_at`) unless a regulation demands otherwise
- **No new deps without a reason** — each dependency is a supply-chain and maintenance cost; prefer boring, maintained libraries

## Dev Commands

```bash
npm run dev          # dev server (http://localhost:3000)
npm run lint         # eslint — must pass before commit
npm run test         # vitest unit tests
npm run db:migrate   # apply pending migrations in order
npm run build        # production build — run before any PR
```

## Commit & PR Conventions

- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`
- Every PR: (1) what changed, (2) why, (3) how it was tested — screenshots for UI
- Run `npm run lint` + `npm run test` + `npm run build` locally before opening a PR
