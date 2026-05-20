# CLAUDE.md

## Stack And Versions

This is a production SaaS app built with:

- Next.js 15 App Router
- React 19
- TypeScript with `strict` enabled
- SQLite through `better-sqlite3` for local/single-region deployments or Turso/libSQL for hosted edge-style deployments
- Zod for runtime validation at every boundary
- Server Components by default, Client Components only when browser state or browser APIs are required

Rule: keep framework versions explicit in `package.json` and update this file when the stack changes.
Why: Claude should optimize for the actual runtime instead of mixing Pages Router, older React, or ORM assumptions into the codebase.

## Dev Commands

Use these commands unless `package.json` says otherwise:

```bash
npm run dev
npm run build
npm run lint
npm run typecheck
npm run test
npm run db:migrate
npm run db:studio
```

Rule: before calling work done, run `npm run lint`, `npm run typecheck`, and the narrowest relevant tests.
Why: this project relies on TypeScript and small regression tests to catch most SaaS workflow bugs before deploy.

Rule: do not invent package scripts.
Why: if a command is missing, add it to `package.json` in the same PR with a clear implementation.

## Folder Structure

Use this structure for new code:

```text
app/
  (marketing)/
  (app)/
  api/
  layout.tsx
  page.tsx
components/
  ui/
  forms/
  domain/
db/
  migrations/
  schema.sql
  migrate.ts
src/
  actions/
  auth/
  config/
  db/
    client.ts
    queries/
  domain/
  lib/
  server/
  validation/
tests/
  fixtures/
  unit/
  integration/
```

Rule: route files stay thin. Put business logic in `src/domain`, database access in `src/db/queries`, and server actions in `src/actions`.
Why: route handlers and pages change often; keeping logic outside them makes behavior easier to test and reuse.

Rule: shared UI primitives live in `components/ui`; feature-aware UI lives in `components/domain`; form-specific wrappers live in `components/forms`.
Why: separating generic UI from business UI prevents a button or input abstraction from quietly absorbing product logic.

Rule: never import from `app/` into `src/`.
Why: `app/` is the delivery layer; importing it into core code creates circular dependencies and makes tests depend on Next internals.

## Naming Conventions

Rule: use kebab-case for route segments and file names that map to URLs, such as `billing-history/page.tsx`.
Why: URL-facing names should match the product surface and stay readable in links.

Rule: use PascalCase for React components, camelCase for functions and variables, and SCREAMING_SNAKE_CASE only for process-level constants.
Why: Claude can infer intent quickly when naming follows language conventions.

Rule: name server actions as verb-first operations, such as `createWorkspace`, `inviteMember`, or `cancelSubscription`.
Why: server actions mutate state; verb-first names make side effects obvious.

Rule: name database query files by entity, such as `src/db/queries/workspaces.ts`.
Why: SQLite has no service boundary, so query organization is the boundary.

## Environment And Configuration

Rule: read environment variables only in `src/config/env.ts`.
Why: one validation point keeps runtime errors predictable and prevents scattered `process.env` access.

Rule: validate environment variables with Zod and export typed config values.
Why: SaaS failures from missing secrets are expensive and should happen at startup, not in a user request.

Rule: never use public `NEXT_PUBLIC_` variables for secrets or server-only feature flags.
Why: public environment variables are bundled into browser code.

## SQLite And Migration Rules

Rule: every schema change gets a numbered SQL migration in `db/migrations`, for example `0007_add_workspace_members.sql`.
Why: SQLite schema state must be reproducible across local, preview, and production environments.

Rule: migrations are append-only after merge.
Why: editing old migrations breaks existing databases and makes production drift invisible.

Rule: include `created_at` and `updated_at` on user-owned business tables.
Why: SaaS support, billing investigations, and audit trails need reliable timestamps.

Rule: prefer explicit foreign keys and indexes in the migration that creates the relationship.
Why: SQLite will not rescue vague data modeling later; query performance and integrity must be designed early.

Rule: wrap multi-step writes in a transaction.
Why: SQLite is durable, but partial SaaS workflows such as signup, workspace creation, and billing state sync must not leave half-written state.

Rule: for `better-sqlite3`, keep the connection server-only and singleton-scoped in `src/db/client.ts`.
Why: opening many SQLite handles in a Next.js app can create lock contention and inconsistent pragmas.

Rule: for Turso/libSQL, isolate the client behind the same query modules used by local SQLite.
Why: switching between local and hosted SQLite should not rewrite product logic.

Rule: use parameterized queries only. Never interpolate user input into SQL strings.
Why: SQLite is still SQL; string-built queries are injection bugs.

Rule: turn on `PRAGMA foreign_keys = ON` for local SQLite connections.
Why: SQLite supports foreign keys but does not enforce them unless enabled.

## Data Access Patterns

Rule: database query functions return plain typed objects, not React elements, responses, or framework objects.
Why: data access should be testable without rendering or Next request context.

Rule: validate input at the server boundary before calling query functions.
Why: query modules should assume typed, trusted input so SQL code stays small and predictable.

Rule: map nullable database fields into explicit TypeScript unions when they carry meaning.
Why: SaaS state such as `trial_ends_at` or `deleted_at` should not be treated like accidental absence.

Rule: avoid generic repository classes.
Why: SQLite query needs are concrete; small functions are clearer than an abstraction that hides SQL.

## App Router Patterns

Rule: default to Server Components for pages and layout.
Why: Server Components reduce browser JavaScript and keep database access on the server.

Rule: add `"use client"` only to components that use state, effects, event handlers, browser APIs, or client-only libraries.
Why: unnecessary Client Components bloat the bundle and can accidentally expose server-only logic.

Rule: put route-specific loading and error states next to the route.
Why: App Router conventions make user-facing failure states easier to audit.

Rule: use Route Handlers in `app/api` for webhooks, third-party callbacks, and machine-readable endpoints.
Why: server actions are good for app mutations; external systems need stable HTTP contracts.

Rule: call `revalidatePath` or `revalidateTag` immediately after successful mutations that affect cached UI.
Why: stale SaaS dashboards create support issues and duplicate actions.

## Server Actions

Rule: server actions must validate input, authorize the user, perform the mutation, and return a small typed result.
Why: actions are a trust boundary; each one needs a predictable security and error shape.

Rule: never rely on hidden form fields for authorization.
Why: hidden fields are user input and can be changed.

Rule: return field-level validation errors for forms.
Why: SaaS forms should be repairable by the user without guessing what failed.

Rule: keep server action files server-only and do not import them into generic client components.
Why: mixing server and client imports creates confusing bundling errors.

## Component Patterns

Rule: use composition over prop explosion.
Why: SaaS screens grow fast; components with dozens of optional props become impossible for Claude and humans to use correctly.

Rule: forms should have one schema, one server action, and one visible error model.
Why: duplicating validation between UI and server creates contradictory behavior.

Rule: keep table/list components controlled by typed data from query functions.
Why: display components should not fetch, mutate, or infer business permissions.

Rule: colocate small component helpers in the same file until there is real reuse.
Why: premature shared components slow down product changes.

## Auth And Authorization

Rule: authenticate once at the request/action boundary and pass the user or session explicitly.
Why: hidden global auth calls make tests brittle and authorization easy to skip.

Rule: check workspace/account membership inside every mutation and sensitive read.
Why: SaaS data leaks usually come from trusting route params.

Rule: distinguish authentication errors from authorization errors.
Why: redirects, 401s, and 403s need different product behavior.

## Testing Rules

Rule: test query functions with a temporary SQLite database.
Why: SQL bugs are behavior bugs; mock-based tests do not prove migrations and queries agree.

Rule: test server actions at the validation and authorization boundary.
Why: most SaaS defects happen where user input becomes a database write.

Rule: add a regression test for every bug fix that changed behavior.
Why: the bug already proved the system lacked coverage there.

Rule: do not snapshot whole pages by default.
Why: broad snapshots create noisy churn without proving business behavior.

## Error Handling And Logging

Rule: throw typed domain errors for expected business failures.
Why: callers need to render precise messages without parsing exception text.

Rule: log unexpected server errors with enough context to debug, but never log secrets, tokens, payment data, or full request bodies.
Why: logs are operational tools and a liability if they contain sensitive data.

Rule: user-facing error messages should explain the next action, not the stack trace.
Why: SaaS users need recovery, while developers need logs.

## Security Rules

Rule: all mutations must verify the current user and target tenant/workspace.
Why: multi-tenant SaaS security depends on checking both identity and ownership.

Rule: webhook handlers must verify provider signatures before parsing business payloads.
Why: webhooks are public endpoints.

Rule: use constant-time comparison for secrets when applicable.
Why: authentication checks should not leak timing information.

Rule: never commit `.env`, SQLite database files, session secrets, API keys, or webhook secrets.
Why: credential leaks are incident work, not cleanup work.

## What We Do Not Do

Rule: do not add Prisma, Drizzle, or another ORM unless the user explicitly asks.
Why: this template is for direct SQLite or Turso/libSQL, and an ORM changes migrations, data access, and deployment assumptions.

Rule: do not add Redux or a global client store by default.
Why: App Router plus Server Components already provide a server-first data model; global client state should be rare.

Rule: do not put business logic in React components.
Why: business rules need tests and reuse outside rendering.

Rule: do not create generic `utils.ts` dumping grounds.
Why: broad utility files hide ownership; create named modules like `src/lib/dates.ts` or `src/lib/money.ts`.

Rule: do not skip migrations by editing `schema.sql` only.
Why: `schema.sql` documents the current shape, but migrations move real databases forward.

Rule: do not add dependencies for simple formatting, date math, validation, or SQL helpers without checking existing code first.
Why: every dependency affects bundle size, audit surface, and maintenance.

## How Claude Should Work Here

When making changes:

1. Read `package.json`, existing routes, `db/migrations`, and the relevant query modules first.
2. State the smallest implementation plan if the task touches database schema, auth, billing, or tenant data.
3. Make the narrowest code change that fits the existing patterns.
4. Add or update focused tests for changed behavior.
5. Run lint, typecheck, and relevant tests.
6. Report changed files, verification commands, and any follow-up risk.

Rule: ask a clarifying question only when the missing answer changes data model, security behavior, billing behavior, or public API shape.
Why: most implementation details are already decided by this project file; questions should protect product correctness, not delay routine work.

