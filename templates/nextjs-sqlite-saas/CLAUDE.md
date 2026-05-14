# CLAUDE.md

This file is the working agreement for Claude Code in this repository. Follow it
when building or changing a Next.js + SQLite SaaS application.

## Product Shape

This is a small-to-medium SaaS app with authenticated users, account-owned data,
server-rendered pages, forms, background-safe database changes, and a billing
path that can be added without rewriting the app.

Prefer boring, explicit code. The app should be easy for one person to maintain
and safe for a small team to extend.

## Stack And Versions

- Runtime: Node.js 22 LTS or newer.
- Framework: Next.js 15 with App Router.
- UI: React 19, TypeScript 5, server components by default.
- Styling: Tailwind CSS 4 plus small local components.
- Database: SQLite for local and single-node deploys.
- SQLite driver: `better-sqlite3` for local/server deployments.
- Optional hosted SQLite: Turso/libSQL through `@libsql/client`.
- Schema and migrations: Drizzle ORM plus `drizzle-kit`.
- Validation: Zod at every external input boundary.
- Tests: Vitest for unit tests, Playwright for critical user flows.

If package versions differ, read `package.json` first and adapt to the existing
project. Do not upgrade framework or database packages as part of an unrelated
feature.

`better-sqlite3` requires the Node.js runtime. Do not put database access in
Edge runtime routes, middleware, or client components. Use Turso/libSQL when the
deployment target needs hosted SQLite or edge-adjacent reads.

## Greenfield Setup

For a new app, start with:

```bash
pnpm create next-app@latest my-saas \
  --ts \
  --tailwind \
  --eslint \
  --app \
  --src-dir=false \
  --import-alias "@/*"

cd my-saas
pnpm add better-sqlite3 drizzle-orm zod
pnpm add -D drizzle-kit @types/better-sqlite3 vitest playwright tsx
pnpm dlx playwright install
```

If using Turso/libSQL instead of local `better-sqlite3`:

```bash
pnpm add @libsql/client
```

Add `drizzle.config.ts`:

```ts
import { defineConfig } from "drizzle-kit";

export default defineConfig({
  schema: "./db/schema/index.ts",
  out: "./db/migrations",
  dialect: "sqlite",
  dbCredentials: {
    url: process.env.DATABASE_URL ?? "local.db"
  }
});
```

Add `.env.example`:

```text
DATABASE_URL=local.db
AUTH_SECRET=replace-with-at-least-32-characters
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

First migration path:

```bash
pnpm db:generate
pnpm db:migrate
pnpm typecheck
pnpm test
```

Do this setup once. After the project is established, follow existing local
scripts and folder conventions.

## Project Commands

Use these commands unless `package.json` says otherwise:

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm db:generate
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
  "db:generate": "drizzle-kit generate",
  "db:migrate": "drizzle-kit migrate",
  "db:studio": "drizzle-kit studio"
}
```

If a command is missing, add it only when the current task needs it.

## Folder Structure

Keep this shape unless the existing repo has a stronger convention:

```text
app/
  (marketing)/
    page.tsx
    pricing/page.tsx
  (app)/
    dashboard/page.tsx
    settings/page.tsx
  api/
    health/route.ts
components/
  ui/
  forms/
  layout/
  domain/
db/
  client.ts
  schema/
    index.ts
    users.ts
    organizations.ts
    subscriptions.ts
  migrations/
features/
  billing/
  organizations/
  settings/
lib/
  auth/
  env.ts
  errors.ts
  result.ts
  validators/
server/
  actions/
  services/
  repositories/
tests/
  unit/
  e2e/
```

Folder rules:

- `app/` owns routing, layouts, route handlers, metadata, and loading/error UI.
- `components/ui/` contains generic primitives with no business logic.
- `components/domain/` contains reusable product-specific display components.
- `features/<name>/` groups feature-specific forms, views, validators, and copy.
- `server/repositories/` is the only layer that writes database queries.
- `server/services/` owns business rules and transactions.
- `server/actions/` adapts forms and UI events into service calls.
- `db/schema/` is the source of truth for tables, indexes, and relations.

## Naming Rules

- Files and folders: kebab-case.
- React components: PascalCase exports.
- Server actions: `verbNounAction`, for example `createProjectAction`.
- Services: `verbNoun`, for example `createProject`.
- Repositories: `verbNounRecord`, for example `insertProjectRecord`.
- Zod schemas: `NounInputSchema` or `NounFormSchema`.
- Database tables: plural snake_case, for example `organizations`.
- Database columns: snake_case, for example `created_at`.
- TypeScript domain types: PascalCase, for example `OrganizationRole`.

Use exact, searchable names. Avoid generic names such as `data`, `helpers`,
`utils2`, `manager`, or `handler` unless they are truly local.

## Data Model Defaults

Most SaaS tables should include:

- `id`: text primary key, generated in application code with `crypto.randomUUID()`.
- `created_at`: integer timestamp or ISO text, defaulted at insert.
- `updated_at`: integer timestamp or ISO text, updated on mutation.
- Ownership columns such as `user_id` or `organization_id`.
- Status columns as constrained text unions when lifecycle matters.
- Indexes for foreign keys, lookup slugs, and dashboard list filters.

Prefer explicit foreign keys. Enable them for SQLite connections:

```sql
PRAGMA foreign_keys = ON;
```

## SQLite Rules

- SQLite is the default database. Do not introduce Postgres-only SQL.
- Keep write paths short and transactional.
- Do not run long network calls inside database transactions.
- Use repository functions for all SQL and Drizzle query calls.
- Validate inputs before calling repositories.
- Always add indexes for new list filters, foreign keys, and unique lookups.
- Store money in integer minor units, for example cents, not floating point.
- Store timestamps consistently. Prefer Unix milliseconds when arithmetic is
  common, or ISO text when human inspection matters more.
- Avoid nullable columns unless the empty state has real meaning.
- Use `CHECK` constraints for small enums when Drizzle supports the shape.

SQLite migration limits matter. For destructive changes, use the safe-copy
pattern:

1. Create the new table.
2. Copy and transform data.
3. Validate row counts and required columns.
4. Rename old and new tables.
5. Drop the old table in a separate reviewed migration when safe.

Never hand-edit a migration that has already been applied anywhere shared.

Migration policy:

- Generate migrations with `drizzle-kit` for ordinary schema changes.
- Name manual migration notes after the intent, for example
  `0007_add_organization_membership_indexes.sql`.
- Keep one logical schema change per migration.
- Include a PR note for every migration explaining whether it is additive,
  backfilled, or destructive.
- Before destructive migrations, take a backup, validate row counts, and include
  the rollback plan in the PR description.
- Run migrations against a copied local database before applying them to shared
  data.

## Drizzle Pattern

Example schema style:

```ts
import { index, sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

export const organizations = sqliteTable(
  "organizations",
  {
    id: text("id").primaryKey(),
    name: text("name").notNull(),
    slug: text("slug").notNull().unique(),
    createdAt: integer("created_at", { mode: "timestamp_ms" }).notNull(),
    updatedAt: integer("updated_at", { mode: "timestamp_ms" }).notNull()
  },
  (table) => ({
    slugIdx: index("organizations_slug_idx").on(table.slug)
  })
);
```

Repository style:

```ts
export async function findOrganizationBySlug(slug: string) {
  return db.query.organizations.findFirst({
    where: (table, { eq }) => eq(table.slug, slug)
  });
}
```

Services call repositories. Components do not.

## Database Client

Use one database module at `db/client.ts`.

For local SQLite:

```ts
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema";

const sqlite = new Database(process.env.DATABASE_URL ?? "local.db");
sqlite.pragma("foreign_keys = ON");

export const db = drizzle(sqlite, { schema });
```

If using Turso/libSQL, keep the public service API the same so repositories do
not care which client is underneath.

## Server Component Rules

- Default to server components.
- Fetch data in server components or services.
- Move only interactive islands to client components.
- Keep client components small and pass serializable props.
- Do not import database, services, secrets, or server-only modules into client
  components.
- Add `loading.tsx` for slow routes and `error.tsx` for recoverable route errors.
- Use `notFound()` for missing owned resources rather than rendering empty shells.

## Server Actions

Use server actions for form mutations when the result updates the current page.
Use route handlers for webhooks, third-party callbacks, public APIs, or requests
that need non-form semantics.

Server action checklist:

- Mark the file or function with `"use server"`.
- Parse `FormData` into a plain object.
- Validate with Zod.
- Check authentication and ownership.
- Call a service function.
- Revalidate or redirect intentionally.
- Return field-level errors for forms.

Do not put raw database calls directly in server actions unless the action is
trivial and local to a one-off admin script.

## Route Handlers

Route handlers live in `app/api/**/route.ts`.

Rules:

- Validate method, body, query params, and headers.
- Return `Response.json(...)` with explicit status codes.
- Never trust incoming IDs without checking ownership.
- Keep webhook signature checks in the route handler, then pass verified events
  into services.
- Use idempotency keys for billing and webhook writes.

## Forms And Validation

- Define form schemas beside the feature that owns the form.
- Use Zod for server validation.
- Keep client validation helpful but never authoritative.
- Return errors as `{ fieldErrors, formError }`.
- Preserve user input after failed submissions.
- Disable submit buttons only while a request is pending.

## Auth And Authorization

Choose one auth system and keep it behind `lib/auth/`.

Every data access path must answer:

- Who is the current user?
- Which organization or account owns this record?
- What role or permission is required?
- What happens when access is missing?

Never rely on hidden form fields or client state for authorization.

## Billing Readiness

Keep billing code isolated under `features/billing/`.

Store:

- customer ID
- subscription ID
- price ID
- subscription status
- current period end
- cancellation state

Billing writes must be idempotent because webhooks can arrive more than once.
Do not let UI state be the source of truth for paid access.

## Error Handling

- Use typed result objects for expected business failures.
- Throw only for unexpected infrastructure failures.
- Log server errors with enough context to debug, but never log secrets.
- Show users plain messages, not stack traces.
- Add route-level `error.tsx` for user-facing recovery.

## Testing Rules

Add tests when changing:

- validators
- services
- repository behavior
- billing logic
- authorization checks
- critical onboarding or checkout flows

Test shape:

- Unit-test pure validators and services.
- Use SQLite temp files for repository tests.
- Use Playwright for sign-in, onboarding, checkout handoff, and dashboard CRUD.

Do not over-test simple presentational components unless they protect a bug fix.

## Environment Variables

All environment reads go through `lib/env.ts`.

Validate with Zod at startup:

```ts
const EnvSchema = z.object({
  DATABASE_URL: z.string().default("local.db"),
  AUTH_SECRET: z.string().min(32),
  NEXT_PUBLIC_APP_URL: z.string().url()
});
```

Rules:

- Only expose variables with `NEXT_PUBLIC_` when the browser truly needs them.
- Do not read `process.env` throughout the app.
- Keep `.env.example` updated when adding a variable.

## UI And Component Rules

- Use semantic HTML first.
- Keep buttons, inputs, dialogs, and menus in `components/ui/`.
- Keep domain-specific cards and tables in `components/domain/`.
- Prefer forms that work with server actions.
- Include empty, loading, and error states for dashboards.
- Keep dashboard layouts dense and scannable.
- Avoid decorative marketing UI inside product surfaces.

Client component checklist:

- Does it need state, effects, browser APIs, or event handlers?
- Are props serializable?
- Can it be smaller?
- Is business logic still on the server?

## Feature Workflow

When adding a feature:

1. Read existing schema, services, and routes.
2. Add or update Zod input schemas.
3. Add schema and migration changes if needed.
4. Add repository functions.
5. Add service functions with authorization checks.
6. Add server actions or route handlers.
7. Add UI with loading, empty, and error states.
8. Add focused tests for risk.
9. Run lint, typecheck, tests, and migrations.

Report what changed, what was tested, and any migration risk.

## What We Do Not Do

- Do not introduce Postgres, Redis, queues, or microservices for ordinary CRUD.
  SQLite is the chosen persistence layer and should stay enough until a real
  scaling need appears.
- Do not use client components as the default. Server components reduce shipped
  JavaScript and keep data access on the server.
- Do not put SQL or Drizzle calls in UI components. Repositories and services
  keep data access testable.
- Do not use floating point for money. Integer minor units avoid rounding bugs.
- Do not add global state libraries unless local React state and URL state are
  clearly insufficient.
- Do not add generic abstractions before two concrete use cases exist.
- Do not create destructive migrations without a backup and review note.
- Do not store secrets in source files, screenshots, logs, or localStorage.
- Do not skip ownership checks because a route is "internal."

## Claude Code Behavior

Before editing:

- Read `package.json`, `db/schema`, and the affected feature folder.
- Identify whether the task changes schema, server behavior, UI, or all three.
- Make the smallest complete change that follows the existing style.

While editing:

- Keep changes scoped to the requested feature.
- Prefer existing helpers and local patterns.
- Add concise comments only for non-obvious business rules.
- Update this file if the project convention changes.

Before finishing:

- Run the relevant checks.
- Mention any commands that could not be run.
- Mention migrations and manual follow-up clearly.
- Do not claim payment, deployment, or external provider changes unless actually
  completed.
