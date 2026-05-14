# CLAUDE.md — Next.js 15 + SQLite SaaS

Use this file as the project memory for a greenfield SaaS built with Next.js 15 App Router, TypeScript, React Server Components, Server Actions, and SQLite through either `better-sqlite3` or Turso/libSQL.

## Stack & versions

- Runtime: Node.js 22 LTS. Use `npm` unless a lockfile proves another package manager is already chosen.
- Framework: Next.js 15 App Router. Do not create a `pages/` directory.
- Language: TypeScript in `strict` mode. Prefer explicit return types for exported functions and server actions.
- UI: React Server Components by default. Add `"use client"` only for state, effects, browser APIs, or event handlers.
- Database: SQLite first.
  - Local development: `better-sqlite3` with a file database at `data/dev.db`.
  - Hosted/serverless option: Turso/libSQL with the same schema and migration files.
- Validation: Zod at every trust boundary: route handlers, server actions, search params, and environment variables.
- Styling: Tailwind CSS plus small, typed components. Do not introduce a component framework unless the project already has one.

Reason: this stack keeps the MVP deployable, easy to run locally, and small enough that Claude can reason about the whole codebase without hidden services.

## Dev commands

Use these commands and keep them working:

```bash
npm run dev          # start Next.js locally
npm run lint         # run eslint / next lint equivalent
npm run typecheck    # run tsc --noEmit
npm run test         # run unit tests, if present
npm run db:migrate   # apply pending SQLite migrations
npm run db:studio    # optional DB browser, if configured
```

If a command is missing, add the smallest script that matches the name instead of inventing a new workflow. CI and Claude tasks should call the same commands developers call locally.

## Folder structure

Use this structure unless an existing file already establishes a stronger convention:

```text
app/
  (marketing)/              # public pages: landing, pricing, terms
  (app)/                    # authenticated product area
  api/                      # route handlers only when HTTP is required
  actions/                  # server actions grouped by domain
  layout.tsx
  page.tsx
components/
  ui/                       # generic presentational primitives
  forms/                    # form components with typed props
  layout/                   # nav, shell, header, footer
features/
  billing/
  auth/
  projects/
  users/
lib/
  db/
    client.ts               # opens SQLite/libSQL connection
    migrations.ts           # migration runner helpers
    queries/                # typed SQL access by domain
  env.ts                    # Zod-validated environment variables
  auth.ts                   # auth/session helpers
  errors.ts                 # shared error helpers
  utils.ts
migrations/
  0001_initial.sql
public/
scripts/
  migrate.ts
  seed.ts
tests/
  unit/
  integration/
types/
```

Rules:

- Put business logic in `features/<domain>` or `lib`, not inside React components.
- Put database reads/writes in `lib/db/queries/<domain>.ts`. Components and actions call query functions; they do not inline SQL.
- Keep route handlers thin: parse input, call a domain function, return a typed response.
- Co-locate tiny component-only helpers with the component; move shared helpers to `lib` only after a second use.

Reason: App Router projects become hard to maintain when data access, UI, and HTTP concerns are mixed in `app/` files.

## Naming conventions

- Files and folders: `kebab-case` except React components, which export `PascalCase` functions.
- Components: `PascalCase`, for example `ProjectCard`.
- Hooks: `useSomething` and only in client components or client-only files.
- Server actions: verb-first names, for example `createProjectAction`, `updateBillingEmailAction`.
- Query functions: describe the SQL operation, for example `insertProject`, `selectProjectById`, `listProjectsForUser`.
- SQLite tables: plural `snake_case`, for example `users`, `projects`, `billing_events`.
- SQLite columns: `snake_case`, with `created_at` and `updated_at` stored as ISO-8601 text unless there is a project-wide timestamp helper.
- IDs: use `TEXT PRIMARY KEY` with generated IDs from application code. Do not rely on SQLite rowids in public APIs.

Reason: predictable names make it easy for Claude to find the right layer and prevent accidental duplication.

## SQL / migration conventions

- Every schema change must be a new immutable file in `migrations/` named `NNNN_short_description.sql`.
- Never edit an already-applied migration. Add a follow-up migration instead.
- Migrations must be idempotent where SQLite allows it: use `IF NOT EXISTS` for tables and indexes.
- Always enable foreign keys when opening a local SQLite connection:

```sql
PRAGMA foreign_keys = ON;
```

- Prefer explicit constraints:

```sql
CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  owner_user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_projects_owner_user_id
  ON projects(owner_user_id);
```

- Use transactions for multi-step writes. If the write touches more than one table, wrap it in a transaction in the query layer.
- Do not build SQL with string concatenation. Use prepared statements / parameter binding.
- Model booleans as `INTEGER NOT NULL DEFAULT 0` and convert at the query boundary.
- Store JSON as `TEXT` only when the shape is validated with Zod before write and after read.

Reason: SQLite is reliable for SaaS MVPs when migrations are explicit, constraints are enforced, and unsafe dynamic SQL is avoided.

## Data access patterns

For `better-sqlite3`:

```ts
import Database from "better-sqlite3";

const db = new Database(process.env.DATABASE_PATH ?? "data/dev.db");
db.pragma("foreign_keys = ON");

export function selectProjectById(id: string) {
  return db.prepare("SELECT * FROM projects WHERE id = ?").get(id);
}
```

For Turso/libSQL, keep the exported query function names the same so the app can switch clients without touching UI code.

Return plain objects from query functions. Convert database rows into domain shapes before they leave `lib/db/queries`.

Reason: one stable query boundary keeps the rest of the app independent from the SQLite driver.

## Component patterns

- Default to server components for pages, layouts, data fetching, and read-only UI.
- Use client components only for interactive islands: form state, dropdowns, optimistic UI, keyboard shortcuts, charts, and browser APIs.
- Pass serializable props from server to client components. Do not pass database clients, class instances, or functions across the boundary.
- Keep forms progressive:
  - Use server actions for mutations.
  - Validate with Zod inside the action.
  - Return typed field errors instead of throwing for expected validation failures.
- Prefer small composition:

```tsx
export default async function ProjectsPage() {
  const projects = await listProjectsForCurrentUser();
  return <ProjectList projects={projects} />;
}
```

Reason: server-first UI minimizes shipped JavaScript and makes database access easier to audit.

## Server actions and route handlers

- Put reusable server actions in `app/actions/<domain>.ts` or `features/<domain>/actions.ts`.
- Start server action files with `"use server"`.
- Authenticate before mutating data.
- Authorize against the specific row being changed, not just the current route.
- Revalidate only the paths/tags affected by the mutation.
- Use route handlers only for webhooks, third-party callbacks, file uploads, or public HTTP APIs.

Reason: most product mutations do not need a custom HTTP endpoint; server actions are simpler and easier for Claude to maintain.

## Environment variables

Validate environment variables once in `lib/env.ts`:

```ts
import { z } from "zod";

const EnvSchema = z.object({
  DATABASE_URL: z.string().optional(),
  DATABASE_PATH: z.string().default("data/dev.db"),
  NEXT_PUBLIC_APP_URL: z.string().url(),
});

export const env = EnvSchema.parse(process.env);
```

- Only variables prefixed with `NEXT_PUBLIC_` may be read by client components.
- Never read `process.env` directly outside `lib/env.ts` unless a framework file requires it.
- Add new variables to `.env.example` in the same change that uses them.

Reason: missing environment variables should fail at startup, not during a user request.

## Testing and verification

Before considering a task complete, run:

```bash
npm run lint
npm run typecheck
npm run test
npm run db:migrate
```

For DB changes, also add one integration test or script that proves the migration can run against an empty database.

For UI changes, verify the affected route in the browser or provide a screenshot when the project workflow supports it.

Reason: SaaS regressions often come from type drift or migrations that only work on the author's machine.

## Patterns to follow

- Use Zod schemas near the boundary they validate.
- Keep SQL in query modules and give every query function a unit/integration test when practical.
- Prefer boring HTML forms plus server actions over custom client-side state machines.
- Add loading and error states for every async page segment that can be slow or fail.
- Use `notFound()` for missing resources and explicit authorization errors for forbidden resources.
- Keep README setup to three steps: install, configure env, migrate/dev.

## Anti-patterns to avoid

- Do not create `pages/api` or mix Pages Router with App Router. It creates two mental models and confuses routing decisions.
- Do not put secrets in client components, `NEXT_PUBLIC_` variables, logs, or screenshots.
- Do not run migrations from a request handler. Migrations are an operational step, not user traffic.
- Do not use an ORM unless the project already has one. Raw typed query functions are easier to inspect for a small SQLite SaaS.
- Do not use `any` to quiet type errors. Fix the type or add a narrow runtime parser.
- Do not make every component a client component. Interactivity should be isolated.
- Do not add global state for server data. Fetch server data in server components and pass only what the client needs.
- Do not silently catch errors in server actions. Return expected validation errors and log unexpected failures with context.

## Claude workflow rules

When Claude Code works in this repository:

1. Read this file, then inspect the relevant files before editing.
2. Make the smallest change that satisfies the task.
3. If a change affects schema, add a migration and update tests or seed data.
4. Run the verification commands listed above. If a command cannot run, explain why and provide the exact command attempted.
5. Summarize changes by layer: UI, data access, migration, tests.

Reason: these rules force each change to preserve the app architecture instead of solving only the immediate prompt.
