# CLAUDE.md — Next.js 15 (App Router) + SQLite SaaS

This file tells Claude Code how to work in a typical production Next.js 15 App Router SaaS using SQLite (local `better-sqlite3` or hosted Turso/libSQL).

## Goals (non-negotiable)
- Keep data access **server-only**.
- Keep UI components **pure** and predictable.
- Make DB changes **migratable** and reviewable.
- Prefer **boring + testable** over clever.

## Stack assumptions (choose one where applicable)
- Next.js 15+ App Router, TypeScript, React Server Components (RSC).
- Package manager: `pnpm` (preferred), but `npm`/`yarn` ok.
- SQLite runtime:
  - Local dev: `better-sqlite3` (fast, single file).
  - Production: Turso/libSQL via `@libsql/client` (or any hosted SQLite).
- DB layer (recommended): **Drizzle ORM** + migrations. (Reason: lightweight, SQLite-friendly, easy to keep server-only.)
- Validation: **Zod** for runtime safety at boundaries.

If the repo uses different tools, adapt patterns but keep the constraints.

## Commands (don’t guess — read package.json first)
Common patterns:
- Install: `pnpm i` / `npm i` / `yarn`
- Dev: `pnpm dev`
- Typecheck: `pnpm typecheck` or `pnpm tsc -p tsconfig.json --noEmit`
- Lint: `pnpm lint`
- Test: `pnpm test`

DB (if Drizzle is used):
- Generate migrations: `pnpm drizzle-kit generate`
- Apply migrations (local): `pnpm drizzle-kit migrate`

## Project structure (opinionated)
Use this baseline:
- `src/app/` — routes, layouts, RSC-first
- `src/components/` — shared UI components (client components allowed, but minimal)
- `src/lib/` — framework-agnostic utilities
- `src/server/` — **server-only** code (db, auth, services, repositories)
- `src/server/db/` — db client + schema + migrations
- `src/server/repos/` — data access (queries, transactions)
- `src/server/services/` — business logic (orchestration; calls repos)
- `src/server/actions/` — Server Actions (thin; call services)
- `src/types/` — shared types (no server secrets)
- `tests/` — unit/integration tests

Reason: Separates UI, data access, and business logic so refactors don’t break everything.

## Naming conventions (be consistent)
- Files:
  - Components: `PascalCase.tsx`
  - Non-components: `kebab-case.ts`
- Exports:
  - React components: `PascalCase`
  - Functions: `camelCase`
  - Constants: `SCREAMING_SNAKE_CASE` only when truly constant
- DB:
  - Tables/columns: `snake_case` (Reason: SQL is nicer to read/port.)
  - IDs: `id` primary key; prefer `text` IDs (ULID/UUID) unless you need integer perf.
  - Timestamps: `created_at`, `updated_at` in UTC (store ISO or integer epoch, but be consistent).

## Database rules (SQLite-first)
### Migrations
- Every schema change ships as a migration (no “manual production edits”).
- Migrations must be:
  - deterministic
  - reversible when feasible (or explicitly documented when not)
  - safe under concurrent app deploys
- Treat migrations like code: review in PRs, keep them small.

### Transactions
- Use transactions for multi-write flows.
- Keep transaction scopes short (no network calls inside).

### Constraints
- Prefer DB constraints (NOT NULL, UNIQUE, FK where practical) over app-only checks.
- Add the index you need **with a reason** (what query becomes fast).

## Server/client boundaries (critical)
### Server-only code
DB clients, SQL, secrets, and auth providers must live under `src/server/**`.

Enforce at the file level:
- Add `"server-only"` at the top of DB modules when possible.
- Never import `src/server/**` from client components.

Reason: accidental bundling of secrets and DB drivers is a production incident.

### RSC-first
- Default every route to a Server Component.
- Only add `"use client"` when you need:
  - hooks/state
  - event handlers
  - browser-only APIs

Reason: fewer bundles, faster pages, fewer hydration bugs.

## Data access pattern (the only allowed one)
1) UI calls a Server Action (or Route Handler).
2) Server Action validates input (Zod) and calls a service.
3) Service enforces business rules and calls repositories.
4) Repository performs DB reads/writes.

Reason: Keeps validation and permissions centralized, and makes it testable.

## Server Actions (do’s and don’ts)
Do:
- Validate all inputs with Zod.
- Return typed results (success/error objects), not thrown errors.
- Keep actions thin; push real work into `services/`.

Don’t:
- Don’t write SQL directly in actions.
- Don’t call external APIs inside DB transactions.
- Don’t return raw DB rows to the client without mapping (avoid leaking columns).

## Auth & multi-tenant SaaS rules (baseline)
Even if the project starts single-tenant, design for tenant boundaries early.
- Every tenant-scoped table has `tenant_id`.
- Every repo query that touches tenant data filters by `tenant_id`.
- Never trust client-provided `tenant_id`; derive it from session.

Reason: the most common SaaS security bug is “forgot tenant filter once”.

## Input validation & output shaping
- Validate at boundaries:
  - Server Action inputs
  - Route Handler request bodies
  - Webhook payloads
- Shape outputs:
  - Map DB rows → domain objects → view models
  - Avoid passing through columns you don’t need

Reason: prevents accidental PII leakage and makes refactors safe.

## Caching & revalidation (App Router)
- Prefer `fetch()` with explicit caching semantics.
- If a mutation changes data shown on a cached page:
  - call `revalidatePath()` or `revalidateTag()`
  - or use `noStore()` for truly dynamic pages

Reason: “it works locally” caching bugs destroy trust in SaaS dashboards.

## Error handling
- Use a single error shape for actions: `{ ok: false, error: { code, message } }`.
- Log unexpected errors server-side with enough context to reproduce.
- Do not leak internals to the client.

## What we don’t do (anti-patterns)
- No direct DB access from React components (even server components) unless it goes through repos.
  - Reason: business rules drift and queries duplicate.
- No “god” `lib/db.ts` exporting random helpers.
  - Reason: makes ownership and testing impossible.
- No `any` / `as unknown as` to “make TypeScript shut up”.
  - Reason: it becomes runtime bugs in billing flows.
- No storing money as floating point.
  - Reason: rounding errors; use integer cents.
- No writing migrations by hand without running them locally.
  - Reason: broken prod deploys.

## Checklist for Claude before opening a PR
- Read `package.json` and existing folders; follow repo conventions if present.
- Keep server-only imports out of client components.
- Add/adjust migrations for any schema changes.
- Add tests for any non-trivial business rule.
- Ensure types are sound; avoid widening types to hide errors.
- Run `lint`, `typecheck`, and `test` (or explain why you can’t).

