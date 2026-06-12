# CLAUDE.md

This file gives Claude Code the operating rules for a greenfield SaaS built with
Next.js 15 App Router, TypeScript, SQLite, and a small server-first architecture.
Follow these defaults unless the user explicitly asks for a different stack.

## Stack & Versions

- Runtime: Node.js 22 LTS.
  Reason: it supports modern Web APIs and keeps local development aligned with
  current Next.js tooling.
- Framework: Next.js 15 App Router.
  Reason: route handlers, server components, metadata, and layouts are first
  class and reduce custom routing code.
- Language: TypeScript with `strict: true`.
  Reason: database rows, form payloads, and auth state must be typed before they
  cross app boundaries.
- UI: React Server Components by default, client components only for browser
  state, event handlers, effects, or imperative APIs.
  Reason: server components keep bundles small and keep data access on the
  server.
- Database: SQLite for local development and small deployments.
  Use `better-sqlite3` for local file-backed apps, or Turso/libSQL when hosted
  SQLite is required.
  Reason: both preserve the SQLite mental model while covering local and remote
  deployment targets.
- ORM/query layer: Drizzle ORM.
  Reason: it keeps migrations explicit, SQL close to the data model, and types
  lightweight.
- Validation: Zod at every external boundary.
  Reason: TypeScript does not validate user input, form data, webhook payloads,
  or environment variables at runtime.
- Styling: Tailwind CSS plus small app-owned components.
  Reason: SaaS screens need consistent spacing and states more than a large
  component abstraction early on.
- Tests: Vitest for unit tests, Playwright for critical flows.
  Reason: fast unit feedback plus one or two browser checks catches most SaaS
  regressions without heavy setup.

## Project Structure

Use this structure for new work:

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
  components/
    ui/
    forms/
    layout/
  db/
    client.ts
    schema.ts
    migrations/
  features/
    billing/
    projects/
    users/
  lib/
    auth.ts
    env.ts
    errors.ts
    result.ts
  server/
    actions/
    queries/
  tests/
```

Rules:

- Put route-level UI in `src/app`, reusable UI in `src/components`, domain logic
  in `src/features`, and server-only data access in `src/server`.
  Reason: this prevents app routes from becoming a dumping ground.
- Keep `src/db/schema.ts` as the single source of truth for tables.
  Reason: duplicated model definitions drift quickly in SaaS projects.
- Keep generated migration files in `src/db/migrations`.
  Reason: migrations are production artifacts and must be reviewed.
- Do not place database calls in client components.
  Reason: it leaks server concerns into browser bundles and creates unsafe
  execution paths.

## Naming Conventions

- Components use PascalCase: `ProjectCard.tsx`.
  Reason: it matches React conventions and keeps imports obvious.
- Hooks start with `use`: `useProjectFilters.ts`.
  Reason: React hook rules and linting expect this shape.
- Server actions use verb-first names: `createProject`, `archiveProject`.
  Reason: mutations should read like commands.
- Queries use noun-first names: `projectById`, `projectsForUser`.
  Reason: reads should describe returned data.
- Database tables use snake_case plural names: `users`, `projects`,
  `project_members`.
  Reason: SQL stays consistent and readable.
- TypeScript types use domain names, not transport names:
  `Project`, `ProjectInput`, `ProjectRow`.
  Reason: it keeps UI, validation, and persistence concerns separate.

## Environment Variables

Validate environment variables in `src/lib/env.ts` and import that module
instead of reading `process.env` throughout the app.

Required defaults:

```env
DATABASE_URL="file:./local.db"
NEXT_PUBLIC_APP_URL="http://localhost:3000"
AUTH_SECRET="replace-with-a-local-secret"
```

Rules:

- Server-only secrets must not use the `NEXT_PUBLIC_` prefix.
  Reason: public variables are exposed to browser code.
- Fail fast when a required env var is missing.
  Reason: a clear boot error is cheaper than a production runtime failure.
- Keep `.env.example` updated when env vars change.
  Reason: setup instructions are part of the feature.

## SQL & Migration Conventions

- Create migrations for every schema change.
  Reason: production databases must be reproducible.
- Never edit a migration after it has been merged.
  Reason: teammates and deployed environments may already have applied it.
- Prefer additive migrations: add nullable columns, backfill, then enforce
  constraints in a later migration.
  Reason: SQLite has limited online schema alteration and safer rollouts need
  smaller steps.
- Use text primary keys with generated IDs for user-facing records.
  Reason: they are stable across sync, imports, and logs.
- Add `created_at` and `updated_at` to mutable business tables.
  Reason: SaaS support and audits need basic lifecycle visibility.
- Use foreign keys for ownership and membership relations.
  Reason: application checks are not a substitute for relational integrity.
- Keep SQL transactions around multi-step writes.
  Reason: partially-created users, projects, or billing records are expensive to
  repair.
- Do not store money as floats.
  Reason: floating point rounding creates billing bugs. Store integer cents or
  the smallest currency unit.

## Data Access Patterns

- Read data in server components or `src/server/queries`.
  Reason: reads stay close to the route while preserving a server-only boundary.
- Write data through server actions or route handlers.
  Reason: mutations need validation, auth checks, and consistent error handling.
- Validate all form input with Zod before calling database code.
  Reason: database constraints are the last line of defense, not the first.
- Return small DTOs to UI components.
  Reason: UI should not depend on raw database row shape.
- Keep authorization checks in the same function that performs the data access.
  Reason: callers forget checks; protected operations should be protected by
  construction.

## Component Patterns

- Default to server components.
  Reason: data fetching, auth checks, and HTML rendering belong on the server
  unless interactivity is required.
- Add `"use client"` only when the component uses state, effects, browser APIs,
  or event handlers.
  Reason: every client boundary increases bundle size and hydration cost.
- Keep forms small and colocate their schema with the action.
  Reason: validation and mutation logic should evolve together.
- Use accessible native elements before custom widgets.
  Reason: SaaS users rely on keyboard navigation, labels, and predictable
  controls.
- Represent async states explicitly: loading, empty, error, and success.
  Reason: dashboards and billing screens must not fail silently.

## API & Server Action Patterns

- Route handlers live under `src/app/api`.
  Reason: App Router treats API routes as part of the app surface.
- Server actions live in `src/server/actions`.
  Reason: it keeps mutation logic out of component files once it grows.
- Use typed result objects for expected failures:

```ts
type ActionResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: { code: string; message: string } };
```

Reason: expected business failures should not look like unhandled exceptions.

- Throw only for unexpected infrastructure failures.
  Reason: operational errors need logs and monitoring, not user-facing branching.
- Log server errors with enough context to debug, but never log secrets.
  Reason: logs are often shared during incident response.

## Dev Commands

Use these commands unless the project has a documented alternative:

```bash
npm install
npm run dev
npm run lint
npm run typecheck
npm run test
npm run db:generate
npm run db:migrate
npm run db:studio
```

If a command is missing, add it to `package.json` when it is part of the change.
Reason: repeatable commands are part of a maintainable SaaS project.

## Testing Rules

- Add unit tests for pure utilities, validation schemas, and permission helpers.
  Reason: these are cheap to test and easy to break.
- Add integration tests for server actions that write to the database.
  Reason: validation, auth, and persistence must work together.
- Add Playwright coverage for signup, login, project creation, and billing
  critical paths when those features exist.
  Reason: one end-to-end check can catch wiring errors that unit tests miss.
- Do not mock the database for migration or query behavior.
  Reason: SQLite behavior is the thing being tested.

## What We Do Not Do

- Do not introduce a second database.
  Reason: this project is intentionally SQLite-first.
- Do not add global state management for server data.
  Reason: server components and query functions already own server data.
- Do not add an API layer only for internal server component reads.
  Reason: direct server queries are simpler and avoid unnecessary HTTP hops.
- Do not put secrets in client components or public env vars.
  Reason: browser bundles are public.
- Do not create generic abstractions before there are two real use cases.
  Reason: premature abstractions hide SaaS business rules.
- Do not skip migrations for "small" schema changes.
  Reason: small schema drift still breaks deployments.
- Do not silently catch errors.
  Reason: users need clear recovery paths and operators need clear logs.

## Working Style for Claude Code

- Before editing, inspect `package.json`, `src/db/schema.ts`, and the relevant
  route or feature folder.
  Reason: local conventions beat assumptions.
- Keep pull requests focused on one issue.
  Reason: small PRs are easier to review and safer to merge.
- Prefer modifying existing patterns over adding new libraries.
  Reason: dependencies create maintenance cost.
- When adding a feature, update docs, commands, env examples, and tests in the
  same change.
  Reason: incomplete setup instructions slow down every future contributor.
- If requirements are ambiguous, choose the safer server-first default and note
  the assumption in the final response.
  Reason: server-first choices reduce data exposure and accidental complexity.

