# CLAUDE.md

Guidance for Claude Code when working in a greenfield SaaS app built with Next.js 15 App Router, TypeScript, Tailwind CSS, and SQLite through `better-sqlite3` or Turso/libSQL.

## Stack And Versions

- Use Next.js 15 with the App Router in `app/`; do not add the legacy Pages Router.
- Use TypeScript in strict mode. Prefer explicit input/output types at module boundaries and inferred types inside small functions.
- Use React Server Components by default. Mark a component with `"use client"` only when it needs browser state, effects, refs, or event handlers.
- Use SQLite as the system of record. Local development uses a file database through `better-sqlite3`; hosted deployments may use Turso/libSQL with the same schema.
- Use Tailwind CSS for styling and keep design tokens in `tailwind.config.ts` or CSS variables, not inline magic values spread through components.
- Use a validation library such as `zod` at request, form, and environment boundaries because SQLite and TypeScript do not validate runtime input.

## Folder Structure

```text
app/
  (marketing)/
  (app)/
  api/
  layout.tsx
  page.tsx
components/
  ui/
  forms/
  domain/
db/
  migrations/
  schema.ts
  client.ts
  queries/
lib/
  auth/
  env.ts
  validation/
  utils.ts
server/
  actions/
  services/
tests/
  unit/
  integration/
```

- Route groups separate public marketing screens from authenticated app screens without leaking layout state across the two.
- `components/ui` contains reusable primitives with no business rules. Domain components live in `components/domain` and may call typed props from server-loaded data.
- `db/client.ts` is the only place that opens database connections. This prevents accidental connection churn in route handlers and tests.
- `db/queries` contains small typed query functions. UI and route handlers must not inline SQL strings because query ownership becomes impossible to audit.
- `server/services` holds multi-step business operations. Server Actions and route handlers should validate input, call a service, and translate the result for the caller.

## Dev Commands

```bash
npm run dev          # start the local app
npm run lint         # run lint rules before every PR
npm run typecheck    # run TypeScript without emitting files
npm run test         # run unit and integration tests
npm run db:migrate   # apply pending SQLite migrations
npm run db:studio    # inspect local data when available
```

- Add a script before documenting a command. Claude should not invent commands that are not present in `package.json`.
- Run `lint`, `typecheck`, and the narrowest relevant test command after any behavior change.

## Environment Rules

- Read environment variables only from `lib/env.ts`.
- Validate `process.env` once at startup with `zod`; export typed values from that module.
- Keep local defaults in `.env.example`, not in application code.
- Never log secrets, access tokens, database URLs, session cookies, or raw OAuth payloads.

## SQL And Migration Conventions

- Every schema change gets a numbered migration in `db/migrations`, for example `0004_add_customer_plan.sql`.
- Migrations are append-only after merge. If a migration is wrong before merge, edit it; after merge, add a corrective migration.
- Keep migrations deterministic: no calls to wall-clock time, network APIs, random values, or local filesystem state.
- Prefer explicit column lists in `INSERT` and `SELECT` statements. This keeps future schema additions from changing query behavior.
- Use `INTEGER` for booleans with `0` and `1`, and convert at the query boundary.
- Store timestamps as ISO 8601 UTC text unless the project has a documented reason to use integer epoch values.
- Add indexes in the same migration as the query pattern that needs them. Name indexes as `idx_<table>_<columns>`.
- Wrap multi-step writes in transactions. SQLite is reliable when writes are intentional; partial writes are usually application bugs.
- Do not use `SELECT *` outside throwaway diagnostics. Returned shapes should be deliberate and typed.

## Data Access Patterns

- Query functions return plain objects, not framework response objects.
- Services own authorization checks for domain operations. UI checks are for hiding controls, not enforcing permissions.
- Keep write functions idempotent when they can be retried by the client or by a route handler.
- Model expected failures as typed results, for example `{ ok: false, code: "SLUG_TAKEN" }`, instead of throwing for normal product states.
- Throw only for programmer errors, corrupted state, and infrastructure failures.

## Component Patterns

- Server components load data and pass serialized props down to client components.
- Client components handle interaction only; they should not import database modules, secrets, or server-only services.
- Keep forms close to their route segment and put reusable field controls in `components/forms`.
- Use Server Actions for same-app mutations that naturally return UI state. Use route handlers for webhooks, public API endpoints, and integrations.
- Use `Suspense` around slow server-rendered regions instead of turning the whole page into a client component.
- Prefer composition over prop switches. If a component gains many boolean props, split it into named variants.

## Naming Conventions

- Files that export React components use kebab-case filenames and PascalCase component names.
- Server Actions end in `.action.ts`; service modules end in `.service.ts`; query modules end in `.query.ts`.
- Database table names are plural snake_case. TypeScript identifiers are camelCase.
- Use domain names in code, such as `workspace`, `subscription`, and `invoice`, instead of generic names such as `item` or `record`.

## Testing Rules

- Unit-test pure validation, formatting, and query-shaping logic.
- Integration-test database queries against a temporary SQLite database with migrations applied.
- Add a regression test for every bug fix that changes behavior.
- Tests should create their own data and clean up after themselves. Do not depend on a developer's local database file.
- Do not snapshot large rendered pages. Assert the user-visible state or database change that matters.

## Security And Auth

- Treat every Server Action and route handler as a public entry point.
- Validate input before authorization-sensitive work. Then authorize against server-loaded session data, not client-supplied user IDs.
- Use parameterized SQL for every user-provided value.
- Keep webhook verification in the route handler before parsing business payloads.
- Set cookies as `httpOnly`, `secure` in production, `sameSite=lax` by default, and scoped to the narrowest useful path.

## What We Do Not Do

- Do not add an ORM by default. SQLite is simple enough for typed query helpers, and avoiding an ORM keeps migrations and SQL performance visible.
- Do not create client components for entire pages just to use one interactive control. Isolate the control instead.
- Do not duplicate validation schemas between client and server. Share schema modules when the validation is identical.
- Do not bury product rules in React components. Put product decisions in services so API routes, Server Actions, and tests share the same behavior.
- Do not make migrations depend on generated TypeScript code. Migrations must remain runnable even if the app build is broken.
- Do not silently swallow database errors. Convert expected constraint failures to typed results and let unexpected failures surface.
- Do not introduce global mutable singletons other than the database connection cache needed for development hot reload.

## Pull Request Checklist

- The change keeps the App Router structure intact and does not add Pages Router files.
- Database changes include a migration, query updates, and integration coverage.
- Server Actions and route handlers validate input and enforce authorization on the server.
- New client components are justified by interaction needs.
- `npm run lint`, `npm run typecheck`, and relevant tests pass or the PR explains why they could not run.
