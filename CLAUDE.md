# CLAUDE.md — Next.js 15 + SQLite SaaS

This file tells Claude Code how to work inside a production-minded SaaS project built with Next.js 15 App Router, TypeScript, SQLite, and either `better-sqlite3` for local/server deployments or Turso/libSQL for hosted edge-friendly SQLite.

## Stack and Versions

- Framework: Next.js 15 App Router.
- Language: TypeScript in strict mode.
- UI: React Server Components by default; Client Components only where browser state or browser APIs are required.
- Styling: Tailwind CSS plus small component-level utilities. Avoid global CSS except tokens, resets, and third-party overrides.
- Database: SQLite.
  - Local/server runtime: `better-sqlite3`.
  - Hosted/serverless runtime: Turso/libSQL.
- Validation: Zod at every trust boundary.
- Tests: Vitest for unit tests, Playwright for browser flows when needed.
- Package manager: use the lockfile already present. If no lockfile exists, prefer `pnpm`.

Reason: this stack keeps the app simple, typed, cheap to deploy, and easy to reason about. Do not introduce Postgres, Prisma, Redis, tRPC, or a state manager unless the task explicitly requires it.

## Core Rules

1. Prefer boring server-side code.
   - Use Server Components and Server Actions for data reads/writes.
   - Use Route Handlers only for webhooks, external API endpoints, or non-form clients.
   - Reason: fewer client bundles, fewer loading states, fewer security mistakes.

2. Keep SQLite as the source of truth.
   - Do not add cache layers until there is a measured bottleneck.
   - Do not duplicate relational data into JSON files.
   - Reason: SQLite is fast enough for this SaaS shape and easier to back up.

3. Validate input twice when needed.
   - Client validation is for user experience.
   - Server validation is mandatory for safety.
   - Reason: users and bots can bypass the browser.

4. Make every mutation explicit.
   - Mutations live in `app/**/actions.ts`, `server/actions/**`, or route handlers.
   - Every mutation checks auth/ownership before writing.
   - Reason: SaaS bugs are usually permission bugs.

5. Keep components small and directional.
   - Page files compose features.
   - Feature components render UI.
   - Server modules load data.
   - Reason: Claude should not have to inspect the whole app to make a safe change.

## Folder Structure

Use this layout unless the existing project already has a clear equivalent:

```text
app/
  (marketing)/
    page.tsx
  (app)/
    dashboard/
      page.tsx
      loading.tsx
      error.tsx
      actions.ts
  api/
    webhooks/
      stripe/route.ts
components/
  ui/                 # reusable primitives: Button, Input, Dialog
  layout/             # nav, shell, page headers
features/
  billing/
    components/
    queries.ts
    actions.ts
    schema.ts
  projects/
    components/
    queries.ts
    actions.ts
    schema.ts
server/
  db/
    index.ts          # DB connection wrapper
    migrations/
    schema.sql
    migrate.ts
  auth/
    session.ts
  env.ts
lib/
  dates.ts
  format.ts
  result.ts
tests/
  unit/
  e2e/
```

Reason: route folders stay thin, domain logic is grouped by feature, and database code has one obvious home.

## Naming Conventions

- Files:
  - React components: `PascalCase.tsx`.
  - Server helpers: `camelCase.ts`.
  - Schemas: `schema.ts` inside the feature.
  - Queries: `queries.ts`.
  - Mutations/server actions: `actions.ts`.
- Components:
  - Use nouns: `ProjectCard`, `BillingBanner`, `UserMenu`.
  - Avoid vague names like `MainView`, `DataBox`, or `ThingItem`.
- Database:
  - Tables: snake_case plural nouns, e.g. `users`, `projects`, `subscription_events`.
  - Columns: snake_case, e.g. `created_at`, `owner_id`, `stripe_customer_id`.
  - TypeScript objects: camelCase after mapping from DB rows.
- Booleans:
  - Prefix with `is`, `has`, `can`, or `should`.

Reason: predictable naming lets Claude find the right file and prevents duplicate abstractions.

## Development Commands

Use the scripts in `package.json`. If missing, add these before inventing alternatives:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "typecheck": "tsc --noEmit",
    "lint": "next lint",
    "test": "vitest run",
    "test:watch": "vitest",
    "db:migrate": "tsx server/db/migrate.ts",
    "db:reset": "rm -f local.db && pnpm db:migrate"
  }
}
```

Before finishing a code task, run the cheapest relevant checks:

```bash
pnpm typecheck
pnpm test
pnpm build
```

If a command is missing or fails because dependencies are not installed, explain the blocker and run the next available check.

## Environment Variables

All environment reads go through `server/env.ts`.

```ts
import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().default("file:local.db"),
  NEXT_PUBLIC_APP_URL: z.string().url().default("http://localhost:3000"),
  SESSION_SECRET: z.string().min(32),
});

export const env = envSchema.parse(process.env);
```

Rules:

- Never read `process.env` directly outside `server/env.ts`.
- Never expose secrets through `NEXT_PUBLIC_` variables.
- Never commit `.env`, `.env.local`, database files, or production dumps.

Reason: environment drift causes deployment bugs and accidental secret leaks.

## SQLite Connection Rules

For `better-sqlite3`, use one process-level connection wrapper:

```ts
// server/db/index.ts
import Database from "better-sqlite3";
import { env } from "@/server/env";

const globalForDb = globalThis as unknown as { db?: Database.Database };

export const db =
  globalForDb.db ??
  new Database(env.DATABASE_URL.replace(/^file:/, ""), {
    fileMustExist: false,
  });

db.pragma("journal_mode = WAL");
db.pragma("foreign_keys = ON");

if (process.env.NODE_ENV !== "production") globalForDb.db = db;
```

Rules:

- Always enable `foreign_keys`.
- Prefer WAL mode for local/server deployments.
- Use prepared statements for user-provided values.
- Do not concatenate SQL with raw user input.
- Keep transactions short and explicit.

Reason: SQLite is safe and fast when constraints are enforced and queries are parameterized.

## SQL and Migration Conventions

Migrations live in `server/db/migrations` and are append-only.

File names:

```text
0001_initial.sql
0002_add_projects.sql
0003_add_billing_events.sql
```

Migration rules:

- Never edit a migration that has already shipped. Add a new migration.
- Every table has:
  - `id text primary key`
  - `created_at text not null default CURRENT_TIMESTAMP`
  - `updated_at text not null default CURRENT_TIMESTAMP` when records are mutable.
- Use foreign keys with `on delete cascade` only when child data has no standalone value.
- Add indexes for every foreign key and common lookup column.
- Store timestamps as ISO-8601 text unless the existing project uses Unix integers consistently.
- Avoid JSON columns for data that needs filtering, joining, or uniqueness.

Example:

```sql
create table projects (
  id text primary key,
  owner_id text not null references users(id) on delete cascade,
  name text not null,
  slug text not null,
  created_at text not null default CURRENT_TIMESTAMP,
  updated_at text not null default CURRENT_TIMESTAMP,
  unique(owner_id, slug)
);

create index projects_owner_id_idx on projects(owner_id);
```

Reason: explicit migrations make local development, CI, and production recovery predictable.

## Query Patterns

Put read functions in `features/<feature>/queries.ts`.

```ts
import { db } from "@/server/db";

export function getProjectForUser(projectId: string, userId: string) {
  return db
    .prepare(
      `select id, owner_id, name, slug, created_at
       from projects
       where id = ? and owner_id = ?`
    )
    .get(projectId, userId);
}
```

Rules:

- Queries return plain objects, not database driver internals.
- Permission-aware queries include the user or tenant id in the `where` clause.
- Avoid loading all rows and filtering in JavaScript.
- Keep `select *` out of app code.

Reason: permission checks in SQL are harder to accidentally bypass.

## Mutation Patterns

Use Server Actions for form-backed app mutations.

```ts
"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { db } from "@/server/db";
import { requireUser } from "@/server/auth/session";

const createProjectSchema = z.object({
  name: z.string().trim().min(2).max(80),
});

export async function createProjectAction(formData: FormData) {
  const user = await requireUser();
  const parsed = createProjectSchema.safeParse({
    name: formData.get("name"),
  });

  if (!parsed.success) {
    return { ok: false, error: "Project name is invalid." };
  }

  const id = crypto.randomUUID();
  db.prepare(
    `insert into projects (id, owner_id, name, slug)
     values (?, ?, ?, ?)`
  ).run(id, user.id, parsed.data.name, slugify(parsed.data.name));

  revalidatePath("/dashboard");
  return { ok: true, projectId: id };
}
```

Rules:

- Auth first, validation second, write third, revalidate last.
- Return small typed results. Do not throw for expected validation errors.
- Use transactions when writing more than one related record.
- Revalidate the narrowest route possible.

Reason: this flow makes failures visible and keeps cached pages correct.

## Component Patterns

Default to Server Components.

```tsx
export default async function DashboardPage() {
  const user = await requireUser();
  const projects = await listProjectsForUser(user.id);

  return <ProjectList projects={projects} />;
}
```

Use Client Components only for:

- local UI state,
- event handlers,
- browser-only APIs,
- optimistic interactions,
- third-party widgets that require the browser.

Client Component rules:

- Put `"use client"` at the smallest possible boundary.
- Pass serialized data only.
- Do not import `server/**`, database modules, or secret env into client files.

Reason: small client boundaries keep bundles light and prevent secret leaks.

## Forms

- Use native forms with Server Actions when possible.
- Disable submit buttons while pending.
- Show field-level errors for user-fixable problems.
- Use optimistic UI only when rollback is simple.

Reason: native forms work without heavy client state and degrade gracefully.

## Auth and Authorization

- `requireUser()` is required before reading private app data.
- Every tenant-owned table includes `owner_id` or `organization_id`.
- Never trust an id from params without checking ownership.
- Admin checks must be explicit and server-side.

Reason: SaaS incidents usually come from missing ownership checks, not missing login checks.

## Error Handling

- Use `notFound()` when a private record is missing or not owned by the current user.
- Use `redirect()` only for expected navigation flows.
- Use route-level `error.tsx` for unexpected UI failures.
- Log server errors without leaking secrets.

Reason: users should see safe errors; developers should see useful logs.

## Testing Rules

Unit tests should cover:

- validators,
- slug/format utilities,
- SQL query helpers,
- permission-aware lookups,
- migration behavior where practical.

For every database bug fix, add a regression test or a migration smoke test.

Example test shape:

```ts
import { describe, expect, it } from "vitest";
import { createProjectSchema } from "@/features/projects/schema";

describe("createProjectSchema", () => {
  it("rejects empty project names", () => {
    expect(createProjectSchema.safeParse({ name: "" }).success).toBe(false);
  });
});
```

Reason: small tests are faster and more useful than broad snapshots.

## Security Rules

- Never expose secrets to Client Components.
- Never build SQL with string concatenation from user input.
- Never skip ownership checks.
- Never log raw webhook payloads if they can include customer data.
- Verify webhook signatures before processing events.
- Use secure, httpOnly cookies for sessions.

Reason: the app handles accounts, billing, and private user data.

## Performance Rules

- Start with simple SQL and proper indexes.
- Use pagination for tables that can exceed 100 rows.
- Avoid fetching data in Client Components after rendering when a Server Component can load it first.
- Avoid `Promise.all` for writes that should be transactional.
- Measure before adding queues, caches, or background systems.

Reason: premature infrastructure makes a small SaaS harder to operate.

## Anti-Patterns to Avoid

- Do not add Prisma just for schema convenience.
  - Reason: this template is intentionally SQLite-first and migration-light.
- Do not put business logic in `app/page.tsx` files.
  - Reason: pages should compose, not own the domain.
- Do not create a `utils.ts` junk drawer.
  - Reason: helpers should live near the feature that owns them.
- Do not use API routes for same-app form submissions by default.
  - Reason: Server Actions are simpler and typed enough for this use case.
- Do not create giant Client Components for whole pages.
  - Reason: it bloats JavaScript and risks importing server-only code.
- Do not silently swallow database errors.
  - Reason: failed writes must be visible during development and safe in production.
- Do not add fake abstractions like repositories/services unless there are multiple real callers.
  - Reason: indirection slows Claude and humans down.

## How Claude Should Work in This Repo

When asked to make a change:

1. Read `package.json`, `server/env.ts`, `server/db/schema.sql`, and the relevant route/feature files first.
2. Identify whether the change is read-only UI, mutation, schema/migration, or external integration.
3. Make the smallest change that fits the existing structure.
4. Add or update validation and tests when behavior changes.
5. Run typecheck/tests/build in that order when available.
6. Report exactly what changed, what was checked, and any remaining risk.

Do not ask clarifying questions unless the task changes product behavior, data ownership, billing, or security boundaries.

## Definition of Done

A change is done when:

- TypeScript passes or the blocker is documented.
- Relevant tests pass or missing tests are explained.
- Database migrations are append-only and reversible by backup restore.
- Auth and ownership checks are present for private data.
- No secrets are exposed to the client.
- The final answer names files changed and commands run.

This CLAUDE.md is intentionally opinionated. Follow it unless the existing project has stronger local conventions.
