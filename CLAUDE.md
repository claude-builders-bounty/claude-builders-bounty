# CLAUDE.md

This file is for Claude Code working inside a greenfield SaaS product built with Next.js 15 App Router and SQLite. The default SQLite runtime is `better-sqlite3` for local-first deployments. Turso is allowed only if the team explicitly needs remote SQLite.

## Stack And Versions

- Next.js 15 App Router on Node 20 LTS
- TypeScript in strict mode
- React Server Components by default
- SQLite via `better-sqlite3`
- Drizzle ORM for schema + migrations
- Tailwind CSS for UI styling
- Zod for request and form validation

Reason: this stack is small, debuggable, and keeps the data model close to the app. SQLite is fast enough for an early SaaS if writes are modest and background jobs stay simple.

## Dev Commands

- `npm install`
- `npm run dev`
- `npm run lint`
- `npm run typecheck`
- `npm run test`
- `npm run db:generate`
- `npm run db:migrate`

Reason: Claude should assume typecheck, lint, and tests all matter before suggesting a task is done. Migration generation and migration execution are separate on purpose so schema diffs stay reviewable.

## Folder Structure

```text
app/
  (marketing)/
  (auth)/
  dashboard/
  api/
components/
  ui/
  forms/
  dashboard/
db/
  schema/
  migrations/
  queries/
lib/
  auth/
  billing/
  env/
  validators/
jobs/
tests/
```

Rules:

- `app/` owns route composition, not business logic.
- `components/ui/` contains primitive reusable UI pieces only.
- `components/forms/` contains form compositions tied to Zod schemas.
- `db/schema/` contains table definitions only.
- `db/queries/` contains named database operations that the rest of the app imports.
- `lib/` holds cross-cutting modules that are not route-specific.
- `jobs/` is for async work such as email, cleanup, digests, and syncs.

Reason: Claude should not place SQL in route handlers or scatter auth checks through random UI components.

## Naming Conventions

- Tables are plural snake_case: `users`, `workspace_memberships`, `invoice_events`
- Columns are snake_case: `created_at`, `trial_ends_at`
- TypeScript files are kebab-case: `workspace-switcher.tsx`
- React components are PascalCase exports
- Server-only modules end with `.server.ts` when ambiguity would be dangerous
- Validation schemas end with `Schema`
- Database query helpers use verb-based names: `createWorkspace`, `listInvoicesForWorkspace`

Reason: predictable naming lowers Claude's need to ask clarifying questions and reduces accidental duplication.

## Component Patterns

- Prefer Server Components for data-backed screens.
- Use Client Components only for interactivity, browser APIs, or local state that cannot live on the server.
- Keep data fetching near the route or server action that owns the workflow.
- Do not pass raw database rows deep into the tree. Map them into view models first.
- Forms must validate with the same Zod schema on both client and server when feasible.
- Destructive actions require explicit confirmation UI and server-side authorization checks.

Reason: App Router projects become fragile when every component becomes a client island and every form invents its own validation rules.

## SQL And Migration Conventions

- Every schema change goes through a checked-in migration.
- Never edit an old migration after it has been applied outside local throwaway work.
- Additive changes come first: add nullable column, backfill, then enforce constraints in a later migration.
- Foreign keys must be explicit.
- Index every column used repeatedly in workspace scoping, lookup tokens, or time-ordered lists.
- Soft-delete only when product requirements need recovery or auditability. Otherwise delete rows normally.
- Monetary values are stored as integer minor units, never floats.
- Timestamps are stored in UTC.

Reason: SQLite is forgiving enough to hide bad habits until production data exists. Migrations need to stay boring and reversible.

## Auth And Multi-Tenancy Rules

- Every user-visible record must have a clear ownership boundary: user-owned or workspace-owned.
- Workspace-scoped queries must filter by `workspace_id` at the query layer, not only in calling code.
- Never trust a client-provided `workspace_id` without membership validation.
- Session reads stay in server code, not browser-only helpers.

Reason: the most common SaaS bug is cross-tenant data leakage caused by inconsistent scoping.

## API And Server Action Rules

- Prefer Server Actions for first-party form mutations that stay inside the app.
- Prefer route handlers for webhooks, external integrations, or public API surfaces.
- Parse input immediately with Zod.
- Return domain errors with stable messages; do not leak raw database exceptions to the UI.
- Idempotency is required for billing webhooks and retryable background jobs.

Reason: this keeps app-internal workflows simple while preserving a clean boundary for external callers.

## What We Do Not Do

- We do not run raw SQL strings from route handlers because it spreads schema knowledge into the web layer.
- We do not put secrets in client components or `NEXT_PUBLIC_` env vars unless they are truly public.
- We do not use Prisma here because for SQLite-first SaaS work, Drizzle keeps generated SQL and migrations easier to reason about.
- We do not use UUID generation inside the browser for authoritative records when the server can assign IDs.
- We do not hide authorization inside UI conditions alone; server code must enforce it.
- We do not create giant `utils.ts` dumping grounds. Helpers live near the domain they support.

Reason: these shortcuts create the exact ambiguity that makes Claude produce noisy or unsafe edits later.

## How Claude Should Behave In This Repo

- Before editing, inspect the owning route, related query module, and relevant schema files.
- When changing data shape, update schema, query layer, validation, and UI together.
- Prefer focused patches over broad refactors unless the task explicitly asks for architectural cleanup.
- Run lint and typecheck after meaningful changes. Run tests for the affected path when available.
- If a task touches billing, auth, or workspace scoping, slow down and verify assumptions from code instead of inferring.

Reason: the project is optimized for operational correctness, not novelty.
