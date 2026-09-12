# CLAUDE.md (Next.js 15 + SQLite Playbook)

Use this as the default context for all tasks in a greenfield SaaS repo built with Next.js 15 App Router and SQLite.

## Stack & versions

- **Node.js**: 20.17+
- **Package manager**: pnpm 9 (or npm/yarn if repo already uses them)
- **Framework**: Next.js 15 (App Router, Server Components by default)
- **Database**: SQLite with one of:
  - `better-sqlite3` for local file-backed deployments
  - `@libsql/client` (Turso) when deploying in serverless environments
- **ORM (optional)**: drizzle-orm for typed migrations and query safety
- **Styling**: Tailwind CSS preferred

## Repository structure

- `app/`: App Router entrypoints.
  - `app/page.tsx` for public landing/home pages.
  - `app/(marketing)/`, `app/(app)/` for route grouping.
  - `app/api/` for server endpoints.
- `components/`: Reusable UI components, no direct DB access.
- `lib/`: Domain logic, validators, service functions, integration clients.
- `db/`: Schema, migration SQL, seeds, and migration helper scripts.
- `public/`: Static assets.
- `tests/` or `__tests__/`: Unit/integration tests.
- `scripts/`: One-off dev/ops scripts (db generation, sanity checks).

## Core conventions

- Use **Server Components** unless interaction needs client behavior.
- If a file uses `use client`, keep it minimal; move data fetching and mutation logic to server files.
- Favor deterministic IDs (`crypto.randomUUID()`), never rely on timestamp-only IDs.
- Validate all external input with a schema library (Zod preferred): request, env var, form DTOs.

## Database model rules

1. **Single source of schema truth**
   - Create schema definitions in `db/schema.sql` (or Drizzle schema) and generate migration SQL from it.
   - Never edit production schema by ad-hoc statements in feature PRs.

2. **Migrations are required for every DB change**
   - For `better-sqlite3`: include both `*.up.sql` and `*.down.sql` when practical.
   - For Turso, include forward-only migration SQL with rollback notes in PR summary.

3. **No destructive default behavior**
   - Never drop/rename columns without migration + backfill path.
   - Any `DROP TABLE`, `ALTER TABLE DROP COLUMN`, or bulk data rewrite requires explicit issue comment and migration rationale.

4. **Query discipline**
   - Use explicit column lists in production reads.
   - Add indexes for repeated query predicates (`WHERE user_id`, `WHERE status`, `updated_at`).

## Naming and folder rules

- Routes: kebab-case (`billing/history`, `admin/settings`).
- React components: PascalCase filenames.
- Utility functions: lower camelCase (`resolveBillingCycle`).
- Database columns: snake_case (`user_id`, `created_at`).

## Commands and workflow

- `pnpm install` — install dependencies.
- `pnpm dev` — run app.
- `pnpm lint` — run lint.
- `pnpm test` — run tests (or `npm test` if project uses npm).
- `pnpm typecheck` / `pnpm build` when configured, before merging DB or API changes.

## Migration conventions

- Store migration files under `db/migrations/<timestamp>-<slug>/`.
- Each migration file must include:
  1. what changed,
  2. why changed,
  3. backward-compatibility impact.
- Migrations touching user data require:
  - dry-run output (row counts before/after when feasible),
  - data consistency checklist.

## Component patterns

- Keep UI components stateless where possible; pass callbacks/props from server actions.
- Data mutations should live in `app/api` routes or server actions near consuming route.
- Reuse response DTOs (single shape) between API and UI types.

## Error handling

- Return structured error codes (`INTERNAL`, `VALIDATION`, `UNAUTHENTICATED`, `FORBIDDEN`) for API routes.
- Never leak raw SQL or secrets in client-facing errors.
- Log operational errors with request IDs and redact PII.

## What we don’t do (and why)

- No implicit DB migrations in application runtime:
  - Reason: runtime migrations block deploys and create rollback uncertainty.
- No storing secrets in source files:
  - Reason: leak risk and non-reproducible environments.
- No unversioned SQL in pull requests:
  - Reason: prevents reproducibility and auditability.
- No broad `SELECT *` in hot paths:
  - Reason: hidden performance regressions and schema drift risk.
- No `setTimeout` polling for critical correctness flows:
  - Reason: introduces race conditions and flaky behavior.

## Onboarding notes for Claude Code

When taking a request, start by mapping: route surface, data source, permission checks, and migration impact before writing code.
Prefer edits in this order:
1. `lib/` domain logic and helpers,
2. `db/` schema/migrations,
3. `app/` UI and API,
4. tests and fixtures.

## Acceptance check for this template

A repo using this file should start with minimal local setup and be understandable from this document alone.
If a new developer can set up schema and understand mutation rules in one pass, this template is functioning as intended.
