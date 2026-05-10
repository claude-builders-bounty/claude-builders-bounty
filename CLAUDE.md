# CLAUDE.md — Next.js 15 + SQLite SaaS

Use this file as the default Claude Code context for a greenfield SaaS built with Next.js 15 App Router and SQLite (`better-sqlite3` locally, Turso/libSQL when deployed). The goal is a boring, typed, server-first product that is easy to migrate and hard to accidentally over-engineer.

## Stack and versions

- **Framework:** Next.js 15 App Router with React Server Components by default.
- **Language:** TypeScript in strict mode.
- **Runtime:** Node.js runtime for routes that touch SQLite. Do not use Edge runtime for database writes.
- **Database:** SQLite through `better-sqlite3` for local/single-node apps, or Turso/libSQL for hosted SQLite.
- **Validation:** Zod at every trust boundary: route handlers, server actions, webhooks, and env parsing.
- **Styling:** Tailwind CSS plus small local components. Avoid adding a design system until the product has repeated patterns.
- **Auth:** Session cookie or an auth provider, but keep auth checks server-side and centralized.
- **Tests:** Unit tests for pure logic and migration tests for database schema changes.

Reason: these choices keep the app deployable as a small SaaS without hiding state in client code or introducing distributed-system complexity too early.

## Folder structure

```text
app/
  (marketing)/             # public landing/pricing/docs pages
  (app)/                   # authenticated product UI
  api/                     # route handlers for webhooks and external clients
  layout.tsx
  page.tsx
components/
  ui/                      # reusable primitive UI components
  feature-name/            # feature-specific components that are reused
lib/
  auth/                    # session helpers, user lookup, permission checks
  db/                      # db connection, migrations runner, query helpers
  env.ts                   # typed environment variable parsing
  errors.ts                # app error helpers
  validators/              # shared Zod schemas
server/
  actions/                 # server actions grouped by feature
  services/                # business logic with no React imports
db/
  migrations/              # numbered SQL migrations
  schema.sql               # current schema snapshot for humans
  seeds.ts                 # idempotent local seed data
tests/
  unit/
  integration/
```

Rules:
- Put route handlers in `app/api/**/route.ts` only when an HTTP endpoint is needed.
- Put form mutations in server actions when they are only used by the app UI.
- Put database access behind `server/services/*` or `lib/db/*`; React components should not contain SQL.
- Keep feature-only components next to the feature. Move to `components/ui` only after reuse is real.

## Naming conventions

- Components: `PascalCase.tsx` (`BillingSummary.tsx`).
- Server actions: verb-first names (`createWorkspace`, `inviteMember`, `cancelSubscription`).
- Route handlers: REST-ish nouns (`/api/workspaces`, `/api/billing/webhook`).
- Database tables: plural snake_case (`users`, `workspaces`, `workspace_members`).
- Columns: snake_case (`created_at`, `workspace_id`, `email_verified_at`).
- TypeScript variables: camelCase after mapping DB rows to app objects.

Reason: SQL remains idiomatic, TypeScript remains idiomatic, and mapping boundaries stay obvious.

## Database and migration rules

1. **Every schema change gets a numbered migration.** Use `db/migrations/0001_initial.sql`, `0002_add_workspace_members.sql`, etc.
2. **Migrations must be forward-only.** Do not rewrite old migrations after they are merged.
3. **SQLite constraints are part of the product logic.** Use `NOT NULL`, `UNIQUE`, `CHECK`, and foreign keys intentionally.
4. **Enable foreign keys on every connection:** `PRAGMA foreign_keys = ON;`.
5. **Prefer additive changes.** Add nullable columns, backfill, then enforce constraints in a later migration if needed.
6. **Never use `Date.now()` as the only ordering source for critical records.** Store `created_at` and use integer primary keys or UUIDs.
7. **Wrap multi-step writes in transactions.** If two tables must change together, use a transaction.
8. **Keep `schema.sql` updated after migrations.** It is the readable snapshot, not the source of truth.

Reason: SQLite is reliable when constraints and migrations are explicit. Most SaaS data bugs come from casual schema changes, not from SQLite itself.

## Data access pattern

Use small service functions that accept validated input and return typed results.

```ts
// server/services/workspaces.ts
export async function createWorkspace(input: CreateWorkspaceInput) {
  const data = createWorkspaceSchema.parse(input);

  return db.transaction(() => {
    const workspace = insertWorkspace(data);
    insertWorkspaceMember({
      workspaceId: workspace.id,
      userId: data.ownerId,
      role: "owner",
    });
    return workspace;
  })();
}
```

Do not import `db` directly in client components. If a component needs data, load it in a server component or call a server action.

## Server Components and Client Components

Default to Server Components.

Use `"use client"` only for:
- local UI state,
- browser APIs,
- focus/keyboard interactions,
- optimistic UI,
- charts or third-party client libraries.

Do not add `"use client"` to a page just because one child is interactive. Put the interactive part in a small child component.

Reason: server-first pages keep secrets server-side, reduce bundle size, and make database reads straightforward.

## Route handlers and server actions

Route handlers are for:
- webhooks,
- public API endpoints,
- integrations,
- callbacks from auth/payment providers.

Server actions are for:
- form submissions from authenticated app pages,
- internal mutations that do not need a public HTTP API.

Both must:
- parse input with Zod,
- check authentication and authorization before writes,
- return safe errors without leaking stack traces,
- avoid logging secrets or full request bodies.

## Authentication and authorization

- Keep `getCurrentUser()` and `requireUser()` in `lib/auth/session.ts`.
- Keep permission checks close to the resource: `canManageWorkspace(userId, workspaceId)`.
- Never trust `userId`, `workspaceId`, or `role` from client input without checking membership in the database.
- Use `httpOnly`, `secure`, `sameSite: "lax"` cookies for sessions.
- Treat webhooks as unauthenticated until signature verification succeeds.

Reason: SaaS bugs are often cross-tenant access bugs. Authorization should be boring and repeated.

## Environment variables

Parse env once in `lib/env.ts`:

```ts
import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().min(1),
  SESSION_SECRET: z.string().min(32),
  NEXT_PUBLIC_APP_URL: z.string().url(),
});

export const env = envSchema.parse(process.env);
```

Rules:
- Only variables prefixed with `NEXT_PUBLIC_` may reach the browser.
- Do not read `process.env` throughout the codebase.
- Tests should provide explicit env values.

## Error handling

- Validation errors: return field-level messages.
- Auth errors: redirect to sign-in or return 401.
- Authorization errors: return 403 and do not reveal whether another tenant's resource exists.
- Unexpected errors: log a request ID and return a generic message.

Do not expose raw SQLite errors to users.

## Testing expectations

Add tests when changing:
- migration logic,
- service functions,
- authorization rules,
- payment or webhook handlers,
- data transformations.

Minimum useful checks:
- migration applies to an empty database,
- service rejects invalid input,
- service rejects cross-tenant access,
- transaction rolls back on failure.

## Development commands

Use these defaults unless the project defines different package scripts:

```bash
npm install
npm run dev
npm run lint
npm run typecheck
npm test
```

SQLite helpers should be scriptable:

```bash
npm run db:migrate
npm run db:seed
npm run db:reset
```

## Patterns to follow

- Keep business logic in `server/services`, not in components.
- Use progressive enhancement: forms should work with server actions before adding optimistic UI.
- Prefer explicit SQL over a heavy ORM for small SaaS apps.
- Use database constraints instead of relying only on UI checks.
- Keep loading and empty states close to the route segment that owns the data.
- Document every webhook with source, signature header, retry behavior, and idempotency key.

## Anti-patterns to avoid

- Do not put secrets in client components, `NEXT_PUBLIC_*`, localStorage, or analytics events.
- Do not use the Edge runtime for SQLite routes.
- Do not create API routes for mutations that are only used by one internal form.
- Do not skip authorization because a page is hidden in the UI.
- Do not rewrite old migrations after review.
- Do not add global state for server data that can be loaded by Server Components.
- Do not catch errors and return success-shaped objects.
- Do not introduce queues, Redis, or microservices before a real bottleneck exists.

## PR checklist for Claude Code

Before finishing a change:

- [ ] Inputs are validated with Zod.
- [ ] Auth and tenant authorization are checked server-side.
- [ ] Database writes are transactional where needed.
- [ ] Migration file and `schema.sql` are both updated for schema changes.
- [ ] Client components are limited to actual interactivity.
- [ ] New environment variables are added to `lib/env.ts` and documented.
- [ ] Tests cover important service or migration behavior.
- [ ] No secrets, payment payloads, or private user data are logged.
