# CLAUDE.md

> Project-level instructions for any Claude Code session working in this repo.
> This file is the source of truth. If a request conflicts with what is below, follow this file.

## Stack

- **Framework:** Next.js 15 (App Router only, no `pages/` directory).
- **Language:** TypeScript, `strict: true`. No `any`. No `// @ts-ignore`. If a type is genuinely impossible to express, use `// @ts-expect-error` with a one-line reason.
- **Database:** SQLite via `better-sqlite3` for local/single-node, or Turso (`@libsql/client`) for hosted/edge. Pick one per project; do not mix in the same repo.
- **Migrations:** plain SQL files in `db/migrations/NNNN_<name>.sql`, applied in order by a script in `db/migrate.ts`. No ORM-managed migrations.
- **Query layer:** raw SQL inside small typed functions in `db/queries/<domain>.ts`. No Prisma, no Drizzle, no query builders.
- **Validation:** Zod at every system boundary (route handler input, env var parsing, third-party API responses). Never inside pure functions.
- **Auth:** Lucia or `@auth/core` (NextAuth v5). Sessions in SQLite, not JWT.
- **Styling:** Tailwind v4. No CSS modules, no styled-components, no inline `style={{}}` outside of dynamic values that genuinely need it.
- **Testing:** Vitest for unit, Playwright for E2E. No Jest.
- **Package manager:** pnpm. Never `npm install` or `yarn add` in this repo.
- **Node:** the version pinned in `.nvmrc`. If absent, latest LTS.

## Folder structure

```
app/                       # Next.js App Router routes — co-located server actions and route handlers
  (marketing)/             # Public marketing routes — no auth
  (app)/                   # Authenticated app routes — wrapped in (app)/layout.tsx that enforces session
  api/                     # REST/webhook endpoints only — UI lives in (app)/
components/
  ui/                      # Pure presentational components — no DB, no auth, no fetch
  features/<domain>/       # Feature-scoped components — may call server actions
db/
  schema.sql               # Canonical schema — what the DB looks like after all migrations
  migrate.ts               # Migration runner
  migrations/NNNN_*.sql    # Forward-only migrations
  queries/<domain>.ts      # Typed query functions per domain
  index.ts                 # Exports the configured DB client
lib/
  env.ts                   # Zod-parsed env, exports a typed env object — import from here, never process.env
  auth.ts                  # Session helpers
  errors.ts                # Typed error classes
server-actions/<domain>.ts # Server actions per domain — input-validated with Zod, return discriminated unions
test/                      # Vitest tests, mirroring the source tree
e2e/                       # Playwright tests
```

Component files use **kebab-case** (`user-card.tsx`). Component names inside use **PascalCase** (`UserCard`). DB query functions use **camelCase** (`getUserById`). Migration files use **snake_case** with a 4-digit prefix (`0001_create_users_table.sql`). No exceptions.

## Database conventions

- **Forward-only migrations.** Never edit a migration after it has been merged to main. To change a table, write a new migration.
- **Every table** has `id INTEGER PRIMARY KEY AUTOINCREMENT`, `created_at INTEGER NOT NULL DEFAULT (unixepoch())`, and `updated_at INTEGER NOT NULL DEFAULT (unixepoch())`. Triggers update `updated_at`.
- **Foreign keys are mandatory** and `ON DELETE` is always specified explicitly (`CASCADE`, `RESTRICT`, or `SET NULL`). No implicit defaults.
- **Boolean columns** are `INTEGER` with a `CHECK (col IN (0, 1))` constraint. SQLite has no native boolean.
- **Timestamps** are `INTEGER` (unix epoch seconds), never `TEXT` ISO-8601. Convert at the application boundary.
- **JSON columns** are `TEXT` with `CHECK (json_valid(col))`. Always parse with Zod when reading.
- **Indexes** are named `idx_<table>_<columns>`. Every foreign key gets an index.
- **No SQLite triggers** for business logic. Triggers are only for `updated_at`.
- **Query functions** live in `db/queries/<domain>.ts`, return typed values, and prepare statements once at module load (`const stmt = db.prepare(...)`). Never build SQL strings with template literals at call time.
- **Transactions** wrap any multi-statement write. Use `db.transaction(fn)`.

## Component patterns

- **Default to Server Components.** Add `"use client"` only when you need state, effects, browser APIs, or event handlers.
- **Server Actions over API routes** for mutations triggered by the UI. API routes are for webhooks, OAuth callbacks, and third-party integrations.
- **Discriminated unions for action results:**
  ```ts
  type Result<T> = { ok: true; data: T } | { ok: false; error: string };
  ```
  Never throw across the server-action boundary. Throw inside, catch at the boundary, return a `Result`.
- **Forms** use `<form action={serverAction}>` directly. No `react-hook-form` unless you have a real reason (multi-step wizard, dynamic field arrays). Validation is server-side via Zod; client-side is progressive enhancement only.
- **Loading and error UI** lives in `loading.tsx` and `error.tsx` siblings. Do not hand-roll spinners inside components.
- **No `useEffect` to fetch data.** If you need client-side data, use a Server Component or a Server Action.
- **Suspense boundaries** wrap async Server Components that take >100ms.

## Environment variables

- All env access goes through `lib/env.ts`. Importing `process.env` directly anywhere else is a review-blocker.
- `lib/env.ts` parses with Zod at module load. Missing or invalid env crashes the app on boot, not at request time.
- Server-only env vars have no `NEXT_PUBLIC_` prefix. Client-exposed env vars are explicitly listed and Zod-validated separately.

## Dev commands

```bash
pnpm dev              # Next dev server with Turbopack
pnpm build            # production build
pnpm start            # production server
pnpm lint             # ESLint with the strict config
pnpm typecheck        # tsc --noEmit
pnpm test             # Vitest
pnpm test:e2e         # Playwright
pnpm db:migrate       # apply all pending migrations
pnpm db:reset         # WARNING destructive — drop and re-migrate (dev only)
pnpm db:shell         # open a sqlite3 REPL on the dev database
```

Before any commit, the pre-commit hook runs `pnpm lint && pnpm typecheck`. Do not bypass with `--no-verify`.

## What we do not do, and why

- **No ORM.** Drizzle and Prisma both win on ergonomics and lose on the ability to read the SQL you are actually running. Raw SQL in typed functions is faster to debug, faster at runtime, and forces the team to actually understand the database. The cost is some boilerplate; we accept that.
- **No `useEffect` data fetching.** Server Components and Server Actions cover the cases. `useEffect` for data fetching is a 2022 React pattern; in App Router it is a smell.
- **No JWT sessions.** Sessions live in SQLite. Revocation is one row delete. JWT revocation is a distributed cache problem we do not have.
- **No state-management library.** Server state lives on the server. Client state lives in `useState`/`useReducer`. We have not yet hit a case where Zustand/Jotai/Redux pulled their weight here.
- **No CSS-in-JS.** Tailwind covers it. The design system lives in `tailwind.config.ts` and `globals.css`.
- **No `npm install`.** pnpm is the only package manager. Mixing produces lockfile drift.
- **No comments that restate the code.** Comments are reserved for the *why* of a non-obvious choice, hidden constraints, or workarounds for specific bugs. `// increment counter` is noise.
- **No barrel files (`index.ts` re-exports)** in app code. They break tree-shaking and IDE go-to-definition. They are fine in `lib/` and `db/`.
- **No `any` to "make TS happy."** If a type is genuinely impossible, `unknown` plus a runtime narrow.
- **No silent catches.** `catch (e) {}` is a review-blocker. Every catch either rethrows, returns a typed error, or logs with a level appropriate to the failure.
- **No deletes against production without a migration.** If a column or table needs to go, write a migration. No manual DB changes ever.

## Workflow conventions

- **Branches:** `<author>/<short-description>` (e.g. `nobanks/add-billing-page`). One feature per branch.
- **Commits:** conventional commit prefixes (`feat:`, `fix:`, `chore:`, etc.) so the changelog generator can categorize. Do not group unrelated changes in one commit.
- **PRs:** describe the user-visible change, the failure modes considered, and how to verify locally. Screenshot or short clip for any UI change.
- **No merging your own PR without a review** unless the project's `MAINTAINERS.md` says otherwise.

---

If something in the codebase contradicts this file, it is the code that is wrong. Bring it back into line.
