# CLAUDE.md

Use this file as the operating contract for a greenfield SaaS built with
Next.js 15 App Router, TypeScript, and SQLite through `better-sqlite3` locally
or Turso/libSQL in hosted environments.

## Stack And Versions

- Next.js 15 with the App Router. Reason: server components, route handlers,
  and server actions keep most SaaS workflows close to the data boundary.
- React 19 and TypeScript in strict mode. Reason: strict types catch schema,
  form, and auth mistakes before they become production data bugs.
- SQLite for the primary relational store. Reason: most early SaaS products need
  simple transactional data more than distributed database complexity.
- `better-sqlite3` for local or single-node deployments; Turso/libSQL for hosted
  edge-friendly SQLite. Reason: both keep SQL explicit while supporting the same
  schema-first design.
- Zod for request, form, webhook, and environment validation. Reason: external
  input must be parsed before it reaches business logic.
- Vitest for unit tests and Playwright for browser flows. Reason: SaaS failures
  usually appear in permissions, forms, billing, and navigation, not only pure
  functions.

## Dev Commands

Prefer `pnpm`. Use the project-local package manager if the lockfile says
otherwise.

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm db:migrate
pnpm db:seed
```

If a script is missing, add it to `package.json` instead of inventing a one-off
command. Reason: repeatable commands belong in version control and CI.

## Folder Structure

```text
src/
  app/
    (marketing)/
    (app)/
    api/
    layout.tsx
  components/
    ui/
    forms/
    layout/
  db/
    client.ts
    schema.ts
    migrations/
    queries/
  features/
    billing/
    auth/
    projects/
    settings/
  lib/
    env.ts
    errors.ts
    ids.ts
    logger.ts
  server/
    actions/
    auth.ts
    permissions.ts
  tests/
    fixtures/
    integration/
    unit/
```

Rules:

- Keep route files thin. Reason: `page.tsx`, `layout.tsx`, and route handlers
  should coordinate rendering or HTTP boundaries, not hide business logic.
- Put reusable domain behavior under `features/<domain>`. Reason: SaaS code
  changes by feature ownership more often than by technical layer.
- Keep shared primitives under `components/ui`. Reason: visual consistency is
  cheaper when buttons, dialogs, inputs, tables, and toasts have one source.
- Keep database access under `db/queries` or feature-specific server modules.
  Reason: scattered SQL makes migrations and authorization audits slow.
- Keep `lib/` small and boring. Reason: a large `lib/` becomes an unowned junk
  drawer that hides product behavior.

## Naming Conventions

- Files and folders use kebab-case: `project-switcher.tsx`. Reason: URLs,
  imports, and generated file names stay predictable across platforms.
- React components use PascalCase exports: `ProjectSwitcher`. Reason: component
  usage remains visually distinct from functions and values.
- Server actions use verb-first names: `createProject`, `archiveWorkspace`.
  Reason: mutations should read like auditable events.
- Query helpers use data-shape names: `getWorkspaceBySlug`,
  `listProjectsForUser`. Reason: callers should know cardinality and scope.
- Boolean columns and variables use `is`, `has`, or `can`. Reason: permission
  and state checks must read unambiguously in reviews.
- Database tables are plural snake_case: `users`, `workspaces`,
  `workspace_members`. Reason: SQL stays idiomatic and easy to scan.
- Primary keys are `id`; foreign keys are `<singular_table>_id`. Reason:
  joins and indexes stay obvious without ORM magic.

## SQL And Migration Rules

- All schema changes go through versioned SQL files in `src/db/migrations`.
  Reason: production data should never depend on an undocumented local change.
- Migration names use sortable prefixes:
  `0001_create_users.sql`, `0002_add_workspace_members.sql`. Reason:
  deterministic order matters for SQLite and for review.
- Every table has `id`, `created_at`, and `updated_at` unless it is a pure join
  table. Reason: SaaS support and billing investigations need timestamps.
- Enable foreign keys on every connection. Reason: SQLite does not enforce them
  unless `PRAGMA foreign_keys = ON` is set.
- Use transactions for multi-write operations. Reason: partial writes are the
  fastest way to create billing, membership, and entitlement bugs.
- Create indexes with the query in mind, not preemptively. Reason: unnecessary
  indexes slow writes and make migrations harder to reason about.
- Do not delete customer-owned records by default. Prefer `archived_at` or
  `deleted_at`. Reason: SaaS products need recovery, audit trails, and billing
  reconciliation.
- Use prepared statements or parameterized queries only. Reason: app code must
  never concatenate user input into SQL.
- Keep enum-like values as constrained text with a central TypeScript union.
  Reason: SQLite stays simple while application code remains type-safe.
- Include a down or rollback note when a migration cannot be safely reversed.
  Reason: irreversible changes must be explicit before deploy.

## Data Access Pattern

Database code should be explicit:

```ts
export async function getWorkspaceBySlug(slug: string) {
  const row = db.prepare("select * from workspaces where slug = ?").get(slug);
  return workspaceSchema.nullable().parse(row ?? null);
}
```

Rules:

- Parse rows at the boundary with Zod or a typed mapper. Reason: SQLite returns
  runtime values, not TypeScript guarantees.
- Return `null` for not-found single records and `[]` for empty lists. Reason:
  callers should not handle three representations of absence.
- Keep authorization near reads and writes. Reason: fetching first and checking
  later invites accidental data exposure.
- Do not call the database from client components. Reason: credentials and
  authorization belong on the server.

## App Router Patterns

- Server components are the default. Reason: they reduce client JavaScript and
  can read authenticated data directly.
- Use client components only for browser state, effects, and event-heavy UI.
  Reason: `"use client"` moves code and dependencies into the browser bundle.
- Use route handlers for public APIs, webhooks, and third-party callbacks.
  Reason: HTTP-specific concerns should not live in page components.
- Use server actions for form submissions that mutate first-party data. Reason:
  forms stay colocated with validation and revalidation.
- Call `revalidatePath` or `revalidateTag` after successful mutations. Reason:
  stale SaaS dashboards cause duplicate work and bad support tickets.
- Use `notFound()` for missing resources and explicit unauthorized UI for
  permission failures. Reason: missing data and forbidden data are different
  product states.

## Component Patterns

- Build small composed forms with server-side validation and field-level errors.
  Reason: SaaS users need to recover quickly from invalid input.
- Keep tables dense and keyboard-accessible. Reason: operational screens are
  used repeatedly and should support scanning, sorting, and bulk decisions.
- Prefer controlled modals for destructive actions. Reason: delete, archive,
  cancel, and refund flows need explicit confirmation and auditability.
- Avoid one-off styling in feature components. Reason: inconsistent UI adds
  review cost and weakens trust in admin and billing surfaces.
- Do not put data fetching in presentational components. Reason: reusable UI
  should not silently depend on auth, caching, or database state.

## Auth, Permissions, And Tenancy

- Every workspace-scoped query must include `workspace_id` or an equivalent
  membership constraint. Reason: multi-tenant leaks are critical incidents.
- Put permission helpers in `src/server/permissions.ts`. Reason: access rules
  must be reviewed centrally.
- Never trust client-provided role, price, plan, or owner fields. Reason: the
  browser is not an authority for billing or authorization.
- Store external provider IDs with a provider prefix when ambiguity is possible.
  Reason: Stripe, GitHub, Google, and internal IDs can otherwise collide in logs.

## Environment And Secrets

- Validate env vars in `src/lib/env.ts` at process startup. Reason: missing
  secrets should fail fast, not halfway through checkout or login.
- Use `.env.local` for local secrets and never commit filled secret files.
  Reason: credentials rotate slowly and leaks are expensive.
- Keep public env vars prefixed with `NEXT_PUBLIC_`. Reason: anything public is
  shipped to the browser and must be reviewed as non-secret.

## Error Handling And Logging

- Throw typed application errors for expected failures. Reason: form errors,
  permission errors, and billing errors need different user-facing handling.
- Log unexpected errors with request, user, and workspace context when available.
  Reason: production debugging needs correlation without exposing secrets.
- Never log tokens, cookies, raw authorization headers, private keys, or full
  payment payloads. Reason: logs are copied into tools and support tickets.

## Testing Expectations

- Unit test pure validation, permission, and SQL mapper logic. Reason: these
  failures are cheap to catch and expensive in production.
- Integration test database mutations with a temporary SQLite database. Reason:
  migrations and transactions must match real SQL behavior.
- Browser test signup, login, workspace creation, billing state display, and the
  highest-value user workflow. Reason: SaaS value depends on complete flows.
- Add a regression test before fixing a bug when the bug is reproducible.
  Reason: otherwise the same edge case returns during refactors.

## What We Do Not Do

- Do not introduce a global state library for server-owned data. Reason:
  database state should come from the server and cache layer, not a browser copy.
- Do not add an ORM unless the project already chose one. Reason: SQLite plus
  explicit SQL is easier to audit for small SaaS teams.
- Do not create migrations from runtime conditionals. Reason: deploys must be
  deterministic and reviewable.
- Do not hide billing logic inside UI components. Reason: pricing, entitlement,
  and invoice behavior must be testable without rendering React.
- Do not use `any` to bypass schema or API uncertainty. Reason: uncertainty
  should be parsed, narrowed, or modeled.
- Do not add broad abstractions before the second real use. Reason: premature
  architecture slows the product and hides simple code.

## Before Coding Checklist

1. Identify the feature owner folder and the route boundary.
2. Confirm the database tables, indexes, and migration impact.
3. Confirm the permission rule for each read and write.
4. Add or update validation schemas before wiring UI.
5. Run lint, typecheck, tests, and build before opening a PR.
