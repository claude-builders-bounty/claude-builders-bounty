# CLAUDE.md - Next.js 15 + SQLite SaaS

Use these instructions for a greenfield SaaS application built with Next.js 15 App Router, TypeScript, React Server Components, Tailwind CSS, and SQLite via better-sqlite3 or Turso/libSQL.

## Stack And Versions

- Next.js 15 App Router with `src/app`.
- TypeScript in strict mode.
- React Server Components by default.
- Server Actions for simple mutations; Route Handlers only for public APIs, webhooks, or third-party callbacks.
- SQLite for local-first persistence. Use `better-sqlite3` for single-node deployments and Turso/libSQL when an edge or hosted SQLite database is required.
- Tailwind CSS for styling. Keep component styling colocated with markup unless the project already has shared design primitives.
- Zod for input validation at every server boundary.

Reason: this stack keeps small SaaS projects fast to ship, cheap to host, and easy to reason about without introducing a service layer before it is needed.

## Folder Structure

```text
src/
  app/
    (marketing)/
    (app)/
    api/
    layout.tsx
    page.tsx
  components/
    ui/
    forms/
  db/
    client.ts
    migrations/
    schema.sql
    queries/
  features/
    billing/
    accounts/
    projects/
  lib/
    auth.ts
    env.ts
    errors.ts
    result.ts
  server/
    actions/
    services/
  tests/
```

Rules:

- Put route UI under `src/app`; put reusable business UI under `src/components`.
- Put feature-specific logic under `src/features/<feature>`.
- Put SQL access in `src/db/queries` and keep raw SQL out of React components.
- Put mutation entry points in `src/server/actions`.
- Use `src/lib/env.ts` as the only place that reads `process.env`.

Reason: App Router code gets messy when pages, database calls, validation, and business rules all live together. This structure keeps the route tree thin and makes data access testable.

## Naming Conventions

- Files that export React components use kebab-case: `project-card.tsx`.
- React components use PascalCase: `ProjectCard`.
- Server Actions use verb phrases: `createProjectAction`, `updateBillingEmailAction`.
- Database query functions describe the database operation: `insertProject`, `selectProjectById`, `listProjectsForAccount`.
- Zod schemas end with `Schema`: `createProjectInputSchema`.
- Database ids use `<entity>Id` in TypeScript and `<entity>_id` in SQL.

Reason: naming should reveal the boundary. A caller should know whether they are touching UI, validation, server mutations, or SQL.

## Database And Migration Rules

- Every schema change must be a migration file in `src/db/migrations`.
- Migration filenames use an ordered prefix: `0001_initial.sql`, `0002_add_accounts.sql`.
- Migrations must be idempotent where SQLite allows it.
- Never edit an already-applied migration. Add a new migration.
- Keep `src/db/schema.sql` as the current full schema snapshot.
- Use explicit constraints: `not null`, `unique`, `check`, and foreign keys.
- Enable foreign keys on every SQLite connection with `PRAGMA foreign_keys = ON`.
- Store timestamps as ISO-8601 UTC text unless the project already uses integer epoch milliseconds.
- Wrap multi-step writes in transactions.

Example table style:

```sql
create table accounts (
  account_id text primary key,
  name text not null check (length(name) between 1 and 120),
  created_at text not null
);
```

Reason: SQLite will let sloppy schema decisions survive for too long. Strong constraints and ordered migrations prevent silent data drift.

## Query Rules

- Prefer small, explicit SQL functions over generic repositories.
- Validate external input before calling SQL.
- Return plain objects, not database driver rows leaking unknown types.
- Keep authorization checks close to the query or service that reads private data.
- Never build SQL by string concatenating user input. Use parameters.

Example:

```ts
export function selectProjectById(db: Database, projectId: string) {
  return db
    .prepare(
      `select project_id as projectId, account_id as accountId, name
       from projects
       where project_id = ?`,
    )
    .get(projectId) as ProjectRow | undefined;
}
```

Reason: SaaS bugs often come from leaking tenant data, not from complicated algorithms. Explicit queries make authorization review easier.

## Server Actions

- Server Actions must live in `src/server/actions`.
- Each action validates input with Zod before doing work.
- Each action returns a typed result object instead of throwing expected validation errors.
- Throw only for unexpected infrastructure failures.
- Revalidate only the paths or tags affected by the mutation.

Preferred result shape:

```ts
type ActionResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: { code: string; message: string } };
```

Reason: predictable action results make forms easier to build and prevent accidental error disclosure to clients.

## Component Patterns

- Components are Server Components unless they need browser state, effects, refs, or event handlers.
- Add `"use client"` only to leaf components.
- Keep data fetching in Server Components or query functions, not in Client Components.
- Keep form state in small Client Components that call Server Actions.
- Prefer composition over large prop objects.
- Do not put feature-specific UI in `components/ui`; that folder is only for primitives.

Reason: unnecessary Client Components increase bundle size and make database boundaries easier to blur.

## Authentication And Authorization

- Treat authentication as identity only. Authorization must be checked per resource.
- Never trust account, team, or role ids coming from the client without verifying membership server-side.
- Centralize session lookup in `src/lib/auth.ts`.
- Use helper functions such as `requireUser()` and `requireAccountMembership(accountId)`.

Reason: multi-tenant SaaS apps fail when "logged in" is mistaken for "allowed to access this row".

## Environment Variables

- Define all environment variables in `src/lib/env.ts`.
- Validate them once with Zod at process startup or module load.
- Export typed values from `env`.
- Never read `process.env` from components, actions, or query files.

Reason: a single typed env module makes deployment failures obvious and avoids scattered runtime checks.

## Error Handling

- Use typed domain errors for expected failures such as `not_found`, `forbidden`, and `invalid_state`.
- Log infrastructure errors on the server with enough context to debug, but never include secrets.
- Show user-facing messages that explain the next action, not internal details.

Reason: clear error boundaries make the app safer for users and easier to operate.

## Testing Rules

- Unit test pure validation, formatting, and permission helpers.
- Integration test database query functions against a temporary SQLite database.
- Test Server Actions by passing validated fake sessions and a test database.
- Add a regression test for every bug fix.
- Do not mock SQLite for query tests; use a real temporary database.

Reason: SQLite tests are fast enough that mocking the database usually removes the behavior you need to trust.

## Dev Commands

Use these command names unless the project already has established scripts:

```bash
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm db:migrate
pnpm db:studio
```

Reason: predictable commands let agents and humans verify changes without reading the whole toolchain first.

## What We Do Not Do

- Do not add Prisma unless the project explicitly chooses it. SQL files are easier to audit for small SQLite SaaS apps.
- Do not put business logic in React components. Components render state; services enforce rules.
- Do not create generic CRUD abstractions before three features need the same pattern.
- Do not use Client Components for data fetching that can happen on the server.
- Do not add background job infrastructure for work that can be done synchronously in one request.
- Do not use `any` to bypass database row typing.
- Do not silently catch errors in Server Actions.

Reason: these shortcuts make early development feel faster, then slow every later change.

## Before Opening A PR

Run:

```bash
pnpm lint
pnpm typecheck
pnpm test
```

Then confirm:

- New migrations are additive and ordered.
- Server Actions validate input and check authorization.
- SQL uses parameters for all user-controlled values.
- Client Components are limited to interactive leaves.
- README or setup docs mention any new environment variables.
