# CLAUDE.md - Next.js 15 + SQLite SaaS

Use this file as the project operating guide for a greenfield SaaS built with Next.js 15 App Router, TypeScript, React Server Components, Server Actions, and SQLite through `better-sqlite3` or Turso/libSQL.

## Stack and Versions

- Runtime: Node.js 20 LTS or newer.
- Framework: Next.js 15 with the App Router under `src/app`.
- Language: TypeScript in strict mode.
- UI: React Server Components by default, Client Components only for browser state and event handlers.
- Database: SQLite for local/single-node deployments or Turso/libSQL for hosted SQLite.
- Validation: Zod at every trust boundary.
- Styling: Tailwind CSS plus a small component system such as shadcn/ui.
- Testing: Vitest for unit tests, Playwright for user flows that cross pages or auth state.

Reason: this stack keeps the default path server-rendered, typed, and deployable without introducing a separate API service before the product needs one.

## Dev Commands

Prefer these commands and keep them working:

```bash
npm run dev
npm run lint
npm run typecheck
npm test
npm run db:migrate
npm run db:studio
npm run build
```

If a command is missing, add it to `package.json` before relying on it in docs or CI. Do not invent one-off commands in PR notes.

## Folder Structure

Use this shape unless the repository already has a stronger convention:

```text
src/
  app/
    (marketing)/
      page.tsx
    (app)/
      dashboard/
        page.tsx
        loading.tsx
        error.tsx
    api/
      webhooks/
        stripe/
          route.ts
    actions/
      billing.ts
      projects.ts
    layout.tsx
    globals.css
  components/
    ui/
    forms/
    tables/
  db/
    client.ts
    schema.ts
    migrations/
    queries/
  lib/
    auth.ts
    env.ts
    ids.ts
    permissions.ts
    validation.ts
  tests/
```

Rules:

- Route UI lives in `src/app/**/page.tsx`, with route-local `loading.tsx`, `error.tsx`, and `not-found.tsx` when needed.
- Shared visual primitives live in `src/components/ui`.
- Feature components live near the route that owns them until at least two routes use them.
- SQL schema, migrations, and low-level query helpers live under `src/db`.
- Cross-cutting helpers live under `src/lib`; do not put route-specific business logic there.

Reason: App Router projects become hard to maintain when every component is globally shared too early. Keep ownership obvious first, then extract when reuse is real.

## Naming Conventions

- Files: kebab-case for components and helpers, for example `project-card.tsx`.
- Components: PascalCase exports, for example `ProjectCard`.
- Server Actions: verb-first names, for example `createProject`, `archiveProject`.
- Database tables: snake_case plural names, for example `projects`, `billing_events`.
- Database columns: snake_case names, for example `created_at`, `owner_id`.
- Environment variables: uppercase snake case and validated in `src/lib/env.ts`.
- IDs: use stable prefixed IDs at the app boundary, for example `proj_...`, while keeping database primary keys simple.

Reason: consistent names reduce Claude's need to infer whether a symbol is a component, action, table, or environment value.

## Server and Client Component Rules

- Start every component as a Server Component.
- Add `"use client"` only when the file needs browser APIs, React state, effects, refs, or event handlers.
- Pass serializable props from Server Components to Client Components.
- Do not import database clients, filesystem code, or secret-reading modules into Client Components.
- Fetch data in Server Components when rendering a page.
- Use Client Components for interactive controls such as menus, charts, drag-and-drop, comboboxes, and optimistic form state.

Reason: Server Components reduce shipped JavaScript and make direct database reads possible without adding internal HTTP calls.

## Data Mutations

Use Server Actions for first-party form and button mutations inside the app:

```ts
"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { getDb } from "@/db/client";

const createProjectSchema = z.object({
  name: z.string().min(1).max(80),
});

export async function createProject(formData: FormData) {
  const input = createProjectSchema.parse({
    name: formData.get("name"),
  });

  const db = getDb();
  db.prepare("insert into projects (name) values (?)").run(input.name);
  revalidatePath("/dashboard");
}
```

Use Route Handlers for webhooks, public APIs, file uploads, and third-party callbacks. Do not create an internal Route Handler just so a Server Component can call it.

Reason: Server Actions keep app mutations close to UI and integrate with cache revalidation; Route Handlers are for HTTP boundaries.

## Database Client Rules

Create database clients lazily:

```ts
import Database from "better-sqlite3";

let db: Database.Database | undefined;

export function getDb() {
  if (!db) {
    db = new Database(process.env.DATABASE_URL ?? "local.db");
  }
  return db;
}
```

Rules:

- Never initialize the database at module scope if it depends on environment variables.
- Keep prepared SQL in `src/db/queries` or next to the feature that owns it.
- Wrap multi-step writes in transactions.
- Always validate untrusted input before passing values into SQL.
- Use parameterized queries only. Never concatenate user input into SQL strings.

Reason: lazy initialization avoids build-time crashes, transactions keep SaaS billing/account flows consistent, and parameter binding prevents SQL injection.

## SQL and Migration Conventions

- Every schema change gets a migration file in `src/db/migrations`.
- Migration filenames use sortable timestamps: `202605270900_create_projects.sql`.
- Migrations are forward-only. Add a compensating migration instead of editing a migration that already ran.
- Include indexes in the same migration as the query pattern that needs them.
- Add `created_at` and `updated_at` to mutable business tables.
- Foreign keys must be explicit and enabled for local SQLite connections.
- Prefer `text` ISO timestamps or integer epoch milliseconds consistently; do not mix both in one schema.

Reason: SQLite is simple, but SaaS data still needs repeatable schema history and predictable rollback through new migrations.

## Query Patterns

- Read queries return plain typed objects, not raw driver rows leaking through the app.
- Paginate list pages from the start, even if the first version only shows 20 records.
- Use explicit column lists instead of `select *`.
- Keep authorization checks beside the query that needs them.
- Create indexes for tenant IDs, owner IDs, status filters, and timestamp ordering used by dashboards.

Reason: SaaS apps usually fail under account growth because unbounded lists and scattered permission checks were accepted early.

## Authentication and Authorization

- Treat authentication as identity only.
- Put authorization in explicit helpers such as `canReadProject(user, project)` or `requireWorkspaceRole(userId, workspaceId, role)`.
- Check authorization in Server Actions, Route Handlers, and server-side page loaders.
- Never trust hidden form fields for ownership, price, role, plan, or quota.
- Store membership and role state in database tables, not in client-only state.

Reason: a logged-in user is not automatically allowed to mutate every row they can name.

## Environment Variables

Define and validate environment variables in one module:

```ts
import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().min(1),
  NEXT_PUBLIC_APP_URL: z.string().url(),
});

export const env = envSchema.parse(process.env);
```

Rules:

- Only expose variables with `NEXT_PUBLIC_` when the browser truly needs them.
- Read secrets only in server-only modules.
- Do not use fallback secrets in production code.

Reason: central validation turns missing deployment config into an obvious startup failure instead of a runtime data bug.

## Error Handling

- Use `error.tsx` for route-level recovery UI.
- Return field-level validation errors from Server Actions in a typed shape.
- Log server errors with enough context to debug, but never log secrets, tokens, full cookies, or payment payloads.
- Convert database constraint errors into user-readable messages at the action boundary.

Reason: users need clear recovery paths, while maintainers need logs that are useful without leaking sensitive data.

## Testing Rules

- Unit test pure validators, permission helpers, ID helpers, and query mappers.
- Add integration tests for migrations and important SQL queries.
- Add Playwright tests for signup, login, billing, project creation, and destructive actions.
- Every bug fix gets a regression test that fails before the fix.
- Do not snapshot large HTML trees; assert behavior and visible text.

Reason: most SaaS regressions are permission, migration, and form-flow regressions rather than isolated component rendering issues.

## Component Patterns

- Server page loads data and passes it to a small view component.
- Client form owns pending state, optimistic UI, and inline validation display.
- Shared table components accept data and callbacks; they do not fetch on their own.
- Use `Suspense` and route `loading.tsx` for slow server reads.
- Keep page headings, empty states, and destructive confirmations consistent across the app.

Reason: separating server data loading from client interaction keeps App Router behavior predictable.

## What We Do Not Do

- Do not use Pages Router. This project uses App Router.
- Do not call internal API routes from Server Components. Query the database or service directly on the server.
- Do not mark whole route trees with `"use client"`.
- Do not put secrets in client components, logs, fixtures, screenshots, or README examples.
- Do not edit already-applied migration files.
- Do not add an ORM or state library just because one file is getting long.
- Do not cache authenticated dashboard data unless the invalidation path is explicit and tested.
- Do not hide authorization in UI conditionals; enforce it on the server.

Reason: these shortcuts create security, caching, and maintenance failures that are expensive to unwind after launch.

## PR Checklist

Before opening a PR, confirm:

- `npm run lint` passes.
- `npm run typecheck` passes.
- `npm test` passes.
- `npm run build` passes.
- New or changed SQL has a migration.
- Server Actions and Route Handlers validate input.
- Authorization is enforced server-side.
- User-facing changes include loading, empty, and error states.
