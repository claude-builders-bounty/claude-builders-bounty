# CLAUDE.md — Next.js 15 + SQLite SaaS template

Use this file as the operating contract for a greenfield SaaS built with Next.js 15 App Router and SQLite via `better-sqlite3` for local/single-node apps or Turso/libSQL for hosted/serverless apps.

## Stack & versions

- Next.js 15 with App Router, React Server Components by default, TypeScript in strict mode.
- SQLite as the system of record:
  - `better-sqlite3` for Node runtime deployments with persistent disk.
  - Turso/libSQL when the deployment target has ephemeral disk or needs managed replicas.
- Tailwind CSS for styling and a small component layer in `src/components/ui`.
- Server actions or route handlers for mutations; no client-side direct database access.
- Zod for all external input validation.

Reason: this stack keeps a SaaS small, inspectable, and cheap. Most early SaaS products do not need distributed databases or a separate API service.

## Dev commands

Use these commands unless the project README overrides them:

```bash
npm run dev          # start local dev server
npm run build        # production build gate
npm run lint         # lint/style gate
npm run typecheck    # TypeScript gate
npm run db:migrate   # apply pending migrations
npm run db:studio    # optional local DB browser if configured
```

If a command is missing, add it to `package.json` before relying on it in docs or CI.

## Folder structure

```text
src/
  app/
    (marketing)/       # public pages: landing, pricing, legal
    (app)/             # authenticated product area
    api/               # route handlers for webhooks or external callbacks only
  components/
    ui/                # reusable primitives with no product logic
    app/               # product-specific composed components
  db/
    index.ts           # DB connection factory
    schema.ts          # typed table/row definitions if using a query builder
    migrations/        # numbered SQL migrations
    queries/           # named read/write functions; no SQL in React components
  lib/
    auth.ts            # session/user helpers
    env.ts             # validated environment variables
    errors.ts          # shared error/result helpers
  features/
    billing/
    onboarding/
    workspaces/
```

Reason: App Router controls routing, `features` holds product domains, and `db/queries` prevents SQL from leaking into UI files.

## Naming conventions

- Files and folders: `kebab-case` (`create-workspace-form.tsx`).
- React components: `PascalCase` exports (`CreateWorkspaceForm`).
- Server actions: verb-first names ending in `Action` (`createWorkspaceAction`).
- Database query functions: verb-first and explicit (`getWorkspaceBySlug`, `insertInvite`).
- SQL migrations: `YYYYMMDDHHMM_description.sql`.
- Environment variables: `UPPER_SNAKE_CASE`, validated in `src/lib/env.ts`.

Reason: predictable names make search, refactors, and code review faster.

## SQL / migration conventions

- Every schema change is a forward-only SQL migration committed to `src/db/migrations`.
- Never mutate an existing migration after it has shipped; create a new one.
- Wrap multi-step migrations in transactions when SQLite supports the statements involved.
- Prefer explicit constraints: `NOT NULL`, `UNIQUE`, `CHECK`, and foreign keys.
- Enable foreign keys on every connection: `PRAGMA foreign_keys = ON`.
- Store timestamps as ISO-8601 UTC text unless the project already standardizes on integer epoch milliseconds.
- Use `INTEGER PRIMARY KEY` for internal row IDs and stable public IDs (`TEXT`) when exposing identifiers in URLs.
- Add indexes for every foreign key and common lookup path.

Reason: SQLite is reliable when schema changes are boring, explicit, and reproducible.

## Data access rules

- React components must not build raw SQL.
- Put reads/writes in `src/db/queries/*` and export small named functions.
- Validate all user input with Zod before calling a mutation query.
- Return typed domain objects, not driver-specific row shapes, from query helpers.
- Keep transactions close to the write operation that needs atomicity.

Reason: one narrow data layer makes auth checks, tests, and future Turso/better-sqlite3 swaps safer.

## Component patterns

- Default to Server Components for data fetching and page composition.
- Use Client Components only for stateful UI, browser APIs, optimistic updates, or event handlers.
- Keep forms small:
  - server-rendered page loads initial data;
  - client form handles local state;
  - server action validates and mutates;
  - redirect/revalidate after success.
- UI primitives in `components/ui` must be product-agnostic.
- Product components in `components/app` may know about SaaS concepts like workspace, plan, or role.

Reason: Server Components reduce client JavaScript and keep database access on the server.

## Auth, tenancy, and permissions

- Every product query must be scoped by the current user or workspace.
- Never trust workspace IDs, role names, or price IDs from the client.
- Centralize permission checks in `src/lib/auth.ts` or a domain-specific policy module.
- Admin-only routes must check authorization on the server, not just hide navigation.
- Webhook handlers must verify signatures before parsing business data.

Reason: most SaaS security bugs are missing tenant filters or client-trusted authorization.

## Error handling

- Use expected errors as typed results: `{ ok: false, code, message }`.
- Throw only for unexpected programmer/system failures.
- Do not expose raw SQL errors to users.
- Log enough context to debug, but never log secrets, tokens, full payment payloads, or private user content.

Reason: predictable errors give users clear feedback and keep logs safe.

## Testing expectations

- Unit-test pure domain logic and query helpers.
- Add at least one integration test for each critical mutation path.
- Use a temporary SQLite database for DB tests; do not reuse a developer's local DB.
- For UI flows, test the happy path and one permission failure.
- Any bug fix should include a regression test when feasible.

Reason: SQLite makes integration tests cheap; use that advantage.

## What we don't do (and why)

- Do not add Prisma by default. It is useful, but for a small SQLite SaaS raw SQL or a tiny query layer is easier to inspect and migrate.
- Do not create a separate backend service until there is a concrete scaling or integration reason.
- Do not put secrets in `.env.example`; use placeholder names only.
- Do not call the database from Client Components. It breaks the security boundary.
- Do not create generic abstractions before there are two real use cases.
- Do not use global mutable singletons for request-specific data like current user/workspace.
- Do not accept large scope changes without updating migrations, tests, and README commands.

Reason: boring architecture ships faster and fails in easier-to-debug ways.

## Before finishing any task

1. Run the smallest relevant gate: `typecheck`, `lint`, targeted tests, or `build`.
2. Update migrations and docs when behavior or schema changes.
3. Check that all new data access is tenant-scoped.
4. Summarize what changed, what was verified, and any remaining risk.
