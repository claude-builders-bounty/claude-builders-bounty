# CLAUDE.md — Next.js 15 + SQLite SaaS

Use this file as the default operating manual for a greenfield SaaS app built with Next.js 15 App Router, TypeScript, SQLite, and either `better-sqlite3` for local/server deployments or Turso/libSQL for hosted SQLite.

## Stack And Versions

- Next.js 15 App Router with React Server Components by default.
- TypeScript in strict mode.
- SQLite as the source of truth.
- `better-sqlite3` for single-node apps; Turso/libSQL only when multi-region or hosted SQLite is required.
- Server Actions for small mutations; Route Handlers for public APIs, webhooks, or non-form clients.
- Tailwind or CSS Modules are acceptable. Do not introduce a second styling system without deleting the first.

Reason: this stack is fastest when server-rendered reads stay simple, mutations stay close to forms, and SQLite remains boring.

## Project Structure

```text
app/
  (marketing)/
  (app)/
  api/
components/
  ui/
  forms/
db/
  migrations/
  schema.sql
  client.ts
features/
  billing/
  auth/
  workspace/
lib/
  env.ts
  errors.ts
  validation.ts
tests/
```

Rules:

- Put route files under `app/`; put business behavior under `features/`.
- Keep reusable visual primitives in `components/ui/`; keep domain forms in `components/forms/` or the relevant feature.
- Put all SQL migrations in `db/migrations/` with increasing timestamp prefixes.
- Do not hide database writes inside React components. Components may call server actions or feature services.

Reason: App Router files should stay thin so routing, UI composition, and business rules can evolve independently.

## Commands

Use these defaults unless the project already defines different package scripts:

```bash
npm run dev
npm run lint
npm run typecheck
npm test
npm run db:migrate
npm run db:studio
```

If a command is missing, add the script before relying on it in docs or CI.

## Environment

All environment access goes through `lib/env.ts`.

- Validate required variables at startup.
- Keep secrets server-only. Never expose private keys through `NEXT_PUBLIC_`.
- Use separate database URLs for development, test, and production.
- Tests must not touch the development database.

## SQLite And Migration Rules

- Every schema change gets a migration file.
- Migrations are append-only after merge. Do not edit an applied migration; add a new one.
- Prefer explicit SQL over magical schema sync.
- Use foreign keys and enable `PRAGMA foreign_keys = ON`.
- Store timestamps as ISO strings or integer milliseconds, consistently across the app.
- Use transactions for multi-table writes.
- Add indexes for foreign keys and common lookup columns.
- Never concatenate user input into SQL. Use parameters.

Reason: SQLite is reliable when schema history is clear and writes are intentionally serialized.

## Data Access Pattern

- `db/client.ts` creates the database connection.
- Feature modules expose functions such as `createWorkspace`, `listInvoices`, or `updateMemberRole`.
- Server Actions validate input, call feature functions, and return typed success/error results.
- Route Handlers validate input, call feature functions, and return JSON with explicit status codes.

Do not pass raw database rows directly into broad UI trees. Map rows to small view models at the feature boundary.

## Naming Conventions

- Files: kebab-case for components and route helpers.
- React components: PascalCase.
- Server actions: verb-first names, for example `createProjectAction`.
- Database tables: snake_case plural nouns, for example `workspace_members`.
- Database columns: snake_case.
- TypeScript types: PascalCase.

Reason: predictable names make it easy to move between routes, feature code, SQL, and generated types without guessing.

## Component Patterns

- Server Components by default.
- Add `"use client"` only for local state, browser APIs, or event handlers.
- Keep Client Components small and leaf-like.
- Forms should have pending, success, validation-error, and unexpected-error states.
- Do not fetch the same data independently in sibling components. Fetch once at the route or feature boundary.

Reason: most SaaS screens are data-heavy; keeping client JavaScript small and data loading centralized prevents duplicated queries and hydration bugs.

## Auth And Authorization

- Authentication answers "who is this user?"
- Authorization answers "can this user perform this action in this workspace?"
- Check authorization inside feature services, not only in UI.
- Never trust workspace IDs, role names, prices, or plan IDs from the client.
- Log security-relevant denials without leaking sensitive data to the browser.

Reason: every privileged action eventually becomes an API surface, so the permission check must live with the write, not with a button.

## Billing

- Treat payment provider events as the source for subscription state changes.
- Webhooks must be idempotent.
- Store provider event IDs and ignore duplicates.
- Never grant paid access from a client-side success redirect alone.

Reason: payment redirects are user-controlled navigation, while signed webhooks are the durable billing record.

## Error Handling

- Expected validation errors return typed objects that the UI can render.
- Unexpected errors are logged server-side and shown to users as plain, non-sensitive messages.
- Do not swallow database errors. Add context and rethrow or return a typed failure.

Reason: typed failures keep normal user mistakes out of exception logs, and unexpected failures keep enough context for debugging.

## Testing

- Unit test feature services with a temporary SQLite database.
- Test migrations from an empty database.
- Add at least one integration test for each critical mutation.
- Mock payment providers at the boundary.
- Do not snapshot large React trees unless the output is genuinely stable and useful.

Reason: the highest-risk bugs are migration, authorization, billing, and write-path regressions; tests should exercise those paths directly.

## What We Do Not Do

- No ORM schema auto-sync in production. It hides migration risk.
- No client-side authorization checks as the only gate. They are cosmetic.
- No direct SQL in components. It makes UI and persistence impossible to evolve separately.
- No global mutable singleton for request-specific user/session data.
- No second database "just for queues" until SQLite is proven insufficient.
- No premature microservices. A modular monolith is the default.

## Definition Of Done

- The feature has a migration if data shape changed.
- `npm run lint`, `npm run typecheck`, and relevant tests pass.
- The UI handles loading, empty, error, and success states.
- Authorization is enforced server-side.
- New environment variables are documented in `.env.example`.
