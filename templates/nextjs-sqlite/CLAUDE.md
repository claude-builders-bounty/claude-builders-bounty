# CLAUDE.md — Next.js 15 + SQLite SaaS

This file defines strict engineering rules for Claude Code in this project.
These rules are opinionated to optimize delivery speed, migration safety, and maintainability.

## 1) Stack & Versions

- Next.js `15.x` (App Router, TypeScript strict mode)
- React `19.x`
- Node.js `>= 20`
- SQLite:
  - local/dev: `better-sqlite3`
  - hosted/prod option: Turso/LibSQL
- Package manager: `pnpm`

Why: one stack baseline removes tooling drift across contributors and CI.

## 2) Project Structure

```txt
src/
  app/                 Route segments, layouts, pages, route handlers
  features/            Domain modules (billing, auth, workspace, invoices)
    <feature>/
      components/
      server/
      schema/
      actions/
      tests/
  lib/
    db/
      client.ts        DB connection singleton
      queries/         Shared SQL helpers that are truly cross-feature
    auth/
    env/
  components/ui/       Reusable UI primitives only
  styles/
migrations/            SQL migration files (ordered, immutable)
scripts/               Operational scripts (seed, migrate, backfill)
```

Rules:
- Put business logic in `features/*/server`, not in `app/*` route files.
- Keep route handlers thin; call domain functions.
- Do not place feature-specific code under global `lib/`.

Why: feature-first structure keeps ownership clear and reduces accidental coupling.

## 3) Dev Commands

- Install: `pnpm install`
- Dev server: `pnpm dev`
- Type check: `pnpm typecheck`
- Lint: `pnpm lint`
- Unit tests: `pnpm test`
- Migrate DB: `pnpm db:migrate`
- Seed DB: `pnpm db:seed`

Why: consistent command contract lets Claude run reliable automation and fixes.

## 4) SQL / Migration Conventions

- Migration filenames must be ordered:
  - `migrations/0001_init.sql`
  - `migrations/0002_add_workspace_table.sql`
- Migrations are immutable after merge.
- Every migration must include an explicit rollback comment section.
- Never run schema changes directly from app code at runtime.
- Add indexes intentionally and document query motivation in migration comments.

Why: immutable ordered migrations are critical for safe deploys and reproducible environments.

## 5) Component & Server Patterns

- Server actions call feature service functions; no inline SQL in components.
- Validation at boundaries only (route handler/server action), not scattered in UI.
- Use `zod` schemas per feature in `features/<feature>/schema`.
- Prefer composable presentational UI components; keep data fetching server-side.

Why: this isolates risk and keeps UI refactors independent from persistence logic.

## 6) Naming Conventions

- Files: kebab-case (`workspace-settings-form.tsx`)
- React components: PascalCase
- Feature folders: singular domain names (`invoice`, `workspace`)
- DB tables: snake_case plural (`workspace_members`)
- DB columns: snake_case

Why: deterministic naming improves grep/discovery and lowers cognitive load.

## 7) What We Do Not Do (And Why)

- Do not add business logic in `page.tsx`:
  - reason: pages should orchestrate, not own domain logic.
- Do not run broad `SELECT *` in production paths:
  - reason: payload bloat and hidden coupling to schema changes.
- Do not edit old migrations:
  - reason: breaks drifted environments and rollback assumptions.
- Do not use global mutable singletons except DB client:
  - reason: state leakage across requests in server runtimes.
- Do not bypass type checks for “quick fixes”:
  - reason: hidden debt blocks safe iteration later.

## 8) Claude Code Execution Rules

- Before creating new modules, search for existing feature-local equivalents.
- Prefer minimal diffs and preserve current architecture boundaries.
- For DB changes: migration + query updates + tests in the same PR.
- For bug fixes: include repro notes and regression coverage.

Why: these rules maximize mergeability and keep each PR production-ready.
