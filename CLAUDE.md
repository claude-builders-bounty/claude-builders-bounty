# CLAUDE.md

This file is the operating guide for Claude Code in a production-minded
Next.js 15 SaaS application using the App Router and SQLite. Follow these
rules unless the user explicitly asks for a different architecture.

## Stack

- Next.js 15 with the App Router in `app/`.
- React Server Components by default. Use Client Components only for browser
  state, event handlers, focus management, optimistic UI, or third-party
  widgets that require the DOM.
- TypeScript in strict mode. Do not introduce `any` unless a boundary truly
  cannot be typed, and isolate it in one place.
- SQLite for application data, preferably through `better-sqlite3` for local
  or single-node deployments, or Turso/libSQL when the deployment target needs
  remote SQLite.
- SQL migrations are the source of truth. Generated schema helpers are allowed,
  but runtime code must not silently mutate schema.
- Authentication, billing, email, and analytics must be kept behind small
  adapter modules so the product code does not depend directly on vendors.

## Project Structure

Use this layout for greenfield work:

```text
app/
  (marketing)/
  (auth)/
  (dashboard)/
  api/
components/
  ui/
  forms/
  dashboard/
db/
  client.ts
  migrations/
  queries/
  schema.ts
lib/
  auth/
  billing/
  email/
  env.ts
  errors.ts
  logger.ts
  permissions.ts
server/
  actions/
  services/
  validators/
tests/
  fixtures/
  integration/
  unit/
```

`app/` owns routing, layouts, loading states, metadata, and thin route handlers.
Business logic belongs in `server/services/`. Database access belongs in
`db/queries/`. Shared UI belongs in `components/`, not inside route folders,
unless it is truly route-specific.

## Naming

- Files and folders use kebab-case: `team-switcher.tsx`, `create-invoice.ts`.
- React components use PascalCase exports.
- Server actions use verb-first names: `createProject`, `inviteMember`,
  `archiveWorkspace`.
- Query helpers describe data, not UI: `getWorkspaceBySlug`,
  `listInvoicesForWorkspace`.
- Boolean database fields use affirmative names: `is_active`, `email_verified`,
  `requires_2fa`.

## Environment

All environment variables must be parsed in `lib/env.ts`. Never read
`process.env` directly from feature code.

`lib/env.ts` should validate required values at startup and expose a typed
object:

```ts
export const env = {
  DATABASE_URL: requireEnv("DATABASE_URL"),
  APP_URL: requireEnv("APP_URL"),
  NODE_ENV: process.env.NODE_ENV ?? "development",
}
```

Use explicit defaults only when the default is safe in production. Missing
secrets should fail fast.

## SQLite Rules

- Keep migrations in `db/migrations/` with sortable names:
  `0001_create_users.sql`, `0002_add_workspaces.sql`.
- Every schema change needs a migration. Do not rely on `CREATE TABLE IF NOT
  EXISTS` in application startup as a substitute for migrations.
- Prefer integer primary keys or text UUID/ULID keys consistently across the
  app. Do not mix styles casually.
- Store timestamps as ISO-8601 text or Unix milliseconds consistently. Document
  the choice in `db/schema.ts`.
- Add indexes when a query filters by tenant, owner, slug, foreign key, or
  timestamp.
- Use transactions for multi-step writes. A SaaS write that creates related
  records must either fully succeed or fully roll back.
- Enable foreign keys for every SQLite connection.
- Use parameterized SQL only. Never concatenate user input into SQL strings.

Example query shape:

```ts
export function getWorkspaceBySlug(slug: string) {
  return db
    .prepare("select * from workspaces where slug = ? limit 1")
    .get(slug)
}
```

## Multi-Tenancy

Most SaaS data is tenant-scoped. Include `workspace_id` or `organization_id`
on tenant-owned tables and enforce it in every query. Never fetch by a global
record id and then check ownership later if the query can include tenant scope.

Correct:

```sql
select * from projects where id = ? and workspace_id = ?
```

Avoid:

```sql
select * from projects where id = ?
```

## Server Actions

Server actions live in `server/actions/`. They should:

- Validate input with a schema in `server/validators/`.
- Check authentication and authorization before calling services.
- Call one service function for the actual business operation.
- Return typed success/error results that the UI can render.
- Revalidate or redirect at the edge of the action, not deep inside services.

Do not put raw SQL in a server action. Do not let Client Components import
server-only modules.

## Route Handlers

Use `app/api/**/route.ts` for webhooks, third-party callbacks, and public API
surfaces. Keep handlers thin:

1. Parse request.
2. Authenticate or verify signature.
3. Validate input.
4. Call a service.
5. Return a typed response.

Webhook handlers must be idempotent. Store provider event ids when the provider
can retry delivery.

## Component Patterns

- Default to Server Components for pages and data loading.
- Keep Client Components small and interactive. Pass plain serializable props
  into them.
- Put reusable primitives in `components/ui/`.
- Put feature components in a feature folder such as `components/dashboard/`.
- Forms should have accessible labels, field errors, pending states, and a
  server-side validation path.
- Avoid fetching client-side data on first page load when a Server Component
  can load it directly.

## Data Flow

Read path:

```text
page/layout -> db query or service -> typed view model -> component props
```

Write path:

```text
form/client event -> server action -> validator -> authz -> service -> query -> revalidate/redirect
```

Services return domain results. UI decides how to display them.

## Error Handling

- Use expected error types for validation, auth, not-found, and conflict cases.
- Do not leak database errors or provider responses to users.
- Log unexpected errors once at the boundary where they are caught.
- Return stable messages from actions and route handlers.

## Auth And Permissions

Authentication answers "who is this user?" Authorization answers "may they do
this in this workspace?" Keep these separate.

Every service that mutates tenant data must receive an actor and workspace
context. Do not trust hidden form fields for ownership.

## Testing

Add focused tests for:

- Query helpers with an isolated SQLite database.
- Services that enforce ownership, billing limits, or state transitions.
- Server actions that validate inputs and map service errors.
- Webhook idempotency.

Use fixture builders rather than large static fixtures. Tests should create
only the records they need.

## Dev Commands

Use these commands unless the repo defines alternatives:

```bash
npm run dev
npm run lint
npm run typecheck
npm test
npm run db:migrate
npm run db:studio
```

Before a PR, run lint, typecheck, tests, and migrations against a fresh local
database.

## What We Do Not Do

- Do not create API routes for internal reads that Server Components can do
  directly. It adds latency and weakens type flow.
- Do not use global mutable state for current user, workspace, or database
  connection context.
- Do not put business rules in React components. Components display state;
  services decide state.
- Do not hide migrations inside app startup. Schema changes must be reviewable.
- Do not add a new dependency for a small helper that TypeScript or the
  platform already provides.
- Do not mix SQLite clients in the same app. Pick `better-sqlite3`, Turso, or
  libSQL and wrap it once.
- Do not create generic abstractions before two real features need the same
  shape.

## Pull Request Expectations

Each PR should explain:

- What user or maintainer problem it solves.
- Which routes, tables, or services changed.
- Any migration and rollback notes.
- Commands run locally.
- Screenshots or request examples for UI/API changes.

Keep PRs narrow. A schema migration, service change, and UI for one feature is
fine. Mixing unrelated dashboard cleanup, dependency upgrades, and billing
logic is not.

## Claude Code Working Rules

- Inspect existing files before editing.
- Prefer the patterns already present in the repository over this template when
  they conflict and the existing pattern is coherent.
- Make the smallest change that satisfies the request.
- Update tests when behavior changes.
- Preserve tenant isolation and authorization checks even in prototypes.
- Ask before changing schema, auth, billing, or production deployment behavior
  if the request is ambiguous.
