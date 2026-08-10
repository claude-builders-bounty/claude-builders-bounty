# CLAUDE.md — Next.js 15 + SQLite SaaS

This file is the single source of truth for how to work in this repository.
Read it before making any change. When in doubt, the rules below beat your
instincts.

## Stack & Versions

| Layer | Choice | Version | Why |
|---|---|---|---|
| Framework | Next.js (App Router) | 15.x | Server Components by default, standard for SaaS in 2026 |
| Language | TypeScript | 5.x | Strict mode everywhere; `noUncheckedIndexedAccess` on |
| Database | SQLite via `better-sqlite3` | 11.x | Zero-ops, file-based, transactions, fast; perfect for a single-node SaaS |
| ORM | none — raw SQL in `src/db/queries/` | — | better-sqlite3 + raw SQL keeps migrations and behavior obvious |
| Migration | hand-written SQL in `src/db/migrations/` | — | No magic; schema is reviewable line by line |
| Auth | NextAuth.js (Auth.js) v5 | 5.x | Session strategy `database` so sessions live in SQLite |
| Styling | Tailwind CSS | 4.x | Utility-first, consistent with the team's velocity |
| Forms | Server Actions + `useActionState` | — | No client state library for forms; keep it simple |

**Do not add** an ORM, Redis, a queue, or a second database unless a task
explicitly asks for it. The project is deliberately small.

## Folder Structure

```
src/
  app/                  # App Router pages & route handlers
    (auth)/             # login / signup / forgot-password routes
    (dashboard)/        # authenticated, sidebar layout
      layout.tsx        # loads the session, redirects if unauthenticated
    api/                # route handlers ONLY when Server Actions can't do it
  components/
    ui/                 # presentational, no business logic (buttons, inputs…)
    features/           # one folder per feature: billing/, settings/, team/
  db/
    migrations/         # 001_init.sql, 002_*.sql … (append-only, never edit)
    queries/            # one file per aggregate: users.ts, teams.ts, invoices.ts
    schema.ts           # SQLite schema constants shared by queries
    client.ts           # better-sqlite3 singleton (see DB rules)
  lib/
    auth.ts             # Auth.js config (the only place auth logic lives)
    session.ts          # `getSession()` helper used by layouts
    validate.ts         # zod schemas per feature, colocated with routes
  middleware.ts         # edge middleware only for public/private routing hints
```

- **A feature owns its folder.** If you touch auth, you are in `src/lib/auth.ts`
  + `src/app/(auth)/`. If a change spreads across five unrelated folders,
  stop and reconsider the design.
- **No barrel files** (`index.ts` re-exports). Import from the real path.
- **No `utils.ts` graveyard.** Put a helper next to the code that uses it.

## SQL & Migration Conventions

1. **Migrations are append-only.** Never edit an existing migration file —
   even to fix a typo. Write a new one: `003_fix_typo.sql`. Existing
   databases must be able to replay `db/migrations/` in order and converge.
2. Naming: `snake_case` tables and columns; singular table names (`user`,
   not `users`). Foreign keys end in `_id` (`user_id`, `team_id`).
3. Every table gets: `id INTEGER PRIMARY KEY AUTOINCREMENT`, `created_at`
   (default `CURRENT_TIMESTAMP`), `updated_at` (default `CURRENT_TIMESTAMP`).
4. Foreign keys are **always** declared with `ON DELETE CASCADE` and
   `PRAGMA foreign_keys = ON` is set in `client.ts` at open time.
5. Queries live in `src/db/queries/<entity>.ts`. They are plain functions
   (`listInvoicesByUserId(userId)`), typed inputs, typed rows. No SQL strings
   in components — ever.
6. Use **named parameters** (`@userId`) in every prepared statement. Never
   string-concatenate user input into SQL. This is the #1 rule.
7. Wrap multi-statement writes in a transaction
   (`db.transaction(() => { … })()`). Single statements are implicitly atomic.
8. Prefer indexed lookups: any column used in a `WHERE` or `ORDER BY` that
   appears in production data gets an index in the same migration that adds it.

## Component Patterns

- Components are **Server Components by default**. Add `"use client"` only
  when you need state, effects, or event handlers — and keep those thin.
- Data fetching happens in the page or layout and is passed down as props.
  No data fetching inside feature components.
- Loading states: use `loading.tsx` + `Suspense` boundaries per route
  segment, not client-side spinners fetched in `useEffect`.
- Forms: Server Action + `useActionState`. The action returns
  `{ ok: true } | { ok: false, error: string }`. Never throw to render an
  error message.
- Buttons/inputs live in `components/ui/` and take props only — no data
  access, no router calls.
- Access control: check the session in the layout/server action. Never trust
  a client-side `useSession()` check for security decisions — it's only for
  UI hints.

## What We Don't Do (and Why)

- **No client-side data fetching with `useEffect` + `fetch`.** Server
  Components + Server Actions exist; adding a loading/error dance on the
  client for no reason doubles complexity and hurts TTFB.
- **No `any` or `@ts-ignore`.** Strict mode is on for a reason; if a type is
  fighting you, the code probably is too.
- **No global `components/ui/index.ts` or shared barrel.** See above.
- **No multiple databases / external services for features that fit SQLite.**
  A queue is a table (`jobs`), a cache is a column or table, rate limits are
  a table. Only leave SQLite when a task explicitly calls for it.
- **No raw `window`/`document` in Server Components.** If you reach for
  `typeof window !== 'undefined'` in a component, you are in the wrong file —
  the logic belongs in a `"use client"` leaf.
- **No `console.log` left in code.** Use the logger in `src/lib/logger.ts`
  if you need output; remove debug prints before finishing a task.
- **No editing migrations retroactively.** Covered above — repeated because
  it's the most common way to corrupt a production database.

## Dev Commands

```bash
npm install          # install deps (uses npm; lockfile is committed)
npm run dev          # start dev server on :3000
npm run build        # production build (must pass before any PR)
npm run lint         # eslint — must be clean
npm run typecheck    # tsc --noEmit — must be clean
npm run db:migrate   # apply pending migrations in order
npm run db:seed      # reset + seed a demo dataset
npm test             # vitest — unit tests for queries & lib
```

**Every task finishes with:** `npm run typecheck && npm run lint && npm test`
green, and if the change touches DB: `npm run db:migrate` on a fresh copy.

## Working Agreement

- Read the migration history before writing a new query.
- If a task needs a schema change, write the migration **first**, then the code.
- Smaller PRs review faster: one feature, one migration, one commit message
  in conventional format (`feat:`, `fix:`, `chore:`).
- If the acceptance criteria are ambiguous, ask — do not guess about
  security-relevant behavior (auth, billing, data deletion).
