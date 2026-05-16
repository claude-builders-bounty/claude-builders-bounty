# CLAUDE.md — Next.js 15 (App Router) + SQLite SaaS (opinionated)

This repo is a **typical SaaS app** built with **Next.js 15 App Router** and **SQLite** (either **Turso/libSQL** or **better-sqlite3** locally).

Claude: follow the rules below when making changes. When something is unclear, prefer **small, testable steps** and **ask one focused question** rather than guessing.

---

## North Star

- Keep changes **boring** and **auditable**: small diffs, clear commit/PR descriptions, minimal magic.
- Prefer **server-side** work by default (Server Components + Route Handlers) to reduce client bundle size and complexity.
- Prefer **end-to-end correctness** over clever abstractions.

---

## Project structure (expected)

```
app/
  (marketing)/
  (app)/
  api/
  layout.tsx
  page.tsx
  error.tsx
  loading.tsx
components/
  ui/
  marketing/
  app/
lib/
  db/
  auth/
  billing/
  env.ts
  http.ts
  errors.ts
  id.ts
server/
  actions/
  services/
  validators/
  jobs/
db/
  schema/
  migrations/
  seeds/
scripts/
tests/
```

Rules:
- `app/**` is **routing + composition** (pages/layouts/route handlers). Keep business logic out.
- `server/**` is **business logic** (pure-ish functions, services, validators). This is what we unit test.
- `lib/**` holds shared utilities, typed environment access, and low-level helpers.
- `db/**` holds schema + migrations + seeds. Database logic lives in `lib/db` and is consumed by `server/services`.

Why: separating routing from business logic keeps the app maintainable and makes it easy for Claude to change one layer without breaking everything.

---

## Next.js App Router conventions (very specific)

- Default to **React Server Components**:
  - Only add `"use client"` when you truly need browser-only features (event handlers, local state, DOM APIs).
  - If you add `"use client"`, ensure you are not importing server-only modules (`lib/db`, `server/*`, secret env access).
- Data fetching:
  - Prefer server-side fetching in route segments (`page.tsx`, `layout.tsx`) or in `server/services/*`.
  - Prefer `fetch()` with explicit cache semantics:
    - `cache: "no-store"` for per-request user data
    - `next: { revalidate: <seconds> }` for cacheable marketing pages
- Error boundaries:
  - Use `app/**/error.tsx` for user-friendly error states and a retry button.
  - Never leak raw error messages to the UI; map to safe messages.
- Route groups `(marketing)` vs `(app)` are not cosmetic:
  - `(marketing)` must not import authenticated app-only modules.
  - `(app)` assumes auth/session exists and must enforce it server-side.

Why: App Router power comes from clear server/client boundaries; violating them creates subtle build/runtime failures.

---

## Naming conventions (do not drift)

- Files:
  - `kebab-case` for folders and non-component files: `billing-webhook.ts`
  - `PascalCase` for React components: `PricingCard.tsx`
- Exports:
  - `camelCase` for functions: `createCheckoutSession()`
  - `PascalCase` for components/types: `User`, `InvoiceLineItem`
  - `SCREAMING_SNAKE_CASE` for constants only when they are truly constants: `PLAN_LIMITS`
- Route Handlers:
  - `app/api/**/route.ts` only exports HTTP methods: `export async function POST(...)`
- Database:
  - Table names: `snake_case` plural: `users`, `billing_events`
  - Column names: `snake_case`: `created_at`, `stripe_customer_id`
  - Foreign keys: `<table>_id` (e.g., `user_id`)
  - IDs are **string** (ULID/UUID) unless we explicitly chose integer autoincrement.

Why: consistent naming makes searches and refactors reliable.

---

## Environment variables

- Access env via `lib/env.ts` only (single source of truth).
- Never read `process.env.*` throughout the codebase.
- Validate at startup using a schema (zod or equivalent).
- Distinguish server-only vs client-exposed values:
  - Client: must start with `NEXT_PUBLIC_`
  - Server: everything else

Why: prevents runtime “undefined env var” bugs and accidental secret leakage to the browser bundle.

---

## SQLite strategy (Turso/libSQL vs local)

We support:
- **Local dev**: file-based SQLite via `better-sqlite3` (fast, simple).
- **Prod**: Turso/libSQL (recommended) or another SQLite-compatible hosted option.

Rules:
- All DB access goes through `lib/db/*`.
- Do not scatter raw SQL strings across the app; keep queries in one place per domain (e.g., `lib/db/users.ts`).
- Prefer parameterized SQL always.
- Do not introduce ORMs without an explicit decision; use the existing query layer.

Why: SQLite is easy to misuse with concurrent access and ad-hoc schema drift; centralizing queries keeps it safe.

---

## Database migrations (strict)

Migration folder: `db/migrations/`

Rules:
- Migrations are **append-only**. Never edit an already-applied migration in shared history.
- Each migration is:
  - named with sortable prefix: `2026-05-16_0459_create_users.sql`
  - **idempotent where feasible** (or guarded)
  - includes **down** steps only if the project standard includes them; otherwise omit.
- Every schema change must be accompanied by:
  - the migration
  - updated TypeScript types (if we mirror schema types)
  - a small targeted test (or a script) that exercises the new column/index constraint

SQLite-specific rules:
- Changing column types is hard; prefer creating a new column + backfill + swap when necessary.
- Use `PRAGMA foreign_keys = ON;` and ensure your connection enables it.
- Add indexes deliberately. Indexes speed reads but slow writes and increase file size.

Why: schema drift is the #1 source of “works on my machine” bugs in small SaaS apps.

---

## API + Server Actions

Default choices:
- Use **Server Actions** for authenticated, app-internal mutations (forms/buttons).
- Use **Route Handlers** (`app/api/**`) for webhooks, public APIs, and integrations.

Rules:
- Route Handlers must:
  - validate input (schema)
  - return typed JSON (`Response.json(...)`)
  - handle auth explicitly
  - never call UI code
- Server Actions must:
  - validate input
  - return a small typed result `{ ok: true } | { ok: false, error: ... }`
  - never throw raw errors to the client; map to safe messages

Why: keeps your app’s mutation surface predictable and makes it easy to harden later.

---

## Auth & billing (common SaaS constraints)

- Never trust client-provided `userId`, `email`, `plan`, or `role`.
- Derive permissions server-side and enforce them in `server/validators/*`.
- Webhooks:
  - verify signatures first
  - write the raw event (idempotently) before side effects
  - use an idempotency key (`event_id`) and unique constraint to avoid duplicates

Why: these are the highest-risk code paths for data leaks and double-charging.

---

## “Do / Don’t” patterns

Do:
- Prefer `async` server functions that accept explicit args (no hidden globals).
- Add tests at the `server/**` layer.
- Keep React components small; push logic down into `server/services`.
- Use feature flags/config objects rather than branching everywhere.

Don’t:
- Don’t put DB calls in React components (including Server Components) unless it’s a thin read wrapper.
- Don’t add new global state libraries (Redux, Zustand, etc.) unless we already use them.
- Don’t add complex build tooling (monorepo, turborepo) for a small app without a clear need.
- Don’t optimize prematurely; measure first.

Why: these guardrails keep a small SaaS from becoming a “framework zoo”.

---

## Development commands (typical)

If `package.json` differs, follow it. Otherwise use these defaults:

```bash
# install
pnpm install

# dev
pnpm dev

# typecheck
pnpm typecheck

# lint
pnpm lint

# tests
pnpm test

# format
pnpm format
```

DB utilities (typical):
```bash
# apply migrations
pnpm db:migrate

# generate seed data
pnpm db:seed

# open a local sqlite shell
pnpm db:studio
```

Why: standardized commands reduce confusion for new contributors and for Claude.

---

## PR checklist (required)

- [ ] Small diff, scoped to one outcome
- [ ] Input validated (schema)
- [ ] DB change includes migration
- [ ] Tests or a reproducible script added
- [ ] No secrets in code, logs, or env examples
