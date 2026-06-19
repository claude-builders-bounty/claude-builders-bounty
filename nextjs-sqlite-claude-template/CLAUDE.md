# CLAUDE.md

## Stack

This is a SaaS app built with Next.js 15 App Router, TypeScript, React Server
Components, and SQLite.

Use `better-sqlite3` for local-first or single-node deployment. Use Turso/libSQL
for hosted SQLite. Default to Server Components; use Client Components only for
browser state, event handlers, animation, local form state, or APIs requiring
`window`.

## Folder Structure

```text
app/
  (marketing)/
  (app)/
  api/
components/
  ui/
  forms/
  data-display/
db/
  client.ts
  migrations/
  queries/
  schema.sql
lib/
  auth/
  config.ts
  errors.ts
  validation/
server/
  actions/
  services/
tests/
```

`app/` owns routes and route-specific actions. `components/ui/` contains reusable
primitives without business logic. `db/queries/` keeps SQL close to typed result
shapes. `server/services/` coordinates use cases that should not live in React
components.

## Naming

- Files and folders use kebab-case.
- React exports use PascalCase.
- Server actions end with `Action`.
- Query functions start with verbs: `listInvoicesByTeam`, `getUserByEmail`.
- Booleans read like predicates: `isOwner`, `hasActiveSubscription`.

## Commands

```bash
npm run dev
npm run lint
npm run typecheck
npm test
npm run db:migrate
npm run db:studio
```

If a command is missing, add it before documenting it.

## SQL And Migrations

- Every schema change gets a numbered migration in `db/migrations/`.
- Migration filenames use `YYYYMMDDHHMM_description.sql`.
- Migrations are forward-only. Do not edit a migration after it may have run.
- Wrap multi-statement migrations in a transaction when SQLite supports it.
- Prefer explicit column lists over `SELECT *`.
- Use ISO-8601 `TEXT` timestamps unless the project already uses Unix milliseconds.
- Enable `PRAGMA foreign_keys = ON` for local SQLite connections.
- Add indexes for real query shapes, especially tenant scope plus sort columns.

## Data Access

- Keep raw SQL in `db/queries/` or migration files.
- Validate external input before query functions.
- Return plain objects from query functions.
- Use transactions for multi-step writes.
- Map database errors to domain errors in `server/services/` or `lib/errors.ts`.

## Components

- Use Server Components by default for pages, layouts, and data-heavy views.
- Put Client Components at the smallest interactive leaf.
- Forms should have a validation schema, a server action, and a tiny client layer only when needed.
- Loading UI belongs in `loading.tsx` or a route-level skeleton.
- Error UI belongs in `error.tsx` or an explicit boundary.

## Route Handlers And Actions

- Server actions are for app-owned form mutations.
- Route handlers are for webhooks, public APIs, downloads, and integrations.
- Always authorize before mutating.
- Revalidate paths or tags after successful mutations.
- Never return secrets, raw SQL errors, stack traces, or database internals.

## Tenancy

Treat `team_id` or `organization_id` as required scope for SaaS data. Every
tenant-owned query must filter by tenant scope. Check membership before private
reads and role before writes.

## Anti-Patterns

- Do not put database queries in Client Components.
- Do not create generic abstractions before the second concrete use case.
- Do not silently coerce invalid form input.
- Do not edit shared migrations.
- Do not use `any` to bypass type errors.
- Do not add global state for server data.

## Before PR

Run `npm run lint`, `npm run typecheck`, `npm test`, and `npm run db:migrate`.
Include exact results or exact failures in the PR.
