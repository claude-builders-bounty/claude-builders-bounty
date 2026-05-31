# CLAUDE.md - Next.js 15 + SQLite SaaS

## Stack

- Next.js 15 App Router with TypeScript.
- React Server Components by default; client components only for browser state, event handlers, or browser-only APIs.
- SQLite through `better-sqlite3` for local/single-node deployments or Turso/libSQL when the app needs hosted SQLite.
- Drizzle ORM is preferred for schema, migrations, and typed query helpers.
- Server Actions or route handlers own writes; UI components do not talk to the database directly.
- Auth, billing, and email providers must be isolated behind small service modules.

Reason: this keeps the app deployable as a normal Next.js project while preserving the simplicity and auditability of SQLite.

## Project Structure

```text
app/
  (marketing)/
  (app)/
    dashboard/
    settings/
  api/
components/
  ui/
  forms/
db/
  schema.ts
  client.ts
  migrations/
  queries/
lib/
  auth/
  billing/
  email/
  env.ts
  errors.ts
server/
  actions/
  jobs/
tests/
```

Rules:

- Put route-specific UI under `app/`.
- Put reusable primitives under `components/ui`.
- Put feature-specific form components under `components/forms`.
- Put database schema only in `db/schema.ts`.
- Put SQL access helpers in `db/queries/*`.
- Put Server Actions in `server/actions/*`.
- Put scheduled/background work in `server/jobs/*`.

Reason: App Router file conventions stay readable, and database access remains easy to find during reviews.

## Commands

Use these conventional scripts:

```bash
npm run dev
npm run lint
npm run typecheck
npm run test
npm run db:generate
npm run db:migrate
npm run db:studio
```

If a script is missing, add it before relying on it in docs, CI, or automation.

## Environment

All environment access goes through `lib/env.ts`.

```ts
import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().min(1),
  AUTH_SECRET: z.string().min(32),
  STRIPE_SECRET_KEY: z.string().optional(),
});

export const env = envSchema.parse(process.env);
```

Rules:

- Do not read `process.env` outside `lib/env.ts`.
- Validate required variables at startup.
- Keep `.env.example` current whenever adding a variable.

Reason: missing or misspelled configuration should fail early instead of creating runtime-only bugs.

## Database

Use Drizzle schema as the source of truth.

```ts
import { integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: text("id").primaryKey(),
  email: text("email").notNull().unique(),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull(),
});
```

Rules:

- Every table has a stable primary key.
- Use `createdAt` and `updatedAt` where records can change.
- Store money as integer minor units, never floats.
- Use explicit unique constraints for user-owned external identifiers.
- Add indexes for foreign keys and common dashboard filters.
- Keep transactions close to the write operation.

Reason: SQLite is reliable when schema and write paths are explicit; implicit data rules become hard to repair later.

## Migrations

Rules:

- Never edit a migration that has already shipped.
- Generate migrations from schema changes with `npm run db:generate`.
- Review generated SQL before committing.
- Apply migrations locally with `npm run db:migrate`.
- Include destructive migration notes in the PR description.

Reason: migration history is operational history. Rewriting it makes local, staging, and production databases disagree.

## Query Patterns

Use query helpers instead of inline database access inside routes.

```ts
// db/queries/users.ts
import { eq } from "drizzle-orm";
import { db } from "@/db/client";
import { users } from "@/db/schema";

export function getUserByEmail(email: string) {
  return db.query.users.findFirst({
    where: eq(users.email, email),
  });
}
```

Rules:

- Reads live in `db/queries/*`.
- Writes live in Server Actions, route handlers, or service modules.
- Return plain objects, not database clients or statements.
- Keep pagination explicit with `limit`, `offset` or cursor fields.

Reason: the UI should not need to know SQL details, and query reuse should not hide write side effects.

## Server Actions

Server Actions must validate input and return predictable results.

```ts
"use server";

import { z } from "zod";

const schema = z.object({
  name: z.string().min(1).max(80),
});

export async function updateWorkspaceName(input: unknown) {
  const parsed = schema.safeParse(input);
  if (!parsed.success) {
    return { ok: false, error: "Invalid workspace name" };
  }

  // write in a transaction when multiple rows change
  return { ok: true };
}
```

Rules:

- Validate every external input with Zod or equivalent.
- Check authorization before database writes.
- Use transactions for multi-step writes.
- Return serializable objects.
- Do not throw for expected validation errors.

Reason: Server Actions are public write boundaries and need the same rigor as API routes.

## Components

Default to Server Components.

Use `"use client"` only when the file needs:

- `useState`, `useReducer`, or `useEffect`
- DOM events
- browser-only APIs
- interactive third-party widgets

Rules:

- Keep client components small and pass plain serialized props.
- Do not import database, filesystem, or server-only modules into client components.
- Use accessible form labels and error messages.
- Keep loading, empty, and error states explicit.

Reason: App Router performance depends on keeping client JavaScript small and server-only code on the server.

## Auth And Authorization

Rules:

- Authenticate once in a server helper such as `requireUser()`.
- Authorize per resource, not only per route.
- Store role and workspace membership in the database.
- Do not trust client-provided user IDs, workspace IDs, prices, roles, or billing state.

Reason: SaaS bugs are often authorization bugs, especially in multi-tenant dashboards.

## Billing

Rules:

- Stripe or billing provider calls live in `lib/billing`.
- Webhooks must be idempotent.
- Store provider event IDs and ignore duplicates.
- Treat local subscription state as a cache of provider truth.
- Never unlock paid features from client-side state alone.

Reason: billing systems retry and reorder events; idempotency prevents duplicate grants and inconsistent access.

## Errors And Logging

Rules:

- Use typed domain errors for expected failures.
- Log unexpected server errors with request or job context.
- Do not log secrets, raw tokens, full payment payloads, or private user content.
- Show generic user-facing messages for unexpected failures.

Reason: logs should help debug production without becoming a security liability.

## Testing

Minimum checks before a PR:

```bash
npm run lint
npm run typecheck
npm run test
npm run db:migrate
```

Rules:

- Test query helpers against a temporary SQLite database.
- Test Server Actions for validation, authorization, and success paths.
- Add regression tests for billing webhooks and permission bugs.
- Keep component tests focused on user-visible states.

Reason: SQLite makes realistic integration tests cheap, so critical data behavior should be tested directly.

## What We Do Not Do

- Do not put database calls in React client components.
- Do not mutate data from GET routes.
- Do not store money as floats.
- Do not skip migrations and patch production manually.
- Do not read `process.env` throughout the app.
- Do not rely on middleware alone for authorization.
- Do not create generic "utils" dumping grounds; name modules by domain.
- Do not introduce global state libraries unless local state and URL state are insufficient.

Reason: these shortcuts save minutes during implementation and cost hours during debugging or incident response.

## PR Checklist

- Schema changes include reviewed migration SQL.
- New env vars are added to `.env.example` and `lib/env.ts`.
- Server writes validate input and authorization.
- Billing/webhook changes are idempotent.
- Tests cover the main data path and at least one failure path.
- README or setup docs are updated when commands change.
