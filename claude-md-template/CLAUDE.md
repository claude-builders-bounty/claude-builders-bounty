# CLAUDE.md — Next.js 15 + SQLite SaaS

Project conventions for a SaaS built on Next.js 15 (App Router) and
SQLite. Every rule here is a decision, not a suggestion — each one carries
its reason. If a rule seems wrong for a specific case, raise it with the
human instead of silently deviating.

## Stack & versions

| Piece | Choice | Pinned |
|---|---|---|
| Runtime | Node.js | 20 LTS |
| Framework | Next.js (App Router) | 15.x |
| UI | React | 19.x |
| Language | TypeScript, `strict: true` | 5.x |
| Database | SQLite via `better-sqlite3` | 11.x |
| Validation | `zod` | 3.x |
| Tests | Vitest | 2.x |
| Styling | Tailwind CSS | 4.x |

- The database lives in **one SQLite file** on a persistent volume
  (`DATABASE_PATH`, default `./data/app.db`). SQLite is the production
  database, not a dev stand-in — because a single-instance SaaS does not
  need a database server, and one file means backups are a file copy.
- If this app ever deploys to multiple instances or serverless, the
  switch point is `src/lib/db/index.ts` only: move to Turso/libSQL,
  which speaks the same SQL dialect. Nothing else in the codebase may
  know which driver is in use — because driver lock-in spreads through
  every query if you let it.

## Folder structure

```
src/
  app/                    # Routes ONLY: page.tsx, layout.tsx, route.ts,
                          # loading.tsx, error.tsx. No business logic.
    (marketing)/          # Public pages (route group)
    (app)/                # Authenticated area (route group)
    api/                  # Route handlers ONLY for webhooks & public API
  features/               # One folder per domain feature
    <feature>/
      actions.ts          # Server Actions (mutations) for this feature
      queries.ts          # Read queries for this feature
      components/         # Components used only by this feature
  components/
    ui/                   # Shared dumb primitives (Button, Input, Dialog)
  lib/
    db/
      index.ts            # The ONLY database connection module
      migrations/         # NNNN_name.sql, append-only (see DB rules)
    env.ts                # Validated environment variables (zod, fail-fast)
    auth.ts               # Session helpers (server-only)
```

- A feature that needs a table, a mutation, and a screen gets a folder
  under `features/` — because code is found by feature, not by file
  type, once the app passes ~10 screens.
- Route files (`page.tsx`, `route.ts`) may import from `features/` and
  `components/` but contain no logic beyond wiring — because routes are
  the least testable files in Next.js, so we keep nothing valuable in
  them.

## Naming conventions

- **Files:** React components are `PascalCase.tsx` (`UserMenu.tsx`);
  every other module is `kebab-case.ts` (`format-date.ts`). Hooks are
  `use-*.ts` exporting a `useCamelCase` function.
- **Exports:** named exports everywhere; default exports only where
  Next.js requires them (`page.tsx`, `layout.tsx`, `route.ts` handlers
  are named). Mixed conventions make grep useless.
- **Server Actions** are verbs: `createInvoice`, `cancelSubscription`.
  **Queries** are nouns or `get*`/`list*`: `getInvoiceById`, `listInvoices`.
- **Database:** tables are `snake_case` plurals (`users`, `invoices`);
  columns are `snake_case`; a foreign key is `<singular>_id`
  (`user_id`); booleans are `is_*` / `has_*` / `can_*`; timestamps are
  `created_at` / `updated_at` stored as INTEGER unix milliseconds;
  enum-like columns are TEXT with a `CHECK` constraint, never a numeric
  code nobody can read in a raw dump.

## Dev commands

```bash
npm run dev          # dev server (Turbopack)
npm run build        # production build
npm run start        # run the production build
npm run lint         # ESLint
npm run typecheck    # tsc --noEmit — run before calling anything "done"
npm run test         # Vitest (unit + integration, in-memory DB)
npm run db:migrate   # apply pending migrations (scripts/migrate.ts)
npm run db:seed      # seed local dev data (scripts/seed.ts)
npm run db:reset     # delete the local DB file and re-migrate + seed
```

## Database & migration rules

1. **One connection, one module.** All database access goes through
   `src/lib/db/index.ts`, which opens a single shared `better-sqlite3`
   connection and is marked `import "server-only"`. The module sets
   `journal_mode = WAL`, `foreign_keys = ON`, `synchronous = NORMAL`,
   and `busy_timeout = 5000` on open. Never open a second connection —
   because `better-sqlite3` is synchronous and single-writer; stray
   connections are how "database is locked" bugs are born.
2. **Migrations are append-only.** Files in `src/lib/db/migrations/`
   are named `NNNN_short_name.sql` (`0001_create_users.sql`) and run in
   order by `scripts/migrate.ts`, each inside a transaction, recorded
   in a `_migrations` table. **Never edit, rename, or delete a migration
   that has been applied anywhere** — because two checkouts would then
   disagree about the schema with no error anywhere. Need a change?
   Write the next migration.
3. **Forward-only.** There are no down migrations. Rollback means a new
   migration that undoes the change — because a tested forward fix beats
   an untested down script at 2 a.m.
4. **Prepared statements only.** Values are always bound parameters
   (`db.prepare("SELECT … WHERE id = ?").get(id)`). String-interpolated
   SQL is forbidden — because that is the entire SQL-injection story.
5. **No ORM.** Schema truth lives in the migration SQL, queries are
   hand-written in each feature's `queries.ts` — because an ORM adds a
   second schema language and hides SQLite-specific behavior (WAL,
   typing quirks) that this stack depends on knowing.
6. **Multi-step writes run in one transaction** (`db.transaction(...)`)
   — because a SaaS write that half-lands (invoice without line items)
   is worse than one that fails loudly.
7. **Server-side only, Node runtime only.** Any route, action, or
   component that touches the DB runs on the Node.js runtime
   (`export const runtime = "nodejs"` where it isn't the default),
   never Edge, never middleware, never a Client Component — because
   `better-sqlite3` is a native Node module and Edge/middleware would
   crash at runtime, not at build time.
8. **No N+1.** Lists are fetched with JOINs or a single `IN (...)`
   query — because per-row queries inside a Server Component render are
   invisible in code review and brutal in production.
9. **Backups are file operations:** `VACUUM INTO` a timestamped copy
   nightly. Never commit a `.db` file to git (it is in `.gitignore`) —
   because a committed database is a leaked database.

## Component & data patterns

- **Server Components by default.** Add `"use client"` only to the leaf
  component that actually needs interactivity — because every client
  boundary ships JavaScript and gives up direct DB access.
- **Reads happen in Server Components** via the feature's `queries.ts`.
  **Writes happen in Server Actions** in the feature's `actions.ts`.
  Route Handlers under `app/api/` exist only for webhooks and public
  API consumers — because two write paths for the same mutation will
  drift apart.
- **Every Server Action starts with auth + validation:** check the
  session, parse input with zod, then act. No exceptions for "internal"
  actions — because Server Actions are public HTTP endpoints whether
  they feel like it or not.
- **Sessions are database-backed** (a `sessions` table, opaque token in
  an `httpOnly`, `SameSite=Lax` cookie). Not JWTs — because a SaaS must
  be able to revoke a session the moment a user logs out everywhere or
  an admin disables an account, and a stateless token cannot be revoked.
- **Forms** use Server Actions with `useActionState` for errors; every
  route segment ships a `loading.tsx` and an `error.tsx` — because
  spinners and error states are part of the feature, not polish.
- **Environment variables** are read only through `src/lib/env.ts`,
  which validates them with zod at startup and throws on a missing one.
  `NEXT_PUBLIC_*` is for genuinely public values only — because anything
  with that prefix is bundled into the browser, permanently.

## Testing

- Vitest. Query and action tests run against an **in-memory database**
  (`new Database(":memory:")` with all migrations applied) — because
  tests must prove the real SQL works, not a mock of it.
- A schema change is not done until a migration test applies cleanly on
  top of the previous migration set.

## What we don't do (and why)

- **Edit an applied migration** — because divergent schemas fail
  silently and surface as corrupted data weeks later.
- **Touch the DB from Client Components, middleware, or Edge routes** —
  because the native driver cannot run there and the failure is a
  runtime crash, not a type error.
- **Build SQL with string interpolation** — because bound parameters
  are free and injection is not worth one saved keystroke.
- **Add an ORM "to move faster"** — because the migration SQL is the
  schema's single source of truth and a second one always wins an
  argument at the worst time.
- **Use JWT sessions** — because they cannot be revoked, and revocation
  is a billing-and-security feature, not a nicety.
- **Fetch data in `useEffect`** — because it creates request waterfalls,
  spinner-first UX, and a second data path that bypasses `queries.ts`.
- **Put business logic in `page.tsx` or `route.ts`** — because routes
  are wiring; logic belongs in `features/` where it can be tested.
- **Use `any`** — because `strict` TypeScript is the cheapest test
  suite this project owns.
- **Reach for a Postgres/MySQL server "just in case"** — because one
  SQLite file is operationally free, and speculative infrastructure is
  how a small SaaS ends up administering a database instead of shipping.
- **Store money as floating point** — amounts are INTEGER cents in the
  DB and formatted only at display time, because floats make
  0.1 + 0.2 a billing bug.

## Working in this repo

- Before saying work is done: `npm run typecheck` and `npm run test`
  pass, and schema changes come with a new migration file.
- When adding a feature, create `src/features/<name>/` with `actions.ts`
  and `queries.ts` first; UI second.
- If these instructions and the code disagree, follow the code's
  *behavior*, flag the disagreement to the human, and update this file
  in the same change.
