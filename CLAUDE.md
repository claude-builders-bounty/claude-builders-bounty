# CLAUDE.md

This file gives Claude Code the project context for a production Next.js 15 SaaS app using the App Router and SQLite. Follow these rules unless the user explicitly asks for a different architecture.

## Product Assumptions

- This is a multi-page SaaS application, not a marketing-only website.
- Server-rendered routes are the default. Client components are used only for browser-only interaction.
- SQLite is the primary database. Use `better-sqlite3` for embedded/local deployments or Turso/libSQL when a managed remote SQLite service is required.
- Authentication, billing, and email may be present, but do not invent vendor-specific integrations until the user confirms the provider.
- Prefer boring, explicit code over clever abstractions. This project should be easy to operate and debug.

## Stack

- Next.js 15 with App Router.
- React Server Components by default.
- TypeScript in strict mode.
- SQLite through a small database access layer.
- SQL migrations committed to the repository.
- Zod for request/input validation when validation is needed.
- Vitest for unit tests and Playwright for end-to-end tests when user-facing flows are changed.

## Project Structure

Use this structure unless the repository already has a clear equivalent pattern:

```txt
app/
  (auth)/
  (dashboard)/
  api/
  layout.tsx
  page.tsx
components/
  ui/
  forms/
  charts/
db/
  client.ts
  schema.ts
  migrations/
  queries/
lib/
  auth/
  billing/
  email/
  env.ts
  errors.ts
  result.ts
server/
  actions/
  services/
  jobs/
tests/
  unit/
  e2e/
public/
```

Reasons:

- `app/` owns routes, layouts, route handlers, metadata, and page composition.
- `components/` owns reusable UI. Keep business rules out of generic UI components.
- `db/` owns connection setup, migrations, schema helpers, and query modules.
- `server/` owns server actions and business workflows that coordinate multiple modules.
- `lib/` owns provider adapters and small shared utilities.

## Naming Rules

- Files and folders use kebab-case: `invoice-list.tsx`, `create-checkout-session.ts`.
- React components use PascalCase exports: `InvoiceList`.
- Server actions start with a verb: `createInvoiceAction`, `archiveWorkspaceAction`.
- Query functions describe returned data: `getWorkspaceBySlug`, `listInvoicesForWorkspace`.
- Mutations describe the write: `insertInvoice`, `markInvoicePaid`, `deleteInvite`.
- Boolean fields and variables use clear predicates: `isActive`, `hasAccess`, `canInvite`.
- Database tables use plural snake_case: `users`, `workspaces`, `workspace_members`.
- Database columns use snake_case: `created_at`, `workspace_id`, `stripe_customer_id`.

Reason: predictable naming lets Claude navigate the project without asking where a concern belongs.

## Development Commands

Use the repository's package manager. If none is established, prefer `pnpm`.

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm db:migrate
pnpm db:studio
```

Expected scripts:

```json
{
  "dev": "next dev",
  "build": "next build",
  "start": "next start",
  "lint": "next lint",
  "typecheck": "tsc --noEmit",
  "test": "vitest run",
  "test:e2e": "playwright test",
  "db:migrate": "tsx db/migrate.ts",
  "db:studio": "drizzle-kit studio"
}
```

If the repo uses npm, yarn, or bun already, keep that tool. Do not switch package managers as part of an unrelated change.

## Environment Variables

Read environment variables from one typed module only:

```ts
// lib/env.ts
import { z } from "zod";

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]),
  DATABASE_URL: z.string().min(1),
  APP_URL: z.string().url(),
});

export const env = envSchema.parse(process.env);
```

Rules:

- Never read `process.env` directly in feature code.
- Add new variables to `.env.example` and `lib/env.ts` together.
- Server-only secrets must never cross into Client Components.
- Use explicit public variables with the `NEXT_PUBLIC_` prefix only when the browser needs them.

Reason: one typed environment module prevents missing secret bugs and accidental client leaks.

## Database Access

Keep all database access behind query or repository functions. Do not scatter SQL across pages and components.

```ts
// db/client.ts
import Database from "better-sqlite3";
import { env } from "@/lib/env";

export const db = new Database(env.DATABASE_URL);
db.pragma("journal_mode = WAL");
db.pragma("foreign_keys = ON");
```

Rules:

- Enable `foreign_keys = ON` for every SQLite connection.
- Use WAL mode for local embedded SQLite unless the deployment environment forbids it.
- Keep one statement per query function unless a transaction is required.
- Wrap multi-step writes in transactions.
- Validate untrusted input before calling database mutations.
- Return plain objects from database modules, not framework-specific response objects.

Reason: SQLite is reliable when constraints, transactions, and connection behavior are explicit.

## Migrations

Migration files live in `db/migrations/` and are committed.

Use timestamped migration names:

```txt
202606241030_create_workspaces.sql
202606241145_add_workspace_invites.sql
```

Rules:

- Never edit a migration that has already been merged or deployed.
- Create a new migration for every schema change.
- Every table has `id`, `created_at`, and `updated_at` unless there is a strong reason not to.
- Use foreign keys for ownership and membership relationships.
- Add indexes for foreign keys and common lookup columns.
- Do not rely on application code for uniqueness that the database can enforce.
- Backfills must be idempotent.

Recommended table pattern:

```sql
CREATE TABLE workspaces (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE workspace_members (
  workspace_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'member')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (workspace_id, user_id),
  FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_workspace_members_user_id ON workspace_members(user_id);
```

Reason: migrations are production history. Editing history creates drift between developer and deployed databases.

## Server Components And Client Components

Default to Server Components.

Use Client Components only when code needs:

- Local interactive state.
- Browser APIs.
- Effects.
- Event handlers.
- Third-party UI libraries that require the browser.

Rules:

- Keep `"use client"` files small and leaf-level.
- Do not import server-only modules into Client Components.
- Fetch initial data in Server Components, then pass minimal props to Client Components.
- Prefer server actions or route handlers for writes.

Reason: Server Components reduce bundle size and keep secrets on the server.

## Server Actions

Put server actions in `server/actions/`.

Rules:

- Each action validates input.
- Each action checks authorization before mutating data.
- Each action returns a serializable result.
- Each action revalidates affected paths or tags after writes.
- Do not expose raw database errors to users.

Pattern:

```ts
"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { requireUser } from "@/lib/auth/require-user";
import { createWorkspace } from "@/server/services/workspaces";

const schema = z.object({
  name: z.string().min(2).max(80),
});

export async function createWorkspaceAction(input: unknown) {
  const user = await requireUser();
  const parsed = schema.safeParse(input);

  if (!parsed.success) {
    return { ok: false, error: "Invalid workspace details." };
  }

  const workspace = await createWorkspace({
    ownerId: user.id,
    name: parsed.data.name,
  });

  revalidatePath("/dashboard");
  return { ok: true, workspace };
}
```

Reason: actions are a security boundary. Validation and authorization must be visible at that boundary.

## Route Handlers

Use route handlers in `app/api/` for:

- Webhooks.
- External API callbacks.
- Programmatic API access.
- File uploads or downloads.

Rules:

- Validate method, headers, and body.
- For webhooks, verify signatures before parsing or trusting payloads.
- Return `Response.json()` with stable error shapes.
- Avoid putting business logic directly in route handlers; call server services.

Reason: route handlers are integration edges and need defensive parsing.

## Authorization

Authorization checks belong close to the data or workflow being protected.

Rules:

- Never trust client-provided `userId`, `workspaceId`, or `role` without checking membership server-side.
- Use helper functions such as `requireUser`, `requireWorkspaceMember`, and `requireWorkspaceRole`.
- Pages may hide UI, but server actions and queries must enforce access.
- Prefer role checks with explicit allowed roles.

Reason: hidden buttons are not security. Every write path must be protected.

## Error Handling

Use user-safe messages at the UI boundary and structured logs at the server boundary.

Rules:

- Expected validation failures return typed results.
- Unexpected failures throw or log once at the boundary.
- Do not swallow errors silently.
- Do not leak stack traces, SQL, secrets, or provider payloads to users.

Recommended result shape:

```ts
type ActionResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string; fieldErrors?: Record<string, string[]> };
```

Reason: predictable result shapes make forms and tests simpler.

## UI Patterns

Build interfaces for repeated daily use.

Rules:

- Use dense, scannable layouts for dashboards.
- Use real form labels and accessible error messages.
- Use loading, empty, error, and success states for user-facing data.
- Use semantic buttons and links.
- Keep destructive actions behind confirmation.
- Do not add marketing hero sections inside authenticated app areas.

Reason: SaaS users need speed and clarity more than decoration.

## Data Fetching And Caching

Rules:

- Fetch user-specific data on the server.
- Use `cache()` only for reads that are safe to memoize within a request.
- Use `revalidatePath` or `revalidateTag` after writes.
- Do not cache permission-sensitive data globally.
- Prefer small query functions over one large "get everything" query.

Reason: caching bugs in SaaS apps often become privacy bugs.

## Testing

Add tests proportional to risk.

Minimum expectations:

- Query functions with non-trivial filters have unit tests.
- Server actions with validation or authorization have tests.
- Critical flows such as signup, login, checkout, invite, and settings have Playwright tests when modified.
- Migration changes are tested against a fresh database.

Rules:

- Use a separate test database.
- Reset database state between tests.
- Test behavior, not implementation details.
- Do not mock the database for query tests unless the repository already does so.

Reason: database and authorization bugs are expensive in SaaS applications.

## Performance Rules

- Avoid Client Components for static display.
- Do not fetch the same data separately in nested components.
- Paginate lists that can grow beyond 100 rows.
- Add indexes before adding filters to large tables.
- Avoid expensive work in layouts that run for many pages.

Reason: most SaaS performance problems are repeated queries, oversized client bundles, and unbounded lists.

## Security Rules

- Treat every form input, route param, search param, cookie, and webhook payload as untrusted.
- Validate inputs with Zod or equivalent existing project tooling.
- Escape or parameterize every SQL value. Never build SQL by string concatenation with user input.
- Store secrets only in environment variables or the configured secret manager.
- Do not log tokens, cookies, API keys, webhook secrets, or payment payloads.
- Rate-limit public write endpoints if the app exposes them.
- Use secure, httpOnly cookies for sessions.

Reason: small SaaS apps are still production apps with real user data.

## Anti-Patterns

Avoid these unless the user explicitly requests them:

- Adding a global state library for simple page state.
- Marking a whole route tree with `"use client"`.
- Running database queries inside generic UI components.
- Creating migrations by editing old migration files.
- Accepting `userId` from the client for authorization.
- Returning raw provider errors to users.
- Creating a new abstraction before there are at least two real call sites.
- Mixing billing, auth, and domain logic in one route handler.
- Switching package managers during an unrelated change.
- Adding background jobs that only work while `next dev` is running.

## Implementation Checklist

Before finishing a change:

- Run linting.
- Run type checks.
- Run relevant unit tests.
- Run relevant e2e tests for user-facing flows.
- Confirm migrations apply to a fresh database.
- Confirm secrets are not exposed to the client.
- Confirm authorization is enforced server-side.
- Update `.env.example` when environment variables change.
- Update this file only when project conventions change.

## How Claude Should Work In This Repo

1. Inspect existing patterns before editing.
2. Keep changes scoped to the user request.
3. Prefer the smallest complete implementation.
4. Use existing utilities and components before adding new ones.
5. Add tests when behavior, database writes, permissions, or user flows change.
6. Explain tradeoffs briefly when there are multiple reasonable approaches.
7. Do not claim a command passed unless it was actually run.
8. If a command cannot run locally, state the blocker and provide the exact command the user should run.

Reason: consistency with the existing repository matters more than applying this template mechanically.
