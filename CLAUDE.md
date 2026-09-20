# CLAUDE.md

This file is a template. Copy it to `CLAUDE.md` at the root of any greenfield
Next.js 15 + SQLite SaaS project. Read it fully before writing code; every rule
below exists because the opposite of it caused a real bug in this stack.

## Stack & versions

Pin these. Do not bump casually; each one is load-bearing.

- **Node.js >= 20 (LTS)**, enforced via `"engines"` in `package.json`.
- **Next.js 15, App Router only**, React 19.
- **TypeScript** in `strict` mode. No `// @ts-ignore`, no `any`.
- **SQLite via `better-sqlite3`**, accessed **only through Drizzle ORM**.
  - Why `better-sqlite3` over Turso/LibSQL: it runs in-process and synchronously,
    so transactions, `foreign_keys`, and locking behave exactly as the SQLite docs
    say — no network, no latency, no replica skew. Turso is reserved for the day we
    actually need horizontal read scaling; adopting it before that adds distributed
    failure modes to a problem a single file already solves.
  - Why Drizzle over Prisma: Prisma hides SQL behind a generated client and a query
    engine, which makes index usage, transactions, and raw SQL awkward. Drizzle keeps
    SQLite semantics visible, has zero runtime overhead, and lets us hand-write SQL
    for the 5% of queries that need it.
- **Tailwind CSS v4** for styling.
- **`zod`** for runtime validation of every input boundary.
- **`nanoid`** for ids. See "Naming conventions".

## Folder structure

```
.
├── app/                     # Next.js App Router tree — routing only
│   ├── (auth)/              # route group: signed-in flows
│   ├── (marketing)/         # route group: public pages
│   ├── api/                 # route handlers (REST) only
│   ├── layout.tsx           # root layout = only place for <html>/<body>
│   └── globals.css
├── components/
│   ├── ui/                  # presentational primitives, all Server Components
│   └── forms/               # interactive components ("use client" lives here)
├── db/
│   ├── schema.ts            # single Drizzle schema = source of truth
│   ├── migrations/          # generated SQL migrations (committed)
│   ├── client.ts            # better-sqlite3 singleton (globalThis-cached)
│   └── seed.ts              # idempotent dev seed
├── lib/
│   ├── auth/                # session, password, auth middleware
│   ├── validators/          # zod schemas, one file per mutation
│   └── email/               # transactional email
├── public/
└── env.ts                   # typed env access — the ONLY place process.env is read
```

Rules behind this layout:

- `app/` contains **zero business logic** — only routing, data fetching, and rendering.
  A file under `app/` that contains a SQL query and a file under `app/` that contains
  a `while` loop are both mistakes.
- Feature logic lives in `lib/`. UI lives in `components/`. The boundary is why we
  can delete a page without tearing out the product.
- One `db/schema.ts`, one migration per change, one seed file. Splitting schema into
  multiple files invites cross-file table references that are unreadable.

## Naming conventions

- **Files & directories**: lowercase kebab-case. `user-settings-page.tsx`,
  `create-billing-plan.ts`.
- **Component identifiers**: exported `PascalCase`, exported from a kebab-case file.
  A file defines one primary export.
- **Route handlers**: always named `route.ts`, one method per file.
- **DB tables**: plural `snake_case` (`subscription_charges`, `user_sessions`).
- **DB columns**: `snake_case`. Every table gets `id` (text PK, nanoid),
  `created_at` (TEXT ISO-8601 UTC), `updated_at` (TEXT ISO-8601 UTC).
- **Indexes**: `idx_<table>_<col1>_<col2>`.
- **Env vars**: `SCREAMING_SNAKE_CASE`, defined and validated once in `env.ts`, never
  read with `process.env` inline.
- **Ids**: `nanoid()` (21 chars). Never auto-increment integer ids: they leak row
  counts and enable enumeration/abuse via any public id endpoint.
- **Timestamps**: stored as ISO-8601 UTC `TEXT`. Comparisons are string comparisons;
  never call SQLite `datetime()` or timezone functions. Define "now" in one place
  (`db` helper), not ad-hoc.

## SQL / migration conventions

- The schema is defined **once** in `db/schema.ts`. `drizzle-kit` generates the SQL
  migration from it; never hand-write a schema migration.
- Order of operations on a schema change:
  1. edit `db/schema.ts`
  2. `npm run db:generate`
  3. **read** the generated SQL and sanity-check it
  4. `npm run db:migrate` locally
  5. commit schema, migration, and dependent code in the same PR
- `npm run db:push` is **dev-only**. CI and production run `npm run db:migrate`.
- Migrations are **additive only**: `CREATE TABLE`, `ADD COLUMN`,
  `CREATE INDEX`. Dropping or renaming a column is a two-step, cross-release process:
  add the new column and backfill in release N, remove the old one in release N+1
  after no code references it. Reason: SQLite `ALTER` support is minimal and teams
  that "just drop it" break running deploys mid-rollout.
- New columns are **nullable or have a default**, plus a data migration that backfills
  existing rows. SQLite cannot add a `NOT NULL` column without a default, and a
  non-backfilled column silently serves `NULL` to every existing row.
- Foreign keys: `ON DELETE RESTRICT` is the default. Use `CASCADE` only where deleting
  the parent must delete the children (e.g. account deletion removes sessions), and
  say why in a comment near the column.
- A mutation that touches more than one table is one transaction. No exceptions.
- `updated_at` is maintained by the app layer (`db` helper writes `now()`), not by
  SQLite triggers — triggers hide writes and break bulk operations.

## Component & data patterns

- **Default to Server Components.** Fetching data happens in server components or
  route handlers — never in a `"use client"` component.
- A file is marked `"use client"` **only** when it needs state, effects, or event
  handling. Keep those files as leaf components: pass serializable props down, and
  never re-fetch data a server component already fetched.
- Props are typed interfaces. No `any`, no non-null assertions to silence errors.
- Add `loading.tsx` / `error.tsx` per route segment that fetches server-side.
  Never throw inside `layout.tsx` — it takes the whole subtree with it.
- **Every mutation** (POST/PATCH/DELETE route handler, server action) validates input
  with a zod schema before touching the database, returns structured errors (not
  thrown strings), and writes inside a single transaction.
- Auth: session lives in an httpOnly, Secure, SameSite=Lax cookie. Auth middleware
  redirects; the route handler that uses the session re-verifies it. Never trust a
  claim the client sent, even if middleware "checked".
- Secrets and env: accessed **only** through the typed `env.ts` module. Never inline
  `process.env.FOO` in a component, route handler, or schema.
- Query results are not caches. Re-fetch is the default; reach for Next.js caching
  (`unstable_cache`, ISR) only when you can name the invalidation key.

## Dev commands

| Command | Purpose |
|---|---|
| `npm run dev` | local dev server |
| `npm run build` | production build — must pass before merge |
| `npm start` | run the production build |
| `npm run lint` | lint — must pass before merge |
| `npm run typecheck` | `tsc --noEmit` — must pass before merge |
| `npm run db:generate` | generate SQL migration from `db/schema.ts` |
| `npm run db:migrate` | apply migrations (CI / prod) |
| `npm run db:push` | dev-only schema sync |
| `npm run db:seed` | idempotent seed data |

Workflow: schema edit → `db:generate` → review SQL → `db:migrate` → commit schema +
migration + code together. Lint, typecheck, and build must be green before a PR.

## What we don't do (and why)

- **No Pages Router, no `getServerSideProps`/`getStaticProps`.** App Router is the
  only rendering boundary; parallel features are dead weight.
- **No Prisma.** See the Drizzle rationale above — generated clients hide SQL and
  make indexes and transactions guesswork.
- **No client-side database access.** `better-sqlite3` cannot run in the browser;
  loading it in a client bundle is a build error at best and a bloated bundle at
  worst. All reads/writes happen server-side.
- **No fetching business data with `fetch` inside client components.** Use server
  components and route handlers so auth and data stay on the server and the client
  only receives what it renders.
- **No module-scope singletons.** Next.js hot reload can instantiate a module twice;
  a singleton created at module scope silently becomes two connections. Cache
  `better-sqlite3` on `globalThis` in `db/client.ts`.
- **No new dependencies without a written reason.** Native modules compiled
  against one Node version break the next. A new dep must state the problem it
  solves that the current stack can't.
- **No plaintext or hashed-once passwords.** Use `argon2` (constant, we already run
  native `better-sqlite3`, so a native argon2 is not new risk).
- **No hand-written schema migrations.** Hand-written schema SQL drifts from
  `schema.ts` and the next `db:generate` fights your cherry-picked hunks. Hand-written
  SQL is allowed only for data backfills, wrapped in a transaction.
- **No `// @ts-expect-error` or `as any` to "move fast".** Type errors are bugs in
  disguise; fix the type.