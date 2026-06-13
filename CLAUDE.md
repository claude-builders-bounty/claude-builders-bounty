# Next.js 15 + SQLite SaaS Project Guide

This project is a small SaaS application built with Next.js 15 App Router, TypeScript, SQLite, and server-first React patterns. Treat the database as the source of truth, keep business rules on the server, and ship small, reversible changes.

## Stack And Versions

- Next.js 15 with the App Router in `app/`
- React Server Components by default
- TypeScript in strict mode
- SQLite through `better-sqlite3` for local/single-node apps or Turso/libSQL for hosted SQLite
- Server Actions for trusted mutations
- Route Handlers only for public APIs, webhooks, or non-form clients
- Tailwind CSS or CSS Modules for styling, but do not mix multiple styling systems in one feature
- Zod for validating external input at server boundaries

Reason: this stack works best when rendering, validation, and persistence stay close together. Avoid client-heavy architecture unless the feature genuinely needs browser state.

## Folder Structure

Use this structure unless the existing app already has a stronger convention:

```text
app/
  (marketing)/
  (app)/
  api/
components/
  ui/
  feature-name/
db/
  client.ts
  schema.sql
  migrations/
lib/
  auth/
  billing/
  validation/
server/
  actions/
  queries/
  services/
tests/
```

Rules:

- Put page-level routes in `app/`.
- Put reusable presentational pieces in `components/`.
- Put database access in `server/queries/`; never query the database directly from UI components.
- Put mutations in `server/actions/` or `server/services/`.
- Put external provider code in `lib/<provider-or-domain>/`.
- Keep migrations in `db/migrations/` with numeric prefixes.

Reason: this separates route composition, UI reuse, data reads, and business actions without creating a large enterprise-style architecture.

## Naming Conventions

- Components: `PascalCase.tsx`
- Server actions: `verbNounAction`, for example `createWorkspaceAction`
- Queries: `getThing`, `listThings`, `findThingById`
- Services: `verbNoun`, for example `sendInviteEmail`
- Zod schemas: `ThingInputSchema`
- Database tables: `snake_case` plural nouns, for example `workspaces`
- Database columns: `snake_case`
- TypeScript variables: `camelCase`

Reason: names should reveal where code runs and whether it reads, mutates, validates, or renders.

## Database And Migration Rules

- Every schema change must have a migration file.
- Migration filenames must use this pattern: `0001_short_description.sql`.
- Migrations must be deterministic and safe to run once.
- Prefer additive migrations over destructive migrations.
- Do not rename or drop columns without a backfill plan.
- Store timestamps as ISO strings or integer milliseconds consistently; do not mix formats.
- Use foreign keys and unique constraints for business invariants.
- Keep indexes close to the query patterns they support.

Example migration:

```sql
CREATE TABLE workspaces (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  owner_user_id TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_workspaces_owner_user_id
ON workspaces(owner_user_id);
```

Reason: SQLite is simple and reliable, but it will not save the project from vague data ownership or missing constraints.

## Database Access Pattern

Use one shared database client module:

```ts
// db/client.ts
import Database from "better-sqlite3";

export const db = new Database(process.env.DATABASE_URL ?? "local.db");
db.pragma("foreign_keys = ON");
```

Keep reads in query functions:

```ts
// server/queries/workspaces.ts
import { db } from "@/db/client";

export function listWorkspacesForUser(userId: string) {
  return db
    .prepare("SELECT id, name, created_at FROM workspaces WHERE owner_user_id = ?")
    .all(userId);
}
```

Reason: this makes authorization, caching, and tests easier than scattering SQL through pages.

## Server Actions

Server Actions must:

- Validate input with Zod.
- Check authentication and authorization before writing.
- Return typed success/error objects.
- Revalidate only the routes or tags affected by the mutation.
- Keep provider side effects after validation but before final success response.

Example shape:

```ts
"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";

const CreateWorkspaceSchema = z.object({
  name: z.string().min(2).max(80),
});

export async function createWorkspaceAction(input: unknown) {
  const parsed = CreateWorkspaceSchema.safeParse(input);
  if (!parsed.success) {
    return { ok: false, error: "Invalid workspace name." };
  }

  // Check current user and insert through a service or query helper.
  revalidatePath("/dashboard");
  return { ok: true };
}
```

Reason: Server Actions are powerful, but without validation and authorization they become hidden API endpoints with weak boundaries.

## Component Patterns

- Default to Server Components.
- Add `"use client"` only for local interactivity, browser APIs, optimistic UI, or controlled form widgets.
- Keep Client Components small and pass serializable props only.
- Do not import database, filesystem, secrets, or server-only modules into Client Components.
- Prefer composition over global state.
- Use forms for mutations where possible.

Reason: App Router performs best when most of the tree remains server-rendered and data fetching stays near the route.

## Caching And Revalidation

- Cache read-heavy public data with explicit tags.
- Do not cache user-specific private data unless the cache key includes the user or tenant.
- After mutations, revalidate the smallest affected path or tag.
- Avoid broad `revalidatePath("/")` unless the whole app truly changed.

Reason: SaaS data is often tenant-scoped. Over-broad caching can leak stale or incorrect state.

## Authentication And Authorization

- Authentication answers: who is the user?
- Authorization answers: can this user perform this action on this resource?
- Check authorization in server queries and mutations, not only in navigation.
- Never trust workspace IDs, role names, or user IDs sent from the browser.
- Use membership tables for multi-tenant access.

Reason: hiding a button is not security. Every write and sensitive read needs a server-side permission check.

## Forms And Validation

- Use Zod at the server boundary.
- Mirror simple constraints in the UI for usability, but treat server validation as final.
- Return field-level errors when the form is user-facing.
- Preserve submitted values after validation errors.

Reason: good validation protects data and reduces buyer/user support issues.

## API Routes And Webhooks

Use Route Handlers for:

- Public APIs
- Payment webhooks
- OAuth callbacks
- Integrations that cannot use Server Actions

Rules:

- Verify signatures for webhooks.
- Make webhook handlers idempotent.
- Store raw event IDs to prevent duplicate processing.
- Return fast and move slow work to a background step when available.

Reason: payment and integration events are retried. Duplicate-safe handlers prevent double billing, double emails, and corrupted state.

## Error Handling

- Use expected error objects for user mistakes.
- Throw only for unexpected system failures.
- Log enough context to debug without exposing secrets or personal data.
- Do not show raw database or provider errors to users.

Reason: users need clear recovery steps, while maintainers need useful diagnostic context.

## Testing Expectations

- Test pure services and validation schemas first.
- Add integration tests around database queries that enforce business rules.
- Test critical Server Actions with success and failure paths.
- Use a temporary SQLite database for tests.
- Do not mock the database for logic that depends on constraints.

Reason: SQLite constraints and migrations are part of the product behavior.

## Dev Commands

Keep commands boring and predictable:

```bash
npm run dev
npm run lint
npm run typecheck
npm run test
npm run db:migrate
```

If a command does not exist yet, add it before relying on it in documentation or CI.

Reason: agents and humans both move faster when the project has a small command surface.

## What We Do Not Do

- Do not put SQL inside React components, because it mixes rendering with persistence.
- Do not create generic helper layers before there is repeated complexity.
- Do not use Client Components for whole pages just to simplify state.
- Do not store secrets in client-visible environment variables.
- Do not skip migrations and edit production tables manually.
- Do not add a second ORM/query style without a migration plan.
- Do not make every route dynamic if only one small component needs fresh data.
- Do not use fake optimistic success for billing, auth, or destructive actions.

Reason: these shortcuts feel fast early and become expensive when users, billing, and data ownership arrive.

## Change Checklist

Before finishing a task:

1. Run lint, typecheck, and relevant tests.
2. Confirm database migrations are included when schema changes.
3. Confirm all mutations validate input and check authorization.
4. Confirm user-facing errors are readable.
5. Confirm no server-only code is imported into Client Components.
6. Update README or feature docs when setup or behavior changes.

Reason: small SaaS projects fail from loose edges more often than from missing architecture.
