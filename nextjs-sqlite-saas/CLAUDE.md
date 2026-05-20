# CLAUDE.md - Next.js 15 + SQLite SaaS

Use this file as the working contract for a greenfield SaaS app built with
Next.js 15 App Router, TypeScript, React Server Components, Tailwind CSS, and
SQLite. The default database path is local SQLite through Drizzle ORM and
`better-sqlite3`; Turso can be used later behind the same repository boundary
when deployment needs a managed database.

## Stack And Versions

- Use Next.js 15 with the App Router because routes, loading states, server
  actions, metadata, and layouts should live in one predictable routing model.
- Use TypeScript in strict mode because SaaS apps accumulate business rules and
  weak types become expensive once billing, teams, and permissions appear.
- Use React Server Components by default because most SaaS screens render
  account, project, and settings data that does not need client JavaScript.
- Use client components only for browser-only state, form interactivity, charts,
  keyboard shortcuts, optimistic UI, and third-party widgets.
- Use SQLite with Drizzle ORM because migrations stay explicit, schema changes
  are reviewable, and SQL is still close enough to inspect when debugging.
- Use `better-sqlite3` for local development and single-node deployments. Use
  Turso only when the app needs remote edge-friendly SQLite.
- Use Tailwind utility classes for layout and spacing. Extract components when
  behavior or repeated structure matters, not just to hide class names.

## Dev Commands

Prefer these commands unless the package manager in `package.json` says
otherwise:

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm db:generate
pnpm db:migrate
pnpm db:studio
pnpm build
```

If a command is missing, add it before relying on it. A Claude session should not
guess how to verify changes when `package.json` can make that contract explicit.

Recommended scripts:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "db:generate": "drizzle-kit generate",
    "db:migrate": "drizzle-kit migrate",
    "db:studio": "drizzle-kit studio"
  }
}
```

## Greenfield Smoke Test

After pasting this file into a new project, Claude Code should be able to answer
these setup requests without asking for extra architecture decisions:

```text
Create the initial app folder structure for this SaaS.
Add a projects feature with a create form, server action, validator, and SQLite schema.
Add the smallest meaningful verification commands to package.json.
```

Expected behavior:

- It chooses App Router server components by default.
- It places writes in feature-level server actions.
- It uses Drizzle migrations instead of ad hoc SQL changes.
- It keeps database access out of UI components.
- It reports missing scripts or environment variables instead of inventing them.

## Folder Structure

Use this structure for new work:

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
    health/
      route.ts
components/
  ui/
  forms/
  layout/
db/
  schema.ts
  client.ts
  migrations/
features/
  projects/
    actions.ts
    queries.ts
    components/
    validators.ts
lib/
  env.ts
  errors.ts
  ids.ts
  result.ts
tests/
  fixtures/
```

Reasons:

- `app/` owns routing, layouts, metadata, and route handlers because Next.js
  needs those files in known places.
- `features/` owns business workflows because SaaS domains grow by feature,
  not by technical layer.
- `db/` owns schema, migrations, and database clients because database access
  must stay easy to audit.
- `components/ui/` is for generic primitives only. Feature-specific components
  belong near their feature so behavior and copy are easier to change together.
- `lib/env.ts` validates environment variables once. Do not read
  `process.env` directly across the app because missing configuration should
  fail early and clearly.

## Naming Conventions

- Files that render routes use Next.js names: `page.tsx`, `layout.tsx`,
  `loading.tsx`, `error.tsx`, `route.ts`.
- React components use `PascalCase.tsx`.
- Server action files are named `actions.ts` because imports should make side
  effects obvious.
- Data read files are named `queries.ts` because reads and writes need different
  caching and error behavior.
- Validation files are named `validators.ts` and export Zod schemas named
  after the command they validate, for example `createProjectSchema`.
- Database tables use singular domain nouns in code (`project`, `membership`)
  and explicit SQL table names where useful (`projects`, `memberships`).
- IDs are strings at the app boundary. Generate them in `lib/ids.ts` so tests
  can use stable factories.

## Data Access Rules

- Never query the database directly from React components. Components call
  feature-level query functions so authorization, filtering, and error mapping
  stay in one place.
- Server actions may write to the database, but they must validate input first
  and return a typed result object. This keeps UI error handling predictable.
- Route handlers are for external HTTP surfaces and webhooks. Internal UI forms
  should prefer server actions because they integrate with App Router flows.
- Do not pass raw Drizzle rows to client components when they contain internal
  columns. Map rows into view models first.
- Put reusable WHERE clauses in functions only after the second real use. Early
  abstractions hide important authorization details.

## SQL And Migration Conventions

- All schema changes go through Drizzle migrations. Do not edit a production
  database manually because the repository must explain every schema state.
- Migration filenames should be generated by the migration tool and committed
  with the schema change that required them.
- Each table must have:
  - a stable text primary key
  - `createdAt`
  - `updatedAt` when records can change
  - indexes for foreign keys and common list filters
- Use foreign keys for ownership relationships because SaaS bugs often come
  from orphaned data.
- Use transactions when a workflow writes more than one table. A partially
  created workspace, invite, or subscription record is harder to repair than to
  prevent.
- Prefer additive migrations. Destructive migrations must include a short note
  in the PR explaining data risk and rollback.
- Do not hide raw SQL if the ORM expression is unclear. Use SQL fragments with
  comments when it makes the query easier to review.

Example schema style:

```ts
import { integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

export const project = sqliteTable("projects", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  slug: text("slug").notNull().unique(),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull(),
  updatedAt: integer("updated_at", { mode: "timestamp" }).notNull(),
});
```

## Server Action Pattern

Use this shape for mutations:

```ts
"use server";

import { revalidatePath } from "next/cache";
import { createProjectSchema } from "./validators";

export async function createProjectAction(input: unknown) {
  const parsed = createProjectSchema.safeParse(input);

  if (!parsed.success) {
    return { ok: false, error: "Invalid project details" } as const;
  }

  // Call a feature service or transaction here.
  revalidatePath("/dashboard");

  return { ok: true } as const;
}
```

Reasons:

- `unknown` input forces validation at the boundary.
- A small result union is easier for forms to render than thrown framework
  errors.
- `revalidatePath` sits next to the write so stale UI is not forgotten.

## Component Patterns

- Start every route as a server component. Move code to a client component only
  when it needs hooks, event handlers, browser APIs, or mutable UI state.
- Keep data loading in route-level server components or feature queries.
- Pass plain serializable props into client components. Do not pass database
  clients, class instances, or functions across the server/client boundary.
- Use forms for mutations whenever possible because they work with progressive
  enhancement and server actions.
- Keep table/list filters in the URL when users would share or bookmark the
  view. Keep purely temporary UI state in component state.
- Build empty, loading, and error states with the first version of a feature.
  SaaS screens without these states feel broken during real customer use.

## Error Handling

- Expected user errors return typed results from actions.
- Unexpected errors are logged on the server and shown as a generic message in
  the UI.
- Do not expose database errors, stack traces, provider responses, or internal
  IDs to users.
- Use `notFound()` only when the user is allowed to know the resource does not
  exist. Otherwise show a generic access message.

## Environment Variables

- Validate environment variables in `lib/env.ts` with a schema.
- Keep server-only variables out of `NEXT_PUBLIC_*`.
- Do not add secrets to examples. Use placeholder names such as
  `DATABASE_URL=file:./local.db`.
- Document every required variable in `.env.example` because new contributors
  should not need to inspect runtime errors to start the app.

## Testing Expectations

- Unit-test validators, pure helpers, ID factories, and query builders.
- Add integration tests for feature workflows that write to the database.
- Use a temporary SQLite database per test file or per test suite. Tests must
  not share the developer's local database.
- Test server actions through their exported function when possible. Browser
  E2E tests are reserved for critical customer flows.
- Every bug fix should include either a regression test or a note explaining why
  the behavior is impractical to test locally.

## What We Do Not Do

- Do not put database queries in UI components. Reason: it spreads access rules
  across files that are supposed to render.
- Do not use client components by default. Reason: it ships unnecessary
  JavaScript and weakens the server/client boundary.
- Do not mutate data from route handlers when a server action fits. Reason:
  forms and cache revalidation are simpler with App Router actions.
- Do not create generic `utils.ts` dumping grounds. Reason: they become hidden
  dependency webs; create domain-named files instead.
- Do not introduce a second ORM or query builder. Reason: migrations and type
  expectations must have one source of truth.
- Do not store money, quota, or permission decisions only in the browser.
  Reason: client state can be modified and cannot be the source of authority.
- Do not perform destructive migrations casually. Reason: SQLite is often used
  by small teams without elaborate recovery tooling.
- Do not add background jobs without an explicit runner and retry story.
  Reason: SaaS automation fails silently when ownership is unclear.

## Before Finishing A Task

Run the smallest meaningful verification:

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

Then report:

- files changed
- commands run
- any command that failed and why
- database migrations added
- user-visible behavior changed

If a task touches schema, include the migration file in the same commit. If a
task changes a customer flow, include a short manual test path. If a task cannot
be fully verified locally, say exactly what is missing.
