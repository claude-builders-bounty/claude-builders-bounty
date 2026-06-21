# CLAUDE.md: Next.js 15 + SQLite SaaS

You are working in a production-oriented SaaS app built with Next.js 15 App Router, TypeScript, SQLite, and either `better-sqlite3` for serverful deployments or Turso/libSQL for hosted SQLite.

Follow these rules unless the user explicitly asks for a different architecture.

## Stack & Versions

- Use Next.js 15 with the App Router under `app/`.
  Reason: route handlers, layouts, metadata, Server Components, and Server Actions belong to the same routing model.
- Use TypeScript in strict mode.
  Reason: database rows, auth sessions, billing states, and form payloads need type boundaries before they reach user-facing pages.
- Use SQLite as the system of record.
  Reason: this template is for small SaaS products where simple relational data, local development speed, and easy backups beat distributed database complexity.
- Prefer `better-sqlite3` for Node.js/serverful runtimes and Turso/libSQL for serverless or edge-adjacent hosting.
  Reason: `better-sqlite3` is synchronous and reliable in long-lived Node processes, while Turso/libSQL is designed for remote SQLite access.
- Use Zod for validating form, route handler, and environment inputs.
  Reason: TypeScript types disappear at runtime; paid SaaS flows need runtime guards.
- Use Tailwind CSS only for styling primitives unless an existing design system already exists.
  Reason: SaaS UI should stay predictable, dense, and easy to scan.

## Folder Structure

Use this structure for greenfield projects:

```text
app/
  (marketing)/
    page.tsx
  (app)/
    dashboard/
      page.tsx
    settings/
      page.tsx
  api/
    health/route.ts
  layout.tsx
  globals.css
components/
  ui/
  forms/
  layout/
db/
  client.ts
  schema.sql
  migrations/
    0001_initial.sql
  queries/
    users.ts
    subscriptions.ts
lib/
  auth/
  billing/
  env.ts
  result.ts
server/
  actions/
  services/
tests/
  fixtures/
```

Rules:

- Put route UI in `app/` and reusable UI in `components/`.
  Reason: route files should describe screens; shared widgets should not know about routing.
- Put SQL schema, migrations, and typed query functions in `db/`.
  Reason: database behavior needs one obvious home and should not be scattered through components.
- Put use-case orchestration in `server/services/`.
  Reason: services make billing, auth, and multi-step database writes testable without rendering pages.
- Put Server Actions in `server/actions/`.
  Reason: actions are request entrypoints; they should validate input, call services, and return typed results.
- Put environment parsing in `lib/env.ts`.
  Reason: all missing or malformed configuration should fail at boot, not during a customer action.

## Naming Conventions

- Name route folders by product language: `dashboard`, `projects`, `billing`, `settings`.
  Reason: URLs are part of the product surface.
- Name Server Actions with a verb phrase: `createProjectAction`, `updateBillingEmailAction`.
  Reason: actions mutate state and should read like commands.
- Name query functions by the row or use case: `getUserByEmail`, `listProjectsForUser`, `insertSubscriptionEvent`.
  Reason: query names should reveal cardinality and ownership.
- Name service functions by business outcome: `provisionWorkspace`, `cancelSubscription`, `inviteTeamMember`.
  Reason: services should encode product behavior, not SQL mechanics.
- Use `PascalCase` for React components, `camelCase` for functions, and `SCREAMING_SNAKE_CASE` only for environment variable names.
  Reason: consistent names make generated edits easier to review.

## Dev Commands

Use or create these commands in `package.json`:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "db:migrate": "tsx db/migrate.ts",
    "db:reset": "tsx db/reset.ts",
    "test": "vitest run"
  }
}
```

Before finishing code changes, run the smallest useful set:

1. `npm run typecheck`
2. `npm run lint`
3. `npm run test` when business logic, database code, or validation changed
4. `npm run build` when routing, server/client boundaries, or config changed

## SQL / Migration Conventions

- Treat `db/schema.sql` as documentation of the latest complete schema.
  Reason: reviewers need one file that shows the current database shape.
- Treat `db/migrations/*.sql` as append-only history.
  Reason: production databases cannot replay rewritten history safely.
- Name migrations with zero-padded sequence numbers and a short purpose: `0002_add_workspace_members.sql`.
  Reason: sequence order should be obvious in file listings and reviews.
- Every migration must be idempotent where SQLite allows it.
  Reason: local resets, preview deployments, and failed deploy retries should not corrupt state.
- Wrap multi-statement data changes in explicit transactions.
  Reason: partially applied SaaS state creates billing and permission bugs.
- Add foreign keys and indexes in the migration that introduces the relationship or query.
  Reason: constraints and performance belong with the schema change that needs them.
- Enable foreign keys when opening a SQLite connection:

```ts
db.pragma("foreign_keys = ON");
```

Reason: SQLite does not enforce foreign keys unless they are enabled per connection.

- Store timestamps as ISO-8601 UTC text unless the project already standardizes on Unix milliseconds.
  Reason: ISO text is readable in SQLite shells, logs, and support exports.
- Do not interpolate user input into SQL strings.
  Reason: even internal SaaS tools eventually receive hostile input.
- Use prepared statements or libSQL parameter binding:

```ts
db.prepare("select * from users where email = ?").get(email);
```

## Data Access Pattern

Keep components away from raw SQL. Use this flow:

```text
Route or Server Action
  -> validate input with Zod
  -> call service
  -> service calls db/queries
  -> query returns typed row or domain object
```

Reason: this keeps UI, validation, business rules, and persistence independently reviewable.

Example:

```ts
// server/actions/create-project.ts
"use server";

import { z } from "zod";
import { createProject } from "@/server/services/projects";

const schema = z.object({
  name: z.string().min(2).max(80),
});

export async function createProjectAction(input: unknown) {
  const parsed = schema.safeParse(input);
  if (!parsed.success) {
    return { ok: false, error: "Invalid project name" } as const;
  }

  return createProject(parsed.data);
}
```

## Component Patterns

- Default to Server Components.
  Reason: SaaS pages usually fetch data and render static controls; sending less JavaScript improves reliability.
- Add `"use client"` only for interactivity that needs browser state, effects, or event handlers.
  Reason: client boundaries increase bundle size and make server data access unavailable.
- Keep Client Components leaf-level when possible.
  Reason: a small interactive island is easier to test and avoids moving the whole page to the browser.
- Pass serialized data into Client Components.
  Reason: database rows, Dates, Maps, and class instances can break React serialization.
- Use accessible form labels, button text, and error messages.
  Reason: SaaS users repeat workflows many times; ambiguity becomes support cost.
- Put reusable primitives in `components/ui/` and product-specific composites in feature folders or `components/forms/`.
  Reason: a button is shared infrastructure; a billing form is product behavior.

## Auth, Tenancy, and Permissions

- Check authentication in server-only code before reading tenant data.
  Reason: client-side checks are presentation only.
- Include `workspace_id` or equivalent tenant scope on tenant-owned tables.
  Reason: most SaaS data leaks come from missing tenant filters.
- Centralize permission checks in services or `lib/auth/permissions.ts`.
  Reason: duplicating permission logic across pages creates silent drift.
- Never trust IDs from forms or URLs without verifying ownership.
  Reason: predictable SQLite integer IDs are easy to enumerate.

## Error Handling

- Return typed results from Server Actions instead of throwing for expected validation and business failures.
  Reason: forms need actionable errors without tripping global error boundaries.
- Throw only for unexpected infrastructure failures.
  Reason: unexpected failures should be logged and surfaced as system errors.
- Do not leak raw database errors to users.
  Reason: schema details help attackers and confuse customers.

## Testing Rules

- Unit test `server/services/` for business rules.
  Reason: billing, quotas, invitations, and permissions are where SaaS mistakes cost money.
- Test migrations against a temporary SQLite database.
  Reason: SQL that parses is not the same as SQL that migrates cleanly.
- Use fixture builders for users, workspaces, and subscriptions.
  Reason: tests should show the business state being exercised.
- Add a regression test for every permission bug.
  Reason: tenant boundary regressions are high severity.

## What We Do Not Do And Why

- Do not put database queries inside Client Components.
  Reason: Client Components run in the browser and cannot safely access secrets or the database.
- Do not rewrite existing migrations.
  Reason: deployed databases depend on migration history being stable.
- Do not add an ORM by default.
  Reason: this template chooses explicit SQL so query shape, indexes, and migrations stay obvious.
- Do not create generic `utils.ts` dumping grounds.
  Reason: mixed-purpose files become hard for Claude Code and humans to edit safely.
- Do not use API routes for internal form mutations when Server Actions fit.
  Reason: Server Actions keep validation and mutation close to the page workflow.
- Do not use global mutable singletons for request-specific auth or tenant state.
  Reason: server runtimes reuse processes and can leak state between requests.
- Do not mark large layout trees as `"use client"`.
  Reason: it forces unnecessary JavaScript onto every route below that layout.
- Do not silently create database tables at runtime outside migrations.
  Reason: schema changes should be reviewed, versioned, and deployable.

## Implementation Checklist For Claude Code

When adding or changing a feature:

1. Identify the route, service, query, and migration files involved.
2. Validate all external input with Zod.
3. Keep tenant and permission checks server-side.
4. Add or update migration files before query code.
5. Use typed result objects for expected failures.
6. Run the relevant dev commands before declaring the task complete.

