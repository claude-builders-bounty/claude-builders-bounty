# CLAUDE.md

## Stack And Versions

- Next.js 15 App Router with TypeScript, React Server Components by default, and Server Actions for trusted mutations.
- SQLite through `better-sqlite3` for embedded local-first apps or Turso/libSQL for hosted SQLite. Keep the domain API the same so the app can switch drivers without UI rewrites.
- Zod validates all external input at route, action, webhook, and form boundaries because SQLite will happily store malformed strings unless the app refuses them first.
- Tailwind CSS plus a small component layer. Prefer boring, accessible HTML over clever abstractions.

## Project Structure

```text
app/
  (marketing)/           public pages
  (app)/                 authenticated product routes
  api/                   route handlers and webhooks
components/
  ui/                    generic reusable primitives
  product/               domain-specific components
db/
  client.ts              SQLite connection factory
  migrations/            numbered SQL migration files
  schema.ts              table names, row types, query helpers
lib/
  actions/               server actions
  auth/                  session and permission helpers
  services/              domain services used by routes/actions
  validation/            zod schemas
tests/
  fixtures/
  integration/
```

Folders mirror ownership. Route files orchestrate. `lib/services` owns business behavior. `db` owns persistence details. UI components never import `db`.

## Naming Conventions

- Database tables use `snake_case` plural names: `users`, `projects`, `billing_events`.
- TypeScript values use `camelCase`; React components and exported types use `PascalCase`.
- Server actions are named as commands: `createProject`, `archiveProject`, `inviteMember`.
- Query helpers are named by result: `getProjectById`, `listProjectsForUser`.
- Boolean database columns start with `is_`, `has_`, or `can_` so generated row types read clearly.

## SQL And Migration Rules

- Every schema change is a new committed SQL file: `db/migrations/0007_add_project_slug.sql`.
- Migrations are append-only. Do not edit a migration that has reached `main`; add a corrective migration.
- Prefer explicit constraints: `not null`, `unique`, `check`, and foreign keys with deliberate `on delete` behavior.
- Store timestamps as ISO-8601 UTC text unless the app already standardizes on integer milliseconds.
- Wrap multi-step writes in transactions at the service layer, not inside random route handlers.
- Never build SQL by string concatenation with user input. Use prepared statements and named helpers.
- SQLite has limited `ALTER TABLE`; for complex changes, create the new table, copy validated data, drop the old table, and rename.

## Dev Commands

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm db:migrate
```

If the repo uses `npm`, `bun`, or `yarn`, keep the command names equivalent and update this section before coding.

## Component Patterns

- Start as a Server Component. Add `"use client"` only for local state, browser APIs, effects, or interactive controls.
- Keep data loading in route segments or server helpers. Pass plain serializable props into components.
- Forms should call Server Actions for trusted mutations and return typed field errors.
- Use optimistic UI only after the server path is already correct and tested.
- Keep repeated UI primitives in `components/ui`; keep workflow-specific UI in `components/product`.
- Accessibility is part of done: labels, focus states, keyboard paths, and semantic buttons/links.

## Service And Action Patterns

- Server Actions validate input with Zod, authorize the current user, call one service function, then revalidate or redirect.
- Service functions accept explicit dependencies when useful for tests, but avoid dependency-injection frameworks.
- Route handlers are for webhooks, external APIs, and streaming. Internal product mutations should usually be Server Actions.
- Errors returned to users are safe and specific enough to act on. Logs may include internal detail; UI must not leak secrets.

## What We Do Not Do

- Do not import database helpers into Client Components. It breaks the server/client boundary and leaks architecture into UI.
- Do not add an ORM unless the project already uses one. SQLite migrations and prepared statements are easier to audit here.
- Do not create catch-all utility files. Put helpers near the domain that owns them.
- Do not hide authorization inside components. Permissions belong in server actions, route handlers, or service functions.
- Do not store money as floats. Use integer cents or the smallest currency unit.
- Do not add background jobs without an idempotency key and retry story.
- Do not make a migration depend on local data that only exists on one machine.

## Completion Gates

Before calling work done:

- `pnpm lint`, `pnpm typecheck`, and relevant tests pass.
- New writes have validation, authorization, and transaction coverage where needed.
- User-facing copy explains the outcome without exposing implementation details.
- The change can be reviewed from the diff without relying on unstated local setup.
