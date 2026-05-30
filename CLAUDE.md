# Next.js 15 + SQLite SaaS (App Router) - Claude Code Guide

This repo is a typical Next.js 15 App Router SaaS using SQLite (either local `better-sqlite3` or remote `Turso/libsql`).
Treat this file as the project's operating manual: follow these rules by default, and only deviate when a change request explicitly demands it.

## Stack And Versions

- Next.js: 15.x (App Router)
- React: 19.x
- TypeScript: strict
- DB: SQLite
  - Local: `better-sqlite3` (sync driver)
  - Remote: Turso (libSQL) via `@libsql/client`
- Migrations: SQL files checked into git (no runtime schema drift)

## Dev Commands

- Install: `pnpm i` (preferred) or `npm i`
- Dev server: `pnpm dev`
- Typecheck: `pnpm typecheck` (or `tsc -p tsconfig.json`)
- Lint: `pnpm lint`
- Tests: `pnpm test` (if present)

If a command is missing in package scripts, add it rather than inventing ad-hoc shell commands.

## Project Layout

Assume this layout unless the actual repo differs:

- `src/app/`: App Router routes, layouts, server actions
- `src/components/`: shared React components
- `src/lib/`: pure utilities and shared infrastructure (db, auth, etc)
- `src/server/`: server-only modules (db queries, jobs). Never import from client code.
- `src/db/`:
  - `schema/`: SQL schema and migrations
  - `queries/`: typed query helpers

Do not create new top-level folders unless there's a strong reason. Prefer `src/lib/*` for shared code.

## Server vs Client Rules

- Default to Server Components.
- Only add `"use client"` when you need:
  - client-side stateful UI
  - browser-only APIs
  - event handlers that must run in the browser
- Never import DB code into client components.
- Never expose secrets to the client. Environment variables should be read on the server only.

Reason: server/client boundaries are the #1 source of accidental leaks and bundling errors in App Router apps.

## Database Conventions

### Connection Ownership

- There is exactly one DB entrypoint:
  - Local SQLite: `src/lib/db.ts` exports a singleton connection
  - Turso/libSQL: `src/lib/db.ts` exports a singleton client
- All queries go through `src/db/queries/*`.

Reason: constraining DB access prevents circular deps and makes migrations + testing predictable.

### Migrations

- Migrations are append-only SQL files in `src/db/schema/migrations/`.
- File naming: `YYYYMMDDHHMM_<short_slug>.sql` (UTC).
- Each migration must be idempotent when feasible:
  - Use `IF NOT EXISTS` for tables/indexes
  - For columns, prefer safe patterns (create new column + backfill + switch code) rather than destructive alter
- Never edit old migrations after they have shipped.

Reason: editing historical migrations breaks new environment bootstraps and makes rollbacks impossible to reason about.

### Query Style

- Prefer explicit column lists (no `SELECT *`).
- Always include deterministic ordering for paginated queries: `ORDER BY created_at DESC, id DESC`.
- For deletes/updates:
  - Require a `WHERE` clause unless deleting by primary key.
  - Prefer soft-delete (`deleted_at`) for user content.

Reason: SQLite makes it easy to do the wrong thing quickly; we trade a little verbosity for safety.

### Types And Data Mapping

- Convert DB rows to app types at the query boundary.
- Keep timestamps in ISO strings at the app boundary (or `Date` consistently) but do not mix.
- Never return raw DB rows directly to UI components.

Reason: row shapes drift as schema evolves; mapping at the boundary reduces blast radius.

## Naming Conventions

- Files:
  - components: `kebab-case.tsx`
  - server/lib modules: `kebab-case.ts`
- React components: `PascalCase`
- DB query functions: `verbNoun` (e.g., `listProjects`, `getUserById`, `createInvoice`)
- Server actions: `actionVerbNoun` (e.g., `actionCreateProject`)

Reason: consistent naming makes it obvious which modules are safe to import where.

## Patterns To Follow

### Server Actions

- Validate all inputs (zod or hand-rolled guards).
- Authorization check happens before any DB calls.
- Return structured errors (do not throw raw strings).

### API Routes

- Keep API routes thin: validate, auth, call query layer, format response.
- Prefer server actions over API routes for internal app workflows.

### Background Jobs

- Jobs live in `src/server/jobs/*`.
- Jobs must be idempotent and safe to retry.

## Anti-Patterns (Do Not Do These)

- Do not put DB clients in `src/app/*` directly.
  - Reason: route modules get re-evaluated and can create too many connections.
- Do not put query logic inside React components.
  - Reason: makes caching and testing harder.
- Do not store JSON blobs when a real table makes sense.
  - Reason: SQLite indexing and schema evolution are better with explicit columns.
- Do not mix `better-sqlite3` and `@libsql/client` in the same runtime codepath.
  - Reason: drivers have different semantics (sync vs async); keep the abstraction boundary clean.

## What I Need From You Before Big Changes

If a request touches any of these, ask a clarifying question first:

- auth provider choice (NextAuth, Clerk, custom)
- multi-tenant model (orgs vs workspaces vs teams)
- deployment target (Vercel, Fly, self-hosted) and whether SQLite is local or remote (Turso)
- data retention/soft delete policy

Reason: these decisions change schema and API boundaries.

