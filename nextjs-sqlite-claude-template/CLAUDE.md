# CLAUDE.md — Next.js 15 + SQLite SaaS

You are working in a production-oriented SaaS project built with Next.js 15 App
Router, TypeScript, SQLite, and either `better-sqlite3`, Drizzle, or Turso.

The goal is boring reliability: small server-first changes, explicit data
boundaries, reversible migrations, and UI that remains easy to test.

## Stack and assumptions

- Next.js 15 App Router with React Server Components by default.
- TypeScript in strict mode.
- SQLite for primary relational storage.
- `better-sqlite3` for local/server deployments or Turso/libSQL for hosted edge-ish deployments.
- Drizzle is preferred for schema, typed queries, and migrations.
- Auth is session based; session reads happen on the server.
- Tailwind and shadcn/ui are acceptable for UI, but business rules stay outside components.

Reason: this stack is strongest when the database and auth stay server-side and
the client only receives the minimum state needed to render and interact.

## Folder structure

Use this structure unless the existing project already has a clear equivalent:

```text
app/
  (marketing)/
  (app)/
  api/
components/
  ui/
  forms/
  domain/
lib/
  auth/
  db/
  env.ts
  permissions.ts
server/
  actions/
  queries/
  services/
db/
  schema.ts
  migrations/
tests/
```

Rules:

- `app/` owns routing, layouts, metadata, and page composition.
- `components/ui/` contains generic design-system primitives only.
- `components/domain/` can know product language but must not query the database.
- `server/queries/` contains read-only server functions.
- `server/actions/` contains Server Actions that mutate data or coordinate forms.
- `server/services/` contains business workflows reusable by actions, route handlers, and jobs.
- `lib/db/` owns database connection creation and exports one canonical database client.

Reason: routing, UI, data access, and business rules change for different
reasons. Keeping them separate avoids rewrites when one layer moves.

## Server vs client decision tree

Default to Server Components.

Use a Client Component only when the component needs:

- browser-only APIs;
- local interactive state;
- effects/subscriptions;
- event handlers;
- optimistic UI that cannot be expressed with a Server Action form.

Never mark a whole page `"use client"` just because one child needs interaction.
Wrap the interactive child and keep data loading in the parent Server Component.

Reason: client boundaries pull code, dependencies, and sometimes secrets toward
the browser. Smaller client islands mean fewer leaks and faster pages.

## Database conventions

### Connection

- Export the database client from one file only, usually `lib/db/index.ts`.
- For `better-sqlite3`, use a singleton in development to avoid duplicate handles
  during hot reload.
- Enable WAL mode and foreign keys when using local SQLite.
- Never import the database client from a Client Component.

Reason: SQLite is reliable when connection behavior is explicit. Multiple
ad-hoc clients create locking surprises and inconsistent pragmas.

### Schema

- Prefer explicit table names: `users`, `organizations`, `memberships`,
  `subscriptions`, `audit_events`.
- Use `created_at` and `updated_at` consistently.
- Use `deleted_at` for soft-delete only when the product truly needs recovery or
  audit history; otherwise delete directly with foreign-key rules.
- Store money as integer cents plus currency code.
- Store timestamps as ISO strings or integer epoch milliseconds; do not mix both
  in the same project.

Reason: SaaS bugs often come from ambiguous ownership, time, and billing data.
Make those fields boring and uniform.

### Migrations

- Every schema change gets a migration file.
- Migrations must be forward-only by default.
- Destructive migrations require a comment explaining data impact and rollback
  strategy.
- Do not edit already-applied migrations; add a new one.
- Include indexes in the same migration as the query pattern that needs them.

Reason: SQLite migrations are easy until production data exists. Treat migration
history as an audit log, not a scratchpad.

## Data access rules

- All database reads go through `server/queries/` unless they are one-off admin
  scripts.
- All mutations go through `server/actions/` or `server/services/`.
- Validate input at the boundary using Zod or equivalent.
- Return small DTOs to UI components; do not pass raw database rows everywhere.
- Check authorization next to the data access, not only in the page.

Reason: pages are easy to refactor; authorization bugs survive refactors unless
they live beside the data they protect.

## Authentication and authorization

- `userId` alone is not enough for SaaS authorization.
- Model organization membership and role explicitly.
- Every organization-scoped query must include both resource id and organization
  id.
- Admin-only actions must check role on the server immediately before the
  mutation.
- Do not trust hidden form fields for ownership or price.

Reason: most SaaS access-control bugs are cross-tenant bugs. Tenant id must be a
first-class part of every sensitive query.

## Server Actions

Use Server Actions for form submissions and small mutations.

Pattern:

1. Parse and validate form data.
2. Read current session.
3. Authorize against the target resource.
4. Call a service function.
5. Revalidate or redirect.
6. Return a typed error object for expected validation failures.

Do not put complex business workflows directly inside React components.

Reason: Server Actions are excellent boundaries, but they become untestable when
they contain all business logic inline.

## API route handlers

Use route handlers for:

- webhooks;
- third-party integrations;
- file uploads;
- public API endpoints;
- non-form clients.

Rules:

- Verify webhook signatures before parsing trusted business fields.
- Keep route handlers thin; call services.
- Set explicit response codes.
- Do not leak stack traces or raw database errors.

Reason: route handlers are exposed surfaces. Treat them as adapters, not as the
place where the product rules live.

## Environment variables

- Define all env vars in `lib/env.ts`.
- Validate required variables at startup.
- Expose only `NEXT_PUBLIC_*` values to the browser.
- Never read `process.env` throughout random files.

Reason: centralized env validation fails fast and prevents accidental secret
exposure.

## Naming conventions

- Server query functions: `getUserById`, `listInvoicesForOrg`.
- Server actions: `createInvoiceAction`, `updateWorkspaceNameAction`.
- Services: `createInvoice`, `syncSubscriptionStatus`.
- Boolean fields: `is_active`, `has_access`, `email_verified`.
- IDs: `userId` in TypeScript, `user_id` in SQL.
- Files: kebab-case for components and route segments; camelCase for functions.

Reason: predictable names help Claude Code find the right layer and reduce
duplicate abstractions.

## UI conventions

- Pages compose; components render.
- Domain components receive typed props, not database clients.
- Form components accept `action`, `defaultValues`, and optional `errors`.
- Keep loading, empty, and error states explicit.
- Use accessible labels and buttons by default.

Reason: SaaS UI is mostly forms and tables. Consistent shapes make later changes
safe and fast.

## Testing expectations

Minimum useful coverage:

- unit tests for services with branching business rules;
- integration tests for critical Server Actions;
- route handler tests for webhooks and public endpoints;
- one happy-path Playwright test for signup/login/core workflow if the project
  already has browser tests.

When changing SQL, include at least one test or seed script that exercises the
new query shape.

Reason: SQLite makes integration tests cheap. Use that advantage.

## Dev commands

Prefer these command names:

```bash
npm run dev
npm run typecheck
npm run lint
npm run test
npm run db:generate
npm run db:migrate
npm run db:studio
```

Before finishing a non-trivial change, run the fastest relevant checks:

```bash
npm run typecheck
npm run lint
npm run test
```

If the project uses different package tooling, adapt commands but keep the same
verification intent.

## Patterns to follow

- Load data in Server Components, then pass DTOs to client islands.
- Keep authorization checks in server query/action/service functions.
- Use transactions for multi-step mutations.
- Prefer explicit SQL indexes over hoping SQLite will be fast enough.
- Add comments for business rules, not for obvious syntax.
- Return typed, user-safe errors from actions.

## Anti-patterns to avoid

- Whole-page `"use client"` without a narrow reason.
- Importing `db` into UI components.
- Reading `process.env` in many files.
- Mutating data in `server/queries/`.
- Using email address as a stable foreign key.
- Creating migrations after manually editing production schema.
- Catching all errors and returning `"Something went wrong"` without logging.
- Trusting client-submitted role, price, organization id, or subscription status.

Each anti-pattern either leaks secrets, weakens tenant isolation, or makes
future migrations harder.

## How to approach tasks

When implementing a feature:

1. Identify the tenant boundary.
2. Find or create the schema/query.
3. Add authorization at the data boundary.
4. Build the Server Action or route handler.
5. Compose the page with a small client island only if needed.
6. Run typecheck and the closest tests.

When fixing a bug:

1. Reproduce the behavior.
2. Add the smallest regression test or documented reproduction.
3. Fix in the layer that owns the problem.
4. Check for similar code paths.

When uncertain:

- Prefer server-side code.
- Prefer explicit types.
- Prefer a small service function over clever component logic.
- Ask only if the product behavior is ambiguous; do not ask about routine file
  placement when these conventions answer it.

