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

- Database tables use `snake_case` plural names: `users`, `projects`, `billing_events`, because SQL stays readable and table names do not fight generated TypeScript names.
- TypeScript values use `camelCase`; React components and exported types use `PascalCase`, because the code should match the wider React and TypeScript ecosystem.
- Server actions are named as commands: `createProject`, `archiveProject`, `inviteMember`, because mutations should read like intentional product actions.
- Query helpers are named by result: `getProjectById`, `listProjectsForUser`, because call sites should reveal what data shape they receive.
- Boolean database columns start with `is_`, `has_`, or `can_`, because generated row types should read clearly and avoid ambiguous flags like `active`.

## SQL And Migration Rules

- Every schema change is a new committed SQL file: `db/migrations/0007_add_project_slug.sql`, because deploy history must be reviewable and replayable.
- Migrations are append-only. Do not edit a migration that has reached `main`; add a corrective migration, because other environments may already have applied the original file.
- Prefer explicit constraints: `not null`, `unique`, `check`, and foreign keys with deliberate `on delete` behavior, because SQLite should reject invalid states before app code has to guess.
- Store timestamps as ISO-8601 UTC text unless the app already standardizes on integer milliseconds, because humans can inspect text timestamps directly during support/debugging.
- Wrap multi-step writes in transactions at the service layer, not inside random route handlers, because consistency belongs with the business operation being protected.
- Never build SQL by string concatenation with user input. Use prepared statements and named helpers, because injection bugs are easier to prevent than audit later.
- SQLite has limited `ALTER TABLE`; for complex changes, create the new table, copy validated data, drop the old table, and rename, because this is the reliable path for constraints and column rewrites.

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

- Start as a Server Component. Add `"use client"` only for local state, browser APIs, effects, or interactive controls, because client boundaries increase bundle size and data-leak risk.
- Keep data loading in route segments or server helpers. Pass plain serializable props into components, because component trees should be easy to render, test, and refactor.
- Forms should call Server Actions for trusted mutations and return typed field errors, because validation and authorization must run on the server path.
- Use optimistic UI only after the server path is already correct and tested, because fast feedback should not mask broken writes.
- Keep repeated UI primitives in `components/ui`; keep workflow-specific UI in `components/product`, because generic components should stay reusable and product flows should stay understandable.
- Accessibility is part of done: labels, focus states, keyboard paths, and semantic buttons/links, because SaaS users repeat workflows and keyboard/screen-reader paths are core usability.

## Service And Action Patterns

- Server Actions validate input with Zod, authorize the current user, call one service function, then revalidate or redirect, because each mutation should have one obvious security and data-flow path.
- Service functions accept explicit dependencies when useful for tests, but avoid dependency-injection frameworks, because simple functions are enough for most Next.js SaaS codebases.
- Route handlers are for webhooks, external APIs, and streaming. Internal product mutations should usually be Server Actions, because product forms should stay close to App Router conventions.
- Errors returned to users are safe and specific enough to act on. Logs may include internal detail; UI must not leak secrets, because supportability cannot come at the cost of disclosure.

## What We Do Not Do

- Do not import database helpers into Client Components, because it breaks the server/client boundary and leaks architecture into UI.
- Do not add an ORM unless the project already uses one, because SQLite migrations and prepared statements are easier to audit here.
- Do not create catch-all utility files, because ownership disappears when unrelated helpers collect in one place.
- Do not hide authorization inside components, because permissions belong in server actions, route handlers, or service functions where they cannot be bypassed by UI changes.
- Do not store money as floats, because rounding errors become billing defects. Use integer cents or the smallest currency unit.
- Do not add background jobs without an idempotency key and retry story, because SaaS background work will be retried after deploys, crashes, and provider timeouts.
- Do not make a migration depend on local data that only exists on one machine, because migrations must run in clean CI, preview, and production environments.

## Completion Gates

Before calling work done:

- `pnpm lint`, `pnpm typecheck`, and relevant tests pass, because type and behavior regressions should be caught before review.
- New writes have validation, authorization, and transaction coverage where needed, because most SaaS bugs are bad input, bad access, or partial writes.
- User-facing copy explains the outcome without exposing implementation details, because users need next steps rather than stack traces.
- The change can be reviewed from the diff without relying on unstated local setup, because reviewers should not have to reverse-engineer local state.
