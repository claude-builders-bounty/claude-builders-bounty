# CLAUDE.md

This file tells Claude Code how to work in a greenfield SaaS product built with Next.js 15 App Router, TypeScript, SQLite, and React Server Components.

The defaults are intentionally narrow. Prefer boring, explicit server-side code over clever abstractions because this stack is usually chosen for small teams that need fast iteration without losing data integrity.

## Stack And Versions

- Runtime: Node.js 22 LTS or newer.
  Reason: Next.js 15, modern `fetch`, stable Web APIs, and native test tooling behave more predictably on current Node.

- Framework: Next.js 15 App Router with React 19 and TypeScript strict mode.
  Reason: Server Components, route handlers, server actions, and colocated layouts are the architectural center of this app. Do not add Pages Router files.

- Database: SQLite through `better-sqlite3` for single-node deployments or Turso/libSQL when remote SQLite is required.
  Reason: SQLite gives transactional local persistence with little operational overhead. The app should treat the database as a real production dependency, not as a toy cache.

- Styling: CSS Modules, Tailwind, or a small component library are acceptable, but choose one primary styling system.
  Reason: Mixed styling systems make visual regressions and component reuse harder to reason about.

- Auth and billing: keep provider integrations behind `lib/auth/*` and `lib/billing/*`.
  Reason: SaaS providers change APIs often; isolating them keeps product code portable.

## Dev Commands

Use these command names unless the repository has already documented different ones:

```bash
npm run dev        # Start the local Next.js server
npm run build      # Production build; run before PRs that touch routing or server code
npm run typecheck  # TypeScript validation
npm run lint       # Static checks, if configured
npm test           # Unit/integration tests, if configured
npm run db:migrate # Apply pending SQLite migrations
npm run db:seed    # Seed local development data
```

If a command is missing, add it to `package.json` before depending on it in docs or CI.
Reason: Claude should not invent commands that future contributors cannot run.

## Folder Structure

Use this shape for greenfield work:

```text
app/
  (marketing)/
    page.tsx
  (app)/
    dashboard/
      page.tsx
      loading.tsx
  api/
    webhooks/
      stripe/
        route.ts
components/
  ui/
  forms/
  layout/
db/
  migrations/
  schema.ts
  seed.ts
lib/
  auth/
  billing/
  db/
    client.ts
    migrate.ts
  env.ts
  errors.ts
  validation/
server/
  actions/
  queries/
  services/
tests/
  fixtures/
  integration/
  unit/
```

Rules:

- Put route UI, layouts, loading states, and route handlers under `app/`.
  Reason: App Router routing is filesystem-driven; colocating route-specific UI reduces search time.

- Put reusable presentational pieces in `components/`.
  Reason: Components should not import database clients, secrets, or request-scoped server state.

- Put database schema, migrations, and seed scripts under `db/`.
  Reason: Data shape is product infrastructure and must be easy to review separately from UI.

- Put server-only domain behavior in `server/`.
  Reason: Server actions, queries, and services frequently touch secrets or persistence and must not drift into client bundles.

- Put cross-cutting utilities in `lib/`, but do not turn `lib/` into a dumping ground.
  Reason: If a helper belongs to one domain, keep it near that domain.

## Naming Conventions

- React components: `PascalCase.tsx`.
  Reason: Components are values rendered by JSX and should visually stand apart from utilities.

- Hooks: `useThing.ts`.
  Reason: React hook naming is runtime-significant and lintable.

- Server actions: `verbNounAction.ts` or grouped `actions.ts` inside a route/domain folder.
  Reason: Server actions mutate state; the verb-first name makes side effects visible.

- Query functions: `getThing`, `listThings`, `findThingById`.
  Reason: Query names should reveal cardinality and nullability.

- Service functions: `createSubscription`, `cancelSubscription`, `syncCustomer`.
  Reason: Services represent business operations, not HTTP verbs.

- Database tables: plural snake_case, for example `users`, `team_members`, `billing_events`.
  Reason: SQL stays readable and avoids case-sensitivity surprises.

- Database columns: snake_case with explicit timestamps such as `created_at`, `updated_at`, `deleted_at`.
  Reason: SQL queries and migration diffs stay consistent.

## Environment And Config

- Read environment variables in `lib/env.ts` only.
  Reason: Central validation catches missing secrets at boot instead of halfway through a request.

- Export a typed `env` object; do not read `process.env` directly in feature code.
  Reason: Feature code should not need to know whether a value came from the environment, a test override, or deployment config.

- Keep `.env.example` complete and secret-free.
  Reason: New developers and Claude Code need a safe map of required configuration.

- Never commit `.env`, SQLite database files, uploaded assets, or generated logs.
  Reason: These files contain secrets, user data, or machine-local state.

## SQLite And Migration Conventions

- Use one SQLite connection factory in `lib/db/client.ts`.
  Reason: Multiple ad hoc connections cause locking, pragma drift, and inconsistent transaction behavior.

- Enable foreign keys on every connection: `PRAGMA foreign_keys = ON`.
  Reason: SQLite does not enforce foreign keys unless explicitly enabled.

- Set `PRAGMA journal_mode = WAL` for local `better-sqlite3` deployments.
  Reason: WAL improves read/write concurrency for web apps.

- All writes that touch more than one table must run in a transaction.
  Reason: SaaS data often spans accounts, memberships, audit records, and billing state; partial writes create support debt.

- Migrations are immutable after merge.
  Reason: Editing an applied migration breaks existing environments. Add a new migration instead.

- Name migrations with sortable timestamps: `YYYYMMDDHHMM_description.sql`.
  Reason: Filesystem order must match execution order without extra tooling.

- Every migration must include forward-only SQL and a short comment explaining the product reason.
  Reason: Reviewers need to know why the schema changed, not just what changed.

- Prefer additive migrations: add nullable columns, backfill, then add constraints in a later migration when possible.
  Reason: SQLite has limited `ALTER TABLE` support and production data needs safer rollout steps.

- Use explicit indexes for foreign keys and frequent filters.
  Reason: SQLite will enforce constraints without automatically creating the indexes your queries need.

- Store timestamps as UTC ISO-8601 text unless the project has already standardized on Unix milliseconds.
  Reason: ISO text is readable in SQLite CLI, logs, and support exports.

- Use `INTEGER` for booleans with `0` and `1`.
  Reason: SQLite has dynamic typing; explicit conventions prevent mixed values.

- Avoid `SELECT *` outside one-off scripts.
  Reason: Explicit columns protect API contracts from future schema additions.

## Data Access Pattern

Use a three-layer split:

```text
server/queries/   read-only database access
server/actions/   server actions that validate input and call services
server/services/  business operations and transactions
```

Rules:

- Server Components may call query functions directly.
  Reason: Server Components already run on the server and can render from trusted reads.

- Client Components must not import database, query, or service modules.
  Reason: This prevents accidental secret leakage and invalid client bundles.

- Server actions validate input, check authorization, call services, and return small typed results.
  Reason: Actions are the boundary between user input and business logic.

- Services do not read raw form data or request objects.
  Reason: Keeping services transport-agnostic makes them testable.

- Every mutation that matters to users should write an audit event.
  Reason: SaaS support needs to explain who changed what and when.

## App Router Patterns

- Use Server Components by default.
  Reason: They reduce client JavaScript and keep data access close to rendering.

- Add `"use client"` only for interactivity, browser APIs, local state, or third-party client widgets.
  Reason: Client Components pull their imports into the browser bundle.

- Keep `page.tsx` thin: load route data and compose feature components.
  Reason: Pages that also contain business logic are hard to test and reuse.

- Use `loading.tsx`, `error.tsx`, and `not-found.tsx` where route UX needs them.
  Reason: App Router has built-in primitives for asynchronous and failure states.

- Use route groups such as `(marketing)` and `(app)` to separate public and authenticated experiences.
  Reason: Layout boundaries should match product boundaries.

- Route handlers under `app/api/**/route.ts` are for external integrations and webhooks, not ordinary form mutations.
  Reason: Server actions are simpler for same-app mutations; route handlers are better for HTTP contracts.

## Component Patterns

- Components should receive plain props, not database rows.
  Reason: UI should not become coupled to schema column names or nullable database details.

- Put form components in `components/forms/` and pair them with a server action.
  Reason: Forms are cross-boundary code and deserve predictable structure.

- Keep reusable `components/ui/` primitives stateless and provider-agnostic.
  Reason: Base UI should remain easy to reuse across marketing, app, and admin surfaces.

- Prefer composition over giant configurable components.
  Reason: SaaS screens change often; small composed pieces are easier to evolve.

- Accessibility is part of done: labels, focus states, keyboard navigation, and semantic HTML are required.
  Reason: Retrofitting accessibility after features ship is slower and usually incomplete.

## Forms And Validation

- Validate all user input on the server with a schema library or explicit parser.
  Reason: Client validation is a UX helper, not a security boundary.

- Return field-level errors from server actions.
  Reason: Forms should recover without forcing users to inspect logs or generic toasts.

- Normalize input before persistence: trim names, lowercase emails, and parse dates at the boundary.
  Reason: Normalized storage avoids duplicate accounts and inconsistent filters.

- Do not trust hidden form fields for authorization decisions.
  Reason: Users can edit client-side HTML.

## Auth And Authorization

- Authentication answers "who is this"; authorization answers "can they do this here." Implement both.
  Reason: Logged-in users still need tenant, role, and ownership checks.

- Every query or service that reads tenant data must accept an `accountId`, `teamId`, or equivalent scope.
  Reason: Multi-tenant leaks are among the worst SaaS failures.

- Check authorization inside server actions and services, not only in UI.
  Reason: Hidden buttons do not protect direct requests.

- Use `middleware.ts` only for broad route gating.
  Reason: Middleware runs at the edge and should not become a database-heavy policy engine.

## Billing And Webhooks

- Treat billing providers as eventually consistent.
  Reason: Webhooks can be delayed, duplicated, or arrive out of order.

- Store webhook event IDs and ignore duplicates.
  Reason: Providers retry delivery and duplicate processing can grant or revoke access incorrectly.

- Verify webhook signatures before reading event data.
  Reason: Billing routes are public HTTP endpoints.

- Keep local subscription state as a projection of provider events.
  Reason: The provider is the source of truth for payment status.

## Error Handling And Logging

- Use typed domain errors for expected failures such as `NotAuthorized`, `NotFound`, and `ValidationFailed`.
  Reason: Expected failures should produce useful UI, not generic 500 pages.

- Log unexpected server errors with request context and without secrets.
  Reason: Production debugging needs context, but logs must not become a data breach.

- Do not swallow errors in server actions.
  Reason: Silent failures make Claude and humans think a mutation succeeded.

- Show users recovery paths, not stack traces.
  Reason: SaaS users need next steps, while stack traces belong in logs.

## Testing Expectations

- Unit test pure utilities, validators, and domain services.
  Reason: These tests are fast and catch most business-rule regressions.

- Integration test database queries and migrations against a temporary SQLite database.
  Reason: SQL correctness depends on the real engine.

- Add at least one route-level test for critical flows such as sign-up, checkout, invitation, and cancellation.
  Reason: SaaS value lives in workflows, not isolated functions.

- Test every migration on an empty database and on a database with representative existing rows.
  Reason: Migration bugs often appear only with old data.

- Prefer fixtures created through factories over copied database files.
  Reason: Factories document intent and are easier to update.

## Security Rules

- Never print secrets, tokens, session cookies, or webhook signatures.
  Reason: Logs are often available to more people than production secrets.

- Use parameterized SQL for every user-influenced value.
  Reason: String-built SQL is injection-prone even in small SQLite apps.

- Add rate limiting or abuse protection to auth, invite, upload, and webhook-adjacent endpoints.
  Reason: SaaS apps attract automated abuse as soon as they are public.

- Validate uploaded file type, size, and storage path on the server.
  Reason: User-controlled files are a common path to storage abuse and data leaks.

- Keep admin features behind explicit role checks.
  Reason: Admin UI is not a security boundary by itself.

## Performance Rules

- Start with simple SQL and add indexes based on query patterns.
  Reason: Premature abstraction hides slow queries; explicit SQL is easy to inspect.

- Avoid N+1 reads in Server Components.
  Reason: Server rendering can still produce slow waterfalls.

- Cache only values that are safe to reuse across users and tenants.
  Reason: Cross-tenant cache leaks are subtle and severe.

- Use pagination for lists that can grow beyond a dashboard screen.
  Reason: SaaS tables grow forever.

## Anti-Patterns To Avoid

- Do not add Prisma unless the project explicitly chooses it.
  Reason: The target stack is SQLite with direct `better-sqlite3` or Turso patterns; adding an ORM changes migration and query conventions.

- Do not create a global mutable "current user" or "current tenant" module.
  Reason: Request state must not leak between users in a server environment.

- Do not put business logic in React Client Components.
  Reason: Client code is untrusted, harder to test, and visible to users.

- Do not call provider SDKs directly from route UI.
  Reason: Provider behavior belongs behind service boundaries.

- Do not edit old migration files after they have shipped.
  Reason: Existing deployments cannot replay history that has changed.

- Do not use local component state as the source of truth after a server mutation.
  Reason: Revalidate or refetch server data so the UI matches persisted state.

- Do not store money as floating point numbers.
  Reason: Currency needs integer minor units such as cents to avoid rounding errors.

- Do not ignore timezone boundaries in billing, trials, or reporting.
  Reason: SaaS users notice when dates change at surprising times.

## How Claude Should Work In This Repo

- Before editing, inspect existing folders, commands, schema, and migrations.
  Reason: Local conventions override this template when they are already established.

- Make the smallest change that satisfies the product goal.
  Reason: Greenfield SaaS projects become hard to maintain when every feature invents a framework.

- When adding a feature, update the route, service, query, validation, tests, and docs together when relevant.
  Reason: SaaS behavior crosses UI, server, and database boundaries.

- If a task requires a new table or column, create a migration and explain the data lifecycle.
  Reason: Schema changes are durable product decisions.

- If a requirement is ambiguous, choose the safer default and record the assumption in the PR.
  Reason: Claude should keep momentum without hiding uncertainty.

- After implementation, run `npm run typecheck`, `npm run lint`, relevant tests, and `npm run build` for routing/server changes.
  Reason: TypeScript catches shape drift, while build catches App Router boundary mistakes.

## PR Checklist

- [ ] Uses App Router patterns and Server Components by default.
- [ ] Keeps client-only code behind explicit `"use client"` boundaries.
- [ ] Validates input on the server.
- [ ] Checks tenant/user authorization in server code.
- [ ] Uses parameterized SQL and transactions for multi-table writes.
- [ ] Adds immutable migrations for schema changes.
- [ ] Covers critical behavior with tests.
- [ ] Updates `.env.example` when configuration changes.
- [ ] Runs typecheck, lint, tests, and build where applicable.
