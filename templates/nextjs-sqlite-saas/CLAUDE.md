# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

Opinionated operating manual for Claude Code on a greenfield SaaS built with
**Next.js 15 (App Router)** and **SQLite** (`better-sqlite3` locally or **Turso**
in production). Paste this file at the repo root. Do not ask clarifying questions
about stack defaults below unless the user overrides them.

---

## Stack & versions (locked)

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js **15** App Router + TypeScript strict | Server Components default; RSC-first |
| Runtime | Node 22 LTS | Matches Vercel Fluid / local |
| Package manager | `pnpm` | Deterministic lockfile, fast |
| DB | SQLite via `better-sqlite3` (dev) / `@libsql/client` Turso (prod) | One schema, zero Docker for solo builders |
| Migrations | SQL files in `db/migrations/` applied by `scripts/migrate.ts` | Diffable, reviewable, no magic ORM churn |
| Auth | Auth.js (NextAuth v5) with DB sessions | Cookie sessions beat brittle JWT for SaaS |
| UI | Tailwind CSS v4 + shadcn/ui primitives only when interactive | No decorative card spam |
| Validation | Zod at every boundary (forms, route handlers, webhooks) | Fail closed |
| Testing | Vitest + Playwright smoke | Unit near domain; e2e for money paths only |

Do **not** introduce Prisma, Drizzle, Redux, or a separate Express server unless
the user explicitly asks. Prefer Server Actions + route handlers.

---

## Folder structure

```text
app/                    # App Router only — no pages/
  (marketing)/          # Public marketing routes
  (app)/                # Authenticated product shell
  api/                  # Webhooks + rare non-RSC endpoints
components/
  ui/                   # shadcn primitives
  domain/               # Feature components (not generic wrappers)
db/
  migrations/           # 0001_init.sql, 0002_….sql — ordered, never rewrite
  schema.sql            # Current full schema snapshot (generated or hand-maintained)
  queries/              # Typed SQL helpers — one file per domain
lib/
  db.ts                 # Single connection factory
  auth.ts
  env.ts                # Zod-parsed env
scripts/
  migrate.ts
  seed.ts
tests/
```

Naming: `kebab-case` files, `PascalCase` components, `camelCase` functions.
SQL tables: `snake_case` plural (`users`, `billing_events`).

---

## SQL / migration rules

1. **Additive first.** Prefer `ALTER TABLE … ADD COLUMN` over destructive rewrites.
2. Every migration is a new numbered file. Never edit a migration that already ran
   in any shared environment.
3. Include both schema and index changes in the same migration when they belong
   together.
4. `scripts/migrate.ts` records applied versions in `schema_migrations(id, applied_at)`.
5. Foreign keys **ON**. Enable with `PRAGMA foreign_keys = ON` on every connection.
6. Money columns: integer **cents** (`amount_cents`), never floats.
7. Timestamps: ISO-8601 text UTC (`created_at`), set in SQL defaults when possible.

Anti-pattern: generating migrations from an ORM sync in CI. Review SQL in PRs.

---

## Component & data patterns

- Default to **Server Components**. Add `"use client"` only for event handlers,
  local UI state, or browser APIs.
- Fetch in the server component / Server Action that owns the page. Do not create
  a parallel REST layer for first-party UI.
- Mutations: Server Actions with Zod input → SQL transaction → `revalidatePath`.
- Prefer one domain query module (`db/queries/billing.ts`) over scattering SQL.
- Forms: progressive enhancement with `<form action={serverAction}>` first.

Anti-patterns we reject:
- `useEffect` data loading for first paint
- Global client stores for server data
- Passing DB clients into Client Components
- `select *` in hot paths

---

## Dev commands

```bash
pnpm install
pnpm db:migrate          # apply db/migrations
pnpm db:seed             # optional local fixtures
pnpm dev                 # next dev
pnpm test                # vitest
pnpm test:e2e            # playwright (CI + before billing changes)
pnpm lint && pnpm typecheck
pnpm build
```

Env via `.env.local` validated by `lib/env.ts`. Required keys at minimum:
`DATABASE_URL`, `AUTH_SECRET`, `AUTH_URL`.

---

## Auth & tenancy

- Every product query is scoped by `user_id` (or `org_id` if multi-tenant is on).
- Never trust client-provided ids without joining to the session user.
- Soft-delete with `deleted_at` when user data may need recovery; hard-delete
  only for ephemeral caches.

---

## What we don't do (and why)

| Don't | Why |
|-------|-----|
| Pages Router | App Router is the product surface; dual routers double cognitive load |
| Prisma / heavy ORM | SQL + Zod is enough for SQLite SaaS; migrations stay readable |
| Microservices | One deployable until a real scaling boundary appears |
| Float money | Rounding bugs; use integer cents |
| Client-side secrets | Anything in `NEXT_PUBLIC_*` is public — no DB URLs, no auth secrets |
| Drive-by refactors | Ship the task; leave unrelated files alone |
| Silent `any` | TypeScript strict; narrow at boundaries with Zod |

---

## PR / agent checklist

Before finishing work:

1. Types + lint clean
2. Migration included if schema changed (and `schema.sql` updated)
3. Money / auth paths have a test or a clear manual verification note
4. No secrets committed; `.env*` stays gitignored
5. UI matches existing product patterns — no new design system

When unsure, choose the option that keeps **one SQLite schema**, **one Next app**,
and **server-owned data**.
