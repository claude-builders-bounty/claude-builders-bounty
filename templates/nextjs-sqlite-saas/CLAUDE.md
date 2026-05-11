# CLAUDE.md - Next.js 15 + SQLite SaaS Project

You are working in a production SaaS project built with Next.js 15 App Router, React 19, TypeScript, and SQLite. Follow these instructions without asking clarifying questions unless the request is impossible or would change product scope. When a detail is not specified, choose the convention in this file and continue.

## Stack & Versions

- Use Next.js 15 App Router with `src/app`. Reason: route groups, server components, server actions, and route handlers are the stable shape for new Next.js SaaS projects.
- Use React 19 and TypeScript in strict mode. Reason: server/client boundaries and database rows need type checking to avoid runtime-only failures.
- Use SQLite through Drizzle ORM. Reason: Drizzle keeps schema, migrations, and inferred TypeScript types in one place without hiding SQL.
- Use `better-sqlite3` for local or single-node deployments, and Turso/libSQL when the project must run against a remote SQLite-compatible database. Reason: `better-sqlite3` is simple and fast in Node.js, while Turso works better for distributed/serverless deployments.
- Use Zod for runtime validation at every external boundary: forms, route handlers, webhooks, environment variables, and imported data. Reason: TypeScript does not validate user input.
- Use Tailwind CSS plus small local UI primitives. Reason: most SaaS screens need consistent spacing and states more than a large component framework.
- Use Vitest for unit tests and Playwright for browser-level flows. Reason: database logic and route behavior should be tested quickly before browser tests cover the happy path.

## Dev Commands

Prefer `pnpm`. If the repository already uses another package manager lockfile, keep that package manager.

- `pnpm dev` - run the local Next.js app.
- `pnpm build` - compile production output; run before PRs touching routes, database code, or auth.
- `pnpm lint` - run lint rules.
- `pnpm typecheck` - run TypeScript without emitting files.
- `pnpm test` - run Vitest.
- `pnpm test:e2e` - run Playwright.
- `pnpm db:generate` - generate Drizzle migrations from `src/db/schema.ts`.
- `pnpm db:migrate` - apply migrations to the configured SQLite database.
- `pnpm db:studio` - inspect local data with Drizzle Studio.

If a command is missing, add it to `package.json` instead of inventing one-off commands in chat. Reason: repeatable commands are part of the project contract.

## Folder Structure

Use this structure for greenfield work:

```text
src/
  app/
    (marketing)/
      page.tsx
      pricing/page.tsx
    (auth)/
      login/page.tsx
      signup/page.tsx
    (dashboard)/
      layout.tsx
      dashboard/page.tsx
      settings/page.tsx
    api/
      health/route.ts
      webhooks/stripe/route.ts
  components/
    ui/
    layout/
    features/
      billing/
      organizations/
      users/
  db/
    client.ts
    schema.ts
    migrations/
    queries/
      organizations.ts
      users.ts
  lib/
    auth/
    env.ts
    permissions.ts
    result.ts
  server/
    actions/
    services/
  tests/
    fixtures/
    integration/
```

Rules:

- Put route files only under `src/app`. Reason: App Router routing is file-system based and should be obvious.
- Put reusable design primitives in `src/components/ui` and domain components in `src/components/features/<domain>`. Reason: a button is reusable everywhere; an invoice table is not.
- Put database schema in `src/db/schema.ts`, database connection code in `src/db/client.ts`, and query helpers in `src/db/queries`. Reason: route handlers and components should not assemble SQL directly.
- Put business workflows in `src/server/services`. Reason: services can be called from route handlers, server actions, jobs, and tests without duplicating rules.
- Put server actions in `src/server/actions` unless they are tiny and route-local. Reason: shared actions need validation, authorization, and tests.

## Naming Conventions

- Use kebab-case for route segments and file-system paths: `billing-settings`, `team-members`. Reason: URLs should stay readable and stable.
- Use PascalCase for React components: `BillingSettingsForm.tsx`. Reason: it distinguishes components from plain helpers.
- Use camelCase for functions and variables: `getCurrentOrganization`. Reason: this matches TypeScript conventions.
- Use `*.queries.ts` for database read helpers and `*.mutations.ts` for write helpers when a domain grows large. Reason: reviews can see read/write intent from the file name.
- Use `*.schema.ts` for Zod schemas that validate inputs, not database tables. Reason: Drizzle schema and validation schema solve different problems.
- Name server actions by user intent: `updateOrganizationSettingsAction`, not `submitForm`. Reason: action names appear in logs and tests.
- Name database tables in snake_case plural form: `organizations`, `organization_members`, `billing_events`. Reason: SQLite inspection and migrations stay predictable.

## SQL & Migration Conventions

- Change tables only in `src/db/schema.ts`, then run `pnpm db:generate`. Reason: generated migrations should match the typed schema.
- Review every generated SQL migration before committing it. Reason: migration tools can generate destructive operations when a rename was intended.
- Never edit a migration that has been applied to any shared environment. Create a follow-up migration instead. Reason: migration history must be append-only after sharing.
- Use explicit foreign keys and indexes for every tenant or ownership lookup. Reason: SaaS bugs often come from missing organization scoping or slow dashboard queries.
- Every tenant-owned table must include `organizationId` unless there is a written reason in the schema comment. Reason: tenant isolation must be visible in the data model.
- Use transactions for multi-step writes that must succeed or fail together. Reason: SQLite supports transactions and partial writes create support tickets.
- Prefer Drizzle query builders for normal reads and writes. Use raw SQL only for SQLite-specific features that Drizzle cannot express, and parameterize every value. Reason: string interpolation in SQL is a security bug.
- Store timestamps as SQLite integers or text consistently across the whole schema. Do not mix conventions per table. Reason: sorting and date comparisons break when formats drift.
- Keep seed data under `src/db/seed.ts` or `tests/fixtures`. Reason: production migrations should not contain demo data.

Example table pattern:

```ts
export const organizations = sqliteTable("organizations", {
  id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
  name: text("name").notNull(),
  slug: text("slug").notNull().unique(),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull(),
  updatedAt: integer("updated_at", { mode: "timestamp" }).notNull(),
});
```

## Data Access Rules

- Components do not import `db` directly. They call query helpers or services. Reason: authorization and tenancy rules belong near data access, not scattered through UI.
- Query helpers return typed domain data, not raw driver rows, when the result crosses a module boundary. Reason: callers should not know column aliases.
- Every write validates input with Zod before touching the database. Reason: server actions and API routes can be called with malformed input.
- Every query that reads tenant data must accept `organizationId` explicitly. Reason: implicit global state makes data leaks hard to review.
- Route handlers and server actions must check authentication and authorization before data access. Reason: the database layer should not be the first security boundary.

## Component Patterns

- Use Server Components by default. Add `"use client"` only for state, effects, browser APIs, or interactive event handlers. Reason: Server Components reduce bundle size and avoid unnecessary client data fetching.
- Keep client components as leaves in the tree. Reason: one client boundary high in the tree turns all children into client code.
- Put data loading in pages, layouts, or server-only query helpers. Reason: loading should be close to routing and authorization.
- Use forms with server actions for normal dashboard mutations. Use route handlers for webhooks, public API endpoints, and non-form clients. Reason: server actions reduce boilerplate for first-party UI.
- Convert `FormData` with `Object.fromEntries(formData)` and validate it with the domain Zod schema. Do not cast form values with `as any`. Reason: form values are untrusted strings and unsafe casts bypass the validation layer.
- Prefer composition over prop drilling. If a value must pass through more than two layers, use a small provider at the route boundary or move the component closer to its data. Reason: long prop chains make dashboard screens brittle.
- UI components must expose loading, empty, and error states. Reason: SaaS data is often async and account-specific.
- Use accessible labels for every form control and interactive icon. Reason: internal tools still need keyboard and screen-reader support.

## API & Result Shape

Use one response shape for route handlers:

```ts
type ApiResult<T> =
  | { data: T; error: null; meta?: Record<string, unknown> }
  | { data: null; error: { code: string; message: string }; meta?: Record<string, unknown> };
```

- Return `401` when the user is not signed in, `403` when signed in but not allowed, `404` when the tenant-scoped resource does not exist, and `422` for validation errors. Reason: clients need stable error semantics.
- Do not leak internal error messages to clients. Log details server-side and return a stable error code. Reason: stack traces and SQL messages can reveal internals.
- Webhook routes must verify signatures before reading or mutating data. Reason: unauthenticated webhook handlers are public write endpoints.

## Environment & Runtime

- Validate environment variables in `src/lib/env.ts` with Zod at startup. Reason: missing secrets should fail fast.
- Do not run `better-sqlite3` in Edge runtime. Set `export const runtime = "nodejs"` on route handlers that use it. Reason: native SQLite bindings require Node.js.
- Use Turso/libSQL for edge-compatible or remote deployments. Reason: remote SQLite access needs an HTTP/WebSocket driver.
- Keep `.env.local` out of git and document required variables in `.env.example`. Reason: contributors need setup guidance without secrets.

## Testing Rules

- Unit-test pure services and validation schemas with Vitest. Reason: these catch most business-rule regressions quickly.
- Integration-test database queries against a temporary SQLite database file. Reason: in-memory tests can hide migration and file-locking issues.
- E2E-test one happy path per critical flow: signup, login, organization switch, billing settings, and webhook ingestion. Reason: more browser tests slow down PRs without covering new logic.
- Tests must create their own data and clean it up. Reason: order-dependent tests are unreliable.
- When fixing a bug, add a test that fails before the fix. Reason: the test should prove the regression is covered.

## Implementation Workflow

Before editing:

1. Inspect `package.json`, `src/db/schema.ts`, existing route groups, and relevant domain folders.
2. Identify whether the change is UI-only, database-only, or full-stack.
3. Reuse existing patterns first; create a new pattern only when the project has no local convention.

When adding a full-stack feature:

1. Add or update Drizzle schema and migrations.
2. Add query or service helpers with tenant scoping.
3. Add Zod input schemas.
4. Add server actions or route handlers.
5. Add Server Component pages and small Client Component leaves.
6. Add tests for validation, data access, and one user-facing path.
7. Run typecheck, tests, lint, and build.

## What We Do Not Do

- Do not ask the user which package manager, ORM, or folder structure to use in a greenfield task. Use this file. Reason: the template exists to remove those choices.
- Do not put all code for a feature inside `page.tsx`. Reason: pages should compose services and components, not become untestable modules.
- Do not fetch tenant data from Client Components with ad hoc `fetch` calls when the page can load it on the server. Reason: server loading is faster, safer, and easier to authorize.
- Do not use `any` to get around Drizzle, Zod, or React types. Reason: type escapes hide exactly the bugs this stack is meant to catch.
- Do not use `as any` in examples, implementation plans, or submitted code. Reason: Claude often copies examples directly into the project, so examples must model the standard.
- Do not write raw SQL with template-string values. Reason: parameterized queries prevent injection and quoting bugs.
- Do not mutate the database in React components. Reason: writes belong in server actions, route handlers, services, or jobs.
- Do not skip migrations and call `db.run("ALTER TABLE ...")` from application code. Reason: schema changes must be reviewed and repeatable.
- Do not mix organization-scoped and user-scoped authorization checks in UI components. Reason: permissions must be enforced server-side before data is returned.
- Do not introduce global state for current organization unless it is derived from the authenticated request or route. Reason: global mutable state leaks across users in server environments.
- Do not add a dependency for a problem solved by a small typed helper. Reason: SaaS maintenance cost grows with every package.

## Default Decisions For Ambiguous Requests

- If a feature needs persistence, add Drizzle schema, migration, and typed query helpers.
- If a feature is tenant-owned, require `organizationId` in every read and write path.
- If a page is under the authenticated dashboard, place it in `src/app/(dashboard)`.
- If a mutation is triggered by a first-party form, use a server action.
- If a mutation is triggered by an external service, use a route handler.
- If the user asks for a UI component, include loading, empty, and error states.
- If the user asks for production readiness, run or add `typecheck`, `test`, `lint`, and `build` commands.
