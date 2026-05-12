# CLAUDE.md - Next.js 15 App Router + SQLite SaaS

Use this file as the project-level operating guide for a greenfield SaaS app built with Next.js 15 App Router, TypeScript, and SQLite. Prefer the boring path: predictable folders, explicit migrations, Server Components by default, and small feature slices that can be shipped safely.

## 1. Stack & versions

- Rule: Use Next.js 15 App Router, React Server Components, TypeScript strict mode, and Node.js 20 LTS or newer.
  Why: This keeps server rendering, routing, and runtime behavior aligned with the current App Router model while avoiding legacy Pages Router patterns.

- Rule: Use SQLite as the application database, with `better-sqlite3` for local/self-hosted Node deployments and Turso/libSQL when the app needs a managed or geographically distributed SQLite service.
  Why: Local SQLite is simple and fast on one durable host, while Turso/libSQL avoids filesystem persistence problems on serverless platforms.

- Rule: Use Drizzle ORM and checked-in SQL migrations unless the project has already chosen a different SQLite migration tool.
  Why: Drizzle keeps the TypeScript schema close to the app while producing reviewable migration files instead of hidden database drift.

- Rule: Use Zod at all input boundaries: Server Actions, Route Handlers, webhook payloads, and env parsing.
  Why: SaaS bugs usually cross trust boundaries; validating there keeps database writes and billing/auth flows predictable.

## 2. Folder structure

```text
app/
  (marketing)/
  (auth)/
  (dashboard)/
  api/
    webhooks/
components/
  ui/
db/
  client.ts
  schema.ts
  migrations/
features/
  billing/
    actions.ts
    components/
    queries.ts
    schema.ts
  users/
    actions.ts
    components/
    queries.ts
lib/
  auth/
  env.ts
  errors.ts
  validation.ts
tests/
  integration/
  e2e/
```

- Rule: Put route groups in `app/` by audience: marketing, auth, dashboard, and API.
  Why: SaaS apps have different layout, caching, and auth rules for each audience; route groups make those rules visible.

- Rule: Put feature-specific actions, queries, and components under `features/<feature>/`.
  Why: Billing, users, teams, and settings evolve independently, so feature folders reduce cross-feature edits.

- Rule: Put shared primitives in `components/ui/` and shared infrastructure in `lib/`.
  Why: This prevents a reusable button or auth helper from being buried inside one feature folder.

- Rule: Put database connection, schema, and migrations under `db/`.
  Why: SQLite migration order and connection behavior are core infrastructure and must be easy to audit.

## 3. Naming conventions

- Rule: Use `snake_case` for database tables and columns.
  Why: SQL examples, migration diffs, and SQLite tooling are easier to read when database names stay SQL-native.

- Rule: Use `camelCase` for TypeScript variables and object fields returned to the app.
  Why: Application code should follow TypeScript conventions even when the stored columns are SQL-native.

- Rule: Use `PascalCase` for React components and `kebab-case` for route segments.
  Why: This matches the expectations of React and file-system routing without inventing a local dialect.

- Rule: Name Server Actions as `verbNounAction`, such as `createTeamAction` or `updateBillingEmailAction`.
  Why: The suffix makes mutations easy to distinguish from pure queries during review.

- Rule: Name query helpers as `getNoun`, `listNouns`, or `findNounById`.
  Why: A consistent verb tells Claude Code whether a helper returns one row, many rows, or an optional row.

## 4. Dev commands

Use these commands unless `package.json` says otherwise:

```bash
npm run dev          # start the local Next.js app
npm run build        # production build
npm run lint         # lint source files
npm run typecheck    # TypeScript check without emitting
npm test             # unit and integration tests
npm run test:e2e     # Playwright smoke tests
npm run db:generate  # generate migration from schema changes
npm run db:migrate   # apply checked-in migrations
```

- Rule: Before opening a PR, run `npm run typecheck`, `npm run lint`, `npm test`, and any migration test that touches `db/`.
  Why: Most SaaS regressions are type, auth, or data-shape regressions that should be caught locally.

## 5. SQLite, better-sqlite3, and Turso selection

- Rule: Choose `better-sqlite3` for a single Node server, local-first SaaS admin tools, or a VPS with a durable disk.
  Why: It is synchronous, simple, and very fast when the database file lives beside the app process.

- Rule: Choose Turso/libSQL for Vercel-style serverless, multi-region reads, or deployments without durable local storage.
  Why: Local SQLite files are unsafe on ephemeral serverless filesystems; Turso gives SQLite semantics with managed persistence.

- Rule: Expose one database client from `db/client.ts`; do not import driver clients across features.
  Why: A single client boundary makes it possible to swap `better-sqlite3` and Turso without editing business logic.

- Rule: Keep database access in `features/*/queries.ts`, `features/*/actions.ts`, or `db/*`.
  Why: Scattered SQL inside components makes caching, transactions, and permissions hard to review.

## 6. SQL / migration conventions

- Rule: Migrations are append-only and committed in order under `db/migrations/`.
  Why: Production databases need a reproducible history; rewriting old migrations breaks deploys and teammate databases.

- Rule: Never use schema push commands against production data.
  Why: Push-style sync can drop or rewrite data without a reviewed migration plan.

- Rule: Every destructive migration needs a backup note and a reversible manual plan in the PR.
  Why: SQLite is easy to copy before migration, and the PR should make rollback practical.

- Rule: Add indexes for columns used in dashboard filters, tenant scoping, webhook lookup, and auth/session lookup.
  Why: SaaS datasets grow around tenants and time ranges; missing indexes first hurt customer-facing dashboards.

- Rule: Prefer soft delete columns such as `deleted_at` for user-owned business records.
  Why: Customers often need recovery, audit trails, and billing dispute context.

## 7. Server Actions and Route Handlers

- Rule: Use Server Actions for first-party form submissions and dashboard mutations.
  Why: They keep validation, auth checks, and revalidation close to the UI that triggered the mutation.

- Rule: Use Route Handlers for public APIs, webhooks, third-party callbacks, and non-browser clients.
  Why: These need explicit HTTP methods, status codes, signature verification, and stable external contracts.

- Rule: Every mutation must check auth and tenant membership on the server.
  Why: Client-side guards improve UX but do not protect SaaS data.

- Rule: Return typed action results instead of throwing raw database errors into UI paths.
  Why: Users need actionable messages, while logs can keep the detailed error for debugging.

## 8. Component patterns

- Rule: Use Server Components by default.
  Why: SaaS dashboards benefit from smaller client bundles and direct server-side data access.

- Rule: Use Client Components only for browser state, effects, event handlers, charts, drag/drop, or optimistic UI.
  Why: Marking everything `use client` moves too much logic and data into the browser.

- Rule: Keep data loading in pages, layouts, query helpers, or Server Components; pass plain data into Client Components.
  Why: Client Components should not own database access or secret-bearing logic.

- Rule: Put feature UI under `features/<feature>/components/` unless it is a true reusable primitive.
  Why: Locality makes it faster to modify one SaaS workflow without disturbing unrelated pages.

## 9. Auth and session conventions

- Rule: Resolve the current user and tenant in dashboard layouts or server helpers, not inside every leaf component.
  Why: Central auth checks reduce duplicated authorization mistakes.

- Rule: Treat `user_id`, `team_id`, and `organization_id` as scoped access controls in every query.
  Why: Multi-tenant data leaks are high-impact SaaS failures.

- Rule: Never trust a tenant id, role, or price id submitted from the client without reloading it server-side.
  Why: Hidden form fields and client state are user-controlled input.

## 10. Validation and error handling

- Rule: Parse environment variables in `lib/env.ts` at startup with Zod.
  Why: A missing database URL or auth secret should fail loudly before a broken deploy serves users.

- Rule: Validate every Server Action and Route Handler payload with a named schema.
  Why: Named schemas are reusable in tests and make review easier than inline shape checks.

- Rule: Use domain errors from `lib/errors.ts` for expected failures such as `not_found`, `forbidden`, and `invalid_state`.
  Why: Expected failures should produce stable UI messages and HTTP responses.

- Rule: Log unexpected errors server-side, but do not expose stack traces or SQL details to users.
  Why: Good observability should not leak implementation details.

## 11. Testing rules

- Rule: Unit test pure helpers, validation schemas, and permission functions.
  Why: These are cheap to test and often carry business rules.

- Rule: Integration test database queries and Server Actions with a temporary SQLite database.
  Why: SQLite behavior, migrations, and constraints must be exercised against a real database engine.

- Rule: Add one Playwright smoke test for each paid or account-critical flow.
  Why: Signup, login, billing, and dashboard flows fail across component boundaries that unit tests miss.

- Rule: When changing migrations, test a fresh database and an upgraded database.
  Why: SaaS deploys must work for both new installs and existing customers.

## 12. Performance rules

- Rule: Select explicit columns instead of `SELECT *`.
  Why: Dashboards should not fetch large text blobs, secrets, or unused columns by accident.

- Rule: Paginate list pages with stable cursors or indexed timestamp/id pairs.
  Why: Offset pagination gets slow and unstable as customer data grows.

- Rule: Cache marketing pages more aggressively than authenticated dashboard pages.
  Why: Public pages can be shared across users, while dashboard pages are tenant-specific and permission-sensitive.

- Rule: Keep long-running jobs out of request/response paths.
  Why: SaaS users should not wait on imports, billing sync, email fanout, or report generation.

## 13. Security rules

- Rule: Store secrets only in environment variables or the deployment secret manager.
  Why: Committed secrets are difficult to rotate and can expose customer data.

- Rule: Verify webhook signatures before reading or trusting the payload.
  Why: Webhooks often change billing or account state and must be authenticated before processing.

- Rule: Use parameterized queries or ORM query builders only.
  Why: String-built SQL invites injection and escaping bugs.

- Rule: Apply tenant filters inside query helpers, not only in calling pages.
  Why: The safest query is one that cannot forget tenant scoping.

- Rule: Do not add security scanners, external telemetry, or paid APIs without explicit human approval.
  Why: This project should remain local-first and cost-free unless the maintainer chooses otherwise.

## 14. What we don't do (and why)

- Do not mix Pages Router and App Router.
  Why: Mixed routing creates duplicate data-fetching and auth conventions.

- Do not put every component behind `use client`.
  Why: It loses App Router's server-first performance and secret isolation.

- Do not run local SQLite on ephemeral serverless filesystems.
  Why: The database can disappear between invocations; use Turso/libSQL instead.

- Do not skip migrations by editing the production database manually.
  Why: Manual drift makes future deploys unreliable and hard to debug.

- Do not create generic repository-wide abstractions before two features need them.
  Why: Early SaaS work benefits from explicit feature code that is easy to change.

- Do not copy payment, auth, or webhook examples without adapting their tenant and validation rules.
  Why: These flows carry money and account access, so generic snippets are risky.

## 15. Claude Code behavior rules

- Rule: Before editing, inspect `package.json`, `next.config.*`, `db/schema.ts`, existing migrations, and the relevant `features/<feature>/` folder.
  Why: The local project may already have a chosen driver, ORM, or auth provider.

- Rule: Make the smallest useful change and keep it inside the feature folder when possible.
  Why: Small changes are easier to review and less likely to break unrelated SaaS flows.

- Rule: When adding a table, update schema, migration, query helpers, validation, and at least one test together.
  Why: Database changes are only complete when the app can safely read, write, and verify them.

- Rule: If a product decision is missing, make one conservative assumption and write it down in the PR.
  Why: Blocking on every detail slows delivery, but hidden assumptions cause review churn.

- Rule: Do not add paid services, background platforms, analytics, or auth providers without explicit maintainer approval.
  Why: External services create cost, account, and compliance work outside the code change.

- Rule: After changes, report the exact commands run and any skipped checks.
  Why: Maintainers need to know what was actually verified before merge.
