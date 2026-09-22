# CLAUDE.md

Guidance for Claude Code working in this repository. This is an opinionated
setup for a **Next.js 15 (App Router) + SQLite** SaaS. Every rule has a reason;
follow them unless the user explicitly overrides.

## Stack & versions

- **Next.js 15**, App Router only (no `pages/`). React 19 Server Components by default.
- **TypeScript**, `strict: true`. No `any` — use `unknown` + narrowing.
- **SQLite** via **better-sqlite3** (synchronous, single-node) or **Turso/libSQL**
  (edge/hosted). Pick one per project; do not mix drivers.
- **Drizzle ORM** for schema + typed queries and **drizzle-kit** for migrations.
- **Tailwind CSS** for styling. **Zod** for input validation. **Vitest** for tests.
- Package manager: **pnpm** (lockfile committed).

Reason: pinning the stack keeps generated code consistent and avoids Claude
guessing between App/Pages router, ORMs, or drivers.

## Dev commands

```bash
pnpm install            # install deps
pnpm dev                # start dev server (localhost:3000)
pnpm build              # production build (must pass before PRs)
pnpm lint               # eslint + typecheck
pnpm test               # vitest
pnpm db:generate        # drizzle-kit generate (create migration from schema)
pnpm db:migrate         # apply migrations
```

Always run `pnpm lint` and `pnpm build` before declaring a task done.

## Folder structure

```
app/                    # App Router routes (route groups in parentheses)
  (marketing)/          # public pages
  (app)/                # authenticated app
  api/                  # route handlers (prefer Server Actions over these)
  layout.tsx, page.tsx
components/
  ui/                   # presentational, reusable, no data fetching
  <feature>/            # feature-specific components
lib/
  db/
    schema.ts           # Drizzle schema (single source of truth)
    index.ts            # db client (singleton)
    migrations/         # generated SQL migrations — never edit by hand
  auth.ts, validation/  # zod schemas
server/
  actions/              # Server Actions ("use server"), one file per feature
  services/             # business logic, framework-agnostic, unit-tested
tests/
```

Reason: separating `server/services` (pure logic) from `server/actions`
(framework glue) keeps business rules testable without booting Next.js.

## SQL / migration conventions

- **Schema is the source of truth** (`lib/db/schema.ts`). Change the schema, then
  `pnpm db:generate` to produce a migration. **Never hand-edit generated SQL** in
  `lib/db/migrations/` — it breaks drizzle's checksum tracking.
- **Never** run `DROP TABLE`, `TRUNCATE`, or `DELETE` without `WHERE` against a
  real database. Destructive schema changes go through a reviewed migration.
- Table names `snake_case` and plural (`users`, `api_keys`); TS fields `camelCase`
  (Drizzle maps them). Every table has `id` (text UUID or autoincrement),
  `created_at`, `updated_at`.
- All money as **integer cents**, never floats. All timestamps stored **UTC**.
- The db client is a **singleton** (`lib/db/index.ts`); do not open a new
  connection per request — better-sqlite3 is synchronous and one handle is
  correct and fastest.

Reason: migration-first prevents drift between code and DB; the destructive-op
ban prevents accidental data loss during agentic edits.

## Component & data patterns

- **Server Components by default.** Add `"use client"` only when you need state,
  effects, or browser APIs — and push it to the smallest leaf component.
- **Fetch data in Server Components / Server Actions**, never in client
  `useEffect`. Mutations go through Server Actions that validate input with Zod
  first, then call a `server/services` function.
- Route handlers (`app/api/*`) only for webhooks or third-party callbacks;
  prefer Server Actions for app mutations.
- Validate **every** external input (form, query, webhook) with a Zod schema at
  the boundary. Never trust `formData` directly.
- Keep components presentational; business logic lives in `server/services`.

Reason: Server-first data flow removes client/server waterfalls and keeps
secrets server-side; centralised validation prevents injection and bad data.

## Auth & security

- Session checks happen in a `middleware.ts` and are re-verified inside each
  Server Action (defence in depth) — never rely on the client to enforce access.
- Scope every query by the authenticated user/tenant id; never accept a
  tenant/user id from the request body for authorization.
- Secrets only in `.env` (server) — never `NEXT_PUBLIC_*` for anything secret.

## What we DON'T do (and why)

- **No Pages Router / `getServerSideProps`** — App Router only. Mixing the two
  confuses routing and data-fetching conventions.
- **No client-side data fetching for first render** (`useEffect` + `fetch`) —
  causes waterfalls and leaks logic to the client.
- **No raw SQL string interpolation** — always parameterised Drizzle queries, to
  prevent SQL injection.
- **No hand-edited migrations** — breaks drizzle checksums.
- **No `any`, no non-null `!` assertions** to silence TS — fix the type.
- **No floats for money**, **no local time** stored — cents + UTC only.
- **No new dependency** without a reason; prefer the stack above. Pin versions.

Reason: these are the recurring ways SaaS codebases rot or get breached; banning
them up front keeps Claude's output production-safe by default.
