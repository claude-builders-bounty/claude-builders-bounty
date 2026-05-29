# CLAUDE.md

This file is the operating manual for a greenfield SaaS built with Next.js 15
App Router, TypeScript, Drizzle ORM, and SQLite. Follow it before adding code.

## Stack And Versions

- Runtime: Node.js 22 LTS.
- Framework: Next.js 15 App Router with React 19 and TypeScript strict mode.
- Database: SQLite through Drizzle ORM.
- Local database driver: `better-sqlite3`.
- Hosted database option: Turso/libSQL through `@libsql/client`.
- Styling: Tailwind CSS 4 with CSS variables for tokens.
- Forms: React Hook Form plus Zod. Server actions must revalidate the same Zod
  schema before mutating data.
- Auth: Auth.js v5 when the product needs accounts. Keep auth code isolated in
  `src/server/auth`.
- Tests: Vitest for unit tests, Playwright for browser flows, and Drizzle Kit
  migration checks.

Reason: this stack keeps the project simple enough for SQLite while preserving a
clean path to Turso, server actions, and production deployment.

## Dev Commands

Use these scripts in `package.json` and keep them working:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:e2e": "playwright test",
    "db:generate": "drizzle-kit generate",
    "db:migrate": "drizzle-kit migrate",
    "db:studio": "drizzle-kit studio",
    "db:seed": "tsx src/server/db/seed.ts",
    "check": "npm run lint && npm run typecheck && npm run test && npm run build"
  }
}
```

Run `npm run check` before a PR. If the change touches schema, also run
`npm run db:generate` and inspect the generated SQL before committing it.

## Folder Structure

Create this structure and keep ownership boundaries intact:

```text
src/
  app/
    (marketing)/
      page.tsx
    (app)/
      dashboard/
        page.tsx
    api/
      health/
        route.ts
    layout.tsx
    globals.css
  components/
    ui/
    forms/
    layout/
  features/
    billing/
      actions.ts
      components/
      queries.ts
      schema.ts
    projects/
      actions.ts
      components/
      queries.ts
      schema.ts
  lib/
    env.ts
    dates.ts
    ids.ts
    result.ts
  server/
    auth/
    db/
      client.ts
      schema.ts
      migrations/
      seed.ts
    permissions.ts
  tests/
    unit/
    e2e/
```

Rules:

- `src/app` handles routing, metadata, layouts, loading states, and thin page
  composition only.
- `src/features/<feature>` owns feature-specific UI, actions, queries, and Zod
  schemas.
- `src/components/ui` contains reusable presentational primitives only. It must
  not import database, auth, or feature modules.
- `src/server` contains privileged code. Client components must never import it.
- `src/lib` contains small framework-agnostic helpers. If a helper imports
  Next.js, Drizzle, Auth.js, or React, it does not belong in `src/lib`.

Reason: App Router projects decay quickly when pages become service layers. This
layout keeps routing, domain behavior, and database access separate.

## Naming Conventions

- Files and folders use kebab-case except React components, which use
  PascalCase filenames when the file exports one main component.
- Server actions are named as commands: `createProject`, `updateWorkspacePlan`,
  `deleteInvite`.
- Database query helpers are named by the data they return:
  `getProjectById`, `listWorkspaceMembers`, `countOpenInvites`.
- Zod schemas end in `Schema`: `createProjectSchema`.
- Drizzle table objects use plural camelCase: `users`, `workspaces`,
  `workspaceMembers`.
- URL params use stable nouns: `/workspaces/[workspaceId]/projects/[projectId]`.

Reason: predictable names let Claude modify the right layer without asking where
logic belongs.

## Environment

Validate all environment variables in `src/lib/env.ts` with Zod:

```ts
import { z } from "zod";

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  DATABASE_URL: z.string().min(1),
  AUTH_SECRET: z.string().min(32).optional(),
});

export const env = envSchema.parse(process.env);
```

Rules:

- Read `process.env` only in `src/lib/env.ts`.
- Do not provide silent fallbacks for secrets.
- Keep `.env.example` complete and safe to commit.
- Use separate database files for local dev and tests, such as
  `file:./.data/dev.sqlite` and `file:./.data/test.sqlite`.

Reason: hidden environment reads make deployments fail late and make tests leak
state between runs.

## Database And Migrations

Use Drizzle schema as the source of truth. Do not hand-edit generated migration
SQL unless the migration needs a data backfill that Drizzle cannot express.

Required conventions:

- Define tables in `src/server/db/schema.ts`.
- Use `text("id").primaryKey()` with generated CUID2 or UUID strings.
- Store timestamps as integer milliseconds or SQLite timestamps consistently.
  Pick one at project creation and do not mix them.
- Use explicit indexes for every foreign key used in list pages.
- Use foreign keys with `onDelete` behavior declared deliberately.
- Add `createdAt` and `updatedAt` to mutable business tables.
- Never use `db.run(sql.raw(userInput))`.

Example:

```ts
import { relations } from "drizzle-orm";
import { index, integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

export const workspaces = sqliteTable("workspaces", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  slug: text("slug").notNull().unique(),
  createdAt: integer("created_at", { mode: "timestamp_ms" }).notNull(),
  updatedAt: integer("updated_at", { mode: "timestamp_ms" }).notNull(),
});

export const projects = sqliteTable(
  "projects",
  {
    id: text("id").primaryKey(),
    workspaceId: text("workspace_id")
      .notNull()
      .references(() => workspaces.id, { onDelete: "cascade" }),
    name: text("name").notNull(),
    createdAt: integer("created_at", { mode: "timestamp_ms" }).notNull(),
    updatedAt: integer("updated_at", { mode: "timestamp_ms" }).notNull(),
  },
  (table) => ({
    workspaceIdx: index("projects_workspace_id_idx").on(table.workspaceId),
  }),
);

export const workspacesRelations = relations(workspaces, ({ many }) => ({
  projects: many(projects),
}));
```

Migration workflow:

1. Change `schema.ts`.
2. Run `npm run db:generate`.
3. Read the generated SQL.
4. Add a data migration only when existing rows need transformation.
5. Run `npm run db:migrate` on a disposable local database.
6. Add or update tests that prove the schema behavior.

Reason: SQLite is forgiving in development, so migration discipline has to be
explicit before production data exists.

## Data Access

Use query files for reads and server actions for writes:

```ts
// src/features/projects/queries.ts
import { eq } from "drizzle-orm";
import { db } from "@/server/db/client";
import { projects } from "@/server/db/schema";

export async function getProjectById(projectId: string) {
  const [project] = await db
    .select()
    .from(projects)
    .where(eq(projects.id, projectId))
    .limit(1);

  return project ?? null;
}
```

Rules:

- Pages may call read queries directly when rendering server components.
- Mutations go through server actions or route handlers, never through client
  component fetch wrappers unless an external API contract is required.
- Every write must check authorization inside the same server-side function that
  writes to the database.
- Return serializable objects from server actions. No Drizzle result objects, no
  raw errors, no database client leakage.

Reason: putting auth checks next to writes prevents "checked in the UI" security
bugs.

## Server Actions

Server actions must be small command handlers:

```ts
"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { requireUser } from "@/server/auth/session";
import { assertWorkspaceRole } from "@/server/permissions";
import { createProjectSchema } from "./schema";

export async function createProject(input: z.infer<typeof createProjectSchema>) {
  const user = await requireUser();
  const data = createProjectSchema.parse(input);

  await assertWorkspaceRole(user.id, data.workspaceId, ["owner", "admin"]);

  // Write through the feature repository/query helper.
  // Return a stable shape that client components can render.

  revalidatePath(`/workspaces/${data.workspaceId}`);
  return { ok: true };
}
```

Rules:

- Validate with Zod inside the action even if the form already validated.
- Check auth and permissions before writes.
- Use `revalidatePath` or `revalidateTag` after successful writes.
- Return `{ ok: true }` or `{ ok: false, error: "..." }` for expected failures.
- Throw only for unexpected system failures.

Reason: forms can be bypassed; server actions are the real trust boundary.

## Components

Default to server components. Add `"use client"` only for state, effects,
browser APIs, or interactive event handlers.

Component rules:

- Page components compose data and feature components.
- Feature components may import their feature schemas and types.
- UI primitives accept props and render markup only.
- Do not pass whole database rows to client components when only a few fields
  are needed.
- Keep loading and empty states close to the route that owns them.

Reason: fewer client components means less JavaScript, fewer hydration bugs, and
cleaner data ownership.

## Forms

Every form uses one schema shared between client validation and server action
validation:

```ts
// src/features/projects/schema.ts
import { z } from "zod";

export const createProjectSchema = z.object({
  workspaceId: z.string().min(1),
  name: z.string().trim().min(2).max(80),
});
```

Rules:

- Trim user-facing strings in schemas.
- Use controlled error messages for fields users can fix.
- Do not trust hidden inputs for ownership or pricing.
- Disable submit buttons while pending, but keep the server action idempotent.

Reason: schema reuse prevents the client and server from accepting different
data.

## Routing

Use route groups for product areas:

- `(marketing)` for public pages.
- `(auth)` for sign-in, sign-up, and password flows.
- `(app)` for authenticated product pages.

Rules:

- Put auth gates in layouts when every child route needs the same gate.
- Use `notFound()` for missing resources and `redirect()` for auth navigation.
- Keep `route.ts` handlers for webhooks, health checks, and external API
  surfaces. Internal product mutations should usually be server actions.

Reason: route groups keep URL design clean without mixing public and private
layout state.

## API Route Handlers

Use route handlers only when a non-browser client needs an HTTP API or when
receiving webhooks.

Rules:

- Validate request bodies with Zod.
- Return JSON with stable error codes.
- Verify webhook signatures before reading side effects.
- Avoid calling route handlers from server components. Import the underlying
  query or service function instead.

Reason: internal HTTP calls add latency and duplicate validation.

## Authentication And Authorization

Rules:

- `requireUser()` returns the current user or redirects/throws.
- Authorization helpers live in `src/server/permissions.ts`.
- Check role membership by workspace or resource, not by trusting route params.
- Never expose admin-only fields in client component props.
- Tests must cover at least one denied case for every new privileged mutation.

Reason: SaaS bugs usually come from cross-tenant access, not missing login
checks.

## Error Handling

Use three categories:

- User-fixable validation errors: return field errors or a stable message.
- Expected domain failures: return `{ ok: false, error: "..." }`.
- Unexpected system failures: throw and let `error.tsx` or monitoring catch them.

Rules:

- Do not leak SQL, stack traces, tokens, or provider payloads to the browser.
- Log unexpected errors on the server with enough context to debug.
- Add `error.tsx` for product route groups.

Reason: users need actionable messages; developers need server-side details.

## Testing

Minimum test coverage for new work:

- Zod schemas: valid payload, invalid payload, boundary values.
- Query helpers: empty result and authorized result.
- Server actions: success, validation failure, authorization failure.
- Critical flows: one Playwright happy path per user-facing workflow.

Testing rules:

- Tests use a disposable SQLite database.
- Seed through explicit helpers, not shared production seed scripts.
- Keep Playwright tests focused on flows, not every visual detail.
- Do not mock permission checks in server action tests unless testing an
  unrelated branch.

Reason: SQLite makes integration tests cheap; use that advantage.

## Styling

Use Tailwind utilities and a small set of design tokens in `globals.css`.

Rules:

- No one-off hex colors in components. Add a token first.
- Prefer semantic component props such as `variant="destructive"` over passing
  classes through product code.
- Keep forms accessible: label every field, connect errors with
  `aria-describedby`, and preserve keyboard navigation.

Reason: SaaS interfaces grow by repetition; tokens and primitives keep them
consistent.

## Performance

Rules:

- Query only the columns needed for list views.
- Paginate unbounded lists from day one.
- Prefer server components for data-heavy screens.
- Use `Suspense` around slow panels, not around the whole dashboard.
- Add indexes before adding filters to large lists.

Reason: SQLite performs very well for small SaaS apps when queries are explicit
and indexed.

## Security Checklist

Before merging any feature:

- Inputs validated on the server.
- Auth checked on every write.
- Tenant/resource ownership checked in the database path.
- Secrets read only through `env`.
- Webhook signatures verified.
- No raw SQL with user input.
- No private fields passed to client components.
- File uploads restrict type, size, and storage path.

Reason: this checklist catches the common SaaS failure modes early.

## What We Do Not Do

- Do not create a generic `services` folder. Put behavior in the owning feature
  or in `src/server` when it is cross-feature infrastructure.
- Do not put database calls in client components.
- Do not create API routes just to call them from server components.
- Do not use `any` to escape schema or Drizzle types.
- Do not add an ORM abstraction over Drizzle until two real databases are
  supported.
- Do not mix Prisma and Drizzle in the same app.
- Do not hand-edit generated migrations for cosmetic changes.
- Do not store money as floating point numbers. Use integer cents and currency.
- Do not rely on middleware as the only authorization layer.
- Do not add dependencies for helpers that fit in a small local function.

Reason: these shortcuts make the project feel faster for one day and slower for
the rest of its life.

## PR Expectations

Every PR should include:

- What changed.
- Why the change belongs in this layer.
- Screenshots or a short video for UI changes.
- Migration notes for schema changes.
- Commands run, including failures that shaped the final fix.

Before opening a PR, run:

```bash
npm run check
```

If the PR changes database schema, also include:

```bash
npm run db:generate
npm run db:migrate
```

Reason: reviewers should be able to verify the change without reverse
engineering your local workflow.
