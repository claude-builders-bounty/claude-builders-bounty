# CLAUDE.md - Next.js 15 + SQLite SaaS

You are working in a production SaaS project built with Next.js 15 App Router, React Server Components, TypeScript, SQLite, and either `better-sqlite3` for embedded deployments or Turso/libSQL for hosted edge-friendly deployments.

Every rule below is intentional. Follow it unless the user explicitly asks for a different architecture.

## Stack And Versions

- Use Next.js 15 App Router in `app/`. Reason: route handlers, server actions, layouts, metadata, and streaming should live in one routing model.
- Use TypeScript in strict mode. Reason: most SaaS defects here are shape mismatches between forms, DB rows, and auth/session state.
- Use SQLite as the source of truth. Reason: this template optimizes for small teams, simple deploys, easy local development, and transactional correctness.
- Use `better-sqlite3` when the app runs on a long-lived Node.js runtime. Use Turso/libSQL when the deployment target is serverless/edge-like. Reason: `better-sqlite3` is synchronous and fast locally, while Turso avoids filesystem persistence assumptions.
- Use Zod at trust boundaries: form submissions, route handlers, webhooks, and env parsing. Reason: TypeScript does not validate runtime input.
- Prefer server components by default. Use client components only for browser state, event handlers, optimistic UI, or browser APIs.

## Project Structure

Use this structure for greenfield work:

```text
app/
  (marketing)/
  (app)/
    dashboard/
  api/
    health/route.ts
  layout.tsx
  page.tsx
components/
  ui/
  forms/
db/
  client.ts
  migrations/
    0001_initial.sql
  schema.ts
  queries/
lib/
  auth/
  env.ts
  errors.ts
  ids.ts
  validators/
server/
  actions/
  services/
tests/
```

Rules:

- Put route UI in `app/`, reusable UI in `components/`, database access in `db/`, domain workflows in `server/services/`, and server actions in `server/actions/`.
- Keep SQL in `db/queries/` or migration files. Reason: scattered SQL makes audits and indexes harder.
- Keep shared validation schemas in `lib/validators/`. Reason: forms, actions, and route handlers must agree on accepted input.
- Do not put business logic in React components. Components render; services decide.

## Naming Conventions

- Files and folders use `kebab-case`: `billing-plan-card.tsx`, `create-checkout-session.ts`.
- React components use `PascalCase`: `BillingPlanCard`.
- Server actions use verb phrases ending in `Action`: `createWorkspaceAction`.
- Service functions use verb phrases without framework names: `createWorkspace`, not `handleCreateWorkspaceServerAction`.
- Database tables use `snake_case` plural nouns: `users`, `workspaces`, `workspace_members`.
- Primary keys use `id`. Foreign keys use `<table_singular>_id`, such as `workspace_id`.
- Timestamps use `created_at`, `updated_at`, and `deleted_at`. Store ISO strings or integer milliseconds consistently; do not mix formats.

## SQL And Migration Conventions

- Migrations are append-only SQL files in `db/migrations/`.
- Name migrations with a sortable prefix: `0001_initial.sql`, `0002_add_workspace_members.sql`.
- Never edit a migration after it has been applied outside your local throwaway database. Add a new migration instead.
- Wrap multi-statement migrations in a transaction when SQLite supports the statements:

```sql
BEGIN;
-- changes
COMMIT;
```

- Always add indexes for foreign keys and common lookup fields. Reason: SQLite will not create every index you need.
- Enable foreign keys on every connection:

```ts
db.pragma("foreign_keys = ON");
```

- Use `CHECK` constraints for enum-like values and numeric invariants. Reason: the database should reject impossible states even if an action has a bug.
- Prefer soft deletes only when the product needs restore/audit behavior. Otherwise hard delete within a transaction.
- For Turso/libSQL, keep queries compatible with remote execution and avoid relying on local filesystem paths.

## Database Access Pattern

- Create exactly one database client module: `db/client.ts`.
- Route handlers, server actions, and services must import query/service functions, not create new connections directly.
- Use transactions for multi-step writes:

```ts
const result = db.transaction((input) => {
  const workspace = createWorkspaceRow(input);
  addWorkspaceMember(workspace.id, input.ownerId, "owner");
  return workspace;
})(input);
```

- Return typed domain objects from query functions. Do not leak raw driver responses to UI.
- Validate external input before calling database functions.

## Server Actions And Route Handlers

- Use server actions for first-party form mutations.
- Use route handlers for third-party callbacks, webhooks, public API endpoints, and health checks.
- Every mutation should:
  1. Authenticate the caller.
  2. Authorize access to the target workspace/resource.
  3. Validate input with Zod.
  4. Execute database writes in a transaction when more than one row changes.
  5. Revalidate the affected path or tag.
  6. Return a small typed result.

- Never trust `workspaceId`, `userId`, `role`, price IDs, or plan names from the client.
- Webhooks must verify signatures before parsing business fields.

## Component Patterns

- Default to server components for pages and data-loaded sections.
- Put interactive islands in small client components with `"use client"` at the leaf.
- Keep forms split into:
  - a server action in `server/actions/`,
  - a Zod schema in `lib/validators/`,
  - a form component in `components/forms/`.
- Pass serialized primitives to client components. Do not pass database clients, class instances, or functions across the server/client boundary.
- Use accessible form labels, error text, and disabled/loading states.

## Dev Commands

Use these commands unless the project already has equivalent scripts:

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm db:migrate
pnpm db:studio
```

Expected scripts:

```json
{
  "scripts": {
    "dev": "next dev",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "db:migrate": "tsx db/migrate.ts",
    "db:studio": "drizzle-kit studio"
  }
}
```

If this project uses npm or yarn instead of pnpm, keep script names the same and only change the package manager command.

## Environment Rules

- Parse env vars once in `lib/env.ts`.
- Fail fast at boot when required env vars are missing.
- Never read `process.env` deep inside components or services.
- Keep secrets server-only. Never expose database URLs, API keys, webhook secrets, or auth secrets through `NEXT_PUBLIC_`.

## Patterns To Follow

- Thin route handlers, thick services.
- Server-first data loading.
- Zod validation at every external boundary.
- SQL migrations checked into git.
- Transactional writes for billing, membership, and permissions.
- Small client components for interactivity.
- Explicit empty/loading/error states.
- Tests for validators, query functions, and permission checks.

## Anti-Patterns To Avoid

- Do not create API routes for first-party form submissions when a server action is simpler. Reason: it duplicates auth, validation, and error handling.
- Do not put SQL inside React components. Reason: UI changes should not risk data access regressions.
- Do not create a new SQLite connection per query. Reason: it causes inconsistent pragmas, slower requests, and lock surprises.
- Do not use `any` to bypass form or database typing. Reason: SaaS bugs often become billing or authorization bugs.
- Do not mutate applied migrations. Reason: teammates and production databases will drift.
- Do not use client components for whole pages unless browser-only behavior dominates. Reason: it gives up server rendering and increases bundle size.
- Do not trust client-provided authorization fields. Reason: users can modify requests.
- Do not add background jobs inside request handlers. Reason: Vercel/serverless requests can end before long work completes.

## Before You Commit

Run:

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm db:migrate
```

Then check:

- New SQL has a migration and rollback/recovery notes when needed.
- Every write path has auth, authorization, validation, and transaction boundaries.
- Client components are leaf-level and justified.
- New env vars are documented and validated in `lib/env.ts`.
- Errors shown to users are helpful but do not leak secrets.
