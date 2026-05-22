# CLAUDE.md - Next.js + SQLite SaaS

Use this file as the project instruction file for a SaaS app built with Next.js App Router and SQLite through better-sqlite3, Drizzle, Prisma, or Turso/libSQL.

## Project Shape

- app/: routes, layouts, loading states, server actions, and route handlers.
- components/: reusable UI components. Keep route-specific components near the route when they are not shared.
- lib/: framework-neutral helpers, auth/session helpers, billing helpers, and typed service clients.
- db/: schema, migrations, seed scripts, database client, and query helpers.
- server/: server-only business workflows that do not belong in route files.
- tests/: unit, integration, and end-to-end tests.
- public/: static assets only.

Prefer server components by default. Add "use client" only for interactive state, browser APIs, or client-only libraries.

## Commands

- pnpm install: install dependencies.
- pnpm dev: run the local app.
- pnpm lint: run lint checks.
- pnpm typecheck: run TypeScript without emitting files.
- pnpm test: run unit/integration tests.
- pnpm db:generate: generate migration files when the ORM requires it.
- pnpm db:migrate: apply local migrations.
- pnpm db:studio: inspect local data when the project provides a studio.

If the project uses npm, yarn, or bun instead of pnpm, keep the same command intent and use the repository's configured package manager.

## Naming

- React components: PascalCase.tsx.
- Hooks: useThing.ts.
- Server actions: thing.action.ts or colocated actions.ts.
- Route handlers: app/**/route.ts.
- Database schema files: db/schema.ts or db/schema/*.ts.
- Migrations: timestamped, ordered, and immutable after merge.
- Environment variables: uppercase snake case and documented in .env.example.

Use clear domain names over generic nouns. Prefer SubscriptionPlan, WorkspaceMember, and InvoiceLineItem over Data, Item, or Record.

## TypeScript

- Keep strict TypeScript enabled.
- Do not use any unless the external API is genuinely untyped and the value is narrowed immediately.
- Validate untrusted input with a schema library such as Zod, Valibot, or the repository's existing validator.
- Keep shared types close to the boundary that owns them. Export domain types from db/ or server/ only when multiple modules need them.

## Data And SQLite

- Treat SQLite as a production database with explicit transaction boundaries.
- Use prepared statements or ORM query builders. Do not concatenate untrusted strings into SQL.
- Wrap multi-step writes in transactions.
- Add indexes for foreign keys and frequently filtered columns.
- Store timestamps consistently as ISO strings or integer milliseconds; do not mix formats.
- Keep soft-delete, audit, and tenant scoping rules consistent across all queries.
- In SaaS code, every tenant-owned query must include workspace/account ownership checks.

## Migrations

- Migrations are append-only after merge.
- Never edit a migration that has already been applied in a shared environment. Add a new migration instead.
- Every schema change should include either a migration or a clear explanation for why one is not needed.
- Destructive migrations require a data-preservation plan, rollback notes, and a test against a copy of representative data.
- Backfills should be idempotent and safe to rerun.
- Do not run production migrations from build scripts.

## Auth And Sessions

- Keep auth checks on the server.
- Route handlers and server actions must verify the current user before reading or mutating tenant data.
- Do not trust client-sent user IDs, workspace IDs, roles, plan names, or prices.
- Store secrets only in environment variables or the platform secret store.
- Never log session tokens, OAuth tokens, API keys, reset tokens, or payment provider secrets.

## Billing

- Treat billing webhooks as the source of truth for subscription state.
- Verify webhook signatures before processing events.
- Make webhook handlers idempotent by storing processed event IDs.
- Keep pricing IDs in environment variables or a typed config module.
- Do not calculate final invoice totals on the client.

## UI Patterns

- Use existing design system components before adding new primitives.
- Keep forms accessible with labels, errors, disabled states, and pending states.
- Prefer server-rendered data tables and paginated queries for large collections.
- Client state should represent UI state, not authoritative business state.
- Avoid marketing-style layouts inside operational SaaS dashboards.

## Testing

- Add focused tests for authorization checks, tenant scoping, billing webhooks, and migration/backfill behavior.
- Test server actions and route handlers with authenticated and unauthenticated cases.
- For SQLite query changes, include at least one test that exercises real SQL against a test database.
- Update snapshots only when the rendered behavior intentionally changes.

## Patterns To Follow

- Small route handlers that call typed server functions.
- Explicit input validation at the boundary.
- Centralized database client creation.
- Transaction helpers for multi-step writes.
- Idempotent webhook and background job handlers.
- .env.example kept in sync with required environment variables.

## Patterns To Avoid

- Client-side authorization gates as the only protection.
- Raw SQL string interpolation with user input.
- Hidden database writes inside React render paths.
- Schema changes without migrations.
- Running worker infrastructure during next build.
- Committing local SQLite database files, .env, logs, or generated secrets.

## Before Finishing A Change

1. Run the smallest relevant test or typecheck.
2. Confirm migrations are present and ordered when schema changed.
3. Check tenant ownership on all new data reads and writes.
4. Update .env.example and setup docs for new configuration.
5. Summarize validation performed and any remaining risk.
