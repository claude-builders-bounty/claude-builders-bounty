# CLAUDE.md — Next.js 15 + SQLite SaaS Project

Use this file as the operating guide for a greenfield SaaS app built with Next.js 15 App Router, TypeScript, Tailwind CSS, and SQLite through `better-sqlite3` for local/single-node deployments or Turso/libSQL for hosted edge-like deployments.

## Stack and versions

- Next.js 15 with the App Router in `app/`.
- React Server Components by default; Client Components only when browser state, effects, event handlers, or DOM APIs are required.
- TypeScript in strict mode.
- SQLite as the system of record.
- `better-sqlite3` for local or serverful Node.js runtime. Use Turso/libSQL only when the app must run on hosted distributed infrastructure.
- Tailwind CSS for styling and shared primitives in `components/ui/`.
- Server Actions for small mutations; route handlers for webhooks, public APIs, file downloads, and third-party callbacks.

Reason: this stack keeps the product cheap, inspectable, and easy to deploy while preserving a clean path from prototype to paid SaaS.

## Folder structure

```text
app/
  (marketing)/          # public landing, pricing, docs
  (app)/                # authenticated product routes
  api/                  # route handlers for external HTTP surfaces
  layout.tsx
  page.tsx
components/
  ui/                   # generic UI primitives
  feature/              # product-specific composed components
lib/
  db/                   # connection, schema helpers, migrations
  auth/                 # session and permission helpers
  config/               # env parsing and typed app config
  services/             # business operations used by routes/actions
  validators/           # zod schemas or equivalent validation
migrations/             # ordered SQL migrations
scripts/                # local maintenance scripts
public/
tests/
```

Rules:

- Put business logic in `lib/services/*`, not directly in React components.
- Put SQL in `lib/db/*` or migration files, not inline across pages.
- Keep route handlers thin: parse input, call a service, return a response.
- Keep Server Components data-loading oriented and side-effect free.

Reason: feature work stays easy to review when UI, SQL, validation, and business actions do not blur together.

## Naming conventions

- Components: `PascalCase.tsx`.
- Hooks: `useThing.ts` and only in Client Component paths.
- Server actions: `thing.actions.ts`.
- Services: `thing.service.ts`.
- DB files: `client.ts`, `schema.ts`, `queries.ts`, and `migrate.ts` under `lib/db/`.
- Migrations: `YYYYMMDDHHMM_descriptive_name.sql`.
- Tables: plural snake_case, for example `users`, `billing_events`, `team_members`.
- Columns: snake_case. Use `created_at`, `updated_at`, and nullable `deleted_at` for soft-delete tables.

Reason: predictable names reduce search time and keep Claude Code from inventing parallel structures.

## Dev commands

Assume these scripts exist or add them when creating the project:

```bash
npm run dev          # start Next.js locally
npm run build        # production build
npm run lint         # lint TypeScript/React
npm run typecheck    # tsc --noEmit
npm run test         # unit tests
npm run db:migrate   # apply migrations
npm run db:studio    # optional local DB browser
```

Before finishing a change, run the narrowest relevant command first, then `npm run lint`, `npm run typecheck`, and tests for touched code. Run `npm run build` for routing, config, or server/client boundary changes.

Reason: fast checks catch local mistakes; full builds catch Next.js boundary mistakes.

## SQL and migration conventions

- Every schema change must be an ordered SQL migration in `migrations/`.
- Never edit a migration that has already shipped. Add a new migration.
- Wrap multi-step migrations in transactions when SQLite supports the operations involved.
- Use explicit foreign keys and enable `PRAGMA foreign_keys = ON` when opening connections.
- Prefer integer primary keys or UUID text keys, but do not mix styles within the same domain.
- Store money as integer cents plus currency code, never floating-point dollars.
- Store timestamps as ISO-8601 text or integer Unix milliseconds; choose one and stay consistent.
- Add indexes for foreign keys and common lookup filters.
- Do not put secrets, API keys, or raw payment credentials in SQLite.

Reason: SQLite is reliable when migrations are boring, reversible by backup, and explicit about constraints.

## Data access patterns

Use service functions as the only write boundary:

```ts
// lib/services/projects.service.ts
export async function createProject(input: CreateProjectInput, actor: Actor) {
  assertCanCreateProject(actor);
  const parsed = createProjectSchema.parse(input);
  return db.transaction(() => insertProject(parsed, actor.id));
}
```

Rules:

- Validate all external input before calling SQL.
- Keep transactions inside service functions.
- Return plain objects that components can render.
- Do not let Client Components call DB utilities directly.

Reason: one write boundary makes permissions, validation, and audit logging enforceable.

## Component patterns

- Prefer Server Components for pages, lists, dashboards, and detail views.
- Use Client Components for forms with local interactivity, optimistic UI, keyboard shortcuts, charts, and browser APIs.
- Pass serialized data from Server Components into Client Components.
- Keep shared UI primitives prop-driven and free of database calls.
- Use accessible HTML before custom widgets.

Reason: Server Components keep the app fast and secure; Client Components stay focused on interaction.

## Server Actions and route handlers

Use Server Actions for authenticated product mutations initiated by app UI. Use route handlers for:

- webhooks
- public API endpoints
- OAuth callbacks
- file upload/download endpoints
- health checks

Rules:

- Re-check authorization inside every action or route handler.
- Parse and validate request bodies at the boundary.
- Never trust hidden form fields for user, team, role, price, or entitlement values.
- Make mutations idempotent when retry is plausible.

Reason: Next.js boundaries are convenient, but every boundary is still an external input surface.

## Auth and permissions

- Treat authentication as identity only.
- Put authorization checks in services close to the data mutation.
- Model team membership and roles explicitly in SQLite.
- Deny by default when role, team, or ownership is unclear.
- Log security-relevant actions such as billing changes, role changes, exports, and destructive deletes.

Reason: SaaS bugs often come from confusing “logged in” with “allowed to do this.”

## Environment and configuration

- Read environment variables through `lib/config/env.ts`.
- Validate env vars at startup with a typed schema.
- Keep `.env.example` current with placeholder values only.
- Do not read `process.env` throughout the codebase.
- Do not commit `.env`, local SQLite databases, production dumps, or credentials.

Reason: centralized config prevents silent production misconfiguration.

## Testing expectations

- Unit-test pure services, validators, and permission checks.
- Add integration tests around migrations and important SQL queries.
- Add at least one smoke test for critical app routes.
- For bug fixes, add a regression test that fails before the fix.
- Do not write tests that only assert implementation details.

Reason: the highest-value tests protect billing, permissions, migrations, and user data.

## Patterns to follow

- Small service functions with explicit input/output types.
- SQL migrations reviewed like application code.
- Server Components for data fetching.
- Client Components isolated at interaction leaves.
- Integer cents for money.
- Idempotency keys for payment, email, import, and webhook flows.
- Audit rows for destructive or billing-related actions.

## Anti-patterns to avoid

- Do not add a second database or ORM just because a task is awkward. First improve the SQLite boundary.
- Do not put business rules in JSX event handlers. Put them in services.
- Do not use floats for money. They introduce rounding bugs.
- Do not create API routes for actions used only by internal app forms. Use Server Actions.
- Do not make every component a Client Component. It increases bundle size and leaks server concerns.
- Do not skip migrations by calling `CREATE TABLE IF NOT EXISTS` from random runtime paths.
- Do not log secrets, session tokens, webhook signatures, or full payment payloads.
- Do not add dependencies for one-line helpers.

Reason: these shortcuts make the project harder to ship, audit, and operate.

## Claude Code working rules

When making changes:

1. Inspect existing structure before adding folders.
2. State which boundary is being changed: UI, service, DB, route, config, or test.
3. Prefer the smallest coherent patch.
4. Add or update migrations for schema changes.
5. Run the relevant checks and report exact commands.
6. If a requirement touches money, auth, or deletion, identify the safety check before editing.

Reason: this keeps autonomous changes reviewable and prevents accidental architecture drift.
