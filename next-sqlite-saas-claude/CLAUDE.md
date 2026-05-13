# CLAUDE.md

Guidance for Claude Code in a greenfield SaaS app using Next.js 15 App Router, TypeScript, and SQLite through `better-sqlite3` or Turso/libSQL.

## Stack And Versions

- Next.js 15 App Router with React Server Components by default.
- TypeScript in `strict` mode.
- SQLite for the primary app database. Use `better-sqlite3` locally or Turso/libSQL when deployment needs remote access.
- Drizzle ORM is the preferred query layer because it keeps SQL visible and migrations reviewable.
- Tailwind CSS and shadcn/ui are allowed, but app logic must not live in UI components.

Reason: this stack keeps deployment simple while preserving type checks, explicit SQL, and fast local development.

## Folder Structure

```text
src/app/                 Route groups, layouts, pages, server actions
src/components/          Reusable presentational components
src/features/            Product features with UI, actions, and queries
src/lib/                 Framework adapters, auth, env, db client
src/db/schema.ts         Drizzle schema
src/db/migrations/       SQL migrations committed in order
src/server/              Services that do not belong to one route
tests/                   Unit and integration tests
```

Reason: `app/` stays route-focused, while `features/` prevents business logic from scattering across pages.

## Naming Conventions

- Components use `PascalCase.tsx`.
- Server actions use `*.actions.ts`.
- Database query modules use `*.queries.ts`.
- Validation schemas use `*.schema.ts`.
- Test files mirror the source file name with `.test.ts`.

Reason: file suffixes tell Claude which runtime and responsibility a file has before opening it.

## Dev Commands

```bash
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm db:generate
pnpm db:migrate
```

If a command is missing, add it to `package.json` before inventing a one-off command.

## Database Rules

- All schema changes start in `src/db/schema.ts`.
- Generate SQL migrations and commit them under `src/db/migrations/`.
- Never edit an applied migration. Create a new migration that moves the schema forward.
- Use transactions for multi-row writes and billing/auth state transitions.
- Prefer explicit column names in selects. Avoid `select *` in application code.
- Store timestamps as ISO strings or integer milliseconds consistently; do not mix formats.

Reason: SQLite migrations are easy to reason about when every change is append-only and reviewable.

## Server Actions And Data Flow

- Validate all user input with a schema before writing to the database.
- Return typed result objects: `{ ok: true, data }` or `{ ok: false, error }`.
- Keep redirects and cache revalidation at the route/action boundary.
- Do not call server actions from low-level components. Pass intent handlers from feature entry points.

Reason: server actions are API boundaries; treating them that way prevents UI-driven data corruption.

## Component Patterns

- Server Components fetch data and choose layout.
- Client Components handle interactivity only.
- Forms live near the feature they mutate.
- Shared UI components must be stateless unless they are generic controls.

Reason: App Router performance depends on keeping client boundaries small and intentional.

## Authentication And Authorization

- Check authentication in route loaders, server actions, and API routes.
- Authorization checks belong next to the database query or service call they protect.
- Never trust a client-provided `userId`, `teamId`, or `role`.
- Include tenant/workspace scoping in every query that reads or mutates tenant-owned records.

Reason: SaaS bugs are often cross-tenant data leaks, not missing login screens.

## Error Handling

- User-facing errors should be short and actionable.
- Logs should include stable identifiers, not secrets.
- Catch expected validation and constraint failures. Let unexpected failures surface to the error boundary.
- Never silently fall back to empty data after a failed write.

Reason: quiet failures create billing, permission, and data integrity problems.

## Anti-Patterns

- Do not put database calls in reusable visual components.
- Do not mutate SQLite schema by hand in production.
- Do not use client-side auth checks as the only protection.
- Do not add a second state manager unless React state and URL state are insufficient.
- Do not hide failed writes behind optimistic UI without rollback.
- Do not create generic service layers before two features actually share behavior.

## Before Completing Work

Run:

```bash
pnpm lint && pnpm typecheck && pnpm test
```

For database changes, also run:

```bash
pnpm db:generate && pnpm db:migrate
```

Summarize changed files, migrations, and any commands that could not be run.
