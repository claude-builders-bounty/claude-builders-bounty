# CLAUDE.md: Next.js 15 + SQLite SaaS

Use this file as the operating context for a greenfield SaaS app built with Next.js 15 App Router, TypeScript, React Server Components, SQLite, Drizzle ORM, and either `better-sqlite3` for local/server deployments or Turso/libSQL for hosted SQLite.

## Stack And Commands

- Runtime: Node.js 22 LTS.
- Framework: Next.js 15 App Router with TypeScript and React Server Components by default.
- Database: SQLite through Drizzle ORM. Use `better-sqlite3` for local file-backed deployments and Turso/libSQL only when remote SQLite is explicitly required.
- Styling: Tailwind CSS plus small local components. Use a design system only after repeated UI patterns exist.
- Auth: Auth.js or a small session table. Never mix multiple auth systems.

Expected commands:

```bash
npm run dev
npm run lint
npm run typecheck
npm run test
npm run db:generate
npm run db:migrate
npm run db:studio
```

If a command is missing, inspect `package.json` and add the smallest script that matches the existing toolchain before inventing a new workflow.

## Project Structure

Use this structure unless the repository already has a clear equivalent:

```text
app/
  (marketing)/
  (dashboard)/
  api/
components/
  ui/
  forms/
  data/
db/
  schema.ts
  index.ts
  migrations/
lib/
  auth/
  config/
  server/
  validation/
server/
  actions/
  services/
  queries/
tests/
  unit/
  integration/
```

Reasons:

- `app/` owns routes, layouts, loading states, and route handlers.
- `components/ui/` contains reusable primitives only; feature components live close to the route or in `components/forms` and `components/data`.
- `db/schema.ts` is the single source of truth for tables, relations, and indexes.
- `server/queries` contains read-only data access; `server/actions` contains mutations exposed to forms or client interactions; `server/services` contains reusable business workflows.
- `lib/server` is for server-only utilities. Do not import it from client components.

## Naming Conventions

- Files and folders: kebab-case, for example `billing-plan-card.tsx`.
- React components: PascalCase, for example `BillingPlanCard`.
- Server actions: verb-first names, for example `createWorkspace`, `inviteMember`, `cancelSubscription`.
- Query functions: noun-first or `get/list` names, for example `getWorkspaceBySlug`, `listWorkspaceMembers`.
- Database tables: plural snake_case, for example `workspace_members`.
- Database columns: snake_case in SQLite, camelCase in TypeScript mapping when the ORM supports it.
- Environment variables: uppercase with a product prefix when useful, for example `APP_DATABASE_URL`.

Reason: these rules make file search, imports, and database inspection predictable for both humans and agents.

## Database Rules

- Define every table in `db/schema.ts`. Do not create tables ad hoc in route handlers or tests.
- Every table must have `id`, `created_at`, and `updated_at` unless it is a pure join table.
- Add indexes for foreign keys and common lookup fields such as `email`, `slug`, `workspace_id`, and `user_id`.
- Store money as integer minor units, for example cents, plus an ISO currency code.
- Store timestamps as UTC ISO strings or integer epoch milliseconds consistently across the app. Do not mix formats.
- Use transactions for multi-table writes. A mutation that creates a workspace and membership must be atomic.
- Never run destructive migrations automatically in request paths, server actions, or startup code.
- Migration files are append-only. If a migration has shipped, create a follow-up migration instead of editing history.
- For Turso/libSQL, assume network latency and avoid chatty per-row queries.

Migration workflow:

```bash
npm run db:generate
npm run db:migrate
npm run typecheck
npm run test
```

Before adding a migration, explain the schema change in the PR or task summary and include rollback notes when data could be lost.

## Server And Data Access

- Prefer Server Components for reads. Fetch data in the route segment that owns the screen.
- Keep database reads in `server/queries`. Keep writes in `server/actions` or `server/services`.
- Validate all external input with a schema parser before it reaches the database.
- Return typed result objects from server actions: `{ ok: true, data }` or `{ ok: false, error }`.
- Do not leak raw database errors to users. Map them to stable messages.
- Use `cache` or `unstable_cache` only for read paths that can tolerate staleness. Never cache user-specific authorization decisions unless the cache key includes the user and workspace.
- Revalidate the smallest useful path or tag after mutations.

Reason: this keeps App Router boundaries clear and prevents client components from becoming data-access glue.

## Component Patterns

- Components are Server Components unless they need state, browser APIs, event handlers, or optimistic UI.
- Mark client components with `"use client"` at the smallest possible leaf.
- Forms should use server actions for durable writes. Use client state only for local interaction and progressive enhancement.
- Keep page components thin: load data, check authorization, compose feature components.
- Use accessible labels for every form control and icon-only button.
- For tables and lists, define empty, loading, and error states before adding secondary features.
- Do not put business rules in presentational components. Put them in `server/services` or domain helpers.

## Auth And Authorization

- Authentication answers "who is this user"; authorization answers "what can this user do here." Keep them separate.
- Every workspace-scoped query must include a workspace or membership check.
- Never trust `workspaceId`, `userId`, `role`, price, or plan values from the client.
- Route handlers and server actions must derive the current user from the server session.
- Use role constants from one module. Do not scatter string literals such as `"admin"` across the app.

## API Routes

- Use route handlers for webhooks, third-party integrations, and machine clients.
- Keep internal form mutations as server actions unless there is a real API consumer.
- Verify webhook signatures before parsing business payloads.
- Make route handlers idempotent when providers can retry requests.
- Return structured errors with stable status codes.

## Testing Expectations

- Unit-test pure domain helpers and validation schemas.
- Integration-test database queries and server services against a temporary SQLite database.
- Add at least one regression test for every bug fix.
- For migrations, test that a fresh database can apply all migrations.
- For server actions, test success, validation failure, and authorization failure.

Minimum local gate before claiming done:

```bash
npm run lint
npm run typecheck
npm run test
npm run db:migrate
```

If the repository does not have one of these gates, say so explicitly and add the missing gate when it is within scope.

## Anti-Patterns To Avoid

- Do not import database clients into client components. It breaks the server/client boundary.
- Do not create one giant `lib/utils.ts`. Split utilities by domain so future agents can find them.
- Do not use raw SQL strings for normal CRUD when the ORM schema can express the query. Use raw SQL only for performance-sensitive or SQLite-specific operations.
- Do not hide authorization in UI conditionals. The server must enforce it.
- Do not add global state for data that belongs in the URL, server query, or form state.
- Do not add a background job system for work that can be done in a transaction or webhook handler.
- Do not store secrets in `.env.local.example`, fixtures, screenshots, or test output.
- Do not add dependencies for problems solved by the framework, the standard library, or a small local helper.

## Response Style For Claude Code

When working in this project:

- Start by identifying the route, table, or server action that owns the change.
- Name the files you expect to edit before editing them.
- For schema changes, describe the migration and data-safety impact first.
- After changes, report the exact commands run and whether each passed.
- If a requested shortcut would bypass auth, validation, migrations, or tests, choose the safe implementation and explain the tradeoff briefly.
