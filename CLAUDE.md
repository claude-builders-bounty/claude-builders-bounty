# CLAUDE.md

This project is a Next.js 15 SaaS starter backed by SQLite.
This file is the source of truth for how code is written and structured.

## Stack & versions
- Next.js 15 (App Router), React 19, TypeScript strict.
- SQLite: `better-sqlite3` locally; Turso (`@libsql/client`) in production/serverless.
- Drizzle ORM for schema and migrations; no raw SQL in app code.
- Zod for input validation at the action/API boundary.
- Tailwind CSS 4 for styling; `src/components/ui` holds shadcn-style primitives.
- pnpm is the only package manager.

## Dev commands
- `pnpm dev` — start the dev server
- `pnpm build` — type-check and create a production build
- `pnpm lint` — lint and type-check
- `pnpm test` — run unit/integration tests
- `pnpm db:generate` — create a migration from Drizzle schema changes
- `pnpm db:migrate` — apply pending migrations
- `pnpm db:studio` — inspect the local SQLite database

## Project structure

    src/
      app/
        (marketing)/
        (dashboard)/
      components/
        ui/
        features/<name>/
      db/
        schema/
        client.ts
        migrations/
      lib/
      server/
        actions/
        services/
      validations/

## Naming conventions
- Routes and non-component files are `kebab-case`.
- React components are `PascalCase.tsx`.
- Server Actions and service functions are `camelCase` in `kebab-case` files.
- Drizzle table names are plural `snake_case`; columns are singular `snake_case`. Foreign keys end in `_id`.
- Timestamps end in `_at` and are stored as ISO-8601 UTC text (e.g. `created_at`, `updated_at`).
- Use reserved Next.js filenames exactly: `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`, `not-found.tsx`.
- Do not hand-write DB types; infer them with `InferSelectModel<typeof users>` from the schema.

## DB / migration rules
- The Drizzle schema is the source of truth. Change `src/db/schema/**`, then run `pnpm db:generate`.
- Never edit files in `src/db/migrations/`. Generate a new migration for each change.
- One migration per logical change. Do not squash or rewrite merged migration history.
- SQLite ALTER TABLE is limited. New columns must be nullable or have a default.
- Destructive changes (drop column/table, change constraint) require creating a new table, copying data, renaming, and updating indexes inside one migration.
- Enable `PRAGMA foreign_keys = ON` and `PRAGMA journal_mode = WAL` on every better-sqlite3 connection.
- Use `TEXT` + `CHECK` instead of native enums; SQLite has no enum type.
- All reads/writes go through Drizzle. No hand-written SQL strings in app code.

## Component patterns
- Default to Server Components. Add `'use client'` only for interactivity, state, or browser-only APIs.
- When a file becomes a client component, its imports are client too. Pass server-rendered `children` into client components instead of importing server modules.
- Mutations are Server Actions called directly from forms. No client `fetch('/api/...')` for CRUD.
- After a successful mutation, `redirect()` from `next/navigation`; don't use client-side `router.push()` from an action.
- Use `useTransition` / `useFormStatus` for pending states instead of `useState` loading flags.
- Read data in server components or services and pass primitives/plain objects down to components.
- Fetch nested data with Drizzle relations via `db.query`; avoid N+1 queries by preloading relations.
- For expensive shared reads, wrap the query in Next.js `cache()`.
- Every Server Action/service that touches user data calls `auth()` first and never trusts a client-sent `userId`.
- `params` and `searchParams` are Promises in Next.js 15 — always `await` them in layouts/pages.

## What we don't do (and why)
- No `useEffect` + `fetch` for data that can be rendered server-side. Reason: extra round trips, loading states, and stale cache.
- No REST API routes for plain CRUD. Reason: Server Actions are the typed mutation layer; API routes are only for webhooks/public integrations.
- No raw SQL in components or services. Reason: Drizzle gives compile-time column safety; raw SQL becomes unmaintainable and bypasses migrations.
- No `any` or `@ts-ignore` in db/action code. Reason: DB rows are a contract; losing types causes silent production bugs.
- No auth/session data in `localStorage`. Reason: XSS can steal it; use httpOnly cookies.
- No deleting or rewriting merged migrations. Reason: migration history must stay identical across every environment or databases drift.
- No business logic in components. Reason: services are testable and reusable; components should render.
- No using npm/yarn. Reason: pnpm's strict node_modules catches missing dependencies that npm silently allows.