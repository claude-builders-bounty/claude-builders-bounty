# CLAUDE.md — Next.js 15 + SQLite SaaS

Opinionated project guide. Claude Code: follow every rule here. Each rule
exists because the alternative has burned this project before.

## Stack & versions

- Next.js 15 (App Router, React Server Components by default)
- TypeScript strict mode. No `any` without a `// why:` comment.
- SQLite via better-sqlite3 (sync API, WAL mode). No ORM.
- Tailwind CSS 4 for styling. No CSS-in-JS, no styled-components.
- Node 20+. npm only - do not add yarn/pnpm lockfiles.

## Folder structure

```
app/                    # routes only. No business logic in route files.
  (app)/                # authed app routes
  api/                  # route handlers; thin wrappers over lib/
  layout.tsx            # one root layout; nested layouts only for real section shells
components/             # dumb UI. No data fetching here, ever.
lib/
  db/                   # connection.ts (singleton), migrations/, queries/
  actions/              # server actions, one file per resource
  domain/               # pure business logic, no imports from next/*
scripts/                # one-off operational scripts
tests/                  # vitest; mirrors lib/ structure
```

Rules:
- Data flows: `lib/db/queries/` -> `lib/actions/` -> `app/` pages. Never
  import from `lib/db/` inside a component or route file directly.
- `app/` files orchestrate; `lib/` files decide. If a route handler grows
  past 40 lines, the logic belongs in `lib/`.

## Naming conventions

- Files: kebab-case (`user-settings.tsx`). Components: PascalCase exports.
- Server actions: verbNoun (`createInvoice`, `archiveProject`).
- DB tables: plural snake_case (`user_sessions`). Columns: snake_case.
- Query functions: `getXByY` (`getUserByEmail`), `listX`, `insertX`, `updateX`.
- Booleans: `is/has/can` prefix everywhere, code and schema alike.

## SQL / migration conventions

- WAL mode and `foreign_keys = ON` are set in `lib/db/connection.ts`. Never
  override them per-query.
- Migrations live in `lib/db/migrations/`, named `NNNN_description.sql`,
  applied in order at startup by `lib/db/migrate.ts`. Never edit an applied
  migration - add a new one. Rollbacks are forward-only fix migrations.
- All SQL goes through prepared statements in `lib/db/queries/`. String
  interpolation into SQL is a bug by definition.
- Every table has `created_at` and `updated_at` INTEGER columns (unixepoch).
- No `SELECT *`. Name the columns. Schema changes are cheaper when readers
  declare what they need.
- Writes that belong together go in a `db.transaction()`. If you can't name
  the transaction boundary, you haven't found it yet.

## Dev commands

- `npm run dev` - dev server (Turbopack)
- `npm run build` - production build; must pass before every PR
- `npm run test` - vitest
- `npm run lint` - next lint + tsc --noEmit
- `npm run db:migrate` - apply pending migrations
- `npm run db:reset` - drop and reseed the dev database. Dev only; this
  script refuses to run with NODE_ENV=production.

## Patterns to follow

- Server Components fetch data; Client Components (`'use client'`) only for
  interactivity. Push the client boundary as far down the tree as possible.
- Mutations happen in server actions (`'use server'`) in `lib/actions/`.
  Validate every input with zod at the action boundary - never trust the
  client, including our own.
- Forms use `useActionState` + progressive enhancement: they must work with
  JS disabled.
- Errors: actions return `{ ok: false, error }` objects; they never throw
  across the boundary. Log the real error server-side.
- Auth checks live at the top of every server action and every (app) layout.
  No middleware-only auth - defense in depth.

## What we don't do (and why)

- No ORM. better-sqlite3 is fast, synchronous, and honest; an ORM hides the
  three queries that actually matter.
- No `SELECT *`, no N+1 in loops - batch with `WHERE id IN (...)`.
- No client-side data fetching libraries (SWR/React Query). The router is
  the cache; revalidate with `revalidatePath` after mutations.
- No environment-specific `process.env` reads outside `lib/env.ts`. One
  validated env module, imported everywhere else.
- No `Date` objects across the client/server boundary - serialize as ISO
  strings. Hydration mismatches are always timezone bugs in disguise.
- No barrel `index.ts` re-export files. They defeat tree-shaking and make
  refactors silent landmines.
