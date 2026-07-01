# CLAUDE.md - Next.js 15 + SQLite SaaS

Use this file as the operating guide for a greenfield SaaS project built with
Next.js 15 App Router, TypeScript, SQLite, and either `better-sqlite3` for a
local file database or Turso/libSQL for hosted SQLite.

## Stack And Versions

- Runtime: Node.js 20 LTS or newer.
  Reason: Next.js 15 and modern SQLite client libraries expect current web APIs
  and stable ESM/CJS interop.
- Framework: Next.js 15 with the App Router.
  Reason: Server Components, Server Actions, route handlers, and layouts should
  share one routing model.
- Language: TypeScript with `strict` enabled.
  Reason: database rows, form input, and billing/account state should fail at
  build time before they become production data bugs.
- Database: SQLite through `better-sqlite3` for local-first apps or Turso/libSQL
  for remote production.
  Reason: both keep the SQL dialect close to SQLite and avoid designing for
  features that are unavailable in production.
- Styling: Tailwind CSS plus small colocated components.
  Reason: SaaS screens need dense, consistent interfaces more than decorative
  one-off CSS.

## Project Shape

Use this structure unless an existing project already has a stronger convention:

```text
app/
  (marketing)/
  (app)/
    dashboard/
    settings/
  api/
    health/route.ts
components/
  ui/
  forms/
  layout/
db/
  client.ts
  migrations/
  queries/
  schema.ts
lib/
  auth/
  billing/
  env.ts
  errors.ts
  validation/
tests/
  fixtures/
  integration/
```

Rules:

- Keep route-specific UI under `app/**` and reusable UI under `components/**`.
  Reason: pages remain easy to delete or move without breaking shared widgets.
- Keep SQL and database access under `db/**`.
  Reason: direct SQL in React components makes caching, transactions, and test
  setup unpredictable.
- Keep provider integrations under `lib/<domain>`.
  Reason: auth, billing, email, and analytics each need one obvious boundary.
- Prefer `index.ts` only for package-style public exports.
  Reason: broad barrel files hide import direction and often create circular
  dependencies in App Router projects.

## Commands

Use these scripts in `package.json`:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "typecheck": "tsc --noEmit",
    "lint": "next lint",
    "test": "vitest run",
    "db:migrate": "tsx db/migrate.ts",
    "db:studio": "sqlite-web ./data/dev.db"
  }
}
```

Rules:

- Run `typecheck`, `lint`, and focused tests before any PR.
  Reason: these catch different classes of failures; one passing command is not
  enough signal.
- Keep migration commands explicit.
  Reason: automatic schema changes during `dev` can mask destructive migration
  mistakes.
- Do not add a command that requires production secrets for local validation.
  Reason: contributors should be able to verify app behavior with local test
  configuration.

## Naming Conventions

- Files containing React components use `kebab-case.tsx`, for example
  `account-menu.tsx`.
  Reason: it keeps imports readable on case-sensitive and case-insensitive file
  systems.
- React component symbols use `PascalCase`.
  Reason: JSX and React DevTools expect component-like names to stand out.
- Server-only helpers use a `.server.ts` suffix when they touch secrets, the file
  system, or the database.
  Reason: the suffix makes accidental client imports obvious during review.
- Validation schemas end with `Schema`, for example `createWorkspaceSchema`.
  Reason: schemas are values, not types, and the suffix prevents confusing them
  with inferred TypeScript types.
- Inferred types use the noun without `Schema`, for example `CreateWorkspace`.
  Reason: call sites should read as data models, not parser implementations.

## Environment Variables

Create `lib/env.ts` as the only module that reads `process.env`.

Rules:

- Validate environment variables at startup with a schema.
  Reason: missing database URLs and auth secrets should fail fast, not after a
  user reaches checkout or onboarding.
- Keep `.env.example` complete and non-secret.
  Reason: new developers and deployment previews need a single setup checklist.
- Never read `process.env` in Client Components.
  Reason: only `NEXT_PUBLIC_*` variables are exposed to the browser, and mixing
  server/client config causes confusing hydration behavior.

## SQLite And Migration Rules

SQLite is the source of truth. Treat migrations as product code.

Rules:

- Every schema change gets a numbered migration file in `db/migrations`.
  Reason: SQLite databases are long-lived files; reproducible history matters.
- Use forward-only migrations.
  Reason: rollback scripts for SQLite often create false confidence around data
  loss. Prefer backups plus a corrective forward migration.
- Wrap multi-step migrations in a transaction.
  Reason: partially applied SQLite migrations are difficult to diagnose and can
  leave production data in an impossible state.
- Avoid `DROP TABLE`, `DROP COLUMN`, and destructive `ALTER TABLE` operations
  unless the PR includes a data preservation plan.
  Reason: SQLite has limited schema-alter support and SaaS data is customer data.
- Prefer explicit column lists in `INSERT` and `SELECT`.
  Reason: column-order coupling breaks silently after migrations.
- Store timestamps as ISO 8601 UTC text unless there is a strong reason to use
  Unix milliseconds.
  Reason: ISO text is readable, sortable, and portable between local SQLite and
  Turso/libSQL.
- Use `TEXT` ids generated at the application boundary, such as UUID v7 or cuid2.
  Reason: generated ids allow optimistic UI and cross-service references before
  commit.
- Add indexes in the same migration as the query pattern they support.
  Reason: SaaS tables grow slowly until they suddenly do not; query intent should
  be recorded with the schema.

## Database Access Patterns

- Put query functions in `db/queries/<domain>.ts`.
  Reason: route handlers, Server Actions, and tests can share the same behavior.
- Return plain objects from query functions.
  Reason: React Server Components serialize simple data reliably.
- Keep transactions inside database modules.
  Reason: callers should request a business operation, not orchestrate SQL
  consistency by hand.
- Normalize not-found results to `null`, not thrown errors.
  Reason: `null` is easier to compose in App Router loading and empty states.
- Throw typed domain errors for permission and invariant failures.
  Reason: route handlers and Server Actions can map them to consistent UI and
  HTTP responses.

## App Router Patterns

- Use Server Components by default.
  Reason: most SaaS screens read account, billing, and database state before they
  need interactivity.
- Add `"use client"` only at the smallest interactive boundary.
  Reason: large Client Components increase bundle size and move server-only data
  risks into the browser.
- Keep `page.tsx` focused on data loading and composition.
  Reason: complex page files are hard to test and encourage copy-pasted forms.
- Use route groups like `(marketing)` and `(app)` for layout separation.
  Reason: auth-gated product screens and public pages should not share accidental
  loading, metadata, or navigation behavior.
- Use route handlers for third-party webhooks and machine-facing APIs.
  Reason: they make request/response behavior explicit and testable.

## Server Actions And Forms

- Validate all form input on the server with the same schema used by the client.
  Reason: client validation is a convenience, not a trust boundary.
- Return typed action states instead of raw strings.
  Reason: forms need stable success, field error, and form error states.
- Keep mutation actions narrow.
  Reason: one action that updates unrelated account, billing, and profile state
  becomes impossible to retry safely.
- Revalidate only the paths or tags affected by the mutation.
  Reason: broad invalidation hides stale data bugs and slows common workflows.

## Component Patterns

- Use `components/ui` for primitive design-system wrappers.
  Reason: buttons, dialogs, inputs, and tables should have one accessibility and
  styling baseline.
- Use domain components for business concepts, for example
  `components/workspaces/workspace-switcher.tsx`.
  Reason: business components change with product language and should not pollute
  primitives.
- Prefer controlled form components only when a workflow needs live validation or
  derived state.
  Reason: uncontrolled forms plus Server Actions are simpler for common SaaS
  create/update flows.
- Keep loading and empty states next to the component that owns the data.
  Reason: repeated dashboards need predictable local fallbacks, not global
  spinners.

## Auth And Authorization

- Authentication answers "who is this user"; authorization answers "what can they
  do in this workspace".
  Reason: SaaS bugs often come from mixing identity with membership.
- Check authorization in server-only modules before every database mutation.
  Reason: hiding buttons in the UI is not permission enforcement.
- Include `workspaceId` or tenant scope in every multi-tenant query.
  Reason: missing tenant filters are the most expensive SaaS data leaks.
- Do not cache user-specific authorization decisions globally.
  Reason: role changes must take effect without waiting for unrelated cache
  expiry.

## Testing Expectations

- Unit test validation schemas and pure helpers.
  Reason: these tests are fast and prevent common edge-case regressions.
- Integration test database queries against a temporary SQLite database.
  Reason: SQL behavior, constraints, and indexes need real database coverage.
- Test Server Actions through their exported functions.
  Reason: actions hold the important validation, authorization, and mutation
  behavior.
- Add at least one smoke test for each critical paid workflow.
  Reason: billing, onboarding, and account deletion are high-impact paths.

## Pull Request Checklist

Before opening a PR:

- Run `npm run typecheck`.
- Run `npm run lint`.
- Run focused tests for touched domains.
- Include a migration note for every database change.
- Confirm `.env.example` is still accurate.
- Describe any cache revalidation or authorization changes.

## Anti-Patterns To Avoid

- Do not put SQL in Client Components.
  Reason: it is impossible to keep database credentials and tenant checks safe in
  browser code.
- Do not build generic CRUD abstractions before the third repeated use case.
  Reason: SaaS workflows usually differ in permissions, audit needs, and side
  effects.
- Do not use `any` for database rows or form payloads.
  Reason: it defeats the point of strict TypeScript at the app boundary.
- Do not store money as floating-point numbers.
  Reason: billing math needs integer cents or provider-native decimal strings.
- Do not silently catch errors in Server Actions.
  Reason: users need actionable failures and maintainers need observable bugs.
- Do not create migrations by editing old migration files after they have been
  applied anywhere.
  Reason: migration history must be append-only for shared environments.
- Do not mix marketing copy, product logic, and database calls in one component.
  Reason: it makes product iteration risky and slows every review.

## How Claude Should Work In This Repo

- First inspect existing files and follow the local pattern.
  Reason: consistency beats generic framework advice.
- If a task touches data, identify the table, migration, query function, and UI
  path before editing.
  Reason: database changes need an end-to-end plan.
- Prefer small PRs with one product outcome.
  Reason: SaaS regressions are easier to review when data, UI, and cache changes
  have a narrow purpose.
- When uncertain, write down the assumption in the PR body.
  Reason: maintainers can correct a visible assumption much faster than a hidden
  one.
