# CLAUDE.md

This file gives Claude Code the project rules for a production Next.js 15 App Router SaaS using SQLite through `better-sqlite3` locally or Turso/libSQL in production.

## Stack and Versions

- Next.js 15 with the App Router. Use Server Components by default.
- React 19. Use client components only for browser state, event handlers, effects, and third-party client-only widgets.
- TypeScript with `strict` enabled. Do not use `any` unless an external library forces it and the boundary is documented.
- SQLite as the source of truth. Use `better-sqlite3` for local single-node deployments or Turso/libSQL for hosted/serverless deployments.
- SQL migrations are committed files, not runtime guesses.
- Authentication is session based. Keep auth, billing, and organization membership checks server side.
- Styling uses Tailwind CSS plus small, local UI components. Avoid introducing a component library unless the product already depends on it.

## Dev Commands

Use these commands unless the repository defines different scripts:

```sh
npm run dev          # start local Next.js
npm run lint         # lint and formatting checks
npm run typecheck    # TypeScript checks
npm test             # unit/integration tests
npm run db:migrate   # apply local SQLite migrations
npm run db:studio    # optional local DB browser
```

If a command is missing, inspect `package.json` and use the closest project script. Do not invent scripts without updating `package.json`.

## Folder Structure

Use this structure for new work:

```text
app/
  (marketing)/        Public pages that do not require auth
  (app)/              Authenticated product routes
  api/                Route handlers for webhooks and external callbacks
components/
  ui/                 Generic presentational primitives
  forms/              Reusable form components
  product/            Domain-specific product components
db/
  client.ts           SQLite/libSQL client creation
  schema.ts           Table and row types if using a query builder
  migrations/         Ordered SQL migrations
  queries/            Server-only query modules
lib/
  auth/               Session, password, OAuth, and permission helpers
  billing/            Stripe or billing provider integration
  env.ts              Runtime environment validation
  validators/         Zod schemas shared by forms and server actions
server/
  actions/            Server actions grouped by domain
  services/           Business workflows that compose queries and side effects
tests/
  factories/          Test data builders
  integration/        DB-backed tests
```

Keep route folders focused on UI and request boundaries. Put business rules in `server/services` so they can be tested without rendering pages.

## Naming Conventions

- Files use kebab-case: `create-project-form.tsx`, `billing-service.ts`.
- React components use PascalCase exports: `CreateProjectForm`.
- Server actions use verb-first names: `createProjectAction`, `inviteMemberAction`.
- Database query functions state their scope: `getProjectByIdForUser`, `listInvoicesForOrg`.
- Boolean columns and variables start with `is`, `has`, or `can`.
- IDs are explicit: use `userId`, `orgId`, `projectId`, never generic `id` outside a tiny local scope.

Reason: SaaS code becomes permission-heavy. Explicit names reduce accidental cross-tenant access.

## SQL and Migration Conventions

- Every schema change gets a migration in `db/migrations`.
- Migration filenames use sortable timestamps: `202605131030_add_org_members.sql`.
- Migrations must be forward-only. Do not edit an already-applied migration; add a new one.
- Always include `created_at` and `updated_at` for business tables.
- Use `deleted_at` for soft deletes when records are part of billing, audit, or customer history.
- Add indexes for foreign keys and common filters in the same migration that introduces them.
- Do not store JSON blobs for fields that need filtering, sorting, permissions, or reporting.
- Use transactions for multi-step writes.
- Enable foreign keys for SQLite connections with `PRAGMA foreign_keys = ON`.

Example migration:

```sql
CREATE TABLE projects (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX projects_org_id_idx ON projects(org_id);
```

Reason: SQLite is reliable when constraints are explicit. Hidden application-only constraints turn into production data cleanup.

## Data Access Rules

- Query modules in `db/queries` must not read cookies or request headers.
- Permission checks happen before query calls or inside clearly named `ForUser` query functions.
- All organization-scoped reads and writes must filter by `orgId`.
- Never trust client-provided `userId`, `orgId`, role, price, or subscription status.
- Return plain objects from queries. Do not return database driver objects to UI components.
- Avoid N+1 queries in dashboards. Prefer one query that returns the table view data.

## Server Actions and Route Handlers

- Validate all inputs with Zod before touching the database.
- Return typed success/error objects from server actions; do not throw for expected validation errors.
- Use `revalidatePath` or `revalidateTag` after mutations that affect rendered data.
- Route handlers are for external systems, webhooks, or API clients. Prefer server actions for internal form submissions.
- Webhooks must verify signatures before parsing business payloads.
- Idempotency is required for billing webhooks and email delivery callbacks.

Pattern:

```ts
const input = CreateProjectSchema.safeParse(formData);
if (!input.success) {
  return { ok: false, fieldErrors: input.error.flatten().fieldErrors };
}
```

## Component Patterns

- Start with Server Components. Add `"use client"` only at the leaf that needs interactivity.
- Keep data fetching in pages, layouts, or server-only loaders.
- Form components may be client components, but submit to server actions.
- Loading and empty states are part of the feature, not polish. Add them with the first implementation.
- Do not put billing, role, or ownership decisions in client components.
- Use accessible labels, button text, and error messages.

Reason: Server Components reduce client bundle size and keep secrets, permissions, and SQL out of the browser.

## Auth, Organizations, and Permissions

- Treat every authenticated user as belonging to zero or more organizations.
- All product routes under `app/(app)` must require a session.
- Organization membership must be checked for every org-scoped route.
- Admin actions require an explicit role check, not just membership.
- Invitations expire and are single-use.
- Leaving an organization must not delete user-owned global identity data.

Anti-pattern:

```ts
// Bad: trusts the route param without checking membership.
const project = await getProject(params.projectId);
```

Preferred:

```ts
const project = await getProjectByIdForUser({
  projectId: params.projectId,
  userId: session.user.id,
});
```

## Environment Variables

- Validate environment variables in `lib/env.ts` at process start.
- Separate public and server-only variables. Only `NEXT_PUBLIC_` values may reach the browser.
- Do not read `process.env` throughout the app. Import validated config.
- Fail fast when required production secrets are missing.
- Provide safe defaults only for local development.

## Testing Rules

- Unit test pure services and validators.
- Integration test query modules against a temporary SQLite database.
- Test migrations by applying them to an empty database.
- Add at least one regression test for every bug fix.
- Mock external services at the HTTP boundary. Do not mock your own query functions in service tests unless the database is irrelevant.

Useful test targets:

- Permission checks for cross-tenant access.
- Billing webhook idempotency.
- Invite acceptance and expiration.
- Server action validation errors.
- Migration compatibility with existing rows.

## Pull Request Checklist

- Database migration added for schema changes.
- Query paths include `orgId` or user membership checks.
- Server action inputs are validated.
- Empty, loading, and error states are handled.
- Tests cover new business rules.
- `npm run lint`, `npm run typecheck`, and relevant tests pass.
- No secrets, tokens, customer data, or local database files are committed.

## What We Do Not Do

- Do not add client-side data access to SQLite. The database is server-only.
- Do not put authorization in React components. Components can hide UI, but the server enforces access.
- Do not use global mutable state for current user or organization. Read it from the session/request boundary.
- Do not introduce an ORM, RPC layer, or state manager just for one feature. Use the existing patterns until repetition proves the need.
- Do not create catch-all utility files like `lib/helpers.ts`. Name modules by domain and responsibility.
- Do not swallow errors with `catch {}`. Log unexpected errors with context and return safe user-facing messages.
- Do not skip migrations because "SQLite is just a file." Production data still needs repeatable change control.

## When Unsure

Choose the smallest server-side change that preserves tenant isolation, keeps data constraints in SQLite, and leaves a clear test path. Ask for clarification only when the product behavior is ambiguous; do not ask for permission to follow the rules in this file.
