# CLAUDE.md — Next.js 15 + SQLite SaaS Project Guide

This file gives Claude Code the project-specific rules needed to work safely and productively in this repository. The app is a production-oriented SaaS built with **Next.js 15 App Router**, **TypeScript**, and **SQLite** using either **better-sqlite3** for local/single-node deployments or **Turso/libSQL** for hosted edge-friendly deployments.

## Stack & Versions

- Runtime: Node.js 20 LTS or newer.
- Framework: Next.js 15 with App Router only.
- Language: TypeScript with `strict` enabled.
- UI: React Server Components by default; Client Components only when browser state, effects, or event handlers are required.
- Database: SQLite.
  - Local/default: `better-sqlite3`.
  - Hosted/serverless option: Turso/libSQL.
- Styling: Tailwind CSS plus small, composable components.
- Validation: Zod at all trust boundaries.
- Testing: Vitest for units, Playwright for critical flows.

Reason: this stack keeps the product fast to build, cheap to operate, and easy to reason about. SQLite is a product advantage when we keep writes simple and schema changes explicit.

## Dev Commands

Prefer these commands unless `package.json` says otherwise:

```bash
npm install
npm run dev
npm run typecheck
npm run lint
npm run test
npm run test:e2e
npm run db:migrate
npm run db:studio
npm run build
```

If a command is missing, inspect `package.json` and use the closest existing script. Do not invent new package managers or switch from npm to pnpm/yarn unless the repository already uses them.

## Project Structure

Use this structure for greenfield work and preserve it in existing projects:

```text
app/
  (marketing)/          # Public pages: landing, pricing, docs
  (auth)/               # Sign in, sign up, password reset
  (dashboard)/          # Authenticated product area
  api/                  # Route handlers for webhooks and public API
components/
  ui/                   # Generic UI primitives
  forms/                # Form components tied to validation schemas
  layout/               # Navigation, shell, page chrome
lib/
  auth/                 # Sessions, current user, permissions
  db/                   # SQLite connection, migrations, query helpers
  env.ts                # Environment validation
  validators/           # Shared Zod schemas
  services/             # Business operations and use cases
  utils.ts              # Tiny generic helpers only
db/
  migrations/           # Ordered SQL migrations
  schema.sql            # Snapshot of current schema when used
  seeds/                # Development seed data
server/
  actions/              # Server Actions grouped by domain
  jobs/                 # Background jobs or cron handlers
tests/
  unit/
  e2e/
```

Reason: routes stay thin, database access stays centralized, and business logic can be tested without rendering pages.

## Naming Conventions

- Files and folders: kebab-case, for example `subscription-card.tsx`.
- React components: PascalCase exports, for example `SubscriptionCard`.
- Server actions: verb-first names, for example `createWorkspace`, `inviteMember`.
- Database tables: snake_case plural nouns, for example `workspaces`, `workspace_members`.
- Database columns: snake_case, for example `created_at`, `owner_id`.
- TypeScript types: PascalCase, for example `WorkspaceRole`.
- Zod schemas: suffix with `Schema`, for example `CreateWorkspaceSchema`.

Reason: names should reveal where code runs and what data shape it owns.

## App Router Rules

- Default to Server Components.
- Add `'use client'` only at the smallest possible boundary.
- Keep `page.tsx` and `layout.tsx` thin; move business logic into `lib/services` or `server/actions`.
- Use Route Handlers in `app/api` for webhooks, integrations, and public API endpoints.
- Use Server Actions for first-party form mutations from the app UI.
- Do not call the database directly from Client Components.

Reason: Server Components reduce shipped JavaScript and keep secrets on the server.

## Database Connection Rules

### better-sqlite3

- Create one shared connection helper in `lib/db/client.ts`.
- Enable WAL mode for local production-like behavior.
- Enable foreign keys on every connection.
- Keep transactions explicit for multi-step writes.

Example:

```ts
import Database from 'better-sqlite3';

const db = new Database(process.env.DATABASE_URL ?? 'data/app.db');
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

export { db };
```

### Turso/libSQL

- Put the client in `lib/db/client.ts`.
- Read URL and token from validated environment variables.
- Never expose database tokens to Client Components.

Reason: all database access should have one obvious entry point and one place to configure safety settings.

## SQL & Migration Conventions

- Migrations live in `db/migrations`.
- Migration files are immutable after merge.
- Name migrations with an ordered prefix and intent:

```text
0001_create_users.sql
0002_create_workspaces.sql
0003_add_billing_status_to_workspaces.sql
```

- Every table has:
  - `id TEXT PRIMARY KEY` unless there is a strong reason for integer IDs.
  - `created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP`.
  - `updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP` when records are mutable.
- Use ISO timestamp strings for portability.
- Add indexes for every foreign key and common lookup.
- Use foreign keys with explicit `ON DELETE` behavior.
- Prefer additive migrations. For destructive changes, create a backfill plan first.
- Wrap related schema/data changes in a transaction when SQLite supports it.

Reason: SQLite migrations are simple and reliable when they are explicit, ordered, and never rewritten after deployment.

## Query & Service Patterns

- Do not scatter raw SQL through UI files.
- Put query helpers in `lib/db/queries/<domain>.ts`.
- Put business workflows in `lib/services/<domain>.ts`.
- Validate all user input with Zod before it reaches a query.
- Return typed domain objects, not raw database rows, when data crosses service boundaries.
- Use prepared statements for all dynamic values.

Example shape:

```text
lib/db/queries/workspaces.ts   # SQL statements and row mapping
lib/services/workspaces.ts     # create workspace, invite member, change role
server/actions/workspaces.ts   # form/action boundary
```

Reason: database code should be easy to audit and impossible to accidentally call from the browser.

## Authentication & Authorization

- Centralize session lookup in `lib/auth/current-user.ts`.
- Centralize permission checks in `lib/auth/permissions.ts`.
- Check authorization in services or server actions before every write.
- Never rely on hidden form fields for ownership or role decisions.
- Store session/user IDs as strings.
- Use `workspace_members` or equivalent join tables for multi-tenant access.

Reason: SaaS bugs are usually authorization bugs. Every mutation must prove who is acting and what they can access.

## Environment Variables

- Validate environment variables once in `lib/env.ts` with Zod.
- Import `env` from `lib/env.ts`; do not read `process.env` throughout the app.
- Prefix browser-safe values with `NEXT_PUBLIC_` only when they are truly public.
- Never put secrets in `NEXT_PUBLIC_` variables.

Reason: failing fast at startup is safer than discovering missing secrets during a user request.

## Component Patterns

- Use Server Components for data loading and page composition.
- Use Client Components for interactive controls, optimistic UI, and local form state.
- Keep reusable UI primitives free of business logic.
- Co-locate one-off components near the route that uses them.
- Prefer composition over configuration-heavy components.
- Do not create global state unless URL state, server state, or component state is insufficient.

Reason: most SaaS screens are data views plus forms. Keeping component boundaries boring makes the app easier to maintain.

## Forms & Validation

- Define Zod schemas in `lib/validators` or next to the server action.
- Reuse the same schema for server validation and client form hints when practical.
- Server actions return structured errors, not thrown strings.
- Show field-level errors when possible.
- Re-check authorization inside the action even if the page already checked it.

Reason: forms are a trust boundary. Client validation improves UX; server validation provides security.

## API Route Handlers

Use `app/api` for:

- Webhooks.
- Public API endpoints.
- OAuth callbacks.
- Integration callbacks.

Rules:

- Validate method, headers, and body.
- Verify webhook signatures before parsing trusted data.
- Return typed JSON responses.
- Keep handlers thin; call services for business logic.
- Log enough context to debug without logging secrets or tokens.

Reason: route handlers are external boundaries and need stricter validation than internal pages.

## Testing Expectations

- Unit-test services, validators, and query helpers.
- Add regression tests for every bug fix.
- Use Playwright for critical flows:
  - sign up
  - sign in
  - create workspace
  - invite member
  - billing or checkout redirect when present
- Tests must not require production secrets.
- Use an isolated SQLite database for tests.

Reason: the database and permission model are the product core. Test them directly.

## Security Rules

- Never expose server secrets to Client Components.
- Never build SQL with string interpolation for user input.
- Always verify ownership on reads and writes for tenant-scoped data.
- Treat webhook payloads as untrusted until signatures are verified.
- Do not log passwords, tokens, cookies, or full payment payloads.
- Use secure, httpOnly cookies for sessions.
- Rate-limit public auth and API endpoints when the project has middleware support.

Reason: small SaaS apps fail from simple security mistakes, not exotic attacks.

## Performance Rules

- Avoid loading large dashboard datasets in one query.
- Paginate tables from the beginning.
- Add indexes when adding new list/filter screens.
- Use `revalidatePath` or targeted cache invalidation after mutations.
- Avoid unnecessary Client Components because they increase JavaScript shipped to the browser.

Reason: SQLite performs very well when queries are indexed and pages do not over-fetch.

## What We Do Not Do

- Do not add an ORM unless the project already uses one.
  - Reason: raw SQL plus small helpers is clearer for SQLite SaaS apps.
- Do not put database calls in React Client Components.
  - Reason: it leaks server concerns and can expose secrets.
- Do not create migrations by editing old migration files.
  - Reason: deployed databases need an append-only history.
- Do not use `any` to bypass domain modeling.
  - Reason: SaaS bugs often come from unclear data shapes.
- Do not add global state for server data.
  - Reason: the URL, server rendering, and query invalidation should own server state.
- Do not create generic abstractions before there are at least three real call sites.
  - Reason: premature abstractions make product code harder to change.
- Do not silently swallow database or payment errors.
  - Reason: operators need actionable failures.

## Working Agreement for Claude Code

When making changes:

1. Inspect `package.json`, existing folders, and current database tooling first.
2. Make the smallest change that satisfies the request.
3. Keep server-only logic out of Client Components.
4. Add or update tests for behavior changes.
5. Run typecheck, lint, tests, and build when available.
6. Summarize changed files, validation commands, and any follow-up migration steps.

When uncertain:

- Prefer explicit SQL over hidden magic.
- Prefer Server Components over Client Components.
- Prefer Zod validation at boundaries.
- Prefer asking for product intent before inventing billing, role, or permission behavior.

This project values boring, auditable, production-ready code over clever abstractions.
