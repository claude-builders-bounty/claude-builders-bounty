# CLAUDE.md — Next.js 15 + SQLite SaaS

This project is a production SaaS app using Next.js 15 App Router, TypeScript, Tailwind, and SQLite through either `better-sqlite3` for single-node deployments or Turso/libSQL for hosted edge-adjacent deployments.

## Stack and versions

- Next.js 15 App Router. Use Server Components by default.
- React 19-compatible patterns. Avoid legacy Pages Router conventions.
- TypeScript strict mode. Do not use `any` unless the boundary is untyped and isolated.
- SQLite as the source of truth. Keep schema changes explicit and reversible.
- Tailwind for styling. Keep component variants in code, not scattered string soup.

Reason: this stack is fast to ship, cheap to run, and easy to reason about if server/client boundaries stay clean.

## Project structure

```text
app/
  (marketing)/        Public pages
  (app)/              Authenticated product routes
  api/                Route handlers only when HTTP is required
components/
  ui/                 Small reusable primitives
  forms/              Form components with validation wiring
  layout/             Shells, nav, page chrome
lib/
  db/                 SQLite client, schema helpers, migrations
  auth/               Session/user helpers
  actions/            Server actions grouped by domain
  validators/         Zod schemas shared by forms/actions
  services/           Business logic that should not import React
migrations/           Numbered SQL files
scripts/              One-off maintenance scripts
```

Rules:
- Route files should orchestrate, not contain business logic.
- `lib/services/*` must not import from `app/*` or React.
- Database access goes through `lib/db/*`; never open ad-hoc SQLite connections in components.

## Commands

Use these unless the project README says otherwise:

```bash
npm run dev          # local app
npm run build        # production build gate
npm run lint         # lint gate
npm run typecheck    # TypeScript gate
npm run db:migrate   # apply migrations
npm run db:studio    # inspect local data, if available
```

Before calling work done, run at least:

```bash
npm run typecheck && npm run lint && npm run build
```

If a command is missing, add it to `package.json` instead of inventing a one-off command in chat.

## SQLite and migrations

- Migrations live in `migrations/` and are named `YYYYMMDDHHMM_description.sql`.
- Every schema change gets a migration. Do not edit old migrations after they have shipped.
- Prefer additive migrations: add nullable column, backfill, then enforce constraints in a later migration.
- Use transactions for multi-step migrations.
- Foreign keys must be enabled with `PRAGMA foreign_keys = ON` at connection setup.
- Store timestamps as ISO-8601 text or integer epoch consistently. Do not mix both in one table.
- Money values are integer minor units, e.g. cents. Never store currency amounts as floats.

Reason: SQLite is reliable, but only if schema history is boring and deterministic.

## Data access pattern

Use small typed functions:

```ts
export async function getProjectById(id: string): Promise<Project | null> {
  return db.prepare("select * from projects where id = ?").get(id) ?? null;
}
```

Do not inline SQL inside Server Components. Components should ask services for typed data.

For writes:
- validate input with Zod
- check authorization before mutation
- write in a transaction when touching multiple tables
- return a typed success/error object

## Server and client components

Default to Server Components.

Use `"use client"` only for:
- local interactive state
- browser APIs
- animations requiring client state
- controlled form UX that cannot be handled by server actions alone

Never import `lib/db/*`, secrets, or server-only services into a client component.

## Server actions

Server actions belong in `lib/actions/<domain>.ts`.

Pattern:
1. parse/validate input
2. load current user/session
3. authorize
4. call service/database layer
5. revalidate affected paths
6. return `{ ok: true, data }` or `{ ok: false, error }`

Do not throw expected validation errors. Return them.

## API routes

Use route handlers for:
- webhooks
- third-party integrations
- public API endpoints
- file uploads/downloads

Do not create API routes just so client components can call your own server. Prefer Server Components or Server Actions.

## Auth and authorization

- Authentication answers “who is this?”
- Authorization answers “can they do this?”

Every write path must call an authorization helper near the mutation. UI hiding is not authorization.

Keep session helpers in `lib/auth/`. Do not duplicate cookie parsing across routes.

## Component patterns

- Components should be small and named by domain intent: `ProjectSettingsForm`, not `Form2`.
- Keep shared UI primitive names boring: `Button`, `Input`, `Dialog`.
- Pass typed props. Avoid spreading unknown database rows directly into components.
- Loading states go in `loading.tsx` or local Suspense boundaries.
- Error states go in `error.tsx` or explicit empty/error components.

## Forms and validation

- Define Zod schemas in `lib/validators/*`.
- Reuse the same schema in forms and server actions where practical.
- Show field-level errors when possible.
- Disable submit while pending, but do not rely on that for duplicate prevention. Enforce idempotency server-side when needed.

## Naming conventions

- Files: kebab-case for components and modules.
- Components/types: PascalCase.
- Functions/variables: camelCase.
- Database tables: snake_case plural nouns, e.g. `projects`, `user_memberships`.
- Database columns: snake_case.
- IDs: use text IDs (`uuid`, `cuid`, or similar) unless there is a strong reason for autoincrement.

## Error handling

- Expected user errors: return typed result objects.
- Unexpected system errors: log server-side, show generic message client-side.
- Never expose raw SQL errors, stack traces, tokens, or environment variables to the browser.

## Security defaults

- Never trust `FormData` or JSON request bodies.
- Validate webhook signatures before parsing business data.
- Use parameterized SQL only. No string-concatenated SQL.
- Keep secrets server-only and read them through a typed env helper.
- Add rate limits to auth, invite, upload, and expensive AI/API routes.

## Testing expectations

For meaningful changes, include the smallest useful gate:

- pure functions: unit test
- database behavior: migration + query test with temp SQLite DB
- server action: validation/authorization test
- page flow: Playwright smoke test when the repo already has e2e tests

Do not add a new test framework unless the project has none and the change needs it.

## Anti-patterns

Do not:
- put SQL in React components
- mutate data from Client Components without Server Actions/API validation
- add dependencies for one helper function
- use `any` to silence real type problems
- store money as floats
- edit shipped migrations
- create API routes for internal-only calls
- duplicate auth checks in five places
- claim a fix is done without running the relevant gate

## Definition of done

A change is done when:
- types pass
- lint/build pass, or the missing gate is documented
- migrations are included for schema changes
- authorization is enforced on write paths
- README/env docs are updated if setup changed
- no secrets or generated local files are committed
