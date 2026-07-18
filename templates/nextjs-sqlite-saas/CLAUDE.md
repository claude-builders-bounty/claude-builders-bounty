# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

Opinionated rules for Claude Code on a greenfield SaaS. Every rule has a reason.

## Stack & versions

| Piece | Choice | Why |
|-------|--------|-----|
| Framework | **Next.js 15** (App Router only) | RSC + nested layouts; no Pages Router dual-stack |
| Language | **TypeScript strict** | Catch null/undefined at the boundary |
| DB | **SQLite** via `better-sqlite3` (local) or **Turso** (`@libsql/client`) in prod | One SQL dialect; zero cold-start DB ops for MVP |
| ORM / SQL | **Drizzle ORM** + drizzle-kit migrations | Typed SQL without magic; migrations are real files |
| Auth | **Auth.js (NextAuth v5)** credentials/OAuth | Standard session cookies; avoid rolling crypto |
| Styling | **Tailwind CSS 4** + shadcn/ui patterns | Utility-first; copy components, don't invent a design system mid-feature |
| Validation | **Zod** at every external boundary | Forms, route handlers, webhooks share schemas |
| Package manager | **pnpm** | Strict node_modules; faster CI |

Do **not** add Prisma, Redux, Moment, or CSS-in-JS without an ADR.

## Folder structure

```
src/
  app/                 # routes only — no business logic
    (marketing)/
    (app)/             # authenticated shell
      layout.tsx
      dashboard/
    api/               # route handlers (thin)
  components/
    ui/                # primitives (button, input)
    features/          # feature-scoped composites
  db/
    schema.ts          # drizzle tables
    index.ts           # client singleton
    migrations/        # generated SQL
  lib/
    auth.ts
    money.ts           # integer cents only
    errors.ts
  server/
    actions/           # 'use server' mutations
    queries/           # read models
  types/
```

**Reason:** keep `app/` boring so routing refactors never break domain code.

## Naming conventions

- Files: `kebab-case.ts` / `kebab-case.tsx`
- React components: `PascalCase` export matching filename when single-export
- DB tables: `plural_snake` (`users`, `billing_events`)
- Columns: `snake_case`; TS models map to `camelCase` in app layer only
- Server actions: `verbNounAction` (`createInvoiceAction`)
- Env vars: `SCREAMING_SNAKE`, validated in `src/lib/env.ts` with Zod on boot

## SQL / migration rules

1. **All schema changes go through drizzle-kit** — never hand-edit prod SQLite without a migration.
2. Migrations live in `src/db/migrations` and are committed.
3. Prefer additive migrations; destructive changes require a two-step expand/contract.
4. Money is **integer cents** (`amount_cents INTEGER NOT NULL`). No floats.
5. Timestamps: `created_at` / `updated_at` as ISO text or integer unix — pick one per project and stick to it (default: integer unix UTC).
6. Soft deletes: `deleted_at` nullable; default queries filter `IS NULL`.
7. Foreign keys ON; enable `PRAGMA foreign_keys = ON` on every connection.

### Dev commands (DB)

```bash
pnpm db:generate   # drizzle-kit generate
pnpm db:migrate    # apply migrations
pnpm db:studio     # inspect
```

## Component patterns

- Server Components by default; add `"use client"` only for state/effects/browser APIs.
- Data fetching in server components / `server/queries`, not `useEffect` + fetch.
- Forms: Server Actions + Zod. Show field errors; never swallow `ZodError`.
- Colocate feature UI under `components/features/<feature>/`.
- No prop-drilling past 2 levels — pass IDs and re-query on the server when possible.

## Auth & security

- Session check in **layouts** and **sensitive actions**, not only middleware.
- CSRF: rely on Next.js Server Action tokens; for raw POST route handlers, verify origin.
- Secrets only in server code; never `NEXT_PUBLIC_` for keys.
- Rate-limit auth and webhook routes (even a simple in-memory limiter in MVP).
- Authorize by **resource ownership** in every mutation (`where userId = session.user.id`).

## API / route handlers

- Thin: parse → authorize → call `server/` → map errors → response.
- Return consistent JSON: `{ ok: true, data } | { ok: false, error: { code, message } }`.
- Prefer Server Actions for first-party UI; route handlers for webhooks/external clients.

## What we don't do (and why)

| Don't | Why |
|-------|-----|
| Pages Router | Dual mental models slow every change |
| Float money | IEEE floats break invoices |
| Client-side secret checks | Trivial bypass |
| Mega `utils.ts` | Becomes an unowned junk drawer |
| Premature multi-tenant | Schema tax before first customer |
| Generic "repository pattern" over Drizzle | Extra layer without payoff at this scale |
| `any` to silence TS | Hides the bug you'll ship |

## Dev commands

```bash
pnpm dev
pnpm build
pnpm lint
pnpm test
pnpm db:generate && pnpm db:migrate
```

## Definition of done (every PR)

1. Types pass (`tsc --noEmit`)
2. New user input has a Zod schema
3. Mutations check authz
4. Migration included if schema changed
5. No new dependency without a one-line justification in the PR body
