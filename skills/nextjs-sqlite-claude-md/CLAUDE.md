# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

Opinionated conventions for a greenfield B2B SaaS on Next.js 15 and SQLite.
Paste this file at the repository root. Do not ask the user to clarify stack choices —
they are fixed below.

## Stack & versions

| Piece | Choice | Pin | Why |
|-------|--------|-----|-----|
| Framework | Next.js App Router | 15.x | RSC + Server Actions; no Pages router |
| Runtime DB (local) | better-sqlite3 | 11.x | Sync API, WAL mode, single-writer discipline |
| Runtime DB (prod) | Turso libSQL | latest | Same SQL dialect; edge replicas without Postgres ops |
| ORM | Drizzle | 0.38+ | Schema-as-code migrations; no Prisma client weight |
| Auth | better-auth | 1.x | Cookie sessions; SQLite adapter; no JWT in localStorage |
| Validation | Zod | 3.x | Shared schemas between Server Actions and forms |
| UI | shadcn/ui + Tailwind | 4.x / 3.4+ | Copy-paste components; no opaque component library |
| Tests | Vitest + Playwright | 2.x / 1.x | Unit vs E2E split; no Jest |
| Package manager | pnpm | 9.x | `packageManager` field enforced; no npm/yarn |

**Rule:** Never introduce Prisma, tRPC, Redux, or Mongo. If the user asks, explain the SQLite
single-writer model and offer Drizzle + Server Actions instead.

## Folder structure

```
app/
  (marketing)/          # Public pages — no auth check
  (app)/                # Authenticated shell — layout verifies session
    dashboard/
    settings/
  api/
    webhooks/stripe/    # Raw body + signature verify only here
  actions/              # Server Actions (*.ts); one file per domain
components/
  ui/                   # shadcn primitives only
  app/                  # Product components (not reusable primitives)
db/
  schema.ts             # Drizzle table defs
  migrations/           # SQL files — never edit after merge to main
  client.ts             # getDb() — libsql in prod, better-sqlite3 in dev
lib/
  auth.ts               # better-auth server instance
  stripe.ts             # Stripe server client (lazy init)
  env.ts                # Zod-validated process.env
scripts/
  migrate.ts            # Applies pending migrations; run in CI before deploy
```

**Naming:** kebab-case files; PascalCase React components; `use-` prefix only for client hooks.
Route groups use parentheses and never appear in URLs.

## SQL & migration conventions

1. Migrations are forward-only SQL in `db/migrations/NNNN_description.sql` (4-digit zero pad).
2. Every table has `id TEXT PRIMARY KEY` (UUID v7 generated in app) and `created_at INTEGER NOT NULL`
   (Unix ms). No auto-increment integers — they leak ordering and complicate replication.
3. Soft-delete via `deleted_at INTEGER` nullable; hard-delete only in GDPR erasure scripts.
4. Foreign keys ON in dev (`PRAGMA foreign_keys = ON`); Turso enforces in prod.
5. One migration per PR. Never squash merged migrations.
6. Indexes: name `idx_<table>_<columns>`; add index in same migration as the query that needs it.

**WAL:** Local SQLite uses `journal_mode=WAL` and `busy_timeout=5000`. Writers go through a single
`getDb()` module; readers may use replicas on Turso.

## Component & data patterns

- **Server Components default.** Add `"use client"` only for event handlers, browser APIs, or
  Radix primitives that require it.
- **Mutations:** Server Actions in `app/actions/<domain>.ts`. Each action: Zod parse → auth check →
  Drizzle transaction → `revalidatePath` or `revalidateTag`.
- **Reads:** Fetch in Server Components with Drizzle; no `useEffect` data loading.
- **Forms:** `react-hook-form` + Zod resolver; submit via Server Action; show toast on result.
- **Errors:** Throw `ActionError` with code; map to user-safe messages in the action boundary.
  Never return stack traces to the client.
- **Stripe:** Checkout Sessions for subscriptions; webhooks update `subscriptions` table;
  idempotency keys on webhook handlers.

## Dev commands

```bash
pnpm install
cp .env.example .env.local          # fill DATABASE_URL, AUTH_SECRET, STRIPE_* 
pnpm db:migrate                     # scripts/migrate.ts
pnpm dev                            # localhost:3000
pnpm test                           # vitest
pnpm test:e2e                       # playwright (needs dev server)
pnpm lint                           # biome check .
```

## What we do not do (and why)

| Anti-pattern | Why |
|--------------|-----|
| API routes for CRUD the UI owns | Server Actions are simpler and type-safe |
| `use client` on layout.tsx | Forces full-tree client JS |
| Storing JWT in localStorage | XSS steals sessions; use httpOnly cookies |
| `SELECT *` in hot paths | Explicit columns; SQLite still parses unused cols |
| Shared DB connection in Serverless without pooler | Use Turso HTTP or singleton in Node runtime |
| Editing old migrations | Breaks prod; add a new forward migration |
| `any` or `@ts-ignore` | Fix the type; Zod at boundaries |
| Feature flags in env without defaults | `env.ts` must fail fast at boot |

## Billing & multi-tenancy

- `organizations` table; users belong via `memberships` with role enum `owner|admin|member`.
- Row scope: every query filters `organization_id = session.activeOrgId` in the action layer.
- Stripe `customer_id` on org, not user. Seat limits enforced in Server Actions before invite.

## When unsure

1. Prefer Server Component + Server Action over new API route.
2. Prefer Drizzle transaction over multiple round trips.
3. Prefer explicit SQL migration over `drizzle-kit push` in production.
4. Ask one clarifying question only if the request violates a rule above; otherwise implement.
