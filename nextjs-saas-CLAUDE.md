# CLAUDE.md — Next.js 15 + SQLite SaaS

This file tells Claude Code (and any engineer) how to work in this repository without asking
clarifying questions. Follow the rules below; each rule states its reason. If a change would
violate a rule, surface it in the PR description instead of silently deviating.

## 1. Stack & versions

| Layer | Choice | Reason |
| --- | --- | --- |
| Framework | Next.js 15 (App Router only) | Pages Router is frozen; App Router is the only supported direction in 15. |
| UI runtime | React 19 | Ships with Next.js 15; use server components by default. |
| Language | TypeScript, `strict: true` | SaaS code is long-lived; strict typing catches drift before review. |
| Database | SQLite — better-sqlite3 (server/sync) **or** Turso/libSQL (edge) | One file, zero ops for early SaaS; pick one driver per project, do not mix. |
| Query layer | Thin SQL helpers, no heavy ORM | SQL is portable and inspectable; an ORM hides N+1 and lock behavior we need to reason about. |
| Auth | Auth.js v5 (credentials + OAuth) | Keeps sessions server-side; never hand-roll password hashing. |
| Styling | Tailwind CSS 4 | Utility-first keeps component styles colocated with markup. |
| Package manager | `pnpm` | Lockfile is deterministic; use the version in `packageManager`.

Pinned versions live in `package.json` / `pnpm-lock.yaml`. Do not bump a major version inside a
feature PR; open a separate dependency-update PR.

## 2. Folder structure

```
.
├── app/                    # App Router routes, layouts, pages, route handlers
│   ├── (auth)/             # Route group: sign-in/sign-up, shared auth layout
│   ├── (dashboard)/        # Route group: authenticated app shell
│   ├── api/                # Route handlers only for webhooks / external APIs
│   ├── layout.tsx          # Root layout: <html>, fonts, providers
│   └── globals.css
├── components/
│   ├── ui/                 # Primitive, presentational, no data fetching
│   ├── features/           # Domain components composed from ui + data
│   └── providers/          # Client-side context providers
├── lib/                    # Framework-agnostic helpers (format, validate, constants)
├── db/
│   ├── index.ts            # Connection/singleton setup for the chosen driver
│   ├── schema.sql          # Current canonical schema (mirrors applied migrations)
│   ├── migrations/         # Numbered forward-only SQL files
│   └── queries/            # Parameterized query functions by domain
├── public/
├── tests/                  # Unit/integration tests mirroring lib/ and db/
└── CLAUDE.md
```

**Reason:** route code lives under `app/`, reusable UI under `components/`, pure logic under `lib/`,
and every SQL statement stays under `db/`. If a file does not fit one of these, that is a signal the
boundary is wrong.

## 3. Naming conventions

- Components: **PascalCase** file and export — `OrderCard.tsx`, `OrderCard`.
- Non-component modules: **kebab-case** — `format-currency.ts`, `session-guard.ts`.
- Query functions: verb-first, domain-scoped — `getOrdersByUser`, `createInvoice`, `markPaid`.
- Database tables: **snake_case** plural — `orders`, `invoice_items`; columns `created_at`, `user_id`.
- Files that export one component match the component name; no index barrels for small directories.

**Reason:** PascalCase immediately marks a file as renderable; snake_case matches SQLite/Postgres
conventions so data names do not translate twice between DB and code.

## 4. Database, SQL & migration rules

### Connection

- Open one cached connection per process (`db/index.ts`). Never `new Database()` inside a request
  handler — repeated opens leak file handles and break locking.
- For better-sqlite3, enable foreign keys (`PRAGMA foreign_keys = ON`) and WAL mode
  (`PRAGMA journal_mode = WAL`) at startup.

### Migrations

- Every schema change is a numbered file: `db/migrations/0001_init.sql`,
  `0002_add_invoices.sql`.
- Migrations are **forward-only**: once a migration has been applied anywhere, do not edit or rename
  it. Add a new migration that reverses or alters the change.
- Each migration is idempotent where possible (`CREATE TABLE IF NOT EXISTS`, guarded `ALTER`), and
  runs in a single transaction for DDL that the driver supports.
- Keep `db/schema.sql` regenerated to match the latest applied migration so a new developer can read
  the current shape in one place.

### Writing queries

- Always use **parameterized statements** (`?` placeholders). Never concatenate user input into SQL.
  ```ts
  // Good
  db.prepare("SELECT * FROM orders WHERE user_id = ?").get(userId);
  // Bad
  db.prepare(`SELECT * FROM orders WHERE user_id = ${userId}`);
  ```
- Keep queries short and explicit; avoid `SELECT *` in production code — name columns so adding a
  column does not silently widen the result.
- Put joins, filters, and aggregates in `db/queries/`, not inline in components or route handlers.
- Dates are stored as ISO-8601 text or Unix epoch integers; never rely on driver-local timezone
  defaults.

**Reason:** SQLite lock-write behavior and missing parameterization are the two most common
production incidents in small SaaS apps; these rules make both visible by default.

## 5. Component & data-fetching patterns

- **Server components by default.** A component becomes a Client component (`"use client"`) only when
  it needs interactivity (state, event handlers, browser APIs) or a client-only hook.
- Fetch data in **server components** or in `db/queries/` called from them. Do not use `useEffect` to
  load initial data the server could have rendered.
- Pass serializable props from server to client components. Do not pass DB row objects with
  functions; pass plain serializable fields.
- Presentational primitives in `components/ui/` must not fetch data or read cookies directly; the
  parent feature component supplies everything through props.
- Use streaming (`loading.tsx`, `Suspense`) for slow segments instead of blocking the whole route.

## 6. Mutations: Server Actions vs route handlers

- Prefer **Server Actions** for form mutations initiated inside the app (create/update/delete).
  Revalidate the relevant route with `revalidatePath` / `revalidateTag` after a successful action.
- Use **route handlers** only for external entry points: webhooks, OAuth callbacks, public API
  consumers that cannot call a server action.
- Every mutation validates input with a schema validator before touching the database, and checks
  ownership (`user_id` matches the session) before updating or deleting a row.

## 7. Dev commands

```bash
pnpm install        # install dependencies
pnpm dev            # start the dev server (App Router hot reload)
pnpm build          # production build (type-check + compile)
pnpm lint           # ESLint
pnpm test           # unit/integration tests
pnpm db:migrate     # apply pending migrations in order
pnpm db:studio      # open the local SQLite file for inspection (driver-specific)
```

Run `pnpm build` and `pnpm test` before opening a PR. A green build is the minimum review gate.

## 8. What we don't do (and why)

- **No Pages Router routes.** Mixing two routers doubles navigation and data-fetching mental models.
- **No raw SQL string interpolation.** It is the single easiest SQL-injection path; parameters are
  mandatory.
- **No secrets in client code.** Anything read by `"use client"` ships to the browser; secrets,
  connection strings, and service keys live in server-only environment variables.
- **No global mutable query cache outside the documented data layer.** Caching belongs in `lib/` or via
  Next.js cache tags, not ad-hoc module maps that drift per request.
- **No client-side auth checks as the only guard.** UI hiding a route is not authorization; every
  server action and data query re-checks the session and row ownership.
- **No edited applied migrations.** History must stay replayable; corrections are new migrations.
- **No ORM magic that hides queries.** If a relation fetch turns into N+1, it must be visible in
  `db/queries/` so it can be fixed.

## 9. Anti-patterns to catch in review

- `useEffect` + `fetch` on a route that could fetch on the server.
- A `"use client"` component that only renders static markup.
- `SELECT *` passed wholesale into a client component.
- A query that filters or updates without a `WHERE` on the owned row.
- Environment variables prefixed `NEXT_PUBLIC_` holding a secret.
- New dependency introduced without a note on why a standard library / existing package cannot do it.
- Schema changed in code but no migration file added.

When in doubt, default to the server, explicit SQL, and small pure modules — and note the tradeoff in
the PR description.
