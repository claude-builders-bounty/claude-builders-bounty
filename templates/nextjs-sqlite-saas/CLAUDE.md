# CLAUDE.md - Next.js 15 App Router + SQLite SaaS

This file is the operating manual for Claude Code in this repository. Follow it before proposing code, creating files, or changing database state.

## Stack and Versions

- Runtime: Node.js 22 LTS or newer. Reason: Next.js 15 and modern SQLite libraries need current Web APIs, stable ESM behavior, and maintained security patches.
- Package manager: pnpm. Reason: deterministic installs and fast workspace support for future packages.
- Framework: Next.js 15 with the App Router in `src/app`. Reason: route groups, layouts, server components, and server actions are the default architecture for new SaaS apps.
- Language: TypeScript in strict mode. Reason: SaaS code moves money, identity, and customer data; implicit `any` hides boundary mistakes.
- UI: React 19, React Server Components by default, Client Components only where interactivity needs browser APIs.
- Styling: Tailwind CSS plus small component wrappers. Reason: fast iteration without inventing a theme layer too early.
- Database: SQLite through `better-sqlite3` for local/single-node deployments, or Turso/libSQL when remote replication is required. Reason: both keep SQL explicit and avoid hidden schema changes.
- Validation: Zod at every external input boundary. Reason: forms, route handlers, webhooks, and env vars are untrusted.
- Testing: Vitest for unit tests, Playwright for browser flows that cross routing, auth, or billing boundaries.

If an existing project differs from this stack, inspect the current files first and adapt the smallest possible change. Do not rewrite the stack to match this file without a direct request.

## Dev Commands

Run the command that matches the task, then report the result.

```bash
pnpm install
pnpm dev
pnpm build
pnpm lint
pnpm test
pnpm test:e2e
pnpm db:migrate
pnpm db:seed
pnpm db:studio
```

If one of these scripts is missing, add it to `package.json` only when the task needs it. Do not invent commands in the final answer that the repository cannot run.

## Folder Structure

Use this structure for greenfield work and preserve it unless the repository already has a clear pattern.

```text
src/
  app/
    (marketing)/
    (app)/
    api/
    layout.tsx
    page.tsx
  components/
    ui/
    layout/
  features/
    billing/
      actions.ts
      components/
      queries.ts
      schema.ts
      service.ts
    teams/
      actions.ts
      components/
      queries.ts
      schema.ts
      service.ts
  lib/
    auth/
    db/
      client.ts
      migrate.ts
      sqlite.ts
    env.ts
    errors.ts
  server/
    actions/
    queries/
  db/
    migrations/
    seeds/
  tests/
    unit/
    e2e/
```

Rules:

- Put route files, layouts, loading states, and metadata in `src/app`. Reason: the App Router owns URL structure and rendering boundaries.
- Put reusable visual primitives in `src/components/ui`. Reason: UI primitives should not know about billing, teams, or auth.
- Put domain code in `src/features/<domain>`. Reason: SaaS logic changes by feature, not by technical layer.
- Keep database connection code in `src/lib/db` and import it only from server code. Reason: SQLite credentials and file handles must never enter client bundles.
- Keep cross-feature server-only helpers in `src/server`. Reason: server actions and queries need a place that cannot be confused with browser code.
- Keep migrations in `src/db/migrations` and seeds in `src/db/seeds`. Reason: schema history must be reviewable and separated from runtime code.

## Naming Conventions

- Routes and route groups: kebab-case, for example `src/app/(app)/team-settings/page.tsx`. Reason: URLs should be stable and readable.
- React components: PascalCase files and exports, for example `TeamSwitcher.tsx`. Reason: component names appear in stack traces and reviews.
- Hooks: `useNounVerb`, for example `useInvoiceFilters`. Reason: hooks must be easy to distinguish from server utilities.
- Server actions: verb-first names ending in `Action`, for example `createTeamAction`. Reason: callers should know that the function mutates state and crosses a server boundary.
- Server queries: noun-first names ending in `Query`, for example `teamMembersQuery`. Reason: read paths should be distinguishable from writes.
- Service functions: verb phrases without framework terms, for example `createTeam` or `archiveSubscription`. Reason: business logic should remain testable outside Next.js.
- Database tables: plural snake_case, for example `team_members`. Reason: SQL should read consistently and avoid ORM-style singular/plural drift.
- Database columns: snake_case, for example `billing_status`. Reason: SQL and JSON boundaries stay explicit.
- TypeScript types and interfaces: PascalCase, for example `BillingStatus`. Reason: types should stand apart from runtime values.
- Environment variables: SCREAMING_SNAKE_CASE and read through `src/lib/env.ts`. Reason: direct `process.env` use spreads validation gaps.

## SQL and Migration Conventions

Use SQL as the source of truth. Keep migrations small, reviewed, and reversible in practice.

- Name migrations with UTC timestamp prefixes: `202606231430_add_team_billing_status.sql`. Reason: ordering must be stable across machines and branches.
- Never edit a migration that has been applied outside a disposable local database. Reason: changing history breaks teammates, previews, and production.
- Each migration must state its intent in a leading SQL comment. Reason: reviewers need to understand the business reason, not only the DDL.
- Wrap multi-statement migrations in a transaction where SQLite supports it. Reason: partial schema changes are hard to recover from.
- Enable and preserve foreign keys with `PRAGMA foreign_keys = ON`. Reason: SQLite does not protect relationships unless foreign keys are active.
- Use `CHECK` constraints for enums such as billing status. Reason: SQLite has no native enum type, and app-only checks drift.
- Add indexes with the query shape in mind. Reason: indexes are product decisions, not decoration.
- Prefer additive migrations. Reason: renames and destructive changes need a data backfill and rollback note.
- Include rollback notes in the migration comment even when the project uses forward-only migrations. Reason: an operator needs to know the recovery path.
- Keep seed scripts idempotent. Reason: local setup and preview deployments rerun seeds.
- Use parameterized SQL only. Reason: string interpolation in SQL is a security bug.
- Return plain objects from DB helpers and map them before crossing to client components. Reason: database rows may include internal fields or non-serializable values.

Example migration style:

```sql
-- Adds billing status to teams so the app can gate paid workspace features.
-- Rollback: create a replacement table without billing_status, copy data back, and swap tables.
PRAGMA foreign_keys = ON;

BEGIN;

ALTER TABLE teams
  ADD COLUMN billing_status TEXT NOT NULL DEFAULT 'trial'
  CHECK (billing_status IN ('trial', 'active', 'past_due', 'canceled'));

CREATE INDEX IF NOT EXISTS idx_teams_billing_status
  ON teams (billing_status);

COMMIT;
```

## Component Patterns

- Start pages and layouts as Server Components. Reason: reads are faster, safer, and keep secrets on the server.
- Add `"use client"` only to leaf components that need state, effects, browser APIs, or event handlers. Reason: large client trees increase bundle size and leak boundaries.
- Fetch data in server queries, not inside visual components. Reason: UI should render data; query modules should own filtering, auth checks, and SQL.
- Validate form input with Zod before calling services. Reason: server actions are public entry points, even when called by internal forms.
- Keep server actions thin: validate, authorize, call a service, revalidate or redirect. Reason: actions are transport glue, not the business layer.
- Use `revalidatePath` or `revalidateTag` immediately after successful mutations. Reason: stale SaaS dashboards cause duplicate work and support tickets.
- Keep optimistic UI local and reversible. Reason: billing, invitations, and permissions can fail after the browser updates.
- Model empty, loading, and error states in the same component pass. Reason: SaaS users spend real time in partial states.
- Pass only serializable, least-privilege props into Client Components. Reason: client bundles are visible and replayable.
- Use accessible controls from the start: labels, focus states, keyboard behavior, and semantic buttons. Reason: retrofitting accessibility is slower and riskier.

## Server, Auth, and Data Boundaries

- Every query and mutation that depends on a user must call the auth helper at the server boundary. Reason: client-side checks are presentation, not protection.
- Authorization belongs in services or query helpers, not only in route layouts. Reason: the same operation may be reached from a server action, API route, or background job.
- Use `src/lib/env.ts` for all env reads and validate at startup. Reason: failed configuration should be loud before a request mutates data.
- Keep webhook handlers in `src/app/api/<provider>/route.ts`, but move verification and business logic into feature services. Reason: route handlers should be small and testable.
- Log operational facts, not secrets or full payloads. Reason: production logs are shared more widely than application state.
- Convert database errors into typed application errors in `src/lib/errors.ts`. Reason: UI should not depend on driver-specific messages.

## Testing Expectations

- Add unit tests for services that compute billing, permissions, or state transitions. Reason: those rules are expensive to verify through the browser.
- Add query tests when SQL includes joins, filters, pagination, or permission scopes. Reason: SQL bugs often pass TypeScript.
- Add Playwright tests for signup, login, team switching, billing gates, and destructive settings changes. Reason: these flows depend on routing and browser state.
- For migrations, test from an empty database and from the previous schema when practical. Reason: greenfield setup and upgrades fail differently.

## What We Do Not Do and Why

- Do not import DB clients into Client Components. Reason: it leaks server-only code and can expose credentials or file paths.
- Do not put business logic directly in `page.tsx`, `route.ts`, or JSX event handlers. Reason: logic there is hard to test and reuse.
- Do not edit applied migrations. Reason: schema history must be append-only after use.
- Do not interpolate raw strings into SQL. Reason: SQL injection remains possible with SQLite.
- Do not pass raw DB rows to the browser. Reason: rows often include internal IDs, audit fields, or values that need mapping.
- Do not use `any` to silence type errors. Reason: it hides the exact contract Claude Code should be preserving.
- Do not scatter `process.env` reads across the app. Reason: validation and defaults become inconsistent.
- Do not prefix secrets with `NEXT_PUBLIC_`. Reason: that publishes them to the browser bundle.
- Do not add an ORM or migration framework unless the task explicitly adopts it. Reason: this template chooses explicit SQL for reviewability.
- Do not create generic utility folders before there are two real call sites. Reason: premature abstraction makes small SaaS projects harder to navigate.
- Do not add background jobs, queues, or caches before a measured need. Reason: SQLite SaaS apps should stay simple until product load proves otherwise.

## Working Rules for Claude Code

- Inspect existing schema, migrations, route groups, and feature folders before changing code.
- Prefer the smallest change that satisfies the product requirement and keeps boundaries intact.
- When adding a feature, update types, validation, database schema, tests, and UI states together.
- When a business rule is missing, ask one focused question instead of guessing.
- When unsure between `better-sqlite3` and Turso/libSQL, keep the data access interface small and server-only so the driver can change later.
- Before finalizing, run the relevant commands and list what passed. If a command cannot run, explain the missing prerequisite and what was checked instead.
