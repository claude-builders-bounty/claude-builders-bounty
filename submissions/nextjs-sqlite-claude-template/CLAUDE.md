# CLAUDE.md — Next.js 15 + SQLite SaaS

You are working in an opinionated SaaS codebase using Next.js 15 App Router, TypeScript, SQLite, Server Actions, Route Handlers, Tailwind, and shadcn/ui.

Your job is to ship production code with small, reversible changes. Prefer explicit server-side data flow, typed boundaries, and simple SQLite-first architecture.

## Stack and versions

- Next.js 15 App Router
- React Server Components by default
- TypeScript strict mode
- SQLite locally with `better-sqlite3`
- Turso/libSQL may be used in hosted production, but local development remains SQLite-compatible
- Zod for request/form validation
- Tailwind CSS and shadcn/ui for UI primitives
- Vitest or Playwright only when tests are requested or already present

Reason: this stack optimizes for fast iteration, low hosting cost, easy local debugging, and no unnecessary distributed systems before product-market fit.

## Project structure / folder structure

Use this structure unless the project already has a conflicting convention:

```text
src/
  app/
    (marketing)/
      page.tsx
    (app)/
      dashboard/
        page.tsx
    api/
      webhooks/
        stripe/
          route.ts
  components/
    ui/                 # shadcn/ui generated primitives only
    app/                # product-specific reusable components
    marketing/          # landing page components
  db/
    client.ts           # database connection factory
    schema.ts           # table/type declarations if using a typed helper
    migrations/         # numbered SQL migrations
      0001_initial.sql
  features/
    billing/
      actions.ts
      queries.ts
      types.ts
    waitlist/
      actions.ts
      queries.ts
      components/
  lib/
    env.ts              # env parsing/validation
    auth.ts             # auth helpers
    errors.ts           # shared error helpers
```

Rules:

- Route files stay thin. They validate input, call feature functions, and return responses.
- Business logic lives in `src/features/<feature>/`.
- Database access lives in `queries.ts` or `actions.ts`, not inside React components unless it is a small server component read.
- Shared generic helpers go in `src/lib`; feature-specific helpers stay inside the feature folder.

Reason: this keeps product domains isolated and prevents the `lib/` dumping ground that makes SaaS apps hard to maintain.

## Naming conventions

- Components: `PascalCase.tsx`
- Server Actions: verb-first names like `createWaitlistSignup`, `updateWorkspaceName`
- Query functions: read-first names like `getWorkspaceBySlug`, `listInvoicesForWorkspace`
- Migration files: zero-padded and monotonic, e.g. `0001_initial.sql`, `0002_add_billing_events.sql`
- Table names: plural snake_case, e.g. `users`, `workspaces`, `billing_events`
- Columns: snake_case in SQL, camelCase in TypeScript objects only after mapping

Reason: SQL and TypeScript have different idioms. Keep the boundary explicit instead of pretending they are the same language.

## Database and migration rules

SQLite is the source of truth. Treat migrations as production artifacts.

Rules:

1. Never edit an already-applied migration. Add a new migration instead.
2. Every schema change gets a migration under `src/db/migrations/`.
3. Every migration must be idempotent when practical: use `IF NOT EXISTS` for tables/indexes.
4. Prefer additive migrations. Avoid destructive migrations unless explicitly requested.
5. Add indexes for foreign keys and common lookup columns.
6. Store timestamps as ISO-8601 text or integer epoch milliseconds. Pick the existing convention and stay consistent.
7. Use transactions for multi-step writes.
8. Do not hide schema changes inside application startup code.

Example migration:

```sql
-- src/db/migrations/0002_add_waitlist.sql
CREATE TABLE IF NOT EXISTS waitlist_signups (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  source TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_waitlist_signups_created_at
  ON waitlist_signups(created_at);
```

Reason: simple migrations make rollback, review, and deployment predictable. Startup-time schema mutation creates invisible production risk.

## Database client pattern

Use one connection factory and keep writes explicit.

```ts
// src/db/client.ts
import Database from 'better-sqlite3';

let db: Database.Database | undefined;

export function getDb() {
  if (!db) {
    db = new Database(process.env.DATABASE_PATH ?? 'data/app.db');
    db.pragma('journal_mode = WAL');
    db.pragma('foreign_keys = ON');
  }
  return db;
}
```

Rules:

- Never instantiate SQLite connections throughout the app.
- Enable foreign keys.
- Use WAL locally for better concurrent reads.
- Keep SQL parameterized; never interpolate user input into SQL strings.

Reason: SQLite is reliable when access patterns are disciplined. Connection sprawl and string-interpolated SQL are the usual failure modes.

## Server Components, Client Components, and Actions

Default to Server Components.

Use Client Components only for:

- local interactive state
- browser APIs
- optimistic UI
- controlled inputs that need client behavior

Use Server Actions for app-internal mutations from forms/buttons.

Use Route Handlers for:

- webhooks
- public APIs
- third-party callbacks
- endpoints called outside the Next.js app

Reason: Server Components reduce client bundle size and keep data access server-side. Route Handlers should be explicit network boundaries, not a replacement for internal function calls.

## Validation and errors

- Use Zod at all external boundaries: forms, route handlers, webhooks, env parsing.
- Return field-level errors for forms.
- Throw only for exceptional states. Expected validation failures should be returned as typed results.
- Never leak raw database errors to users.

Example result shape:

```ts
type ActionResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string; fieldErrors?: Record<string, string> };
```

Reason: predictable result types let Claude and humans wire UI states without guessing how failures propagate.

## Environment variables

All env access goes through `src/lib/env.ts`.

Rules:

- Parse with Zod.
- Fail fast for required server env vars.
- Never expose secrets through `NEXT_PUBLIC_` unless they are intentionally public.
- Use separate variables for development and production databases.

Reason: direct `process.env` access spreads implicit requirements across the app and causes runtime-only failures.

## Component patterns

- shadcn/ui generated primitives stay in `src/components/ui` and should not contain business logic.
- Product-specific components live under `src/components/app` or the relevant feature folder.
- Keep server data loading in page/layout server components or feature query functions.
- Pass plain serializable props into client components.

Reason: this prevents design-system primitives from becoming coupled to product logic.

## Authentication and tenancy

For SaaS features, assume multi-workspace support unless explicitly out of scope.

Rules:

- Every workspace-owned table includes `workspace_id`.
- Every query for workspace data filters by the authorized workspace.
- Do not trust client-provided workspace IDs without server-side membership checks.
- Keep auth checks close to data access.

Reason: retrofitting tenancy after launch is expensive and security-sensitive.

## Billing conventions

- Stripe/webhook logic belongs in `src/features/billing` and `src/app/api/webhooks/stripe/route.ts`.
- Store raw webhook event IDs to enforce idempotency.
- Never fulfill billing state changes without verifying webhook signatures.
- Keep plan/entitlement checks server-side.

Reason: billing bugs create support load and revenue leakage. Idempotency is mandatory because providers retry webhooks.

## Dev commands

Prefer these commands when available:

```bash
npm run dev          # start local dev server
npm run lint         # lint
npm run typecheck    # TypeScript validation
npm run test         # tests, if configured
npm run db:migrate   # apply migrations, if configured
```

If scripts are missing, add minimal scripts rather than inventing one-off commands.

Reason: repeatable commands are easier for Claude Code, CI, and humans to share.

## Anti-patterns to avoid

- Do not put business logic directly in route handlers.
- Do not create API routes for internal server-only calls.
- Do not use Client Components for pages that only read server data.
- Do not edit old migrations.
- Do not store money as floating-point numbers; use integer cents.
- Do not interpolate user input into SQL.
- Do not add a global state library unless a concrete client-state problem exists.
- Do not introduce Prisma/Drizzle unless explicitly requested; this template is SQLite-first and SQL-explicit.
- Do not add background queues before there is a real async workload.
- Do not make broad refactors while implementing a feature request.

Reason: most early SaaS failures come from accidental complexity, not missing architecture.

## How to approach tasks

When adding a feature:

1. Identify the feature folder.
2. Add/modify migrations first if persistence changes.
3. Add query/action functions.
4. Add server component data loading.
5. Add client component only where interaction requires it.
6. Add validation and error states.
7. Run lint/typecheck/tests.

When fixing a bug:

1. Reproduce or state the likely failing path.
2. Make the smallest targeted change.
3. Add a regression test if the project has tests.
4. Avoid opportunistic refactors.

When unsure:

- Follow existing local patterns over this file.
- If no pattern exists, use the conventions above.
- Prefer boring, explicit code over clever abstractions.
