# CLAUDE.md: Next.js 15 + SQLite SaaS

You are working in a greenfield SaaS application built with Next.js 15 App Router, TypeScript, Tailwind CSS, and SQLite through `better-sqlite3` for local/self-hosted deployments or Turso/libSQL for managed deployments. Make conservative implementation choices, prefer boring production patterns, and do not ask clarifying questions when this file gives a default.

## Stack Defaults

- Rule: Use Next.js 15 App Router with `src/app`.
  Reason: App Router keeps data loading close to routes and makes Server Components the default.
- Rule: Use TypeScript in strict mode.
  Reason: SaaS code has many authorization, billing, and persistence boundaries where implicit `any` becomes expensive.
- Rule: Use `pnpm` for examples and commands.
  Reason: It is deterministic, fast, and common in modern Next.js workspaces.
- Rule: Use Tailwind CSS plus a small `cn()` helper for styling.
  Reason: This avoids one-off CSS drift while keeping components portable.
- Rule: Use SQLite with raw SQL behind typed helper functions, not an ORM by default.
  Reason: SQLite is simple and predictable; hiding it behind a heavy abstraction makes migrations and performance harder to reason about.
- Rule: Use Zod at every external boundary.
  Reason: Form data, route params, environment variables, and webhooks are untrusted input.

## Dev Commands

Assume these scripts exist or add them when scaffolding:

```bash
pnpm dev
pnpm build
pnpm lint
pnpm typecheck
pnpm test
pnpm db:migrate
pnpm db:seed
```

When adding a feature, run at least:

```bash
pnpm typecheck
pnpm lint
pnpm test
```

If the change touches migrations, SQL, auth, billing, or permissions, also run:

```bash
pnpm db:migrate
pnpm build
```

## Folder Structure

Use this structure unless the existing project already chose a compatible layout:

```text
src/
  app/
    (auth)/
    (dashboard)/
    api/
    layout.tsx
    page.tsx
  components/
    ui/
    forms/
    layout/
  db/
    client.ts
    migrations/
    queries/
    schema.ts
    seed.ts
  features/
    billing/
    organizations/
    projects/
    users/
  lib/
    auth.ts
    env.ts
    errors.ts
    ids.ts
    permissions.ts
    result.ts
    utils.ts
  server/
    actions/
    services/
  tests/
```

- Rule: Put route files in `src/app`, shared UI in `src/components`, domain logic in `src/features`, persistence in `src/db`, and cross-domain primitives in `src/lib`.
  Reason: SaaS projects grow by domain; this layout prevents route folders from becoming the only place business logic can live.
- Rule: Keep SQL in `src/db/queries` or small repository functions near the owning feature.
  Reason: Query ownership should be obvious during schema changes.
- Rule: Do not import from `src/app` into `src/features`, `src/db`, or `src/lib`.
  Reason: Route code is delivery-layer code; importing it downward creates circular dependencies.

## Naming Conventions

- Rule: Components use `PascalCase.tsx`; hooks use `use-kebab-case.ts`; helpers use `kebab-case.ts`.
  Reason: File names reveal the kind of export before opening the file.
- Rule: Database tables use plural `snake_case`, columns use `snake_case`, TypeScript types use `PascalCase`.
  Reason: SQL stays idiomatic while TypeScript remains idiomatic.
- Rule: Use `organizationId`, `projectId`, and `userId` in TypeScript, never ambiguous `id` across boundaries.
  Reason: Multi-tenant bugs often come from mixing IDs with the same primitive type.
- Rule: Prefix server-only modules with `server` only when they may be confused with client-safe modules, such as `server-session.ts`.
  Reason: Over-prefixing adds noise, but auth and secrets need obvious boundaries.
- Rule: Environment variables are parsed once in `src/lib/env.ts`.
  Reason: Central validation prevents runtime surprises in route handlers and server actions.

## SQL And Migration Rules

- Rule: Store migrations in `src/db/migrations` as numbered SQL files like `0001_create_users.sql`.
  Reason: Lexical order must match execution order in CI and local development.
- Rule: Migrations are forward-only.
  Reason: Production rollback should restore from backup or ship a new migration; down migrations for SQLite often create false confidence.
- Rule: Every migration runs inside a transaction unless SQLite explicitly forbids the operation.
  Reason: Half-applied schema changes are worse than a failed deploy.
- Rule: New tables include `id`, `created_at`, and `updated_at`.
  Reason: SaaS support and audits need stable identity and timestamps.
- Rule: Tenant-owned tables include `organization_id` and an index that starts with `organization_id`.
  Reason: Tenant scoping must be fast and visible in query plans.
- Rule: Use foreign keys and enable them at connection startup with `PRAGMA foreign_keys = ON`.
  Reason: Application code should not be the only thing protecting referential integrity.
- Rule: For `better-sqlite3`, also set `PRAGMA journal_mode = WAL` and `PRAGMA busy_timeout = 5000`.
  Reason: WAL improves read/write concurrency; a busy timeout prevents avoidable request failures.
- Rule: Never interpolate user input into SQL strings.
  Reason: Prepared statements are the boundary against SQL injection.
- Rule: Destructive migrations require a comment explaining the data loss and a safe replacement path.
  Reason: SQLite makes table rewrites common; the risk must be obvious in review.
- Rule: Add an index in the same migration that introduces a query path used by a list page, dashboard widget, or authorization check.
  Reason: SaaS slowdowns usually begin as innocent unindexed filters.

## Data Access Patterns

- Rule: Expose typed functions such as `getProjectById(db, { organizationId, projectId })`.
  Reason: The tenant boundary travels with the query.
- Rule: Return plain objects from DB functions, not framework response objects.
  Reason: Persistence code should be testable without Next.js.
- Rule: Use service functions for multi-step mutations.
  Reason: Transactions, authorization, and side effects belong together.
- Rule: Prefer explicit column lists over `SELECT *`.
  Reason: Schema changes should not silently change API payloads.
- Rule: Convert SQLite integer booleans at the boundary.
  Reason: UI and domain code should not need to remember `0` and `1`.

## Next.js App Router Patterns

- Rule: Server Components are the default.
  Reason: They keep secrets server-side and reduce client JavaScript.
- Rule: Add `"use client"` only for local interactivity, browser APIs, or client-only state.
  Reason: Client Components create bundle cost and serialization constraints.
- Rule: Mutations go through Server Actions for app flows and Route Handlers for external callers or webhooks.
  Reason: Server Actions pair well with forms; Route Handlers are better API contracts.
- Rule: Validate Server Action input with Zod before touching the database.
  Reason: `FormData` is untyped and user-controlled.
- Rule: Use `redirect()` after successful create/update flows that change the current resource.
  Reason: It prevents duplicate submissions and keeps URL state canonical.
- Rule: Use `revalidatePath` or `revalidateTag` immediately after mutations that affect cached reads.
  Reason: Users should see their write reflected without a manual refresh.
- Rule: Keep `loading.tsx`, `error.tsx`, and `not-found.tsx` close to route segments that fetch data.
  Reason: Route-level states are part of the product experience, not afterthoughts.

## Component Patterns

- Rule: Components in `components/ui` are domain-agnostic and accept explicit props.
  Reason: UI primitives should not know about billing, projects, or organizations.
- Rule: Feature components can know the domain but should not import database clients.
  Reason: Data loading belongs in server pages, actions, or services.
- Rule: Use forms that work without client JavaScript when practical.
  Reason: Server Actions and progressive enhancement reduce state bugs.
- Rule: Keep page components orchestration-focused.
  Reason: Pages should assemble data and components, not hide complex business rules.
- Rule: Prefer small named components over large render branches.
  Reason: SaaS screens accumulate states quickly; names make states reviewable.

## Auth And Permissions

- Rule: Every server mutation starts by resolving the current user and organization.
  Reason: Tenant context is required before authorization can be correct.
- Rule: Keep permission checks in `src/lib/permissions.ts` or feature-local policy files.
  Reason: Repeating inline role checks causes drift.
- Rule: Deny by default when a role, membership, or organization cannot be resolved.
  Reason: Missing data should not become access.
- Rule: Do not trust organization IDs sent from the client without checking membership.
  Reason: Hidden inputs and route params are user-controlled.

## Error Handling

- Rule: Use typed result objects for expected business failures.
  Reason: Validation and permission failures are product states, not crashes.
- Rule: Throw for programmer errors and impossible states.
  Reason: Unexpected invariants should fail loudly in development and observability.
- Rule: User-facing error messages should say what happened and what to do next.
  Reason: Generic failure text increases support burden.
- Rule: Do not leak raw SQL errors to users.
  Reason: Error text can expose schema details.

## Testing Expectations

- Rule: Unit-test pure domain functions and permission rules.
  Reason: These are cheap tests for high-risk logic.
- Rule: Integration-test database queries with a temporary SQLite database.
  Reason: SQL correctness needs a real engine.
- Rule: Add at least one regression test for every bug fix.
  Reason: A bug without a regression test is a recurring bug.
- Rule: For Server Actions, test validation, authorization, and successful mutation paths.
  Reason: Actions are where untrusted input meets persistence.

## Patterns To Follow

- Rule: Start with the smallest vertical slice: schema, query, service/action, route, UI, test.
  Reason: SaaS features fail at integration boundaries, not in isolated layers.
- Rule: Keep tenant scoping explicit in function arguments.
  Reason: Hidden global tenant state is hard to audit.
- Rule: Prefer boring HTML forms and server-rendered data for CRUD.
  Reason: Most SaaS workflows benefit more from reliability than client-side cleverness.
- Rule: Add comments only for business rules, migration risk, and non-obvious SQL.
  Reason: Comments should explain why the code is surprising, not repeat syntax.
- Rule: Use stable IDs for tests and avoid relying on generated copy when testing behavior.
  Reason: Product text changes more often than business behavior.

## Anti-Patterns To Avoid

- Rule: Do not add an ORM unless the project already has one.
  Reason: For SQLite SaaS apps, raw SQL plus typed helpers is easier to debug and migrate.
- Rule: Do not put business logic in React Client Components.
  Reason: Client code is harder to secure and easier to duplicate.
- Rule: Do not call the database from shared UI components.
  Reason: It couples rendering primitives to persistence and breaks reuse.
- Rule: Do not create a migration that edits old migration files.
  Reason: Applied migrations are historical records.
- Rule: Do not rely on row-level filtering in the UI.
  Reason: Authorization belongs on the server and in query constraints.
- Rule: Do not store money as floating-point values.
  Reason: Billing needs integer minor units or exact decimal strings.
- Rule: Do not use global mutable singletons for request-specific data.
  Reason: Server runtimes reuse processes across users.
- Rule: Do not add client state for data already represented by the URL or server.
  Reason: Duplicate state creates stale screens.
- Rule: Do not introduce background jobs without an idempotency key.
  Reason: Retries are normal in production.

## Greenfield Defaults

If the project is empty or underspecified, choose these defaults without asking:

- Package manager: `pnpm`
- Source root: `src`
- Styling: Tailwind CSS
- Validation: Zod
- Tests: Vitest for unit/integration tests
- Local DB: `better-sqlite3`
- Managed DB option: Turso/libSQL
- IDs: generated text IDs through a small `src/lib/ids.ts` helper
- Auth placeholder: session helper in `src/lib/auth.ts`
- Dates: ISO strings at boundaries, SQLite `TEXT` columns with UTC timestamps

## Before Finishing A Change

Check this list:

- Does every DB query that reads tenant data include `organizationId`?
- Did migrations run locally?
- Are new env vars documented and validated in `src/lib/env.ts`?
- Are Server Actions validating input with Zod?
- Did you run `pnpm typecheck`, `pnpm lint`, and relevant tests?
- Is the UI still usable without unnecessary client JavaScript?
