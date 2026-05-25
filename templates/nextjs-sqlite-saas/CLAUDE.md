# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack And Versions

- Next.js 15 App Router with React Server Components by default.
  Reason: server-first routes keep data loading close to the page and reduce
  client JavaScript in a SaaS dashboard.
- TypeScript in strict mode.
  Reason: database rows, billing states, and auth session shapes must fail at
  build time instead of becoming production data bugs.
- SQLite via `better-sqlite3` for local-first deployments or Turso/libSQL when
  the app needs a remote SQLite-compatible database.
  Reason: both keep the SQL model simple while supporting different deployment
  shapes.
- SQL migrations in versioned files, never ad-hoc schema mutation in app code.
  Reason: SaaS data must be reproducible across preview, staging, and
  production.
- Tailwind CSS is allowed for styling, but product state and business logic do
  not live in class strings.
  Reason: visual iteration should not hide domain rules.

## Project Structure

Use this layout unless the user gives a stronger local convention:

```text
app/
  (marketing)/
  (app)/
    dashboard/
    settings/
    billing/
  api/
components/
  ui/
  forms/
  layout/
db/
  migrations/
  schema.sql
  client.ts
  queries/
features/
  accounts/
  billing/
  projects/
  users/
lib/
  auth.ts
  env.ts
  validation.ts
tests/
  unit/
  integration/
```

Rules:

- Put route files in `app/` and reusable domain code in `features/`.
  Reason: routes change with navigation; domain behavior changes with product
  rules.
- Keep raw SQL in `db/queries/` or a feature-local query module, not inline in
  components.
  Reason: queries need tests, transaction boundaries, and reviewable diffs.
- Keep shared UI primitives in `components/ui/` and product-specific composed
  components under `features/<domain>/components/`.
  Reason: a button is reusable, an invoice status panel is not.
- Keep environment parsing in `lib/env.ts`.
  Reason: missing secrets should fail during boot, not during a customer action.

## Naming Conventions

- Route segments use kebab-case: `app/(app)/team-settings/page.tsx`.
  Reason: URLs and folders stay readable.
- React components use PascalCase: `BillingPlanCard`.
  Reason: component names remain visually distinct from functions.
- Server actions end with `Action`: `createProjectAction`.
  Reason: mutating entry points are easy to grep and audit.
- Database tables use snake_case plurals: `users`, `projects`,
  `billing_events`.
  Reason: SQL reads naturally and avoids case-sensitive quoting.
- TypeScript types use domain nouns: `Project`, `BillingEvent`, `UserSession`.
  Reason: types should describe product concepts, not transport details.
- Migration files use monotonically increasing timestamps:
  `20260525143000_create_projects.sql`.
  Reason: ordering is stable in git, CI, and production deploys.

## Dev Commands

Prefer these scripts in `package.json`:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest",
    "db:migrate": "tsx db/migrate.ts",
    "db:reset": "tsx db/reset.ts"
  }
}
```

When changing code:

1. Run the narrowest relevant test first.
2. Run `npm run typecheck` after TypeScript or schema changes.
3. Run `npm run lint` before opening a PR.
4. Run `npm run build` when touching routes, metadata, server actions, auth, or
   database access.

Reason: fast checks guide iteration; full build catches App Router integration
problems.

## SQL And Migration Conventions

- Every schema change gets a new file in `db/migrations/`.
  Reason: deployed databases need an append-only history.
- Migrations are idempotent only where SQLite supports it cleanly; otherwise the
  migration runner records applied filenames in `_migrations`.
  Reason: fake idempotency hides partially applied production changes.
- Use explicit column names in `INSERT` statements.
  Reason: future columns should not break older writes.
- Use `created_at` and `updated_at` as ISO-8601 text unless the project already
  standardizes on integer epochs.
  Reason: SQLite text timestamps sort correctly and are easy to inspect.
- Foreign keys must be enabled with `PRAGMA foreign_keys = ON` when opening a
  connection.
  Reason: SQLite does not enforce them unless requested per connection.
- Wrap multi-step writes in transactions.
  Reason: SaaS actions such as signup, billing changes, and invitations must not
  half-complete.
- Do not use destructive migrations such as `DROP TABLE` or column rebuilds
  without a backup or copy-forward plan in the migration comment.
  Reason: SQLite schema rewrites can silently discard customer data.

## Data Access Patterns

- Server Components may read data directly through typed query functions.
  Reason: server rendering can fetch close to the route without an internal HTTP
  hop.
- Client Components never import `db/`.
  Reason: database credentials and Node-only modules must stay server-side.
- Server actions validate input with Zod or an existing schema helper before
  opening a transaction.
  Reason: validation errors should be user-safe and not leave open writes.
- Return domain objects from query modules, not raw driver rows.
  Reason: the rest of the app should not depend on SQLite column quirks.
- Keep authorization checks beside the query or action.
  Reason: data filtering is part of correctness, not a UI concern.

## Component Patterns

- Start with Server Components. Add `"use client"` only for browser state,
  event handlers, subscriptions, or imperative APIs.
  Reason: fewer client islands means faster pages and smaller bundles.
- Forms use server actions for mutations unless the user experience requires an
  optimistic client workflow.
  Reason: server actions simplify validation, auth, and database transactions.
- Components accept plain props, not database clients or request objects.
  Reason: rendering stays testable and side effects stay outside the tree.
- Loading and empty states are first-class UI states.
  Reason: SaaS dashboards spend real time waiting on remote data and permissions.
- Prefer composition over boolean prop explosion.
  Reason: `variant`, `size`, and slots scale better than many one-off flags.

## Auth, Billing, And Multi-Tenant Rules

- All tenant-owned tables include `account_id` or `workspace_id`.
  Reason: tenant isolation must be visible in the schema.
- Every query for tenant data filters by the current tenant id.
  Reason: UI routing is not an authorization boundary.
- Billing state is append-only where possible: store events, then derive current
  entitlement.
  Reason: payment disputes and webhook retries need an audit trail.
- Webhooks verify signatures before parsing business payloads.
  Reason: billing webhooks are public endpoints.
- Admin-only routes must check role on the server.
  Reason: hidden navigation links do not secure anything.

## Testing Rules

- Unit-test pure domain functions and SQL row mappers.
  Reason: they are cheap and catch most regressions.
- Integration-test migrations against a temporary SQLite database.
  Reason: SQL syntax and migration order are runtime concerns.
- Test server actions with valid input, invalid input, unauthorized user, and
  cross-tenant access.
  Reason: these are the highest-risk SaaS paths.
- Snapshot tests are allowed only for stable text-heavy output.
  Reason: UI snapshots often approve noise instead of behavior.

## What We Do Not Do

- Do not put secrets in `.env.example`.
  Reason: examples should show names, not real values.
- Do not add an ORM unless the project already uses one.
  Reason: this template is intentionally SQL-first and SQLite-specific.
- Do not call internal API routes from Server Components.
  Reason: it adds latency and loses type information.
- Do not use `any` to bypass database or auth typing.
  Reason: SaaS bugs often start as unchecked nullable or permission states.
- Do not create a migration by editing an old migration file after it has been
  shared.
  Reason: teammates and deployed environments may already have applied it.
- Do not mix marketing page refactors with authenticated app behavior.
  Reason: review and rollback scopes should match product risk.

## Default Task Behavior For Claude

When asked to implement a change:

1. Identify the affected route, feature module, query module, and migration
   surface before editing.
2. Make the smallest cohesive change that satisfies the product behavior.
3. Add or update tests at the same layer as the changed behavior.
4. Run the relevant command from `Dev Commands`.
5. Report the files changed, the checks run, and any checks skipped.

If a request is ambiguous, choose the safer SaaS default: preserve data, require
server-side authorization, avoid destructive migrations, and ask one focused
question only when implementation would otherwise risk customer data.
