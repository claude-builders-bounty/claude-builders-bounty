# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions
- Next.js 15 App Router + TypeScript strict mode
- Node.js 22 LTS, pnpm 9
- SQLite via `better-sqlite3` (or Turso + libsql client)
- Drizzle ORM for schema + migrations

Reason: boring, fast local dev stack with deterministic migrations and low infra overhead.

## Folder Structure
- `app/` route segments, layouts, server actions per domain
- `features/<domain>/` business logic, validators, DTOs
- `components/` shared UI primitives only
- `db/` schema, migrations, seed, query modules
- `lib/` framework glue (auth, telemetry, cache)
- `tests/` integration + e2e by user journey

Reason: domain-first organization prevents App Router files from becoming business-logic graveyards.

## Naming Rules
- Files: kebab-case (`billing-invoice-table.tsx`)
- Components: PascalCase exports; one default export max per file
- Server actions: `verbNounAction` (`createInvoiceAction`)
- DB tables: plural snake_case; columns singular snake_case

Reason: mixed naming multiplies cognitive load and breaks grep speed.

## SQL & Migration Conventions
- Never edit an applied migration file.
- One migration per logical change.
- Include forward SQL + rollback notes in migration header.
- Add indexes in same migration as feature query paths.
- Run migrations in CI against a clean DB before tests.

Reason: schema drift kills small SaaS teams; deterministic migrations keep incidents low.

## Component & Data Patterns
- Fetch data server-side first; pass serialized view models to client components.
- Keep client components interactive-only (forms, toggles, optimistic UI).
- Validate all action input with Zod before DB writes.
- Wrap DB writes in explicit transactions for multi-table updates.

Reason: server/client separation improves security, bundle size, and traceability.

## Dev Commands
- `pnpm dev` — app dev server
- `pnpm typecheck` — strict TS gate
- `pnpm test` — unit/integration
- `pnpm test:e2e` — journey validation
- `pnpm db:generate && pnpm db:migrate` — migration flow

## Anti-Patterns (Do Not Do)
- No raw SQL in React components (leaks boundaries).
- No silent `any` or `@ts-ignore` for domain logic (hides defects).
- No direct mutation of request bodies (breaks auditability).
- No force-push to protected branches (kills review integrity).
- No migration squashing after production deploy.

Reason: each anti-pattern causes expensive, recurring defects in SaaS velocity loops.
