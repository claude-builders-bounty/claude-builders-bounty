# CLAUDE.md — Next.js 15 (App Router) + SQLite SaaS Template

> Opinionated. Every rule has a reason. Paste into a greenfield project and Claude Code will understand the context without asking clarifying questions.

## Stack & versions

- Next.js 15 (App Router), React 19, TypeScript 5.x (strict)
- SQLite via `better-sqlite3` (dev) or Turso (`@libsql/client`) in prod
- Tailwind CSS 4, shadcn/ui components
- Zod for validation, `react-hook-form` for forms
- Auth: Auth.js (NextAuth v5) with credentials + OAuth
- No ORM. Raw SQL with parameterized queries. Migrations via a numbered `.sql` files folder.

## Folder structure

```
app/
  (auth)/          # auth routes (login, signup) — no layout chrome
  (dashboard)/     # authenticated app shell (layout with sidebar)
  api/             # route handlers only; thin, delegate to lib/
  layout.tsx       # root layout
components/
  ui/              # shadcn primitives — never edit, regenerate
  <feature>/       # feature-scoped components
lib/
  db.ts            # single DB client instance (singleton)
  queries/         # one file per domain, named exports of SQL functions
  actions/         # server actions ('use server')
  validators/      # zod schemas shared by client + server
migrations/        # 0001_init.sql, 0002_*.sql (numbered, never edited after merge)
```

## Dev commands

```bash
npm run dev          # next dev (Turbopack)
npm run build        # next build
npm run lint         # eslint + tsc --noEmit
npm run db:migrate   # run pending migrations
npm run db:reset     # wipe + migrate + seed (dev only)
```

## SQL / migration conventions

- One migration per logical change. Never edit a merged migration; add a new numbered file.
- Migrations are idempotent where possible (`CREATE TABLE IF NOT EXISTS`).
- All queries are parameterized. String interpolation of SQL is forbidden.
- Money stored as integer cents, never floats.
- Timestamps stored as ISO-8601 UTC text (`datetime('now')`).
- Soft-delete via `deleted_at` column, never hard delete user data.

## Component patterns

- Server components by default. `'use client'` only when state/effects/browser APIs needed.
- Colocate a component's types in the same file unless reused across 3+ files.
- Forms: `react-hook-form` + zod resolver, server action for submit, optimistic UI via `useOptimistic`.
- No `any`. If unavoidable, add a `// eslint-disable-next-line` with a reason.

## What we don't do (and why)

- **No Prisma/Drizzle.** Raw SQL keeps queries explicit and migrations reviewable; ORMs hide N+1s and generate opaque migrations.
- **No `useEffect` for data fetching.** Use server components or `react-query`. Effects for data fetching cause waterfalls and stale state.
- **No global state library beyond React.** Server state via react-query, UI state via useState/useReducer. Redux/Zustand add indirection we don't need.
- **No `any` or non-null assertions without a comment.** They defeat the purpose of strict TS.
- **No committing `.env` or DB files.** `.gitignore` covers them; CI fails if present.
- **No editing `components/ui/`.** Regenerate with shadcn CLI; local edits get overwritten.

## Naming

- Files: kebab-case (`user-profile.tsx`). Components: PascalCase. Hooks: `useXxx`.
- DB columns: snake_case. TS properties: camelCase, mapped at the query boundary.
- Route segments: kebab-case, lowercase.

## Anti-patterns to avoid

- Calling `db.prepare()` inside a loop — prepare once, run many.
- Holding a transaction open across an `await` (better-sqlite3 is sync; keep transactions sync and short).
- Fetching in client components when a server component can do it.
- Storing derived data; compute on read.