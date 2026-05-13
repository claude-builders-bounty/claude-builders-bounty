# CLAUDE.md - Next.js 15 + SQLite SaaS

Use this file as the operating contract for a greenfield SaaS application built with Next.js 15 App Router, TypeScript, Tailwind CSS, and SQLite.

## Stack And Versions

- Runtime: Node.js 22 LTS. Reason: Next.js 15 and modern test tooling are stable on Node 22, and the project should not depend on experimental runtimes.
- Package manager: pnpm. Reason: deterministic installs and strict dependency boundaries reduce "works on my machine" drift.
- Framework: Next.js 15 App Router with React 19 and TypeScript `strict: true`. Reason: server components, server actions, and typed route boundaries are the default architecture.
- Styling: Tailwind CSS with colocated component classes. Reason: SaaS UI needs consistent primitives without a custom CSS framework.
- Database: SQLite through one adapter per deployment target:
  - Use `better-sqlite3` for local-first Node.js server deployments.
  - Use Turso/libSQL for serverless or globally replicated deployments.
  Reason: mixing adapters in product code creates inconsistent transaction and migration behavior.
- Validation: Zod at every external boundary. Reason: form input, route params, webhooks, and env vars are untrusted.
- Tests: Vitest for unit/integration tests and Playwright only for user-critical flows. Reason: fast local feedback first, browser automation only where rendering matters.

## Project Structure

```text
app/
  (marketing)/
  (app)/
  api/
components/
  ui/
  forms/
  layout/
db/
  client.ts
  migrate.ts
  migrations/
  schema.ts
features/
  billing/
  organizations/
  users/
lib/
  auth/
  env.ts
  errors.ts
  permissions.ts
  result.ts
tests/
  fixtures/
  integration/
```

- Keep route files thin. Reason: App Router files should compose feature code, not become service containers.
- Put business behavior in `features/<domain>/`. Reason: each SaaS domain can own its queries, mutations, schemas, and tests.
- Keep `components/ui/` generic and domain-free. Reason: reusable primitives must not import business logic.
- Put database code under `db/` and export explicit query functions from feature modules. Reason: SQL access must be easy to audit.
- Do not create a catch-all `utils.ts`. Reason: unrelated helpers hide ownership and make future cleanup harder.

## Commands

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm db:migrate
pnpm db:studio
```

- Add missing scripts before using ad hoc commands. Reason: CI and future agents need the same entry points as local development.
- `pnpm typecheck`, `pnpm lint`, and impacted tests must pass before a PR is ready. Reason: type and lint failures usually indicate user-visible regressions in App Router projects.

## Environment Rules

- Read env vars only in `lib/env.ts` through a Zod schema. Reason: startup should fail early with a useful error instead of failing inside a request.
- Prefix browser-exposed values with `NEXT_PUBLIC_`. Reason: accidental secret exposure is easy in full-stack Next.js apps.
- Never use production defaults for secrets, database URLs, or webhook signing keys. Reason: defaults leak across environments and make incidents harder to trace.

## SQLite And Migration Conventions

- Migration files use `db/migrations/0001_short_name.sql`. Reason: ordered, human-readable migrations are easy to review and replay.
- Every migration runs in a transaction unless SQLite forbids it. Reason: partial schema changes corrupt local and preview environments.
- Enable foreign keys for every connection with `PRAGMA foreign_keys = ON`. Reason: SQLite does not enforce them unless explicitly enabled.
- Use WAL mode for long-running local deployments with `PRAGMA journal_mode = WAL`. Reason: read/write concurrency is better for SaaS dashboards.
- Prefer additive migrations. Reason: SQLite destructive changes often need table rebuilds and careful data copy steps.
- Destructive migrations require a rollback note and a data-preservation plan in the PR. Reason: SaaS data loss is a product incident, not a refactor.
- Store timestamps as ISO strings or integer milliseconds consistently per table. Reason: mixed timestamp formats break sorting and reporting.
- Never interpolate user input into SQL strings. Reason: prepared statements are the only acceptable default.

## Data Access Patterns

- Feature modules expose verbs such as `createOrganization`, `listInvoices`, or `updateUserRole`. Reason: call sites should describe intent, not SQL mechanics.
- Return typed domain objects, not raw driver rows. Reason: driver-specific shapes should not leak into components.
- Keep transactions close to the use case that needs atomicity. Reason: splitting transaction control across helpers causes partial writes.
- Use pagination for all list queries. Reason: admin dashboards grow beyond local test data.

## App Router Patterns

- Use server components by default. Reason: data loading and access checks stay on the server.
- Add `"use client"` only at interaction boundaries. Reason: smaller client bundles and fewer hydration bugs.
- Server actions are for small authenticated mutations only. Reason: complex workflows need explicit API routes, observability, and retry behavior.
- Validate `params`, `searchParams`, form data, and JSON bodies with Zod. Reason: TypeScript types do not validate runtime input.
- Redirect after successful mutations that change page state. Reason: it prevents duplicate submissions and stale UI.
- Do not fetch internal HTTP routes from server components. Reason: import the server-side function directly to avoid extra network hops and auth drift.

## Components

- Components receive already-authorized data. Reason: authorization belongs in server loaders, actions, and feature services.
- Keep form state local to the form component. Reason: global state for form drafts creates stale writes.
- Use accessible labels, button text, and focus states. Reason: SaaS users repeat workflows and need keyboard reliability.
- Extract a component only after the second real use. Reason: premature shared abstractions make product changes slower.

## Authentication And Authorization

- Check authentication at route boundaries and authorization at feature-service boundaries. Reason: route protection alone fails when functions are reused.
- Permission functions live in `lib/permissions.ts` or the owning feature. Reason: scattered role checks are easy to bypass.
- Never trust organization, project, or user IDs from the client without verifying membership. Reason: multi-tenant SaaS apps fail at tenant boundaries first.
- Log authorization denials with non-sensitive IDs. Reason: support needs traceability without leaking private data.

## Error Handling

- Throw typed application errors from feature code. Reason: UI can render predictable messages and status codes.
- Do not expose raw database errors to users. Reason: they can leak schema and implementation details.
- Use `notFound()` for missing resources and a forbidden response for unauthorized access. Reason: missing and unauthorized states have different security and UX meanings.

## Testing Rules

- Unit-test pure feature logic and validation schemas. Reason: these tests run fast and catch most regressions.
- Integration-test database writes with a temporary SQLite file. Reason: in-memory databases hide migration and file-locking issues.
- Add Playwright tests for signup, login, billing-critical flows, and destructive actions. Reason: browser tests should protect revenue and trust paths.
- Tests must not depend on wall-clock time without injecting a clock. Reason: time-dependent SaaS features become flaky in CI.

## Security Baseline

- Validate and normalize all incoming URLs before storing them. Reason: SaaS apps often render customer-supplied links later.
- Escape or sanitize Markdown/HTML before rendering. Reason: saved content can become stored XSS.
- Use CSRF protection for cookie-authenticated mutations. Reason: App Router server actions are not automatically safe for every auth model.
- Rate-limit login, invite, password reset, and public write endpoints. Reason: these endpoints attract abuse first.
- Keep audit records for role changes, billing changes, and destructive deletes. Reason: support and compliance need a history of sensitive actions.

## What We Do Not Do

- Do not add a second ORM or query builder. Reason: mixed data layers create migration drift and duplicate models.
- Do not use global client state for server-owned data. Reason: server components and cache revalidation already define the source of truth.
- Do not add broad middleware for business rules. Reason: middleware runs before useful context exists and is hard to test.
- Do not hide failed writes behind optimistic UI unless rollback is implemented. Reason: SaaS users need trustworthy state.
- Do not add env vars without documenting them in `.env.example`. Reason: deploy failures should be visible during review.
- Do not add dependencies for simple formatting, parsing, or one-function helpers. Reason: dependency churn increases maintenance and security work.

## Agent Workflow

- Before editing, inspect the relevant route, feature module, schema, migration, and tests. Reason: App Router changes often cross UI, server, and DB boundaries.
- For feature work, update the feature module, route/component, validation schema, migration if needed, and tests in the same PR. Reason: partial slices produce broken product behavior.
- Ask a clarification only when the decision affects product behavior, data retention, billing, or security. Reason: greenfield implementation details are already defined here.
- When blocked by missing credentials or external services, add a local mock or documented manual step. Reason: development should stay reproducible without private secrets.
- Final response should include changed files, verification commands, and any residual risk. Reason: reviewers need the operational state, not a narrative.
