# Project Guide: Next.js 15 + SQLite SaaS

This project is a production-oriented SaaS application built with Next.js 15 App Router, TypeScript, React Server Components, Server Actions, and SQLite. Treat this file as the source of truth when adding features, fixing bugs, or restructuring code.

## Stack And Versions

- Runtime: Node.js 22 LTS or newer.
- Package manager: pnpm.
- Framework: Next.js 15 App Router.
- Language: TypeScript with `strict: true`.
- UI: React 19, Server Components by default, Client Components only for browser state or browser APIs.
- Styling: Tailwind CSS plus small colocated component variants.
- Database: SQLite.
- Local driver: `better-sqlite3`.
- Hosted driver: Turso/libSQL through `@libsql/client`.
- Validation: Zod at all request, form, environment, and database boundary points.
- Testing: Vitest for unit tests, Playwright for full user flows.

Reason: this stack keeps the app simple enough to run locally, durable enough for real users, and explicit enough that data flow can be audited without a large ORM layer hiding SQL behavior.

## Development Commands

Use these commands unless the repository overrides them in `package.json`.

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm build
pnpm db:migrate
pnpm db:studio
```

When changing database code, run at minimum:

```bash
pnpm db:migrate
pnpm test
pnpm build
```

When changing UI flows, run at minimum:

```bash
pnpm lint
pnpm typecheck
pnpm test:e2e
```

## Folder Structure

Use this structure for a greenfield app:

```text
app/
  (marketing)/
    page.tsx
    pricing/page.tsx
  (auth)/
    login/page.tsx
    signup/page.tsx
  (app)/
    dashboard/page.tsx
    settings/page.tsx
  api/
    health/route.ts
components/
  ui/
  forms/
  layout/
db/
  migrations/
  schema.sql
  seed.ts
lib/
  actions/
  auth/
  db/
    client.ts
    queries/
    transaction.ts
  env.ts
  errors.ts
  permissions.ts
  validation/
scripts/
  migrate.ts
  seed.ts
tests/
  unit/
  e2e/
types/
```

Rules:

- `app/` owns routing, page composition, layouts, metadata, and route handlers.
- `components/ui/` contains generic presentational components that do not import app-specific data loaders.
- `components/forms/` contains form shells and input composition.
- `lib/actions/` contains Server Actions. Actions validate input, call `lib/db/queries`, and return typed success/error results.
- `lib/db/client.ts` is the only place that opens database connections.
- `lib/db/queries/` contains named query functions. SQL belongs here, not inside pages or components.
- `lib/permissions.ts` owns authorization checks. Do not duplicate role checks across pages.
- `lib/env.ts` parses and exports environment variables through Zod.

Reason: the structure separates route rendering, input validation, authorization, and persistence so feature work is local and testable.

## Naming Conventions

- Files and folders use kebab-case: `billing-settings-form.tsx`.
- React components use PascalCase: `BillingSettingsForm`.
- Server Actions end in `Action`: `updateWorkspaceAction`.
- Query functions start with the operation: `getWorkspaceBySlug`, `createInvite`, `updateSubscriptionStatus`.
- Zod schemas end in `Schema`: `createWorkspaceSchema`.
- Database tables use snake_case plural nouns: `workspaces`, `workspace_members`, `subscription_events`.
- Primary keys are `id`. Foreign keys are `{singular_table}_id`, for example `workspace_id`.
- Timestamps are `created_at`, `updated_at`, and optional domain-specific names such as `paid_at`.

Reason: predictable names make grep, code review, and migration review faster.

## Data Flow

Use this flow for mutations:

```text
Client form -> Server Action -> Zod validation -> permission check -> query function -> transaction -> typed result
```

Use this flow for reads:

```text
Page or Server Component -> auth/session lookup -> permission check -> query function -> render
```

Do not fetch internal app data from a Server Component by calling this app's own HTTP route. Import the query function directly instead.

Reason: direct server-side calls avoid unnecessary network hops and keep permissions in one path.

## SQLite And Migration Conventions

Migration files live in `db/migrations/` and use this naming pattern:

```text
0001_create_workspaces.sql
0002_add_workspace_members.sql
0003_add_billing_tables.sql
```

Rules:

- Migrations are forward-only.
- Every migration must be safe to run once and recorded in a `schema_migrations` table.
- Wrap multi-statement migrations in a transaction.
- Prefer additive changes: create a new table, add a nullable column, backfill, then enforce constraints later.
- Do not drop or rename a column in a production migration without a copy-and-backfill plan.
- Put indexes in the same migration as the query pattern that needs them.
- Use foreign keys and enable `PRAGMA foreign_keys = ON` for local SQLite connections.
- Store booleans as integer `0` or `1`.
- Store dates as ISO-8601 text unless there is a clear reason to use Unix epoch integers.
- Store money as integer minor units, never floating point.

Migration template:

```sql
BEGIN;

CREATE TABLE example_records (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX example_records_workspace_id_idx
  ON example_records(workspace_id);

COMMIT;
```

Reason: SQLite is reliable when schema changes are explicit and conservative. The dangerous cases are usually hidden destructive migrations, implicit type coercion, and missing indexes.

## Database Access

`lib/db/client.ts` exposes a small adapter:

```ts
export interface DatabaseClient {
  execute<T>(sql: string, params?: unknown[]): Promise<T[]>;
  executeOne<T>(sql: string, params?: unknown[]): Promise<T | null>;
  transaction<T>(fn: (tx: DatabaseClient) => Promise<T>): Promise<T>;
}
```

Use parameterized SQL for all dynamic values:

```ts
await db.execute(
  "select * from workspaces where slug = ? and deleted_at is null",
  [slug],
);
```

Never build SQL by concatenating user input.

Reason: a small adapter keeps the code portable between `better-sqlite3` and Turso while preserving explicit SQL.

## Server Actions

Server Actions must:

- Start with `"use server"`.
- Parse input with Zod.
- Check authentication before touching user-owned data.
- Check authorization before writes.
- Return a typed result instead of throwing for expected validation errors.
- Call `revalidatePath` or `revalidateTag` after writes that affect rendered pages.

Pattern:

```ts
"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { requireUser } from "@/lib/auth/session";
import { canManageWorkspace } from "@/lib/permissions";
import { updateWorkspaceName } from "@/lib/db/queries/workspaces";

const schema = z.object({
  workspaceId: z.string().min(1),
  name: z.string().min(2).max(80),
});

export async function updateWorkspaceNameAction(input: unknown) {
  const parsed = schema.safeParse(input);
  if (!parsed.success) {
    return { ok: false, error: "Invalid workspace name" } as const;
  }

  const user = await requireUser();
  await canManageWorkspace(user.id, parsed.data.workspaceId);
  await updateWorkspaceName(parsed.data.workspaceId, parsed.data.name);
  revalidatePath("/settings");

  return { ok: true } as const;
}
```

Reason: this keeps form behavior predictable and prevents pages from learning database details.

## Component Patterns

Default to Server Components.

Use Client Components only when a component needs:

- `useState`, `useEffect`, or browser-only APIs.
- Focus management or keyboard shortcuts.
- Optimistic UI state.
- Third-party client-only widgets.

Rules:

- Keep Client Components small and leaf-level.
- Pass serializable props from Server Components to Client Components.
- Do not import `lib/db`, `fs`, secrets, or server-only modules into Client Components.
- Put loading states in `loading.tsx` or inside the component that owns the async boundary.
- Put recoverable route errors in `error.tsx`.

Reason: Server Components reduce shipped JavaScript and keep data access on the server.

## Route Handlers

Use route handlers for external HTTP consumers, webhooks, and health checks. Do not use them as an internal service layer for app pages.

Rules:

- Validate request bodies with Zod.
- Verify webhook signatures before parsing trusted business fields.
- Return stable error shapes: `{ "error": { "code": "...", "message": "..." } }`.
- Do not leak raw exception messages to users.

Reason: external APIs need stable contracts, while internal pages should use direct functions.

## Auth And Permissions

- `requireUser()` returns the authenticated user or redirects/throws an auth error.
- `requireWorkspaceRole(userId, workspaceId, role)` enforces workspace permissions.
- Authorization checks live in `lib/permissions.ts`.
- Pages may hide controls based on permissions, but server code must still enforce the permission.

Reason: hidden buttons are not security. Server-side permission checks are.

## Error Handling

Use typed application errors for expected failures:

```ts
export class AppError extends Error {
  constructor(
    public code: string,
    message: string,
    public status = 400,
  ) {
    super(message);
  }
}
```

Rules:

- Expected validation and permission failures return user-safe messages.
- Unexpected errors are logged with request context and return a generic message.
- Do not swallow errors in catch blocks.

Reason: support needs enough context to debug without exposing internals to users.

## Testing Rules

Unit test:

- Zod schemas.
- Permission helpers.
- Query functions using a temporary SQLite database.
- Server Actions with mocked auth/session boundaries.

E2E test:

- Signup/login.
- Create workspace.
- Invite member.
- Upgrade or billing-gated flow if billing exists.
- Primary CRUD workflow for the product.

SQLite test rule:

- Each test gets an isolated temporary database.
- Migrations run before test setup.
- Tests assert database state after mutations.

Reason: SaaS bugs usually happen where permissions, persistence, and UI flow meet.

## Pull Request Checklist

Before opening a pull request:

- Run `pnpm lint`.
- Run `pnpm typecheck`.
- Run relevant unit tests.
- Run relevant Playwright tests for changed flows.
- Include migration notes if the database changed.
- Include screenshots for UI changes.
- Confirm no secrets are committed.

## What We Do Not Do

- Do not put SQL inside React components. Reason: it couples rendering to persistence and makes tests brittle.
- Do not use `any` to bypass TypeScript. Reason: it hides the exact contract that future changes depend on.
- Do not add a new state library for simple form or page state. Reason: React and URL state are enough for most SaaS workflows.
- Do not create API routes for internal Server Component reads. Reason: direct imports are faster and easier to secure.
- Do not write destructive migrations casually. Reason: SQLite migrations are simple, but data recovery is not.
- Do not import server-only modules into Client Components. Reason: it can leak secrets or break the client bundle.
- Do not duplicate permission logic in individual pages. Reason: one missed check becomes a production access bug.
- Do not store money as floats. Reason: rounding errors create billing defects.
- Do not add dependencies before checking whether the platform already solves the problem. Reason: dependency cost compounds over time.

## Default Implementation Behavior

When asked to build a feature:

1. Locate the route in `app/`.
2. Identify the data model and migration impact.
3. Add or update Zod schemas.
4. Add query functions in `lib/db/queries/`.
5. Add Server Actions in `lib/actions/`.
6. Render through Server Components.
7. Use small Client Components only for interaction.
8. Add tests around the boundary most likely to break.

If a requirement is ambiguous, choose the simplest secure SaaS default and document the assumption in the pull request.
