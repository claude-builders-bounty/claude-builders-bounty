# CLAUDE.md - Next.js 15 + SQLite SaaS

## Stack and versions
- Next.js 15 App Router, React Server Components by default, TypeScript strict mode.
- SQLite via better-sqlite3 for local/server deployments or Turso/libSQL for hosted edge-friendly deployments.
- Tailwind or CSS modules are acceptable; keep UI primitives in app/components and business logic in lib/.

## Folder structure
- app/: route groups, pages, layouts, server actions.
- app/api/: thin HTTP adapters only. Put reusable logic in lib/services.
- components/: reusable UI components with no database access.
- lib/db/: connection, migrations, schema helpers, seed scripts.
- lib/services/: business rules and transactional operations.
- tests/: unit tests for services and migration helpers.

## SQL and migration conventions
- Every schema change is a timestamped migration in lib/db/migrations.
- Migrations must be idempotent where possible and wrapped in transactions.
- Never edit an already-applied migration. Add a new migration instead.
- All write paths go through service functions; UI and route handlers do not compose SQL strings.

## Component patterns
- Prefer server components for data loading and client components only for interactivity.
- Validate form inputs at the server boundary with a schema.
- Keep optimistic UI small and reversible; never assume a payment or subscription succeeded until the webhook confirms it.

## What we do not do and why
- No direct database calls from React components: it couples UI to persistence and makes migrations risky.
- No raw string-concatenated SQL: use prepared statements to prevent injection.
- No secret values in client components or NEXT_PUBLIC variables unless truly public.
- No hidden background spending; paid APIs require explicit config and budget limits.

## Dev commands
- npm run dev: start local app.
- npm run lint: lint and typecheck.
- npm test: run service tests.
- npm run db:migrate: apply migrations.
