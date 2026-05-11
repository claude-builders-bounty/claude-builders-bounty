# CLAUDE.md

This file gives Claude Code the project rules for a production SaaS built with Next.js 15 App Router, TypeScript, and SQLite through `better-sqlite3` or Turso/libSQL.

## Stack And Versions

- Use Next.js 15 with the App Router in `app/`.
- Use TypeScript for application code, database access, route handlers, server actions, and tests.
- Use React Server Components by default. Add `"use client"` only for browser-only state, effects, event handlers, or browser APIs.
- Use SQLite for local-first persistence. Use `better-sqlite3` for single-process Node deployments and Turso/libSQL when the app needs remote or replicated SQLite.
- Use SQL migrations stored in the repository. Do not rely on production schema changes hidden in ad hoc scripts.

Reason: this keeps the app deployable, reviewable, and friendly to server-rendered SaaS workflows.

## Folder Structure

Use this layout unless an existing project already has a clear equivalent:

```text
app/
  (marketing)/
  (app)/
    dashboard/
  api/
    health/route.ts
components/
  ui/
  forms/
  layout/
db/
  client.ts
  schema.ts
  queries/
  migrations/
lib/
  auth/
  config.ts
  errors.ts
  validation/
server/
  actions/
  services/
tests/
```

Rules:

- Keep route segments focused on routing and composition.
- Put reusable UI in `components/`, not inside route folders unless it is truly route-specific.
- Put database connection code in `db/client.ts`.
- Put raw SQL in `db/queries/` or migration files, not inline across pages.
- Put business workflows in `server/services/`; pages and actions should call services instead of reimplementing rules.

Reason: App Router encourages colocation, but SaaS code becomes hard to maintain when SQL, validation, and UI are all mixed inside `page.tsx`.

## Naming Conventions

- Components: `PascalCase.tsx`
- Hooks: `useThing.ts`
- Server actions: `thing.actions.ts`
- Service modules: `thing.service.ts`
- Query modules: `thing.queries.ts`
- Migration files: `YYYYMMDDHHMM_description.sql`
- Database tables: plural snake_case, for example `users`, `teams`, `subscriptions`
- Columns: snake_case, for example `created_at`, `team_id`
- TypeScript values: camelCase

Reason: SQLite and SQL tooling read naturally with snake_case, while TypeScript stays idiomatic with camelCase.

## Next.js App Router Rules

- Default to Server Components for pages and layouts.
- Fetch data in Server Components when the data is needed for first render.
- Use `cache: "no-store"` or explicit revalidation when data must be request-fresh.
- Use route handlers only for external HTTP integrations, webhooks, health checks, and public API surfaces.
- Use server actions for form submissions and mutations initiated by the app UI.
- Validate all server action inputs before touching the database.
- Never import `db/client.ts` into Client Components.
- Keep Client Components small and pass already-shaped data into them.

Reason: the App Router is strongest when server data stays on the server and the client bundle contains only interactive UI.

## SQL And Migration Conventions

- Every schema change must be a migration file under `db/migrations/`.
- Migrations must be append-only after merge. Create a new migration instead of editing a migration that may have run elsewhere.
- Use explicit `NOT NULL`, `DEFAULT`, `CHECK`, and foreign key constraints where the domain requires them.
- Include `created_at` and `updated_at` on mutable business tables.
- Enable foreign keys for SQLite connections with `PRAGMA foreign_keys = ON`.
- Use prepared statements for all dynamic values.
- Use transactions for multi-step writes. With `better-sqlite3`, prefer `db.transaction(...)` and do not mix it with manual `BEGIN` / `COMMIT`.
- Do not use async callbacks inside `better-sqlite3` transactions.
- Write down whether a migration is safe to run on an existing database.

Reason: SQLite is reliable when schema rules are explicit and writes are transactional. Hidden migration behavior causes production drift.

## Database Access Pattern

Use query modules with small, named functions:

```ts
// db/queries/team.queries.ts
import { db } from "@/db/client";

export function getTeamById(teamId: string) {
  return db.prepare("SELECT * FROM teams WHERE id = ?").get(teamId);
}
```

Rules:

- Do not concatenate user input into SQL.
- Prefer one module per domain.
- Return plain objects from query modules.
- Convert database rows into app-facing shapes in services when needed.
- Keep authorization checks close to service functions, not scattered through UI files.

Reason: query modules make it easy to audit SQL, test business rules, and avoid injection mistakes.

## Component Patterns

- Use Server Components for list pages, detail pages, settings pages, and dashboards that primarily render data.
- Use Client Components for dialogs, comboboxes, charts with browser APIs, optimistic UI, and components needing local state.
- Keep forms split into a Server Component shell and a focused Client Component only when interactivity requires it.
- Put design-system primitives in `components/ui/`.
- Keep feature-specific components near their route only until they are reused by another route.

Reason: this keeps the client bundle small without making interactive flows awkward.

## Server Actions

Server actions must:

- Parse and validate input.
- Check authentication and authorization.
- Call a service function.
- Revalidate or redirect intentionally.
- Return typed, user-safe errors.

Server actions must not:

- Contain raw SQL.
- Trust form fields for ownership checks.
- Return stack traces or database errors to the client.
- Perform unrelated work like sending emails before the database transaction succeeds.

Reason: actions are public mutation boundaries and should be boring to review.

## Dev Commands

Expected scripts:

```bash
npm run dev
npm run build
npm run lint
npm run typecheck
npm test
npm run db:migrate
npm run db:studio
```

If a command is missing, add it before relying on it in docs or CI.

Reason: Claude Code should run the same checks a human reviewer expects.

## Testing Rules

- Add focused tests for services, validation, and database queries.
- Test migrations on an empty database and on a database with representative existing rows.
- Prefer integration tests for server actions that touch auth or writes.
- Do not snapshot large rendered pages unless the output is intentionally stable.

Reason: SaaS regressions usually happen at the boundary between validation, auth, and persistence.

## What We Do Not Do

- Do not put `"use client"` at the top of a route just to make a child component interactive.
- Do not call SQLite from Client Components.
- Do not edit already-applied migrations.
- Do not hide SQL in random utility files.
- Do not use string-built SQL for user input.
- Do not add an ORM unless the project explicitly chooses one.
- Do not put secrets in `NEXT_PUBLIC_*`.
- Do not swallow database errors without logging a server-side cause.
- Do not make route handlers for UI form submissions when a server action is clearer.

Reason: each of these makes the system harder to audit, slower to ship, or easier to break.

## Before Opening A PR

Run:

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

For database changes, also run migrations from a clean local database and from a copy with existing seed data.

In the PR body, include:

- What changed
- Which routes or actions are affected
- Migration notes
- Validation commands and results
- Any known risks
