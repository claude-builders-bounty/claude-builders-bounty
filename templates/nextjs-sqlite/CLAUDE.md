# CLAUDE.md — Next.js 15 + SQLite SaaS Project

This file tells Claude Code how this project is built and how to work safely inside it.

## Stack & Versions
- Next.js 15 App Router
- TypeScript strict mode
- React Server Components by default
- SQLite via either:
  - `better-sqlite3` for local file-based apps, or
  - Turso/libSQL for hosted SQLite
- Drizzle ORM or raw SQL migrations (pick one and stay consistent)
- Node.js 20+

## Working Style
- Make the smallest correct change.
- Prefer editing existing patterns over inventing new abstractions.
- Before changing code, read the route/page/component/module that already does something similar.
- If a task affects database shape, update schema, migration, query code, tests, and docs together.
- Never leave TODO comments instead of finishing the real wiring unless explicitly asked.

## Dev Commands
- Install deps: `pnpm install`
- Start dev server: `pnpm dev`
- Typecheck: `pnpm typecheck`
- Lint: `pnpm lint`
- Test: `pnpm test`
- DB generate/migrate (example): `pnpm db:generate && pnpm db:migrate`

If the repo uses npm or bun instead of pnpm, mirror the existing package manager. Do not introduce a second one.

## Folder Structure
Expected layout for a greenfield project:

- `app/`
  - Route segments, pages, layouts, server actions
- `components/`
  - Reusable UI components only
- `lib/`
  - Pure helpers, auth wiring, db client, shared utilities
- `db/`
  - schema, migrations, seed scripts
- `tests/`
  - integration and unit tests
- `public/`
  - static assets

### Rules
- Keep route-specific UI close to the route if it is not reused.
- Put generic UI in `components/`, not `app/`.
- Put database access behind `lib/db/*` or `db/*`, not inline in page components.
- Avoid giant `utils.ts` dumping grounds.

## App Router Rules
- Default to Server Components.
- Use Client Components only when state, effects, browser APIs, or event-heavy UI actually require them.
- Fetch data on the server whenever possible.
- Mutations should use server actions or API route handlers consistently; do not mix styles randomly.
- Keep `page.tsx` thin when business logic grows; extract loaders/actions/helpers.

## Database Rules
- SQLite is the source of truth. Do not fake schema changes in TypeScript only.
- Every schema change must ship with a migration.
- Never edit an already-applied migration unless this is explicitly a pre-release reset.
- Use explicit column names and constraints; avoid magic JSON blobs when relational columns are clearer.
- Prefer nullable columns only when the domain genuinely allows missing data.
- Add indexes intentionally for lookup paths that appear in real queries.

## Migration Conventions
- One migration per logical schema change.
- Name migrations descriptively, e.g. `add_invoice_due_date`, not `update_schema_7`.
- In the same change set, update:
  - schema definitions
  - migration files
  - query code
  - tests covering read/write behavior
- If data backfill is needed, write it as a deliberate migration or script; do not bury it in request-time code.

## Query Patterns
- Keep queries close to the domain module that owns them.
- Select only the columns you need for list pages and APIs.
- Wrap multi-step writes in a transaction.
- For user-scoped data, enforce `user_id` filtering in the query itself, not only in caller logic.
- When returning data to the UI, map DB rows into a stable view model instead of leaking raw table shape everywhere.

## Component Patterns
- Components should do one job.
- Shared components must have predictable props and minimal hidden behavior.
- Prefer composition over deeply configurable mega-components.
- Forms should have one source of truth for validation; server validation is mandatory even if client validation exists.
- Tables/lists should receive already-shaped data rather than reaching into DB or global state directly.

## Naming Conventions
- Use explicit names: `createInvoice`, `listInvoicesForUser`, `updateWorkspaceSlug`.
- Avoid vague names like `handleData`, `processItem`, `temp`, `newData`.
- React components: PascalCase.
- Helpers/functions/variables: camelCase.
- DB tables/columns: follow the repo's current convention; do not mix snake_case and camelCase arbitrarily.

## Auth / SaaS Multi-Tenancy Rules
- Every read/write path must be scoped to the current user or workspace.
- Never trust client-provided ownership fields.
- Permission checks belong in server-side code.
- Billing-, subscription-, and admin-only logic should be isolated from generic UI code.

## What We Don't Do
- We do not fetch directly from SQLite inside random React components.
  - Reason: it creates hidden coupling and breaks reuse/testing.
- We do not introduce a new ORM, state library, or UI framework for a small task.
  - Reason: stack drift is expensive.
- We do not mix migration styles.
  - Reason: schema history becomes unreliable.
- We do not store structured relational data in a single JSON text column just to move faster.
  - Reason: querying and migrations become painful.
- We do not silently broaden types with `any` or `as unknown as` to make errors disappear.
  - Reason: that debt comes back immediately.
- We do not create duplicate helper layers that wrap simple framework APIs without a strong reason.
  - Reason: indirection tax.

## When Claude Code Gets a Task
1. Identify whether the change is UI, data, auth, or cross-cutting.
2. Read the nearest existing implementation first.
3. If DB-related, inspect schema + migration + query call sites before editing.
4. Make the smallest coherent patch.
5. Run relevant checks.
6. Summarize what changed, what was verified, and any remaining risk.

## Definition of Done
A task is not done until most of the following are true:
- code builds
- relevant tests pass
- migrations are included if schema changed
- docs are updated if behavior changed
- no dead code or placeholder scaffolding is left behind

If there is uncertainty, prefer leaving a short note in the final summary rather than inventing certainty.
