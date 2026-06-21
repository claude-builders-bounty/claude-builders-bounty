# CLAUDE.md

This file gives Claude Code the project rules for a production SaaS app built
with Next.js 15 App Router, TypeScript, SQLite, and either `better-sqlite3` for
single-node deployments or Turso/libSQL for hosted edge-friendly SQLite.

The goal is predictable, boring, shippable SaaS code. Prefer explicit server
boundaries, small database migrations, and simple components over clever
abstractions.

## Stack And Versions

- Next.js 15 with the App Router under `app/`.
  Reason: the project uses React Server Components, route handlers, metadata,
  and nested layouts as first-class primitives.
- React 19 and TypeScript in strict mode.
  Reason: server/client boundaries and serialized props should fail during
  development, not at runtime.
- SQLite as the application database.
  Reason: the app should start simple, stay easy to inspect locally, and avoid
  distributed database assumptions until the product proves it needs them.
- Use `better-sqlite3` for a single Node.js server, background worker, or
  container deployment.
  Reason: it is synchronous, fast, simple, and predictable for local-first SaaS.
- Use Turso/libSQL only when the deployment target needs remote SQLite access.
  Reason: hosted SQLite changes latency and transaction assumptions, so choose
  it deliberately.
- Use Tailwind CSS and a small local component set in `components/ui/`.
  Reason: SaaS screens need consistency and speed more than a large design
  abstraction.
- Use Zod at every untrusted boundary.
  Reason: form data, route params, search params, and webhook payloads are not
  typed just because TypeScript exists.

## Dev Commands

Use these commands unless the repo documents a replacement:

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm db:migrate
pnpm db:studio
pnpm build
```

If a command is missing, add it to `package.json` before using a one-off shell
command. Reason: future agents and humans need the same project interface.

Recommended scripts:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:e2e": "playwright test",
    "db:migrate": "tsx scripts/migrate.ts",
    "db:studio": "drizzle-kit studio"
  }
}
```

## Folder Structure

Use this structure for greenfield work:

```text
app/
  (marketing)/
  (auth)/
  (dashboard)/
  api/
components/
  ui/
  forms/
  dashboard/
db/
  client.ts
  schema.ts
  migrations/
  queries/
lib/
  auth/
  billing/
  config.ts
  env.ts
  errors.ts
  ids.ts
  logger.ts
  permissions.ts
server/
  actions/
  services/
  jobs/
tests/
  unit/
  integration/
  e2e/
scripts/
  migrate.ts
  seed.ts
```

Rules:

- Put route UI in `app/`, reusable UI in `components/`, and business logic in
  `server/services/`.
  Reason: pages should compose behavior, not hide it.
- Put SQL schema, migrations, and typed query helpers in `db/`.
  Reason: database behavior must be reviewable without scanning UI files.
- Put mutations called from forms in `server/actions/`.
  Reason: Server Actions are a transport layer, not a dumping ground for domain
  logic.
- Put env parsing in `lib/env.ts` and import it everywhere else.
  Reason: the app should fail once at boot for invalid config, not randomly.
- Do not create `utils/` for unrelated helpers.
  Reason: a generic utilities folder becomes a junk drawer and hides ownership.

## Naming Conventions

- Files and folders use kebab-case: `billing-status.tsx`, `create-workspace.ts`.
  Reason: it matches route segment naming and avoids case-sensitive filesystem
  bugs.
- React components use PascalCase exports: `WorkspaceSwitcher`.
  Reason: JSX and React DevTools expect component names to be readable.
- Server Actions start with a verb: `createWorkspaceAction`,
  `updateBillingEmailAction`.
  Reason: actions mutate state and should read as commands.
- Query helpers start with `get`, `list`, or `find`: `getUserById`,
  `listWorkspaceMembers`.
  Reason: reads should be distinguishable from writes during review.
- Database tables use plural snake_case: `users`, `workspace_members`.
  Reason: SQL stays conventional and easy to grep.
- Primary keys are text ids named `id`.
  Reason: branded ids such as `usr_...` or `wrk_...` are safer to log and pass
  through URLs than incrementing integers.

## SQLite And Migration Conventions

Use migrations for every schema change. Never edit an old migration after it
has been merged.

Migration rules:

- Store migrations in `db/migrations/` with ordered names such as
  `0001_create_users.sql`.
  Reason: SQLite applies schema changes sequentially, and order should be
  obvious in code review.
- Every migration must be safe to run exactly once and tracked in a
  `_migrations` table.
  Reason: repeat execution should fail early instead of corrupting schema state.
- Prefer additive migrations: create table, add nullable column, backfill, then
  enforce constraints in a later migration when possible.
  Reason: SQLite has limited `ALTER TABLE` support and production data needs
  cautious transitions.
- Always enable foreign keys on connection with `PRAGMA foreign_keys = ON`.
  Reason: SQLite does not enforce foreign keys unless explicitly enabled.
- Use `created_at` and `updated_at` as ISO-8601 text.
  Reason: text timestamps are portable, readable, and sort correctly when stored
  as UTC ISO strings.
- Use transactions for multi-row writes.
  Reason: SaaS state such as workspace creation, membership, and billing setup
  must not partially commit.
- Use explicit unique indexes for business invariants.
  Reason: duplicate emails, duplicate slugs, and duplicate memberships are data
  bugs, not UI validation bugs.

Recommended table shape:

```sql
CREATE TABLE workspaces (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

Query rules:

- Keep raw SQL close to `db/queries/`.
  Reason: review needs to find data access quickly.
- Never concatenate untrusted strings into SQL.
  Reason: SQLite is still vulnerable to injection.
- Return plain objects from query helpers.
  Reason: Server Components and Server Actions need serializable values.
- Avoid implicit global database clients in tests.
  Reason: tests need isolated temporary databases.

## App Router Patterns

- Use Server Components by default.
  Reason: SaaS dashboards often need data before interaction, and Server
  Components reduce client bundle size.
- Add `"use client"` only for components with state, effects, browser APIs, or
  event handlers.
  Reason: accidental client components make secrets and database imports easier
  to misuse.
- Fetch data in route segments or server-only query helpers.
  Reason: data dependencies should follow the route tree.
- Keep `page.tsx` thin.
  Reason: page files should read like orchestration: auth, data, render.
- Use `loading.tsx`, `error.tsx`, and `not-found.tsx` for real route states.
  Reason: SaaS users need clear recovery paths, not blank screens.
- Use route groups for product areas: `(marketing)`, `(auth)`, `(dashboard)`.
  Reason: layouts and middleware stay understandable as the app grows.

## Server Actions And Route Handlers

- Validate every action input with Zod.
  Reason: `FormData` and JSON payloads are untrusted.
- Check authentication and authorization inside the action or service.
  Reason: UI hiding is not access control.
- Return typed result objects instead of throwing for expected form errors.
  Reason: forms need field-level feedback without turning validation into
  exception control flow.
- Use route handlers for webhooks and third-party integrations.
  Reason: external systems need HTTP semantics, signatures, and status codes.
- Verify webhook signatures before reading business fields.
  Reason: payment and auth webhooks are high-value spoofing targets.

Action result shape:

```ts
type ActionResult<T> =
  | { ok: true; data: T }
  | { ok: false; fieldErrors?: Record<string, string>; message: string };
```

## Component Patterns

- Split components by ownership, not visual size.
  Reason: `BillingPlanCard` can be large and still be cohesive; `DashboardMisc`
  is never cohesive.
- Keep `components/ui/` primitive and business-free.
  Reason: buttons, dialogs, and inputs should not import billing or auth code.
- Pass server-fetched data into client components as serialized props.
  Reason: client components should not import database or secret-bearing modules.
- Prefer composition over boolean prop explosions.
  Reason: `variant`, `size`, and `children` scale better than many one-off flags.
- Keep forms accessible: labels, descriptions, disabled states, and pending
  states are required.
  Reason: production SaaS forms are used repeatedly and must be reliable.
- Use optimistic UI only when rollback is obvious.
  Reason: billing, permissions, and destructive actions should favor correctness.

## Authentication And Authorization

- Centralize session lookup in `lib/auth/session.ts`.
  Reason: auth behavior should be consistent across pages, actions, and route
  handlers.
- Centralize permission checks in `lib/permissions.ts`.
  Reason: roles and workspace membership rules change over time.
- Check workspace membership on every workspace-scoped read and write.
  Reason: multi-tenant leaks are the most serious SaaS bug in this stack.
- Never trust `workspaceId` from the client without verifying membership.
  Reason: users can alter hidden inputs, URLs, and request bodies.
- Keep admin-only behavior behind explicit permission functions.
  Reason: `if (user.role === "admin")` scattered across the app becomes
  unreviewable.

## Billing Patterns

- Treat the payment provider as the source of truth for subscription status, but
  cache the current state locally.
  Reason: the app needs fast authorization while still reconciling provider
  changes.
- Webhooks must be idempotent.
  Reason: payment providers retry events.
- Store provider event ids and ignore duplicates.
  Reason: duplicate webhook processing can create double credits or wrong plan
  state.
- Do not unlock paid features until the local database transaction commits.
  Reason: UI state and billing state must move together.

## Environment And Config

- Read environment variables only in `lib/env.ts`.
  Reason: config validation should happen in one place.
- Use separate schemas for server and client env.
  Reason: client-safe values must be intentionally exposed.
- Never expose database URLs, auth secrets, webhook secrets, or API keys through
  `NEXT_PUBLIC_`.
  Reason: those values are bundled into browser JavaScript.
- Prefer explicit feature flags over checking for missing env vars at call sites.
  Reason: runtime behavior should be intentional.

## Error Handling And Logging

- Use typed domain errors for expected failures.
  Reason: "workspace not found" and "permission denied" need different UI and
  status codes.
- Log with stable fields: `userId`, `workspaceId`, `requestId`, `event`.
  Reason: SaaS incidents are debugged through correlation, not prose logs.
- Never log secrets, raw session tokens, webhook signatures, or full payment
  payloads.
  Reason: logs are often copied into tools and tickets.
- Show friendly errors to users and detailed errors to logs.
  Reason: users need recovery steps, not stack traces.

## Testing Rules

- Unit test pure services and query mappers.
  Reason: business rules should be testable without a browser.
- Integration test database queries with a temporary SQLite database.
  Reason: SQL correctness requires a real database engine.
- E2E test signup, login, workspace creation, billing-gated access, and one
  core paid workflow.
  Reason: these are the flows that decide whether the SaaS works.
- Every migration must be tested on an empty database and on a seeded previous
  schema when practical.
  Reason: migration bugs are production bugs.
- Do not mock permission checks in route/action tests.
  Reason: authorization is part of the behavior under test.

## Security Defaults

- Validate all external input.
  Reason: TypeScript does not protect runtime boundaries.
- Escape or sanitize user-generated HTML; avoid raw HTML by default.
  Reason: SaaS products often render names, comments, notes, and settings.
- Use CSRF-safe mutation paths.
  Reason: authenticated browser requests can be triggered cross-site.
- Rate-limit auth, invitations, billing portal creation, and AI endpoints.
  Reason: these endpoints are expensive or abuse-prone.
- Keep secrets server-only and out of client components.
  Reason: `"use client"` changes what code can ship to the browser.
- Use least-privilege API keys for third-party services.
  Reason: a leaked integration key should not compromise the whole account.

## Performance Rules

- Start with simple server-rendered data fetching.
  Reason: most SaaS screens are easier and faster when rendered on the server.
- Add caching only with a named invalidation strategy.
  Reason: stale permissions and billing state are worse than slower pages.
- Paginate database lists before they are large.
  Reason: dashboards grow from 20 rows to 20,000 rows without warning.
- Avoid loading charting, editor, or analytics libraries in global layouts.
  Reason: heavy client code should stay near the feature that needs it.

## What We Do Not Do

- Do not use Prisma by default.
  Reason: this template is optimized for SQLite-first apps where explicit SQL or
  lightweight query builders keep behavior visible.
- Do not put database access in client components.
  Reason: client bundles cannot keep secrets and should not own server data.
- Do not add Redux or global client state for server-owned data.
  Reason: App Router, Server Components, and URL state cover most SaaS needs.
- Do not hide authorization in middleware only.
  Reason: middleware is useful for coarse routing, but services must enforce
  tenant access too.
- Do not create generic repositories for every table.
  Reason: table-shaped abstractions usually hide the business operation being
  performed.
- Do not add background jobs without an idempotency key.
  Reason: retries are normal, and duplicate side effects are costly.
- Do not skip migrations because "SQLite is just a file."
  Reason: production data deserves the same discipline in every database.
- Do not accept broad refactors while fixing a narrow bug.
  Reason: small PRs are easier to review, test, and merge.

## Before Opening A PR

Run:

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

For database changes, also run:

```bash
pnpm db:migrate
```

PR checklist:

- The change follows the App Router server/client boundary.
- All untrusted input is validated with Zod.
- Database changes include migrations.
- Workspace-scoped reads and writes check membership.
- Tests cover the behavior or the PR explains why testing is not applicable.
- New env vars are documented and parsed in `lib/env.ts`.
