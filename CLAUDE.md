# Claude Instructions: Next.js 15 + SQLite SaaS

Use this file as the project memory for a greenfield SaaS built with Next.js 15 App Router, TypeScript, SQLite, and server-first React.

## Stack And Commands

- Use Next.js 15 App Router with React Server Components by default, because server rendering keeps secrets and database access out of the browser.
- Use TypeScript in `strict` mode, because SaaS code changes frequently and type drift becomes expensive quickly.
- Use SQLite through either `better-sqlite3` for local/single-node deployments or Turso/libSQL for hosted edge-friendly deployments; do not mix both clients in one code path.
- Prefer Drizzle ORM for schema and migrations, because it keeps SQL visible while still giving typed query results.
- Use these baseline commands unless `package.json` says otherwise:
  - `npm run dev` for local development.
  - `npm run lint` before committing UI or API changes.
  - `npm run typecheck` before touching shared types, auth, billing, or database code.
  - `npm test` for unit tests.
  - `npm run db:generate` after editing schema definitions.
  - `npm run db:migrate` before running code that depends on a new column or table.

## Folder Structure

- Put route handlers in `app/api/**/route.ts`, because App Router expects HTTP behavior to live beside the route segment.
- Put page UI in `app/(marketing)` and authenticated product UI in `app/(app)`, because route groups keep public and signed-in layouts separate.
- Put reusable presentational components in `components/ui`, because they should not import database, auth, or billing modules.
- Put feature components in `features/<feature-name>/components`, because colocating feature UI with its use cases prevents a generic components folder from becoming a junk drawer.
- Put database schema in `db/schema.ts`, migrations in `db/migrations`, and query helpers in `db/queries`, because schema, migration history, and read/write intent should be easy to review independently.
- Put server-only services in `server/<domain>`, because server modules may import secrets, database clients, and payment SDKs.
- Put cross-cutting types in `lib/types.ts` only when they are used by at least two domains; otherwise keep types next to the feature that owns them.

## Server And Client Boundaries

- Start every component as a Server Component, because `"use client"` increases bundle size and moves execution into an untrusted environment.
- Add `"use client"` only for browser-only state, effects, event handlers, or DOM APIs, because those are the cases React Server Components cannot handle.
- Never import `db`, `server/*`, environment secrets, or payment SDKs from a Client Component, because that can leak privileged logic or break the client bundle.
- Prefer Server Actions for form submissions that mutate first-party data, because they keep validation and writes on the server.
- Prefer route handlers for webhooks, third-party callbacks, public API endpoints, and non-form clients, because those need explicit HTTP contracts.

## Database And Migrations

- Treat migrations as append-only after they are merged, because changing applied migrations breaks existing databases and CI fixtures.
- Name migrations with the change intent, for example `0004_add_team_members.sql`, because reviewers should understand the data change before reading SQL.
- Keep every migration reversible in practice even if the tool does not generate down migrations, because SaaS incidents often require manual rollback plans.
- Add `created_at` and `updated_at` to business tables, because support, billing, and audit questions always need timelines.
- Use integer primary keys or text UUIDs consistently across the app; do not mix per table without a reason, because joins and route params become harder to reason about.
- Enforce uniqueness and foreign keys in SQLite, because application-only integrity checks fail under retries and concurrent requests.
- Store money as integer minor units plus currency code, because floating point values create billing defects.
- Store external provider IDs in dedicated unique columns, because webhook retries must be idempotent.
- Wrap multi-step writes in transactions, because partial account, team, subscription, or invoice state is worse than a failed request.

## Naming Conventions

- Use `PascalCase` for React components, `camelCase` for functions and variables, and `SCREAMING_SNAKE_CASE` only for true constants.
- Name Server Actions with a verb phrase like `createTeamAction`, because call sites should reveal mutation intent.
- Name query helpers by what they return, such as `getTeamBySlug` or `listInvoicesForCustomer`, because generic names hide authorization boundaries.
- Name route segment folders with URL language, not implementation language, because users and product specs talk in URLs.
- Use `*.server.ts` for modules that must never enter the client bundle, because the suffix makes boundary mistakes easier to spot in review.

## Auth, Tenancy, And Authorization

- Read the current user on the server at the edge of every request or action, because client-provided user IDs are not trusted.
- Check tenant membership inside every query or mutation that touches tenant data, because UI-level gating does not protect direct requests.
- Pass `tenantId` explicitly to server services, because hidden global tenancy makes tests and background jobs unsafe.
- Return `notFound()` for resources outside the current tenant unless product requirements need a distinct forbidden state, because it avoids leaking resource existence.

## Component Patterns

- Keep page files thin: load data, check access, and compose feature components, because large pages are difficult to test and reuse.
- Use small server components for data-specific sections, because each section can own its query and loading boundary.
- Keep client components at leaf nodes, because it minimizes hydration cost and makes server/client boundaries obvious.
- Use controlled forms only when the UI needs live validation or conditional fields, because uncontrolled forms plus Server Actions are simpler for basic CRUD.
- Put loading and error states beside the route segment with `loading.tsx` and `error.tsx`, because App Router handles those boundaries natively.

## API And Validation

- Validate all external input with a schema library such as Zod at the route handler or Server Action boundary, because TypeScript does not validate runtime data.
- Return typed success and error shapes from internal actions, because UI code should not parse thrown errors for normal validation failures.
- Keep webhook handlers idempotent by recording event IDs, because providers retry and can deliver events out of order.
- Do not expose raw database errors to users, because they leak schema details and create poor support experiences.

## Testing Rules

- Add unit tests for pure functions, permission checks, query builders, and billing calculations, because these fail quietly and are cheap to test.
- Add integration tests around Server Actions and route handlers that write to SQLite, because mutations are where schema and authorization mistakes meet.
- Use a temporary SQLite database per test file or test worker, because shared local databases make tests order-dependent.
- Test migrations from an empty database and from the previous schema state, because both new installs and upgrades matter.
- Do not mock authorization in tests that claim to cover tenant access, because the real permission path is the behavior under test.

## What We Do Not Do

- Do not put database calls in Client Components, because the browser is not a trusted execution environment.
- Do not change a migration after it has landed, because checksum drift and existing deployments will break.
- Do not add a global mutable singleton for request-specific state, because concurrent requests can leak user or tenant data.
- Do not store secrets in `NEXT_PUBLIC_*` variables, because that prefix intentionally ships values to the browser.
- Do not build a generic abstraction before two real features need it, because premature shared layers slow down product changes.
- Do not catch every error and return `null`, because silent failures turn bugs into corrupted state.
- Do not introduce a second UI pattern library without removing the first, because mixed primitives create inconsistent accessibility and styling.

## Before Finishing A Change

- Run the smallest relevant test command first, then the broader lint/typecheck commands, because quick feedback keeps the loop tight.
- Check whether the change crosses server/client boundaries, because that is the most common source of Next.js App Router regressions.
- Check whether the change touches tenant data, billing, auth, or migrations; if so, add or update tests before opening a PR.
- Summarize database, auth, and user-visible behavior changes in the PR, because reviewers need to know the risk areas quickly.
