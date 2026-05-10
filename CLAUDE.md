# CLAUDE.md - Next.js 15 + SQLite SaaS Template

Use this file as the working agreement for a greenfield SaaS app built with Next.js 15 App Router, React 19, TypeScript, and SQLite through `better-sqlite3` for local/self-hosted deployments or Turso/libSQL for hosted edge-friendly deployments.

## Stack And Defaults

- Runtime: Node.js 20 LTS or newer. Reason: it matches current Next.js 15 support and keeps native SQLite driver builds predictable.
- Package manager: `pnpm`. Reason: deterministic lockfiles and fast installs matter when Claude Code repeatedly runs tests.
- Framework: Next.js 15 App Router with TypeScript strict mode. Reason: route handlers, server components, and server actions are the default architecture.
- Styling: Tailwind CSS plus small local components. Reason: SaaS screens need consistent spacing and density without inventing a design system first.
- Database: SQLite with `better-sqlite3` for local apps, Turso/libSQL when the database must be remote. Reason: both keep the relational model simple while avoiding a separate database service during early product work.
- Validation: Zod at every boundary that accepts untrusted input. Reason: SQLite is permissive about types, so application-level validation prevents bad writes.
- Auth: use Auth.js or Clerk, but wrap provider calls behind `src/server/auth.ts`. Reason: product code should not depend on one auth vendor everywhere.
- Dates: store UTC ISO strings or integer epoch milliseconds, never local time strings. Reason: SaaS billing, trials, and audits break when time zones are implicit.

## Commands

Assume these scripts exist in `package.json`:

```bash
pnpm dev              # Start the local Next.js server
pnpm build            # Production build, must pass before merging
pnpm lint             # ESLint and Next.js lint rules
pnpm typecheck        # tsc --noEmit
pnpm test             # Unit tests
pnpm test:e2e         # Playwright smoke tests for critical flows
pnpm db:migrate       # Apply pending SQLite migrations
pnpm db:studio        # Open the DB browser or ORM studio
pnpm db:seed          # Seed local development data only
```

If a script is missing, add it instead of using a one-off command. Reason: future Claude Code sessions need stable entry points.

## Project Structure

Use this layout unless the user explicitly gives a different one:

```text
src/
  app/
    (marketing)/
      page.tsx
    (app)/
      dashboard/
        page.tsx
      settings/
        page.tsx
    api/
      health/route.ts
    layout.tsx
    globals.css
  components/
    ui/
    forms/
    charts/
  features/
    billing/
    projects/
    users/
      components/
      queries.ts
      actions.ts
      schema.ts
      types.ts
  server/
    auth.ts
    db/
      client.ts
      migrations/
      migrate.ts
      schema.sql
  lib/
    env.ts
    errors.ts
    format.ts
  tests/
    fixtures/
```

Rules:

- Put route segments under `src/app`; put domain logic under `src/features`. Reason: routes should compose features instead of becoming the business layer.
- Keep shared primitives in `src/components/ui`; keep domain-specific UI inside `src/features/<feature>/components`. Reason: reuse should be earned by repeated use, not guessed early.
- Put all database access behind `queries.ts`, `actions.ts`, or `src/server/db/*`. Reason: SQLite calls scattered through components make transactions and migrations hard to audit.
- Put environment parsing in `src/lib/env.ts` with Zod. Reason: missing secrets should fail at boot, not halfway through a checkout or signup flow.

## Naming Conventions

- Files and folders: kebab-case for routes and components folders, for example `billing-portal`.
- React components: PascalCase exports, for example `ProjectSwitcher`.
- Server actions: verb-first names ending in `Action`, for example `createProjectAction`.
- Queries: verb-first names ending in `Query`, for example `listProjectsQuery`.
- Mutations that write to the database: verb-first names ending in `Mutation`, for example `archiveProjectMutation`.
- Zod schemas: noun plus `Schema`, for example `createProjectSchema`.
- Database tables: plural snake_case, for example `billing_events`.
- Database columns: snake_case, with `created_at`, `updated_at`, and `deleted_at` when relevant.

Do not mix casing styles inside the same boundary. Reason: SQLite and TypeScript already use different naming cultures; consistent translation reduces bugs.

## App Router Patterns

- Use server components by default. Add `"use client"` only for state, browser APIs, focus management, charts, or event handlers. Reason: server components keep secrets and database reads off the client bundle.
- Fetch data in the closest server component or in a cached query helper. Reason: page-level data ownership makes loading, empty, and error states easier to reason about.
- Keep route handlers thin. Validate input, call a feature function, return a typed response. Reason: business logic hidden in `route.ts` is hard to test.
- Use server actions for form submissions that mutate first-party data. Reason: they keep form code ergonomic while staying on the server.
- After a mutation, call `revalidatePath` or `revalidateTag` deliberately. Reason: SQLite writes are immediate, but App Router caches can show stale UI.
- Use `notFound()` for missing user-owned resources only after checking ownership. Reason: leaking whether a record exists is a security issue.

## Component Patterns

- Prefer small server components that pass plain props into client components. Reason: client components should not know how data is loaded.
- Build forms with explicit pending, success, and error states. Reason: SaaS users repeat workflows and need clear feedback.
- Put destructive actions behind a confirmation component. Reason: SQLite writes are often local and fast, so accidental clicks can be permanent.
- Keep tables dense and keyboard-friendly. Reason: SaaS dashboards are used for scanning and repeated operations, not only first impressions.
- Use accessible labels for every input and icon-only button. Reason: admin tooling still needs to work with screen readers and automation.

## SQLite And Migration Rules

- Migrations are append-only files in `src/server/db/migrations`. Name them `YYYYMMDDHHMM_description.sql`.
- Never edit a migration that has been committed. Add a new migration instead. Reason: SQLite has no central migration ledger unless we create one, and history must replay cleanly.
- Every migration must run inside a transaction unless it uses a SQLite operation that cannot be transactional. Reason: partial schema changes corrupt local dev databases.
- Use `PRAGMA foreign_keys = ON` every time a SQLite connection is opened. Reason: SQLite does not reliably enforce foreign keys unless this is enabled per connection.
- Prefer explicit foreign keys and indexes. Reason: SaaS tables grow in surprising places, especially audit and membership tables.
- Use `TEXT` for ids, generated by application code with `crypto.randomUUID()` or a stable id helper. Reason: ids remain portable between local SQLite and Turso.
- Use `INTEGER NOT NULL DEFAULT 0` for booleans. Reason: SQLite has no native boolean type.
- Store JSON only for flexible metadata, never for core relational state. Reason: querying and migrating JSON blobs becomes expensive.
- Do not use `SELECT *` in application queries. Reason: schema changes should not silently change API payloads.
- Write idempotent seed scripts. Reason: Claude Code will rerun setup commands while iterating.

## Data Access Rules

- Use prepared statements for every raw SQL query. Reason: SQL injection is still possible with SQLite.
- Validate all user input before calling a mutation. Reason: database constraints should be the last line of defense, not the first.
- Keep read queries and write mutations separate. Reason: review is easier when side effects are obvious.
- For multi-step writes, use a transaction helper. Reason: subscription creation, team setup, and invite flows must succeed or fail as a unit.
- Return plain objects from query helpers. Reason: React server components and server actions serialize plain data reliably.

## Auth, Tenancy, And Security

- Every user-owned table should include `user_id` or `organization_id`, unless it is truly global reference data. Reason: missing tenancy columns are costly to retrofit.
- Check authorization in the server function that reads or writes the data, not only in the page. Reason: route handlers, actions, and background jobs may reuse the same function.
- Never expose raw database errors to users. Map them through `src/lib/errors.ts`. Reason: constraint names and SQL snippets leak implementation details.
- Keep secrets server-only and read them through `env.ts`. Reason: accidental `NEXT_PUBLIC_` exposure is easy to miss in review.
- Log security-relevant events such as login, invite, billing role change, and destructive delete. Reason: SaaS support and incident review need an audit trail.

## Testing Rules

- Unit test pure feature functions and validation schemas. Reason: these failures are cheap to catch and usually explain the bug directly.
- Add integration tests for database migrations and high-risk queries. Reason: SQLite behavior depends on real schema, indexes, and pragmas.
- Add Playwright smoke tests for signup/login, create main resource, update settings, and destructive confirmation. Reason: these flows prove the SaaS shell works end to end.
- Test both empty and populated states for dashboard pages. Reason: first-run experiences and real customer accounts fail in different ways.
- Before merging, run `pnpm lint`, `pnpm typecheck`, `pnpm test`, and `pnpm build`. Reason: Next.js can pass typecheck while failing production compilation.

If a test is expensive or unavailable, explain why in the PR and include the closest useful verification. Reason: maintainers need to know what confidence they actually have.

## Patterns To Follow

- Make the first version boring, typed, and easy to delete. Reason: SaaS requirements change faster than abstractions.
- Prefer one clear SQL query over a clever helper that hides joins. Reason: the schema is part of the product contract.
- Keep billing, auth, and tenancy boundaries explicit. Reason: these are the areas where small mistakes become support tickets.
- Use optimistic UI only when rollback is obvious. Reason: SQLite writes are quick, but failed remote Turso writes still happen.
- Document non-obvious product decisions near the code. Reason: future Claude Code sessions need context, not folklore.

## Anti-Patterns To Avoid

- Do not put database calls in client components. Reason: it leaks secrets and breaks the server/client boundary.
- Do not create a generic `utils.ts` dumping ground. Reason: it hides ownership and makes reuse accidental.
- Do not use global mutable singletons except the database connection wrapper. Reason: serverless and hot reload behavior can be surprising.
- Do not add an ORM only to avoid writing SQL. Reason: this stack chooses SQLite for explicitness and portability.
- Do not skip migrations by editing `schema.sql` only. Reason: deployed databases need a replayable path.
- Do not build marketing-style dashboards with oversized cards and vague metrics. Reason: SaaS operators need dense, comparable information.
- Do not add background jobs without documenting retries and idempotency. Reason: weekly reports, billing syncs, and webhooks often run more than once.
- Do not silently swallow errors in server actions. Reason: users need a useful message and maintainers need logs.

## When Requirements Are Ambiguous

Make the smallest production-shaped choice and state it in the PR. Prefer server components, explicit SQL, Zod validation, and simple local UI. Ask the user only when the decision affects billing, auth provider, data ownership, destructive behavior, or external integrations.
