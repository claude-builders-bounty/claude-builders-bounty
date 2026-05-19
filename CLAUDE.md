# CLAUDE.md

Project context for Claude Code working on a production SaaS built with Next.js 15 App Router, TypeScript, SQLite, and either `better-sqlite3` locally or Turso/libSQL in hosted environments.

## Stack And Versions

- Use Next.js 15 with the App Router. Put route handlers in `app/api/**/route.ts`, page UI in `app/**/page.tsx`, colocated loading/error boundaries beside the route they affect, and shared server code outside `app`.
- Use TypeScript in strict mode. Prefer explicit return types on exported functions, public helpers, and database access functions so Claude can reason about API boundaries without opening every callsite.
- Use SQLite as the source of truth. Local development may use `better-sqlite3`; production may use Turso/libSQL. Do not introduce Prisma, Drizzle, Postgres, MySQL, Redis, or a second queue/database unless a task explicitly asks for that migration.
- Use React Server Components by default. Add `"use client"` only for browser-only state, effects, event handlers, or third-party widgets that require the DOM.

## Project Structure

```text
app/
  (marketing)/             # public pages, pricing, docs, auth entry points
  (dashboard)/             # authenticated product UI
  api/                     # route handlers only
components/
  ui/                      # reusable primitives with no product-specific data fetching
  forms/                   # form components and field-level validation UI
features/
  billing/
  organizations/
  projects/
  users/
lib/
  auth/                    # session lookup, permission helpers
  db/                      # SQLite connection, migrations, repositories
  env.ts                   # typed environment parsing
  server/                  # server-only utilities
migrations/
  0001_initial.sql
tests/
  unit/
  integration/
```

Feature code should live under `features/<domain>` when it has product meaning. Shared code belongs in `lib` only when at least two features use it. This keeps SaaS domains discoverable and avoids a large generic `utils` folder.

## Commands

- `npm run dev` starts the Next.js dev server.
- `npm run lint` checks framework and TypeScript conventions.
- `npm run typecheck` runs `tsc --noEmit`.
- `npm test` runs the full test suite.
- `npm run db:migrate` applies SQL files from `migrations`.
- `npm run db:reset` recreates the local SQLite database from migrations and seed data.

When adding a command, document it in `package.json` scripts and make it work on macOS, Linux, and Windows shells. Claude should not suggest a command that only works in one shell unless the task is platform-specific.

## SQLite And Migration Rules

- Every schema change must be a new numbered SQL migration. Never edit an already-applied migration except in a throwaway branch before first merge.
- Migrations must be deterministic and idempotent where practical. Prefer `CREATE TABLE IF NOT EXISTS`, explicit indexes, and named constraints.
- Enable foreign keys on every connection with `PRAGMA foreign_keys = ON`.
- Use transactions for multi-statement writes. SQLite can leave partial state when separate statements are executed without a transaction.
- Keep timestamps as ISO-8601 UTC text unless an existing table already uses Unix milliseconds. Do not mix both in the same table.
- Store money as integer minor units plus a currency column. Do not store currency in floating point fields.
- Use soft deletes only for user-owned business records that may need audit history. Use hard deletes for ephemeral tokens, one-time codes, and cache rows.
- For Turso/libSQL compatibility, avoid SQLite extensions that are not available in the hosted runtime unless guarded by environment checks.

Database access should go through small repository functions in `lib/db` or the owning `features/<domain>` folder. Route handlers and React components should not build raw SQL inline because that spreads permission and transaction rules across the app.

## Data Access Pattern

Use prepared statements or the database client's parameter API for all user input.

```ts
export async function getProjectForUser(projectId: string, userId: string) {
  return db
    .prepare(
      `SELECT p.*
       FROM projects p
       JOIN memberships m ON m.organization_id = p.organization_id
       WHERE p.id = ? AND m.user_id = ?`,
    )
    .get(projectId, userId)
}
```

Do not concatenate SQL strings with request data. If a dynamic `ORDER BY` or column name is needed, map user input through an allowlist first.

## App Router Patterns

- Read authentication and authorization on the server before fetching product data.
- In route handlers, validate input at the boundary, call a service/repository function, and return `Response.json`.
- In server actions, validate `FormData`, perform the write in a transaction, call `revalidatePath` or `revalidateTag`, then return a small typed result object.
- Use `notFound()` for missing records only after checking the current user's access. Do not leak whether a private record exists.
- Use `redirect()` after successful mutations that change the main view state.

## Component Patterns

- Server components fetch data and pass plain serializable props to client components.
- Client components handle interactivity only. They should not import `lib/db`, read environment variables, or perform privileged fetches.
- Keep forms accessible: every input has a label, error text is associated with the field, and submit buttons show pending state.
- Prefer small feature-specific components over generic configurable components. A reusable component is justified only after a second real use case exists.
- Use stable empty/loading/error states for every dashboard table and list. SaaS users need to know whether data is loading, absent, or inaccessible.

## Naming Conventions

- Files and folders use kebab-case: `project-settings-form.tsx`.
- React components use PascalCase: `ProjectSettingsForm`.
- Server actions end in `Action`: `updateProjectAction`.
- Repository functions describe both entity and access rule: `listProjectsForUser`, `getInvoiceForOrganization`.
- Boolean columns and props start with `is`, `has`, `can`, or `should`.
- SQL table names are plural snake_case. Column names are snake_case. TypeScript fields may be camelCase only after a deliberate mapper.

## Authentication And Authorization

- Authentication answers "who is this user"; authorization answers "can this user do this action". Keep them separate.
- Check organization membership before loading organization-owned data.
- Never trust organization IDs, role names, prices, or user IDs from the client.
- Session helpers should return `null` for anonymous users and throw only for invalid server configuration.
- Route handlers that modify data must check permissions inside the handler or service function, not only in the UI.

## Testing Rules

- Add unit tests for pure parsing, formatting, permission, and validation helpers.
- Add integration tests for route handlers, server actions, and database migrations.
- Every migration should be tested against a fresh database and, when changing existing tables, against a representative previous schema.
- Use a temporary SQLite database per test file. Tests should not mutate a developer's local database.
- Prefer assertions on persisted state over snapshot-heavy UI tests. Snapshot churn hides real regressions.

## Environment Variables

- Parse environment variables once in `lib/env.ts`.
- Fail fast for required server variables. Public variables must be prefixed with `NEXT_PUBLIC_`.
- Never read secrets in client components or files imported by client components.
- Provide `.env.example` with safe placeholder values whenever adding a new variable.

## What We Do Not Do

- Do not add a new ORM because a single query is awkward. Raw SQL is acceptable here because SQLite behavior and migration control matter.
- Do not put business writes directly in React components. Writes belong in server actions, route handlers, or service functions with permission checks.
- Do not add global state managers for server data. Use the App Router, cache invalidation, and local client state for UI-only interactions.
- Do not introduce background jobs without a durable execution plan. SQLite has no built-in distributed job queue.
- Do not hide errors with broad `catch` blocks. Log server errors with enough context, return safe messages to users, and preserve the original error for observability.
- Do not use destructive database commands in development scripts unless the script name includes `reset` or `destroy` and the command requires explicit confirmation.

## Claude Workflow

Before editing, identify whether the task touches UI, database schema, authorization, or deployment. Database and authorization changes require tests. Keep PRs narrow: one feature, migration, or bug fix at a time. After editing, run `npm run typecheck`, the smallest relevant test command, and any migration verification affected by the change.
