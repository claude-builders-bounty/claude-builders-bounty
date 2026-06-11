# CLAUDE.md

This file defines the project rules for a production SaaS application built with
Next.js 15 App Router, React 19, TypeScript, SQLite, and Tailwind CSS. Follow
these rules for every change unless a local file clearly documents a different
decision.

## Stack And Versions

- Runtime: Node.js 22 LTS. Reason: it is the current stable baseline for modern
  Next.js deployments and has native Web API support.
- Package manager: pnpm 10. Reason: it gives deterministic installs and fast
  workspace support without adding monorepo complexity.
- Framework: Next.js 15 with the App Router in `src/app`. Reason: server
  components, route handlers, metadata, and layouts are first-class here.
- UI: React 19 with TypeScript strict mode. Reason: strict types catch contract
  drift before it reaches runtime.
- Styling: Tailwind CSS plus local component classes only when Tailwind becomes
  unreadable. Reason: most SaaS UI needs consistent spacing and states more than
  custom CSS architecture.
- Database: SQLite for local and self-hosted deployments. Use `better-sqlite3`
  for file-backed SQLite and Turso/libSQL only when the app needs hosted edge
  replication. Reason: both keep SQL explicit and avoid an ORM-specific data
  model.
- Validation: Zod at every external boundary. Reason: TypeScript does not
  validate request bodies, form submissions, environment variables, or database
  rows at runtime.
- Auth: Auth.js or a local session implementation backed by SQLite. Reason:
  session behavior must be auditable and testable inside the same app.
- Tests: Vitest for unit tests, React Testing Library for components, and
  Playwright for critical browser flows. Reason: each tool covers a different
  failure mode.

## Dev Commands

Use these commands unless the repository defines an equivalent script:

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm db:migrate
pnpm db:seed
pnpm build
```

If a command is missing, add the script before relying on it. Do not invent
one-off commands in documentation or PR notes.

## Folder Structure

Use this structure for new files:

```text
src/
  app/
    (marketing)/
      page.tsx
    (app)/
      dashboard/
        page.tsx
      layout.tsx
    api/
      health/
        route.ts
    layout.tsx
    page.tsx
  components/
    ui/
    forms/
    shell/
  features/
    billing/
      actions.ts
      queries.ts
      schema.ts
      components/
    organizations/
      actions.ts
      queries.ts
      schema.ts
      components/
  lib/
    auth/
    db/
      client.ts
      migrations/
      schema.sql
      seed.ts
    env.ts
    errors.ts
    routes.ts
  server/
    services/
    jobs/
  tests/
    fixtures/
    helpers/
```

Rules:

- Put route segments in `src/app`; put reusable business code outside
  `src/app`. Reason: route files should compose behavior, not hide domain logic.
- Put feature-specific code in `src/features/<feature>`. Reason: SaaS features
  grow independently, and co-location keeps queries, actions, validation, and UI
  easy to review together.
- Put shared primitives in `src/components/ui` and product-specific composites
  in `src/components/forms` or `src/components/shell`. Reason: a button is a
  primitive, but an organization switcher is product behavior.
- Put database access in `queries.ts` files or `src/lib/db`. Reason: SQL should
  be easy to audit and should not be scattered through React components.
- Put cross-feature orchestration in `src/server/services`. Reason: service code
  can call multiple features without creating circular imports.

## Naming Conventions

- Files and folders use kebab-case: `invoice-table.tsx`, `user-menu.tsx`.
  Reason: names stay readable on case-sensitive and case-insensitive file
  systems.
- React components use PascalCase exports: `InvoiceTable`. Reason: JSX and
  React DevTools expect component names to stand out.
- Server actions use verb-first names: `createOrganization`, `inviteMember`,
  `cancelSubscription`. Reason: actions should read as commands with side
  effects.
- Query functions use read-first names: `getOrganizationBySlug`,
  `listInvoicesForAccount`. Reason: call sites should reveal that they do not
  mutate state.
- Zod schemas end with `Schema`: `createOrganizationSchema`. Reason: the suffix
  distinguishes runtime validators from TypeScript-only types.
- Database tables use snake_case plural names: `users`, `organizations`,
  `organization_members`. Reason: SQL remains readable and conventional.
- Database columns use snake_case: `created_at`, `owner_user_id`. Reason:
  column names should not depend on JavaScript casing conventions.
- TypeScript types generated or inferred from schemas use PascalCase:
  `CreateOrganizationInput`. Reason: types represent shapes, not values.

## Environment And Configuration

- Define all environment variables in `src/lib/env.ts` and validate them with
  Zod on startup. Reason: broken configuration should fail before a request is
  served.
- Keep `.env.example` current whenever an env var is added, removed, or renamed.
  Reason: new deployments should not require source-code archaeology.
- Do not read `process.env` directly outside `src/lib/env.ts`. Reason: direct
  reads bypass validation and make tests harder to isolate.
- Treat secrets as server-only. Reason: anything referenced by a client component
  can be bundled into the browser.

## Database Client

- Export a single database client from `src/lib/db/client.ts`. Reason: SQLite
  connection ownership must be predictable.
- Use prepared statements for all dynamic values. Reason: string interpolation
  in SQL creates injection risk and weakens query review.
- Keep SQL explicit. Reason: this template is optimized for a small SaaS where
  readable SQL beats a heavy abstraction layer.
- Map database rows at the boundary. Reason: SQL row shapes and UI view models
  change at different speeds.
- Use transactions for multi-step writes. Reason: SaaS workflows such as signup,
  invite acceptance, and billing updates must not partially commit.

Example pattern:

```ts
import { z } from "zod";
import { db } from "@/lib/db/client";

const organizationRowSchema = z.object({
  id: z.string(),
  name: z.string(),
  slug: z.string(),
  created_at: z.string(),
});

export function getOrganizationBySlug(slug: string) {
  const row = db
    .prepare("select id, name, slug, created_at from organizations where slug = ?")
    .get(slug);

  return row ? organizationRowSchema.parse(row) : null;
}
```

## SQL And Migration Conventions

- Migrations live in `src/lib/db/migrations` and are named
  `0001_create_users.sql`, `0002_create_organizations.sql`, and so on. Reason:
  lexical ordering must match execution ordering.
- Migrations are append-only after merge. Reason: production databases cannot
  replay edited history safely.
- Every migration runs inside a transaction unless SQLite disallows it for that
  exact statement. Reason: failed migrations should leave the database unchanged.
- Every table has `id text primary key`, `created_at text not null`, and
  `updated_at text not null` unless there is a documented reason not to.
  Reason: SaaS entities need stable IDs and audit timestamps.
- Use ISO-8601 UTC strings for timestamps. Reason: SQLite stores text reliably,
  and UTC avoids local timezone ambiguity.
- Enable foreign keys on every connection with `PRAGMA foreign_keys = ON`.
  Reason: SQLite does not enforce them unless enabled.
- Prefer `not null` and explicit defaults. Reason: null-heavy schemas push data
  cleanup into application code.
- Add indexes in the same migration as the query pattern they support. Reason:
  performance decisions should be reviewed with the feature that needs them.
- Do not store JSON blobs for core relational data. Reason: membership, billing,
  permissions, and audit data must be queryable and constrained.
- Include a rollback note as a SQL comment when a migration cannot be reversed
  mechanically. Reason: reviewers need to understand operational risk.

Migration skeleton:

```sql
-- 0002_create_organizations.sql
begin;

create table organizations (
  id text primary key,
  name text not null,
  slug text not null unique,
  created_at text not null,
  updated_at text not null
);

create index organizations_slug_idx on organizations(slug);

commit;
```

## App Router Rules

- Use server components by default. Reason: they reduce client JavaScript and
  keep data fetching close to the route.
- Add `"use client"` only for components that need browser state, effects,
  refs, or event handlers. Reason: client boundaries increase bundle size and
  serialization constraints.
- Keep `page.tsx` thin: load data, enforce access, and compose feature
  components. Reason: pages should describe the route, not become feature
  modules.
- Use route handlers in `src/app/api` only for external HTTP surfaces, webhooks,
  or integrations. Reason: internal mutations are usually clearer as server
  actions.
- Use `notFound()` and `redirect()` from `next/navigation` for route-level
  control flow. Reason: App Router handles these paths correctly for rendering
  and caching.

## Component Patterns

- Build accessible primitives first: buttons, inputs, labels, dialogs, menus,
  tables, and empty states. Reason: SaaS quality depends on predictable repeated
  interactions.
- Components that fetch data stay server-side. Components that mutate local UI
  state become client components. Reason: this split keeps data dependencies
  explicit.
- Pass plain serializable props from server components to client components.
  Reason: functions, database handles, Dates, and class instances do not cross
  the server-client boundary safely.
- Keep forms progressive where practical: use server actions with validated
  input and return typed field errors. Reason: forms should work reliably without
  duplicating validation logic.
- Prefer composition over prop explosions. Reason: a component with many boolean
  props usually hides multiple responsibilities.
- Use loading, empty, error, and success states for every user-facing async
  workflow. Reason: SaaS users repeat workflows and need clear system feedback.

## Server Actions

- Validate input with Zod at the start of every action. Reason: actions are
  public server entry points.
- Check authorization in the action or a shared service it calls. Reason: hiding
  buttons in the UI is not access control.
- Return typed results for expected failures and throw only for unexpected
  failures. Reason: validation errors and permission denials are product states.
- Revalidate paths or tags after writes. Reason: App Router caches can otherwise
  show stale data.
- Keep side effects idempotent when possible. Reason: network retries and double
  submissions happen in real SaaS workflows.

## Auth, Tenancy, And Permissions

- Model organizations explicitly. Reason: most SaaS apps eventually need teams,
  ownership transfer, invites, or billing ownership.
- Scope queries by `organization_id` when data belongs to an organization.
  Reason: tenancy bugs are security bugs.
- Store membership roles in `organization_members`. Reason: roles are
  relationship data, not user data.
- Perform permission checks server-side next to the data access. Reason: the
  closer the check is to the query or mutation, the harder it is to bypass.
- Use route groups such as `(marketing)` and `(app)` to separate public pages
  from authenticated product pages. Reason: auth layout and navigation are
  different concerns.

## Error Handling

- Define expected application errors in `src/lib/errors.ts`. Reason: callers
  need stable error categories, not string matching.
- Log unexpected server errors with enough context to debug, but never log
  secrets, tokens, passwords, session cookies, or full payment payloads. Reason:
  logs are durable and often shared across tools.
- Show user-safe error messages in UI. Reason: database and stack details are
  not product copy and can leak internals.

## Testing Rules

- Add or update tests with every behavior change. Reason: a SaaS template should
  make correctness the default path.
- Unit test schema validation, query mapping, permission helpers, and service
  logic. Reason: these fail without needing a browser.
- Component test form states and conditional rendering. Reason: UI regressions
  often happen in empty, loading, and error states.
- E2E test signup, login, organization switching, and one critical paid
  workflow. Reason: these are the paths that block revenue when broken.
- Use a temporary SQLite database per test file or test worker. Reason: tests
  should not depend on local developer state.

## Pull Request Checklist

Before opening a PR:

- Run `pnpm lint`.
- Run `pnpm typecheck`.
- Run `pnpm test`.
- Run `pnpm build`.
- Run migrations on a fresh local database.
- Update `.env.example` if configuration changed.
- Add screenshots for visible UI changes.
- Explain any migration, auth, or tenancy risk in the PR description.

## What We Do Not Do

- Do not add an ORM by default. Reason: this template favors explicit SQL and a
  small, inspectable data layer.
- Do not put database calls in client components. Reason: client code runs in
  the browser and cannot safely hold server credentials or database handles.
- Do not create catch-all utility folders such as `helpers`, `misc`, or
  `common`. Reason: vague folders become ownership dead zones.
- Do not use API routes for every mutation. Reason: server actions are simpler
  for first-party forms and preserve type locality.
- Do not duplicate validation between client and server. Reason: the server
  schema is the source of truth; client validation is only a usability layer.
- Do not commit generated SQLite database files. Reason: databases are runtime
  state, not source code.
- Do not edit merged migration files. Reason: historical migrations are a
  contract with deployed databases.
- Do not rely on `any` to make TypeScript pass. Reason: it removes the safety
  that justifies TypeScript in the stack.
- Do not introduce global state for request-specific data. Reason: serverless
  and concurrent rendering can leak state across users.
- Do not add dependencies without a specific local use. Reason: every dependency
  adds upgrade, security, and bundle cost.

## Claude Code Working Rules

- Start by reading the relevant route, feature folder, schema, and migration
  files before editing. Reason: local patterns are more important than generic
  framework habits.
- Prefer the smallest change that satisfies the request and preserves these
  rules. Reason: SaaS codebases stay maintainable when each PR has a narrow
  purpose.
- If a request conflicts with this file, follow the user's explicit request and
  mention the conflict in the final response. Reason: project rules guide work,
  but the current task owner can override them.
- Do not ask clarifying questions when the task can be completed by following
  the conventions in this file. Reason: this template exists to make common
  Next.js and SQLite decisions upfront.
