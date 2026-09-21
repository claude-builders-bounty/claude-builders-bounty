# CLAUDE.md — Next.js 15 + SQLite SaaS

Production SaaS using Next.js 15 App Router, React 19, TypeScript, and SQLite.

## Stack and versions

- Next.js 15.x with App Router only.
- React 19.x and TypeScript 5.x with strict mode.
- Node.js 22 LTS.
- Package manager: pnpm.
- Database: SQLite via better-sqlite3 on the Node.js runtime.
- Validation: Zod at external boundaries.
- Styling: Tailwind CSS only.
- Tests: Vitest for unit/integration and Playwright for critical flows.

Reason: one explicit stack prevents parallel abstractions and keeps local and production behavior aligned.

## Commands

Use these commands as the project contract:

```bash
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm db:migrate
pnpm db:check
```

## Project structure

```text
app/                 routes, layouts, loading/error boundaries
components/          reusable UI; no data access
features/<name>/     feature-specific UI, schemas, server actions, services
lib/db/               connection, queries, transactions, migrations
lib/auth/             authentication and authorization helpers
lib/                  shared server/client utilities with narrow scope
public/               static assets
scripts/              one-off operational scripts
```

Rules:
- Keep route files thin: compose features, parse route inputs, and choose rendering behavior.
- Put business logic in `features/<name>/` or `lib/`, never directly in page components.
- A module that imports `better-sqlite3` must be server-only and must never enter a Client Component dependency tree.
- Prefer feature-local code until it is reused by at least two features; premature shared folders hide ownership.
- Use lowercase kebab-case for files and route segments, PascalCase for React components, camelCase for functions/variables, and singular SQL table names.

Reason: route/UI boundaries stay obvious and server-only database code cannot leak into browser bundles.

## App Router and component patterns

- Server Components are the default. Add `"use client"` only for browser state, effects, event handlers, or browser APIs.
- Fetch data in Server Components or server-side services; do not fetch your own Route Handler from the server.
- Use Server Actions for authenticated form mutations when the action is internal to this app.
- Use Route Handlers for public APIs, webhooks, callbacks, or clients outside the Next.js app.
- Validate every action/route payload with Zod before using it.
- Check authorization in the server action/service that performs the mutation, not only in UI visibility logic.
- After a mutation, invalidate only the affected cache path/tag; do not call broad refreshes without a reason.
- Keep Client Components small and pass serializable data into them.
- Use `loading.tsx`, `error.tsx`, and `not-found.tsx` at route boundaries instead of ad-hoc global loading/error state.

Reason: this preserves App Router streaming, avoids duplicate HTTP hops, and keeps security checks on the server.

## SQLite connection and query rules

- Open the database through one module: `lib/db/client.ts`. No direct `new Database()` outside it.
- Enable `PRAGMA foreign_keys = ON` on every connection.
- Enable WAL mode for the local/server SQLite file unless the deployment platform forbids it.
- Use parameterized SQL only. Never build SQL by concatenating user-controlled values.
- Keep queries in `lib/db/queries/<domain>.ts`; UI files do not contain SQL.
- Wrap multi-write business operations in a transaction.
- Select explicit columns in application queries; avoid `SELECT *` outside diagnostics/migrations.
- Add an index when a query used on a hot path filters or joins repeatedly on an unindexed column.
- Store timestamps as UTC ISO-8601 text unless integer epoch values are required for measured performance.
- Use integer `0/1` values for booleans and enforce valid values with `CHECK` constraints when practical.

Reason: SQLite is reliable when connection behavior, transactions, and schema constraints are predictable.

## Migration conventions

Migration files live in `lib/db/migrations/` and are named `NNNN_short_description.sql`, for example `0007_add_team_slug.sql`.

Rules:
- Migrations are append-only after merge. Never edit an applied migration; add a new one.
- Each migration must be deterministic and safe inside a transaction unless SQLite requires otherwise.
- Every schema change includes both the schema operation and any required data backfill.
- Add `NOT NULL` columns only with a safe default or a staged backfill.
- Preserve data during table rebuilds: create new table, copy explicit columns, validate counts, swap tables, recreate indexes/triggers.
- Track the applied migration number; rerunning migrations with nothing pending must make no changes.
- `pnpm db:check` runs `PRAGMA foreign_key_check` and fails on violations.
- Do not perform schema changes during ordinary server startup.

Reason: immutable migrations make database state reproducible and deploys auditable.

## Data model conventions

- Generate text primary keys in application code unless an integer key is clearly simpler.
- Name foreign keys `<entity>_id` and define `ON DELETE` behavior explicitly.
- Enforce unique business identifiers with database `UNIQUE` constraints.
- Store money as integer minor units such as `amount_cents`, never floating point.
- Tenant-owned tables include `tenant_id`; tenant queries scope by it in SQL.
- Soft deletion is opt-in, only when recovery or audit requirements justify it.

Reason: critical invariants belong in the database as well as application code.

## Error handling and testing

- Return typed domain failures for expected cases; reserve thrown errors for unexpected failures.
- Never expose raw SQLite errors, stack traces, tokens, SQL, or internal paths to clients.
- Unit-test pure business logic and integration-test database queries against a temporary SQLite database.
- Migration tests apply every migration from an empty database and run `PRAGMA foreign_key_check`.
- Add Playwright coverage for critical flows such as sign-in, onboarding, billing, and account changes.
- Before finishing a task run `pnpm lint`, `pnpm typecheck`, and the relevant tests.

## What we do not do (and why)

- No Pages Router: mixing routers duplicates routing/data conventions.
- No ORM by default: direct SQL keeps SQLite behavior, migrations, and performance explicit.
- No database calls from Client Components: credentials and server resources must stay server-side.
- No SQL string interpolation: parameterized SQL prevents injection and quoting bugs.
- No hidden schema synchronization at startup: production schema changes must be reviewed migrations.
- No business logic in React components: it becomes difficult to test and reuse.
- No `any` to silence TypeScript errors: model the boundary or narrow `unknown` instead.
- No broad cache invalidation when a specific path/tag is known: unnecessary invalidation wastes work.
- No new dependency when a small local function is sufficient: dependencies add supply-chain and maintenance cost.

## Default implementation choices

When a feature request leaves details unspecified, choose the smallest design consistent with these rules, existing repository patterns, and the current schema. Do not introduce a new framework, ORM, state library, queue, or service unless the task requires it.

For database work: inspect existing migrations and queries first, add the next numbered migration, update typed query/service code, add focused tests, run migration checks, then report exactly what changed.
