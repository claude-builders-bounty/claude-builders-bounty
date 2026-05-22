# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & commands
- Next.js 15 App Router, React 19, TypeScript strict.
- SQLite via `better-sqlite3` for local/single-node apps; Turso/libSQL only when deployment needs remote DB.
- Commands: `pnpm dev`, `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm db:migrate`.
- Server-first default: Server Components, Server Actions, Route Handlers. Add `"use client"` only for browser state/events.

## Folder structure
```txt
app/                    routes, layouts, loading/error boundaries
app/(marketing)/        public pages
app/(app)/              authenticated product UI
app/api/                webhooks or third-party API endpoints only
components/ui/          reusable dumb UI
components/features/    feature components with product language
lib/auth/               auth/session helpers
lib/db/                 sqlite connection, migrations, typed queries
lib/actions/            server actions grouped by feature
lib/validators/         zod schemas shared by actions/forms
db/migrations/          numbered SQL migrations
tests/                  unit/integration tests
```
Reason: routes stay thin, DB access is centralized, and product features are easy to delete or move.

## Naming conventions
- Files: kebab-case (`billing-table.tsx`). Components/types: PascalCase. Functions/vars: camelCase.
- Server Actions: verb-first (`createProject`, `archiveInvoice`). Route handlers: resource-first folders.
- DB tables: snake_case plural (`users`, `billing_events`). Columns: snake_case. TS maps to camelCase at boundaries.
- Env vars: uppercase and validated once in `lib/env.ts`; never read `process.env` deep inside features.

## SQLite / migration rules
- Every schema change is a new numbered SQL file: `0001_init.sql`, `0002_add_subscriptions.sql`.
- Migrations are append-only after merge. Never edit an applied migration; add a corrective migration.
- Enable `PRAGMA foreign_keys = ON` on connection open.
- Use WAL mode for better read/write behavior: `PRAGMA journal_mode = WAL` for file SQLite.
- Keep transactions explicit for multi-write flows.
- Prefer simple constraints over app-only checks: `NOT NULL`, `UNIQUE`, `CHECK`, `FOREIGN KEY`.
- Store timestamps as ISO text or integer epoch consistently; do not mix in the same DB.
- Do not build SQL with string interpolation. Use prepared statements/placeholders.

## Data access pattern
- UI never imports DB directly. UI → Server Action/Route Handler → `lib/db/*` query function.
- Each query function returns typed domain objects, not raw driver rows.
- Validate user input with zod before DB calls; validate DB-to-UI shape when external/webhook data is involved.
- Pagination is cursor-based for product lists; offset pagination only for small admin tables.

## Component patterns
- Server Components fetch initial data and compose pages.
- Client Components handle forms, optimistic UI, modals, toasts, and interactive widgets only.
- Forms call Server Actions and show field-level errors from a shared result type:
  `{ ok: true, data } | { ok: false, fieldErrors?, formError? }`.
- Keep product copy near the component that renders it; keep reusable primitives copy-free.
- Use `loading.tsx`, `error.tsx`, and empty states for every app route with remote/db data.

## Auth & tenancy
- Read the current user/session once per request boundary; pass `userId` into service/query functions.
- Every tenant-scoped query includes `user_id` or `workspace_id` in the WHERE clause.
- Never trust IDs from the client without checking ownership in the same query or transaction.

## What we don't do (and why)
- No generic repository/service layers until two features need the same abstraction; they hide simple SQL.
- No client-side data fetching for private DB data by default; it duplicates auth and loading logic.
- No migration edits after merge; SQLite rollbacks are painful in deployed apps.
- No raw SQL in React components; it makes auth, tests, and migrations harder.
- No premature multi-DB support; SQLite-specific constraints and transactions are a feature here.
- No catch-all `utils.ts`; create named modules so Claude can find the right context.

## Before changing code
1. Identify the route/feature and the DB tables touched.
2. Add or update the smallest migration/query/action/component needed.
3. Run `pnpm lint`, `pnpm typecheck`, and the closest tests before reporting done.
