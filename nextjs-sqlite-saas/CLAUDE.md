# CLAUDE.md — Next.js 15 + SQLite SaaS

This file is the operating manual for Claude Code in a greenfield SaaS using Next.js 15 App Router, TypeScript, Tailwind, and SQLite via either `better-sqlite3` for single-node deployments or Turso/libSQL for hosted edge-ish SQLite.

## Stack & Versions

- Next.js 15 App Router with React Server Components by default.
- TypeScript in `strict` mode.
- SQLite is the source of truth; use `better-sqlite3` locally/single-node or Turso/libSQL for managed production.
- Tailwind CSS for styling; do not introduce a second styling system.
- Zod for runtime validation at boundaries: forms, route handlers, webhooks, and env vars.
- Server Actions are allowed for simple authenticated mutations; route handlers are preferred for public APIs, webhooks, and third-party callbacks.

Reason: this stack keeps the app small, inspectable, and deployable without adding a distributed database before the product earns it.

## Project Structure

Use this structure unless there is a strong reason not to:

```text
app/
  (marketing)/              # public landing pages
  (app)/                    # authenticated product area
  api/                      # route handlers for external callers/webhooks
  layout.tsx
  page.tsx
components/
  ui/                       # generic presentational primitives
  app/                      # product-specific components
db/
  client.ts                 # database connection factory
  schema.sql                # canonical schema snapshot
  migrations/               # numbered SQL migrations
  queries/                  # typed query helpers
lib/
  auth/                     # session, user, and permission helpers
  env.ts                    # validated env vars
  errors.ts                 # shared error types
  utils.ts
server/
  actions/                  # Server Actions grouped by domain
  services/                 # business logic, no React imports
tests/
  unit/
  integration/
```

Rules:

- Keep database access in `db/queries/*` or `server/services/*`, never inside client components.
- Keep business rules in `server/services/*`; Server Actions should validate input, call a service, then redirect/revalidate.
- Put reusable UI in `components/ui`; put domain-specific UI in `components/app`.

Reason: the folder names tell Claude where code belongs and prevent mixing UI, persistence, and business rules.

## Dev Commands

Assume these scripts exist or create them when initializing the project:

```bash
npm run dev          # start Next.js locally
npm run build        # production build
npm run lint         # eslint/next lint checks
npm run typecheck    # tsc --noEmit
npm run test         # unit/integration tests
npm run db:migrate   # apply pending migrations
npm run db:reset     # local-only reset from migrations
```

Before finishing a code task, run at least:

```bash
npm run typecheck && npm run lint
```

Run `npm run build` before PRs that touch routing, env vars, auth, or database code.

## Naming Conventions

- Files and routes: kebab-case (`billing-settings.tsx`, `create-checkout-session.ts`).
- React components: PascalCase exports from kebab-case files.
- Server Actions: verb-first names (`createProjectAction`, `updatePlanAction`).
- Query helpers: intent-first names (`getUserByEmail`, `listProjectsForUser`).
- Database tables: plural snake_case (`users`, `subscription_events`).
- Columns: snake_case (`created_at`, `stripe_customer_id`).

Reason: TypeScript code stays idiomatic while SQL remains SQL-native.

## SQL & Migration Conventions

- Every schema change must be a numbered migration: `db/migrations/0001_initial.sql`, `0002_add_teams.sql`.
- Never edit a migration that has been applied outside your local throwaway database. Add a new migration instead.
- Keep `db/schema.sql` updated as the full current schema snapshot.
- Use explicit constraints: `not null`, `unique`, `check`, and foreign keys.
- Prefer integer primary keys or text UUIDs consistently; do not mix without a reason documented in the migration.
- Store timestamps as ISO-8601 text or Unix epoch integers consistently across the entire project.
- Enable foreign keys for every SQLite connection:

```ts
db.pragma("foreign_keys = ON")
```

- Wrap multi-step writes in transactions.
- Do not use `SELECT *` in application queries; list the columns you consume.

Reason: SQLite is reliable when constraints and migrations are treated as product code, not incidental setup.

## Database Access Patterns

- `db/client.ts` owns connection setup and pragmas.
- `db/queries/*` contains small typed functions that map SQL rows to domain objects.
- `server/services/*` composes queries into business workflows.
- Client components receive serialized data as props; they never import `db`, `fs`, or server-only modules.

Example shape:

```ts
// db/queries/users.ts
export async function getUserByEmail(email: string) {
  return db.prepare("select id, email, name from users where email = ?").get(email)
}
```

For Turso/libSQL, keep the same query-helper boundary so the app can move between local SQLite and hosted SQLite without rewriting components.

## Component Patterns

- Default to Server Components.
- Add `"use client"` only for state, browser APIs, subscriptions, or event handlers.
- Keep client components leaf-level when possible.
- Forms should use Server Actions for simple authenticated mutations.
- Use optimistic UI only after the mutation path and rollback behavior are clear.
- Components should not fetch from internal API routes; call server functions directly in Server Components.

Reason: App Router is fastest and simplest when data loading stays server-side and interactivity is isolated.

## Auth & Authorization

- Authentication answers “who is this?”; authorization answers “can they do this?” Keep them separate.
- Every service that reads or writes user-owned data must accept an explicit `actor` or `userId` and check ownership.
- Do not rely on hidden UI controls as authorization.
- Route handlers and Server Actions must validate both session and input.

Reason: SaaS bugs usually come from missing authorization checks, not missing login screens.

## Environment Variables

- Define all env vars in `lib/env.ts` with Zod.
- Never read `process.env` throughout the codebase except inside `lib/env.ts`.
- Separate public vars with `NEXT_PUBLIC_` and never place secrets in public vars.
- Fail fast during boot/build if required env vars are missing.

Reason: env drift causes deployment failures that Claude can prevent with one validated boundary.

## Error Handling

- Return user-safe messages from actions and route handlers.
- Log internal details server-side only.
- Use typed/domain errors for expected failures: `UnauthorizedError`, `PlanLimitError`, `ValidationError`.
- Do not swallow database errors. Add context and rethrow or convert to a domain error.

## Testing Rules

- Unit test pure services and query mapping logic.
- Integration test migrations against a temporary SQLite database.
- Test Server Actions by calling the action/service boundary, not by clicking through the UI unless an e2e framework is already present.
- Every bug fix should include a regression test or a short explanation for why one is not practical.

## Patterns To Follow

- Server-first data fetching.
- Thin route handlers and thin Server Actions.
- Explicit SQL migrations.
- Zod validation at every external boundary.
- Transactions for multi-write operations.
- Small, composable services with no React imports.

## Anti-Patterns To Avoid

- Do not add Prisma unless explicitly requested; raw SQL/query helpers are simpler for this stack.
- Do not put database calls in Client Components.
- Do not create API routes just for Server Components to call internally.
- Do not edit old migrations after they are shared.
- Do not introduce global mutable state for per-request data.
- Do not add background queues, Redis, or microservices before a concrete product need exists.
- Do not use `any` to bypass domain modeling; use Zod and narrow types instead.

## Task Completion Checklist

Before saying a task is done:

1. Confirm code is in the correct folder according to this file.
2. Confirm new database changes have a migration and schema snapshot update.
3. Run relevant checks: typecheck, lint, tests, and build when routing/env/db changed.
4. Summarize changed files and any migration/deployment steps.
5. Call out risks or follow-ups instead of hiding uncertainty.
