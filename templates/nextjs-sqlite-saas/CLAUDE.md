# CLAUDE.md - Next.js 15 App Router + SQLite SaaS

Use this file as the default project memory for a greenfield SaaS built with
Next.js 15 App Router, TypeScript, Tailwind CSS, and SQLite through either
`better-sqlite3` for local-first apps or Turso/libSQL for hosted deployments.

## Stack And Versions

- Runtime: Node.js 22 LTS.
- Package manager: `pnpm`.
- Framework: Next.js 15 with the App Router only.
- Language: TypeScript in `strict` mode.
- Styling: Tailwind CSS plus small local components.
- Database: SQLite for development and tests; Turso/libSQL when remote writes or
  edge deployment are required.
- Validation: Zod at every server boundary.
- Tests: Vitest for unit tests and Playwright for user flows that cross routes.

Reason: this stack keeps the first product cheap, inspectable, and easy to
deploy without adding a second backend service before the product needs it.

## Project Structure

```text
app/
  (marketing)/
  (app)/
  api/
components/
  ui/
  forms/
  domain/
db/
  schema.sql
  migrations/
  queries/
  seed.ts
lib/
  auth/
  config/
  server/
  utils/
tests/
  unit/
  e2e/
```

Rules:

- Put route segments in `app/`, not in `pages/`. Do not create a `pages/`
  directory.
- Put reusable visual primitives in `components/ui/`.
- Put product-specific components in `components/domain/`.
- Put server-only helpers in `lib/server/` and import `server-only` at the top
  of files that must never ship to the client.
- Put SQL text in `db/queries/` when it is reused or has business meaning.
- Keep `db/schema.sql` as the readable current schema snapshot.
- Keep every migration in `db/migrations/` with a sortable timestamp prefix.

Reason: App Router code gets hard to review when server logic, route handlers,
and visual components are mixed together. This layout makes ownership obvious.

## Dev Commands

Use these commands unless the project defines stricter equivalents:

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm db:migrate
pnpm db:seed
```

Expected `package.json` scripts:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:e2e": "playwright test",
    "db:migrate": "tsx db/migrate.ts",
    "db:seed": "tsx db/seed.ts"
  }
}
```

Reason: Claude should be able to verify changes locally without guessing the
toolchain.

## Greenfield Bootstrap Checklist

For a new app, start from this shape:

```bash
pnpm create next-app@latest . --ts --tailwind --eslint --app --src-dir false
pnpm add zod better-sqlite3 server-only
pnpm add -D tsx vitest @playwright/test @types/better-sqlite3
mkdir -p db/migrations db/queries lib/config lib/server components/ui components/domain tests/unit tests/e2e
touch db/schema.sql db/migrate.ts db/seed.ts lib/config/env.ts
```

Then add the `package.json` scripts from this file and create the first
migration before building feature routes.

Reason: the first hour of a SaaS repo should establish repeatable folders,
commands, config, and migrations. Waiting until after feature work makes the
structure inconsistent and harder for Claude to follow.

## Environment Rules

- Read environment variables only through `lib/config/env.ts`.
- Validate environment variables with Zod once at startup.
- Never read `process.env` directly inside components, route handlers, or query
  helpers.
- Use `DATABASE_URL=file:./local.db` for local SQLite.
- Use `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` only in server-only modules.
- Never commit `.env`, local database files, or generated SQLite journal files.

Reason: centralized config prevents silent production defaults and keeps secrets
out of client bundles.

## Database And Migration Conventions

- Migrations are append-only. Never edit a migration after it has been applied.
- Migration filenames use `YYYYMMDDHHMM_description.sql`.
- Every table has:
  - `id TEXT PRIMARY KEY`
  - `created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP`
  - `updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP`
- Store timestamps as ISO-8601 text in UTC.
- Use foreign keys and enable them on every connection with
  `PRAGMA foreign_keys = ON`.
- Add indexes in the same migration that introduces the query needing them.
- Prefer explicit SQL over query-builder magic.
- Do not use `SELECT *` in application queries.
- Do not add nullable columns unless the empty state is a real business state.
- For destructive data changes, write a forward migration and a separate
  backfill script. Do not rely on manual database edits.

Reason: SQLite is reliable when the schema is boring, explicit, and easy to
diff. Migration rewrites destroy that property.

## Query Patterns

- Keep query functions small and named by intent, such as
  `getWorkspaceBySlug`, `listInvoicesForAccount`, or `createInvite`.
- Validate all external input before calling a query function.
- Return typed domain objects, not raw driver rows.
- Wrap multi-step writes in transactions.
- Put authorization checks before the write transaction starts.
- Use pagination for list queries from the start.
- Include stable ordering in every list query.

Reason: most SaaS bugs come from unclear ownership of validation,
authorization, and transaction boundaries.

## App Router Patterns

- Default to Server Components.
- Add `"use client"` only for state, browser APIs, event handlers, or client-only
  libraries.
- Use Server Actions for small authenticated mutations from forms.
- Use Route Handlers for webhooks, third-party integrations, file responses, or
  endpoints consumed outside the app.
- Keep `loading.tsx`, `error.tsx`, and `not-found.tsx` close to the segment that
  owns the user experience.
- Use `revalidatePath` or `revalidateTag` immediately after successful writes
  that affect cached UI.

Reason: Server Components keep data access simple and reduce client JavaScript;
Route Handlers should exist only when an HTTP API is the actual product surface.

## Component Patterns

- Components accept plain props and do not fetch data unless they are route-level
  Server Components.
- Forms keep field-level validation messages close to the field.
- Buttons that trigger writes must show pending state and prevent double-submit.
- Empty, loading, and error states are part of the component contract.
- Keep component files under 220 lines. Split by responsibility, not by visual
  decoration.
- Use accessible labels for every input and icon-only button.

Reason: SaaS screens are edited repeatedly. Small components with explicit
states stay testable after the first launch.

## Naming Conventions

- Route folders use kebab-case: `billing-settings`.
- React components use PascalCase: `InvoiceTable`.
- Hooks use camelCase with `use`: `useDebouncedSearch`.
- Server actions end with `Action`: `createWorkspaceAction`.
- Query functions use verb-first names: `listMembers`, `updatePlan`.
- Migration names use snake_case after the timestamp.
- Database table and column names use snake_case.

Reason: matching names across routes, components, actions, queries, and SQL
reduces lookup time for humans and agents.

## Authentication And Authorization

- Authentication answers "who is this user?"
- Authorization answers "can this user do this action on this resource?"
- Check authorization in server-only code for every mutation and private read.
- Do not hide unauthorized UI as the only access control.
- Include `workspace_id` or `account_id` in tenant-owned tables.
- Query tenant-owned records through helpers that require the tenant id.

Reason: multi-tenant data leaks usually happen when authorization is treated as
a UI concern.

## Testing Rules

- Add unit tests for query helpers that transform data or enforce business
  rules.
- Add one Playwright happy path for each revenue-critical flow.
- Test migrations against a fresh SQLite database.
- Include regression tests for authorization bugs and payment state changes.
- Do not mock the database for query tests; use a temp SQLite file.

Reason: this app type fails at boundaries: SQL, auth, billing, and form
submission. Tests should cover those boundaries first.

## What We Do Not Do

- Do not introduce Prisma by default. SQLite-first SaaS projects should keep SQL
  visible until the schema is complex enough to justify an ORM.
- Do not add Redux or global state for server data. Use the App Router data flow
  and URL state first.
- Do not put business logic in React components.
- Do not call third-party APIs from Client Components.
- Do not create a custom design system before the product has repeated UI
  patterns.
- Do not add background jobs without a concrete recurring task.
- Do not add edge runtime to routes that use Node-only SQLite drivers.
- Do not store money as floating point values. Use integer cents and currency
  codes.

Reason: each of these choices adds operational weight before the product has
proved it needs the complexity.

## How Claude Should Work In This Repo

Before changing code:

1. Read the closest route, component, action, query, and migration files.
2. Identify whether the change is UI-only, data-only, or crosses the boundary.
3. Check existing naming and folder patterns before adding a new abstraction.

When changing code:

1. Keep edits scoped to the feature.
2. Add or update migrations before changing query code.
3. Validate external input with Zod.
4. Keep server-only code out of Client Components.
5. Run `pnpm lint`, `pnpm typecheck`, and the narrowest relevant tests.

When blocked:

1. State the missing file, command failure, or unclear product decision.
2. Leave a minimal safe patch if possible.
3. Do not invent credentials, schema fields, or payment behavior.

Reason: the useful assistant is the one that preserves the product's shape while
moving the requested feature to a verifiable state.

## Smoke Test Prompt

After pasting this file into a greenfield repo, ask Claude:

```text
Create a workspace settings page with a server action that updates the workspace
name in SQLite. Include the migration, query helper, Zod validation, pending
form state, and the narrowest tests you would run.
```

Expected behavior:

- Claude should identify that this crosses UI, server action, query, and
  migration boundaries.
- Claude should create or reference `db/migrations/`, `db/queries/`,
  `lib/config/env.ts`, and route-level App Router files without asking which
  stack or folder structure to use.
- Claude should keep SQLite access in server-only code and avoid Client
  Component database calls.
- Claude should propose `pnpm lint`, `pnpm typecheck`, unit tests for query
  behavior, and a narrow Playwright flow if the page is user-facing.

Reason: this prompt exercises the exact decisions the template is meant to
settle: folder structure, mutation boundaries, migration rules, validation,
component state, and verification.
