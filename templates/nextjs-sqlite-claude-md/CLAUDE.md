# CLAUDE.md — Next.js 15 + SQLite SaaS

Opinionated working agreement for this repository. Every rule below exists because we
got burned by the alternative; the reason is written next to it. Follow it unless the
user explicitly overrides a rule in the conversation.

## Stack and versions

| Piece | Version | Why this one |
| --- | --- | --- |
| Next.js | 15.x, App Router | Server Components remove most client data-fetching code; the App Router is the supported path for 15.x |
| React | 19.x | Ships with Next 15; `use()` and actions are stable here |
| TypeScript | 5.7+, `strict: true` | Untyped data crossing a SQLite boundary is the most common source of runtime bugs in this codebase |
| SQLite | `better-sqlite3` 11.x | Synchronous API keeps route handlers simple; no connection pool to tune for a single-node SaaS |
| Validation | `zod` | One schema validates the API body, the server action and the test fixture |
| Runtime | Node 20+ | `node:test` and `node:sqlite` era; avoids extra test tooling |
| Tests | `node --test` | Zero dependencies, runs in CI with the same Node that serves the app |

Do **not** add an ORM (Prisma, Drizzle). Reason: our queries are hand-written SQL with
explicit column lists, and an ORM hides the plan from `EXPLAIN QUERY PLAN`. If a query
gets complex, optimise the SQL, not the abstraction.

## Folder structure

```
app/                      routes only; no business logic
  (marketing)/            public pages, no DB access
  (app)/                  authenticated pages
  api/<resource>/route.ts route handlers, one per HTTP verb
components/               shared UI, PascalCase files
lib/
  db.ts                   the only place that opens the database
  queries/<entity>.ts     every SQL statement lives here, typed
  validation/<entity>.ts  zod schemas shared by API and forms
db/
  schema.sql              current desired schema, human reference
  migrations/NNNN_*.sql   append-only, never edited
scripts/                  migrate, seed, reset
tests/                    node:test files, one per lib module
```

Reason: the folder tells an agent where a change belongs without reading the whole
codebase. If a file does not fit one of these buckets, the design is wrong, not the
structure.

## Dev commands

| Command | What it does |
| --- | --- |
| `npm run dev` | Next dev server on :3000 |
| `npm run build` | Production build; must pass before any PR |
| `npm run typecheck` | `tsc --noEmit` |
| `npm run lint` | `eslint .` (flat config; `next lint` is deprecated in Next 16) |
| `npm run db:migrate` | Applies unapplied `db/migrations/*.sql` in filename order |
| `npm run db:seed` | Inserts demo rows; refuses to run when `NODE_ENV=production` |
| `npm run db:reset` | Deletes the dev database and re-migrates + seeds |
| `npm run test` | `node --test` — auto-discovery; do not pass a directory, Node 24 rejects it |
| `npm run check` | `typecheck` + `test`; run this before declaring any task finished |

Never run `sqlite3` by hand against `data/app.db` to change schema. Reason: the next
`db:migrate` would disagree with reality, and the fix is manual archaeology.

## SQL and migration conventions

- **Migrations are append-only.** Never edit or renumber a file that may already have
  run anywhere; add `0007_fix_items_index.sql` instead. Reason: the `_migrations` table
  records only the filename, so an edited file silently does nothing.
- **One logical change per migration**, and the filename states it:
  `0006_add_items_archived_at.sql`.
- **Every migration must be safe to re-run on an empty database** and must not lose data.
  For a destructive change, write the new column, backfill, and only then drop the old
  one in a later migration.
- **No `DROP TABLE` / `DELETE FROM` without `WHERE`** in a migration. If a destructive
  migration is genuinely required, the PR description must say so explicitly.
- Tables: `snake_case`, plural (`items`). Columns: `snake_case` (`created_at`).
  Primary key: `id INTEGER PRIMARY KEY`. Foreign keys: `<entity>_id` with an index.
- Timestamps are `INTEGER` epoch milliseconds, never SQLite `TEXT` dates. Reason:
  arithmetic and indexing stay cheap, and JS `Date` round-trips without parsing.
- Always list columns explicitly: `SELECT id, title FROM items`, never `SELECT *`.
  Reason: adding a column must not silently change an API response shape.
- All values are bound parameters (`?`), never string interpolation. Reason: the one
  query built with a template literal is the one that gets injected.
- Multi-statement writes go inside a transaction:
  `db.transaction(() => { ... })()`.
- Enable `pragma journal_mode = WAL` and `pragma foreign_keys = ON` in `lib/db.ts`.
  Reason: readers stop blocking the writer, and ON DELETE CASCADE actually works.

## Component patterns

- **Server Components are the default.** Add `"use client"` only for state, effects or
  browser APIs, and keep those components leaf-level.
- **Only server code touches the database.** `lib/db.ts` is imported from server
  components, route handlers and server actions — never from a `"use client"` file.
- Mutations use **server actions** with a zod parse at the top; API routes exist for
  webhooks and third parties, not for our own forms.
- Every list route ships `loading.tsx`, and every page that can fail ships `error.tsx`.
- Props are typed with an explicit `Props` interface; no `React.FC`, no implicit
  children.

## Naming conventions

| Thing | Convention | Example |
| --- | --- | --- |
| Files and folders | `kebab-case` | `item-list.tsx`, `lib/queries/items.ts` |
| React components | `PascalCase` (file stays kebab-case) | `export function ItemList()` |
| Functions and variables | `camelCase` | `getItemsByUser` |
| Types and zod schemas | `PascalCase`, schema suffixed | `Item`, `ItemInputSchema` |
| DB tables / columns | `snake_case`, tables plural | `items.archived_at` |
| Env vars | `SCREAMING_SNAKE_CASE` | `DATABASE_PATH` |
| Route handlers | exported as the HTTP verb | `export async function POST()` |

## What we don't do (and why)

- **No ORM.** It hides the query plan and adds a build step for no benefit at this size.
- **No `SELECT *`.** Response shapes must change deliberately.
- **No unvalidated request bodies.** Every handler parses with zod first; `unknown` in,
  typed value out.
- **No `any`.** Use `unknown` plus a narrowing function; `any` disables the only safety
  net we have across the SQL boundary.
- **No database access from client components.** The DB file is not a browser API.
- **No editing shipped migrations.** See the migration rules above.
- **No secrets in the repo.** `DATABASE_PATH`, `SESSION_SECRET` and friends live in
  `.env.local`, which is git-ignored; `.env.example` documents them.
- **No `db:seed` in production.** The script checks `NODE_ENV` and exits non-zero.
- **No new dependency without asking.** Every dependency is a maintenance contract.

## Definition of done

1. `npm run check` passes (typecheck + tests).
2. A migration accompanies every schema change, and a test covers it.
3. Queries live in `lib/queries/`, validated inputs in `lib/validation/`.
4. The PR body lists what was verified and how, not what was intended.

## Environment

```
DATABASE_PATH=./data/app.db     # git-ignored directory
SESSION_SECRET=change-me        # required in production
NODE_ENV=development
```
