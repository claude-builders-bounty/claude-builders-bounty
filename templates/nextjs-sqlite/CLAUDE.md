# CLAUDE.md — Next.js 15 + SQLite SaaS

Copy this file to the root of a greenfield project. Everything below is a decision already made: follow it, don't ask about it. Every rule has a reason; if a rule blocks you, say so in your reply instead of silently working around it.

## Stack & versions

| Piece | Choice | Why |
|---|---|---|
| Next.js | 15.x, App Router only | `pages/` is legacy; mixing routers doubles the mental model |
| React | 19 | Required by Next 15; gives `useActionState`, `use` |
| TypeScript | 5.x, `strict: true`, `noUncheckedIndexedAccess: true` | Catches null rows from DB reads |
| Node | 22 LTS | better-sqlite3 prebuilds exist; pin in `.nvmrc` and `engines` |
| Package manager | pnpm | Strict node_modules, fast CI; commit `pnpm-lock.yaml` |
| DB | SQLite via `better-sqlite3` (sync driver) | One file, no network hop, trivially testable |
| Query layer | Hand-written SQL + `zod` row parsing. No ORM | SQL is the schema's source of truth; ORMs hide migrations and N+1s |
| Validation | `zod` | One schema serves forms, actions and API |
| Auth | `better-auth` or `auth.js` with DB sessions | Sessions in SQLite can be revoked; JWT-only can't |
| Styling | Tailwind CSS 4 + `shadcn/ui` copied into `components/ui` | No runtime CSS-in-JS, components are ours to edit |
| Tests | Vitest (unit/integration), Playwright (e2e) | Vitest is fast and ESM-native |
| Lint/format | ESLint (`next/core-web-vitals`) + Prettier | Format never debated in review |

Turso/libSQL instead of better-sqlite3: swap only `lib/db/client.ts`. Everything else talks to the `db` helpers, never the driver directly. That is the entire reason that file exists.

## Dev commands

```bash
pnpm install            # install deps
pnpm dev                # next dev --turbopack, http://localhost:3000
pnpm build              # production build; must pass before merging
pnpm start              # serve the production build
pnpm lint               # eslint
pnpm typecheck          # tsc --noEmit
pnpm test               # vitest run (uses in-memory SQLite)
pnpm test:e2e           # playwright test
pnpm db:migrate         # apply pending migrations to $DATABASE_PATH
pnpm db:new <name>      # create migrations/NNNN_<name>.sql
pnpm db:reset           # dev only: delete the DB file and re-migrate
```

Before saying a task is done, run `pnpm typecheck && pnpm lint && pnpm test`. Don't claim success without it.

Env vars live in `.env.local` (git-ignored); `.env.example` lists every key with a dummy value. Read env only through `lib/env.ts` (zod-validated at boot) so a missing variable fails at startup, not at 2am in a request.

`DATABASE_PATH` defaults to `./data/app.db`. `data/` is git-ignored.

## Folder structure

```
app/
  (marketing)/          # public pages, static where possible
  (app)/                # authenticated area; layout.tsx enforces session
  api/                  # route handlers: webhooks and third-party callbacks ONLY
  layout.tsx
components/
  ui/                   # shadcn primitives, no business logic
  <feature>/            # feature components, e.g. components/billing/
lib/
  db/
    client.ts           # the ONLY file importing better-sqlite3
    migrate.ts          # migration runner
    queries/            # one file per table/aggregate: users.ts, projects.ts
  actions/              # server actions, one file per feature
  auth/                 # session helpers: getSession(), requireUser()
  env.ts                # validated env
  validators/           # zod schemas shared by forms and actions
migrations/             # NNNN_name.sql, append-only
scripts/                # one-off tooling (migrate, seed)
tests/                  # mirrors lib/ ; e2e/ for Playwright
data/                   # SQLite files, git-ignored
```

Why: features read top to bottom (page → action → query). Only `lib/db/queries/` knows SQL, so a schema change touches one layer.

Use the `@/` alias (`@/lib/db/queries/users`), never `../../..`.

## Naming conventions

- Files and folders: `kebab-case.ts`. React components: `PascalCase` export, `kebab-case.tsx` file (`user-menu.tsx` exports `UserMenu`).
- Next special files keep their required names (`page.tsx`, `layout.tsx`, `route.ts`).
- DB tables: plural `snake_case` (`users`, `team_members`). Columns: `snake_case`. PK is `id`. FKs are `<singular>_id`. Timestamps are `created_at` / `updated_at`, stored as ISO-8601 UTC text. Booleans are `is_`/`has_` prefixed integers 0/1.
- Query functions: verb + noun: `getUserById`, `listProjectsForTeam`, `insertInvoice`, `updateProjectName`, `deleteSession`. Rows are mapped to camelCase TS types at the query boundary and nowhere else.
- Server actions: `<verb><Noun>Action` (`createProjectAction`).
- Zod schemas: `<name>Schema`; inferred types: `<Name>`.
- Migrations: `NNNN_verb_noun.sql`, 4 digits, e.g. `0003_add_projects_table.sql`.

## SQL / migration conventions

1. **Migrations are append-only.** Never edit or delete a migration that has been merged. Fix forward with a new file. Why: any deployed DB has already applied the old one; editing it creates silent drift.
2. **Plain `.sql` files**, applied in filename order inside a single transaction, tracked in a `_migrations(name TEXT PRIMARY KEY, applied_at TEXT)` table.
3. **No down migrations.** Rollback = restore the backup + deploy previous code. Why: down scripts are rarely tested and rarely correct. Take a file copy (`VACUUM INTO`) before migrating in production.
4. **One concern per migration.** Schema change and data backfill are separate files.
5. **Every table** has `id INTEGER PRIMARY KEY`, `created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))`, and `STRICT` mode. Why: STRICT stops SQLite silently storing a string in an integer column.
6. **Foreign keys on, always:** `PRAGMA foreign_keys = ON` is set in `client.ts` (SQLite defaults to off per connection). Declare `ON DELETE` explicitly.
7. **Also set** `PRAGMA journal_mode = WAL`, `PRAGMA busy_timeout = 5000`, `PRAGMA synchronous = NORMAL`. Why: concurrent reads during writes, no spurious `SQLITE_BUSY`.
8. **Index every FK and every column used in a `WHERE`/`ORDER BY` on hot paths.** Name indexes `idx_<table>_<cols>`.
9. **SQLite can't drop/alter many column things in place.** To change a column type: create the new table, copy, drop, rename, recreate indexes, all in one migration.
10. **Money is integer cents.** Never `REAL`. IDs exposed in URLs are random (`nanoid`) in a separate `public_id` column; don't leak autoincrement ints.
11. **Parameterized queries only:** `db.prepare('SELECT ... WHERE id = ?').get(id)`. Never interpolate user input into SQL. Dynamic identifiers come from a hard-coded allowlist.
12. **Multi-statement writes use `db.transaction(...)`.** better-sqlite3 is synchronous: never `await` inside a transaction callback.
13. Parse every row with a zod schema (or a typed mapper) before it leaves `lib/db/queries/`. `noUncheckedIndexedAccess` plus `.get()` returning `undefined` means handling "not found" explicitly.

Tests use `new Database(':memory:')` with all migrations applied via the real runner, so migrations are exercised on every run.

## Component patterns

- **Server Components by default.** Add `'use client'` only for state, effects, event handlers, or browser APIs; push it to the smallest leaf component. Why: less JS shipped, and DB access stays server-side.
- **Data reads** happen in Server Components by calling `lib/db/queries/*` directly. No internal `fetch('/api/...')` for your own data.
- **Mutations** are Server Actions in `lib/actions/`. Each one: (1) `'use server'`, (2) `requireUser()` first, (3) parse input with zod, (4) authorize against the resource (check ownership, not just login), (5) run the query, (6) `revalidatePath`/`revalidateTag`, (7) return `{ ok: true, data } | { ok: false, error }`. Don't throw for expected failures.
- **Forms:** `<form action={...}>` with `useActionState`; share the zod schema client and server. Server validation is mandatory, client validation is a nicety.
- **Route handlers (`app/api`)** only for webhooks (Stripe etc.) and external callers. Verify signatures. Why: actions already cover first-party mutations with CSRF protection.
- **Loading/error:** each route segment with data gets `loading.tsx` and `error.tsx`. Use `<Suspense>` around slow queries rather than blocking the page.
- **Props:** pass plain serializable data to Client Components; never pass DB handles or class instances.
- **Caching:** Next 15 does not cache `fetch` or GET handlers by default. Don't add `unstable_cache` until a measured need exists; SQLite reads are microseconds.
- **Dynamic APIs are async in Next 15:** `const { id } = await params`, `await cookies()`, `await headers()`.
- **Metadata:** export `metadata`/`generateMetadata` from pages; no manual `<head>`.
- `components/ui/` stays presentational. Business logic goes in feature components or `lib/`.

## What we don't do (and why)

- **No ORM (Prisma, Drizzle, TypeORM).** Migrations and queries are explicit SQL we can read and review.
- **No `pages/` router or mixing it with `app/`.**
- **No importing `better-sqlite3` outside `lib/db/client.ts`.** Keeps the Turso swap a one-file change.
- **No DB access from Client Components or `'use client'` modules.** It would break the build or leak server code.
- **No editing merged migrations.** See migration rule 1.
- **No `SELECT *` in application queries.** Name columns; adding a column mustn't change payloads or leak fields such as `password_hash`.
- **No string-built SQL.** Injection.
- **No `any` and no `as` casts to silence types** (use zod or a type guard). `@ts-expect-error` needs a comment with the reason.
- **No `useEffect` for data fetching.** Fetch on the server.
- **No global client state library (Redux, Zustand) by default.** URL search params and server state cover most SaaS UIs; add one only with a concrete need.
- **No `process.env` outside `lib/env.ts`.**
- **No secrets in client bundles.** Only `NEXT_PUBLIC_` vars reach the browser; never put keys in them.
- **No `console.log` left in committed code.** Use a small `lib/logger.ts`.
- **No new dependency without a one-line justification in the PR.** Prefer the platform and what's already installed.
- **No serverless deployment with a local SQLite file** (Vercel, Lambda: filesystem is ephemeral). Deploy to a long-running host with a persistent volume (Fly, Railway, a VPS), or use Turso.
- **No running multiple app instances against one SQLite file** on different machines. One writer host, or move to Turso.
- **No committing `data/*.db`, `.env.local`, or WAL/SHM files.**

## Working agreements for Claude

- Don't ask clarifying questions answered in this file. If something genuinely isn't covered, pick the option most consistent with these rules and state the assumption in one sentence.
- Make the smallest change that completes the task; don't refactor unrelated code.
- New feature checklist: migration → query functions (+ test) → zod schema → server action → UI. Add or update tests for each layer touched.
- Schema change? Create it with `pnpm db:new`, never hand-edit an applied migration, and run `pnpm db:migrate` + `pnpm test`.
- Commit messages: imperative, present tense (`Add projects table`), one logical change each.
