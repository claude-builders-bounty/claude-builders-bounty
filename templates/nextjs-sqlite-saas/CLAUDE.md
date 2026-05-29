# CLAUDE.md: Next.js 15 + SQLite SaaS

Use this file as the project instructions for a production SaaS built with Next.js 15 App Router, TypeScript, SQLite, Drizzle or Prisma, and either `better-sqlite3` for local/server deployments or Turso/libSQL for hosted edge-compatible storage.

## Stack And Versions

- Runtime: Node.js 22 LTS. Use one package manager per repo and keep the lockfile committed.
- Framework: Next.js 15 App Router with React Server Components by default.
- Language: TypeScript in strict mode. Do not introduce untyped `any` unless wrapping an external API boundary with a comment explaining why.
- Database: SQLite with Drizzle or Prisma migrations. Use `better-sqlite3` for single-node deployments and Turso/libSQL when distributed reads or managed hosting are required.
- Auth: Prefer a maintained auth library such as Better Auth, Auth.js, or Clerk. Never hand-roll password storage.
- Styling: Tailwind CSS or the existing design system. Keep server logic out of UI components.
- Payments and email: Put provider integrations behind small service modules so Stripe, Lemon Squeezy, Resend, or Postmark can be swapped without touching route handlers.

## Dev Commands

Use the commands already defined in `package.json`. If they are missing, add these names before inventing alternatives:

```bash
pnpm dev          # start local Next.js app
pnpm lint         # run linting
pnpm typecheck    # run TypeScript checks
pnpm test         # run unit/integration tests
pnpm db:generate  # generate migration files
pnpm db:migrate   # apply migrations locally
pnpm db:studio    # inspect local data
```

## Project Structure

Use this structure unless the existing project already has a clear equivalent:

```text
src/
  app/
    (auth)/
    (dashboard)/
    api/
    layout.tsx
    page.tsx
  components/
    ui/
    forms/
    layout/
  db/
    schema.ts
    client.ts
    migrations/
    queries/
  features/
    billing/
    organizations/
    projects/
    users/
  lib/
    auth.ts
    env.ts
    errors.ts
    logger.ts
  server/
    actions/
    services/
    validators/
  tests/
```

Rules:

- `src/app` owns routing, metadata, loading states, and thin request boundaries.
- `src/features/<domain>` owns domain UI and workflows. Keep feature-specific components out of global `components/`.
- `src/server/services` owns business operations that combine auth, validation, database writes, and external APIs.
- `src/db/queries` owns reusable read models. Do not hide writes in query helpers.
- `src/lib/env.ts` is the only place that reads raw environment variables.

## Naming Conventions

- Components: `PascalCase.tsx`.
- Hooks: `useThing.ts`.
- Server actions: `thing.actions.ts`.
- Validators: `thing.schema.ts`.
- Database tables: plural snake_case, for example `users`, `organizations`, `billing_events`.
- Database columns: snake_case in SQL, camelCase in TypeScript if the ORM supports mapping cleanly.
- IDs: use `id` for primary keys and `<entity>Id` for foreign keys in TypeScript.

## App Router Rules

- Prefer Server Components. Add `"use client"` only for state, browser APIs, effects, or event handlers.
- Keep route handlers thin: parse input, call a service, return a typed response.
- Put `loading.tsx`, `error.tsx`, and `not-found.tsx` close to the route they serve.
- Use Server Actions for form mutations inside the app. Use route handlers for webhooks, third-party callbacks, and public API endpoints.
- Always revalidate or redirect after mutations that affect visible pages.

## SQLite And Migration Rules

- Every schema change must be represented by a committed migration file. Never rely on `db push` or implicit sync in production.
- Migrations must be forward-only. Do not edit a migration after it has been applied outside local development.
- Use transactions for multi-table writes.
- Enable foreign keys for SQLite connections:

```sql
PRAGMA foreign_keys = ON;
```

- Add indexes for foreign keys and frequent lookup fields such as `user_id`, `organization_id`, `slug`, `email`, and `created_at`.
- Store timestamps as ISO strings or integer milliseconds consistently across the project. Do not mix formats.
- Avoid long-running write transactions. SQLite has one writer at a time, so keep external API calls outside transactions.
- For Turso/libSQL, design for network latency: batch related statements and avoid chatty request loops.

## Data Access Pattern

Use this layering for mutations:

```text
UI form -> server action or route handler -> validator -> service -> db transaction -> revalidate/redirect
```

Use this layering for reads:

```text
page/server component -> query helper -> db -> typed view model
```

Do not call the database directly from shared UI components. It makes components impossible to reuse and easy to accidentally convert to client components later.

## Validation And Errors

- Validate all external input with Zod, Valibot, or the existing validator.
- Return field-level errors for forms and structured JSON errors for API routes.
- Never expose raw database or provider errors to users.
- Log the original error with request context, then return a safe message.
- Treat webhooks as untrusted until signature verification succeeds.

## Auth, Tenancy, And Security

- Every protected read and write must check the authenticated user.
- For organization-scoped data, require both `userId` and `organizationId` checks. A valid session alone is not authorization.
- Never trust client-submitted role, price, plan, owner, or organization fields.
- Use `httpOnly`, `secure`, and `sameSite` cookies through the auth library.
- Keep secrets server-only. Any variable exposed to the browser must use the framework's public prefix and contain no secret value.
- Add rate limits to auth, invite, billing, and AI endpoints.

## Component Patterns

- Build small form components around explicit props. Avoid components that fetch their own data unless they are Server Components.
- Use accessible labels, keyboard states, and error messages for every input.
- Keep table, list, and dashboard views dense and scannable. SaaS users return to complete work, not to read marketing copy.
- Use optimistic UI only when rollback behavior is clear.
- Prefer composition over global stores. Reach for a client store only when state is shared across distant interactive components.

## Testing Expectations

- Unit test pure utilities, validators, and permission checks.
- Integration test service functions that write to SQLite.
- Add at least one test for each critical SaaS workflow: signup/login, organization access, billing state changes, and destructive mutations.
- For database tests, use an isolated temporary SQLite file or in-memory database per test file.
- Mock payment, email, and AI providers at the service boundary.

## Pull Request Checklist

Before opening a PR:

- Run lint, typecheck, tests, and migrations locally.
- Include migration files for schema changes.
- Confirm protected routes reject unauthenticated users.
- Confirm tenant-scoped routes reject users from other organizations.
- Update `.env.example` when adding or changing environment variables.
- Add or update tests for new service behavior.

## What We Do Not Do

- Do not put business rules in React components. Components should render workflows, not define authorization or billing logic.
- Do not run schema changes manually in production. Manual SQL creates invisible drift.
- Do not read `process.env` throughout the codebase. Centralized env parsing catches missing configuration at startup.
- Do not use `any` to silence TypeScript. Define the boundary type or parse unknown input.
- Do not make client components by default. Client components increase bundle size and can leak server-only assumptions.
- Do not store money as floating point numbers. Use integer minor units such as cents.
- Do not trust webhook payloads without signature verification.
- Do not skip indexes because the local SQLite database is small. SaaS tables grow in the exact places dashboards query repeatedly.
