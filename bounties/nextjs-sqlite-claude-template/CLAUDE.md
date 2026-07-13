# CLAUDE.md - Next.js 15 + SQLite SaaS

This project is a production-minded SaaS built with Next.js 15 App Router, TypeScript, React Server Components, and SQLite through either `better-sqlite3` for single-node deployments or Turso/libSQL for hosted edge-adjacent deployments.

Claude should make small, typed, database-safe changes that preserve App Router boundaries and keep SQLite boring.

## Stack And Versions

- Next.js 15 with App Router in `app/`
- React 19 Server Components by default
- TypeScript in strict mode
- SQLite as the primary relational store
- `better-sqlite3` for local/serverful apps, or `@libsql/client` for Turso
- Tailwind CSS plus small local UI primitives
- Zod for form/input validation
- Vitest for unit tests and Playwright for browser flows

Reason: this stack is fast for SaaS MVPs, but it becomes fragile when client/server boundaries and migrations are treated casually.

## Dev Commands

Prefer these commands and add missing scripts before inventing alternatives:

```bash
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm db:migrate
pnpm db:studio
```

If the project uses `npm` or `bun`, keep the existing package manager. Do not switch package managers in a feature PR.

Reason: package-manager churn creates noisy lockfile changes and slows review.

## Folder Structure

Use this structure for new code:

```text
app/
  (marketing)/
  (app)/
    dashboard/
    settings/
  api/
    webhooks/
components/
  ui/
  forms/
  data-display/
db/
  client.ts
  schema.sql
  migrations/
features/
  billing/
  auth/
  organizations/
  projects/
lib/
  auth.ts
  env.ts
  errors.ts
  result.ts
tests/
  unit/
  e2e/
```

Rules:

- Put route UI in `app/`, reusable UI in `components/`, and business workflows in `features/`.
- Put database access behind `db/` or feature-level repository modules, never inline in React components.
- Keep `lib/` small and cross-cutting. If a file only serves billing, auth, or projects, place it under `features/<name>/`.

Reason: SaaS projects grow around domains, not around generic utility folders.

## Naming Conventions

- Components: `PascalCase.tsx`
- Server actions: `actions.ts`
- Repository/database modules: `<domain>.repo.ts`
- Validation schemas: `<domain>.schema.ts`
- Tests: `<name>.test.ts` or `<flow>.spec.ts`
- Migration files: `YYYYMMDDHHMM_<verb>_<table>.sql`

Examples:

```text
features/projects/projects.repo.ts
features/projects/project.schema.ts
db/migrations/202607131030_create_projects.sql
```

Reason: predictable names let Claude and humans locate behavior without asking for orientation.

## App Router Boundaries

- Server Components are the default.
- Add `"use client"` only for state, effects, browser APIs, or interactive event handlers.
- Do not pass database records directly into Client Components if they contain private fields.
- Use route handlers under `app/api/` only for external clients, webhooks, or browser APIs that cannot use server actions.
- Use server actions for authenticated form mutations from the app UI.

Reason: unnecessary Client Components increase bundle size and often leak server-only assumptions.

## SQLite Access Rules

- All SQL must be parameterized.
- Wrap multi-step writes in transactions.
- Keep one database client module in `db/client.ts`.
- Do not open a new SQLite connection per request unless the chosen driver requires it.
- Enable foreign keys on connection startup:

```sql
PRAGMA foreign_keys = ON;
```

- Use ISO-8601 UTC text timestamps unless the existing schema already uses integer epoch milliseconds.
- Use explicit `created_at` and `updated_at` columns on mutable business tables.

Reason: SQLite is reliable when access is centralized and transaction boundaries are explicit.

## Migration Rules

- Never edit an applied migration. Add a new migration instead.
- Every schema change needs a migration file and, when practical, a rollback note in the PR.
- Migrations must be deterministic and safe to run once.
- Destructive migrations require a comment explaining the data loss and an explicit backup step.
- Prefer expand-and-contract changes:
  1. add nullable column or new table,
  2. backfill,
  3. switch reads/writes,
  4. remove old shape later.

Reason: SQLite has limited online DDL ergonomics; careful migrations prevent local and production data loss.

## Data Modeling

- Use integer primary keys or text UUIDs consistently with the existing project.
- For SaaS ownership, every tenant-owned row should include `organization_id`.
- Add indexes for foreign keys and common list filters.
- Prefer soft delete only when restore/audit is a real product requirement.
- Avoid JSON columns for relational data that needs filtering, joining, or constraints.

Reason: SQLite performs well for SaaS workloads when access paths are intentional.

## Validation And Errors

- Validate all user input with Zod at the boundary.
- Return typed results from server actions:

```ts
type ActionResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string; fieldErrors?: Record<string, string[]> };
```

- Do not throw raw database errors into UI.
- Log internal details on the server and show user-safe messages in the client.

Reason: predictable errors make forms easier to test and prevent leaking implementation details.

## Component Patterns

- Keep UI primitives in `components/ui`.
- Keep domain components near their feature when they encode business meaning.
- Prefer composition over prop explosion.
- Use forms with progressive enhancement: server action first, client enhancement only when it improves UX.
- Loading and empty states are required for every data list.

Reason: SaaS users repeat workflows; boring, consistent states are better than clever components.

## Auth And Authorization

- Authentication answers "who is this user?"
- Authorization answers "can this user do this in this organization?"
- Check authorization in server actions, route handlers, and repository functions that mutate data.
- Do not rely on hidden buttons as authorization.
- Webhooks must verify signatures before reading business payloads.

Reason: UI checks are convenience; server checks are security.

## Testing Expectations

For every meaningful change, add the smallest useful test:

- Pure logic: Vitest unit test
- Repository behavior: SQLite test database
- Critical workflow: Playwright e2e
- Migration: apply migrations to an empty database in CI

Minimum checks before finishing:

```bash
pnpm lint
pnpm typecheck
pnpm test
```

Reason: small SaaS regressions usually happen in forms, permissions, and migrations.

## What We Do Not Do

- Do not introduce Prisma unless the project already uses it.
  - Reason: this template is for direct SQLite/libSQL workflows; adding an ORM changes migration and runtime assumptions.
- Do not add global state for server data.
  - Reason: App Router already provides server data loading boundaries.
- Do not put secrets in `.env.example`.
  - Reason: examples should name variables, not leak values.
- Do not create API routes for internal form submissions by default.
  - Reason: server actions are simpler and keep validation close to UI mutations.
- Do not use raw string interpolation in SQL.
  - Reason: SQL injection is still possible with SQLite.
- Do not create "utils" dumping grounds.
  - Reason: vague folders hide ownership and create accidental coupling.
- Do not skip empty, loading, and error states.
  - Reason: SaaS dashboards spend real time in all three states.

## Before Changing Code

1. Identify the route, feature, and database tables involved.
2. Check existing package manager and scripts.
3. Check whether the change crosses a server/client boundary.
4. Check whether a migration is required.
5. State the smallest implementation plan before editing.

Reason: most bad changes in this stack start by editing the visible component before understanding the data path.

## Done Definition

A change is done when:

- TypeScript passes.
- Relevant tests pass or a clear test gap is documented.
- Migrations are included for schema changes.
- UI has loading, empty, and error states where applicable.
- README or inline docs are updated for new setup steps.
- No unrelated refactors or lockfile churn are included.

Reason: mergeable SaaS work is scoped, tested, and boring to deploy.
