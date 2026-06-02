# CLAUDE.md - Next.js 15 + SQLite SaaS

Use this file as the project operating guide for a greenfield SaaS app built with Next.js 15 App Router, TypeScript, React Server Components, Server Actions, and SQLite through `better-sqlite3` or Turso/libSQL.

## Stack & Versions

- Next.js 15 App Router with TypeScript.
  Reason: route groups, server components, layouts, metadata, and server actions keep SaaS workflows close to the UI that owns them.
- React Server Components by default.
  Reason: most SaaS screens are data-heavy dashboards; server rendering keeps client bundles smaller and avoids unnecessary API layers.
- SQLite for local-first persistence, using `better-sqlite3` for single-node apps or Turso/libSQL for hosted/serverless deployments.
  Reason: the schema stays portable while the runtime adapter can change later.
- Tailwind CSS and a small component layer.
  Reason: product velocity matters; avoid a large custom design system until patterns repeat.
- Zod for all external input validation.
  Reason: form data, route params, and search params are untrusted even inside server actions.

## Folder Structure

```text
app/
  (marketing)/
    page.tsx
  (app)/
    dashboard/
      page.tsx
      loading.tsx
      error.tsx
  api/
    health/route.ts
components/
  ui/
  forms/
  layout/
db/
  client.ts
  migrations/
  schema.sql
features/
  billing/
  onboarding/
  projects/
lib/
  auth.ts
  env.ts
  result.ts
  validators.ts
scripts/
  migrate.ts
  seed.ts
tests/
```

Rules:

- Keep route files thin. Put product logic in `features/<feature>/`.
  Reason: routes change with UX; business logic should survive layout changes.
- Put shared primitives in `components/ui/`, but keep feature-specific components beside the feature.
  Reason: premature global components become hard to change.
- Keep all database access behind `db/client.ts` and feature-level query modules.
  Reason: swapping `better-sqlite3` for Turso should not rewrite UI code.
- Do not put secrets, payment logic, or DB clients in client components.
  Reason: anything under `"use client"` can reach the browser bundle.

## Naming Conventions

- Files and folders use kebab-case: `project-card.tsx`, `billing-summary.tsx`.
  Reason: URLs and imports stay readable across platforms.
- React components use PascalCase exports.
  Reason: JSX diagnostics and React DevTools remain clear.
- Server actions end with `Action`: `createProjectAction`.
  Reason: callers can distinguish actions from pure helpers.
- Query functions start with `get`, `list`, `create`, `update`, or `delete`: `listProjectsForUser`.
  Reason: call sites reveal whether data is read or mutated.
- Zod schemas end with `Schema`: `createProjectSchema`.
  Reason: validation code is easy to find and reuse.

## Dev Commands

Use these scripts in `package.json`:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "db:migrate": "tsx scripts/migrate.ts",
    "db:seed": "tsx scripts/seed.ts",
    "test": "vitest run"
  }
}
```

Before opening a PR, run:

```bash
npm run typecheck
npm run lint
npm run test
```

If a project has no tests yet, add a focused test for the touched logic instead of declaring the gap acceptable.

## SQL / Migration Conventions

- Every schema change gets a timestamped SQL file in `db/migrations/`: `202606011230_add_projects.sql`.
  Reason: SQLite has no central migration service; file order is the source of truth.
- Migrations must be forward-only.
  Reason: SaaS data should be backed up and migrated deliberately, not rolled back casually.
- Use explicit column names; never rely on `SELECT *` in app code.
  Reason: UI should not break when a column is added for another workflow.
- Always include `created_at` and `updated_at` on business tables.
  Reason: support, billing, and audits need timelines.
- Prefer integer primary keys or text UUIDs, but choose one per project and document it in `db/schema.sql`.
  Reason: mixed ID styles cause avoidable bugs in URLs and joins.
- Wrap multi-step writes in transactions.
  Reason: SaaS actions often create records plus audit rows; partial writes are worse than failed writes.
- Validate inputs before SQL and parameterize every query.
  Reason: server actions do not make string interpolation safe.

Example query shape:

```ts
export function createProject(input: CreateProjectInput) {
  const parsed = createProjectSchema.parse(input);
  return db.transaction(() => {
    const project = insertProject(parsed);
    insertAuditEvent({ type: "project.created", projectId: project.id });
    return project;
  })();
}
```

## Component Patterns

- Default to server components for pages, lists, tables, details, and read-only dashboards.
  Reason: data fetching stays close to rendering and avoids extra client state.
- Use client components only for interactivity: forms with local state, popovers, charts, drag-and-drop, keyboard shortcuts.
  Reason: `"use client"` should be a specific choice, not a habit.
- Put mutations in server actions and validate with Zod inside the action.
  Reason: validation belongs at the trust boundary.
- Return typed action results instead of throwing for expected form errors.
  Reason: forms need predictable error rendering.
- Every async route segment should have `loading.tsx` when loading can exceed a quick database read.
  Reason: SaaS dashboards feel broken without feedback.
- Use `error.tsx` for recoverable route errors and log unexpected failures server-side.
  Reason: users need a stable UI even when one workflow fails.

## Data & Auth Patterns

- Read the session in server components or server actions, not in client components.
  Reason: authorization decisions must happen on the server.
- Every query that reads tenant-owned data must filter by `user_id`, `org_id`, or tenant scope.
  Reason: missing tenant filters are the most expensive SaaS bug.
- Do not pass raw database rows directly into complex client components.
  Reason: serialize only the fields the UI needs and keep private columns server-side.
- Keep environment parsing in `lib/env.ts`.
  Reason: missing environment variables should fail at boot, not during checkout or onboarding.

## Patterns To Follow

- Make the smallest useful vertical slice: route, query, validation, UI state, and test.
  Reason: SaaS features fail at integration boundaries, not in isolated helpers.
- Prefer boring HTML forms plus server actions before adding client-side form libraries.
  Reason: server actions cover most CRUD workflows with less code.
- Use route groups for product areas: `(marketing)`, `(app)`, `(admin)`.
  Reason: layouts and auth boundaries stay explicit.
- Keep billing, auth, and tenant checks boring and repetitive when needed.
  Reason: a little duplication is safer than a clever abstraction around money or access.

## Anti-Patterns To Avoid

- Do not create API routes for server-rendered pages just to fetch your own data.
  Reason: server components can call the database directly and avoid extra network hops.
- Do not put `use client` at the top of a page to fix one interactive child.
  Reason: it turns the whole subtree into client JavaScript.
- Do not run migrations automatically inside request handlers.
  Reason: concurrent requests can corrupt or block production traffic.
- Do not hide database writes inside React components.
  Reason: mutations belong in explicit actions or service functions.
- Do not accept raw `FormData` deep in the app.
  Reason: parse it once at the boundary, then pass typed data.
- Do not swallow errors with `catch {}`.
  Reason: support cannot debug silent failures.
- Do not introduce queues, Redis, or Postgres unless a measured requirement needs them.
  Reason: this template is for SQLite-first SaaS; extra infrastructure slows delivery.

## When Claude Works In This Repo

- Start by locating the relevant route under `app/`, then inspect the matching `features/` module and database queries.
- Before editing SQL, read all migrations and `db/schema.sql`.
- Keep changes scoped to one vertical slice unless the user asks for a larger refactor.
- After code edits, run the narrowest useful checks: typecheck for TypeScript changes, migration dry run for SQL changes, and focused tests for business logic.
- If a task would require secrets, production data, payment configuration, or destructive migrations, stop and ask for approval.
