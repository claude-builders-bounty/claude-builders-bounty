# CLAUDE.md — Next.js + SQLite SaaS

> Project memory for Claude Code. Read this first; keep it accurate as the
> codebase evolves. Prefer editing these sections over adding new top-level
> ones.

## 1. Project Overview

A multi-tenant SaaS built on **Next.js (App Router)** with a **SQLite**
database accessed through **Prisma**. Deployed as a single Node process
(docker) with a persistent volume for the SQLite file.

- **Runtime:** Node 20+
- **Framework:** Next.js 14+ (App Router, React Server Components)
- **DB:** SQLite via Prisma (`prisma/schema.prisma`)
- **Auth:** session cookie (httpOnly) + server-side session lookup
- **Styling:** Tailwind CSS
- **Tests:** Vitest (unit) + Playwright (e2e)

## 2. Commands

```bash
npm run dev            # start dev server (http://localhost:3000)
npm run build          # production build
npm run start          # run the production build
npm run lint           # ESLint + Prettier check
npm run typecheck      # tsc --noEmit
npm run test           # Vitest unit tests
npm run test:e2e       # Playwright e2e
npx prisma migrate dev --name <name>   # create + apply a migration
npx prisma generate                    # regenerate the client after schema edits
npx prisma studio                      # inspect the SQLite DB in a GUI
```

## 3. Repository Layout

```
app/                 # App Router routes (pages, layouts, route handlers)
  (marketing)/       # public, unauthenticated routes
  (app)/             # authenticated app shell
  api/               # route handlers (REST-ish endpoints)
components/          # shared React components (server-first)
lib/                 # server-only utils (db, auth, billing, validation)
lib/db.ts            # the single PrismaClient instance (see §5)
prisma/
  schema.prisma      # source of truth for the data model
  migrations/        # committed SQL migrations — never edit by hand
  dev.db             # local SQLite file (git-ignored)
tests/               # Vitest units
e2e/                 # Playwright specs
```

## 4. Conventions

- **Server Components by default.** Add `"use client"` only when you need
  state, effects, or browser APIs. Push interactivity to leaf components.
- **Data access lives in `lib/`**, never inline in components. Route handlers
  and Server Components call `lib/*` functions.
- **Validate all input with Zod** at the boundary (route handlers, server
  actions). Never trust `request.json()`.
- **Mutations via Server Actions** where possible; use route handlers for
  webhooks and third-party callbacks.
- **Naming:** `kebab-case` files, `PascalCase` components, `camelCase`
  functions/variables.
- **No `any`.** Use `unknown` + narrowing, or a Zod schema.

## 5. Database Rules (SQLite-specific — read carefully)

- **Single client instance.** Import `prisma` from `lib/db.ts` only. Creating
  extra `new PrismaClient()` instances exhausts SQLite connections.
- **Enable WAL mode** once at startup for concurrent reads:
  `PRAGMA journal_mode = WAL;`
- **SQLite has no native enums/arrays/JSON columns.** Model them as `String`
  (validated by Zod) or a related table. Do not assume Postgres features.
- **Migrations are SQL and committed.** Never edit an applied migration;
  create a new one. SQLite migrations are often destructive (table rebuild) —
  review the generated SQL before applying.
- **Foreign keys are OFF by default.** Enable with `PRAGMA foreign_keys = ON;`
  per connection, or rely on Prisma's `relationMode = "prisma"`.
- **The DB file is a deployment artifact.** It lives on a persistent volume,
  is git-ignored, and must be backed up before migrations in prod.

## 6. Multi-Tenancy

- Every tenant-scoped table has a `tenantId` column with an index.
- **Always filter by `tenantId`** in queries. A missing tenant filter is a
  data-leak bug — treat it as a security incident.
- Enforce tenancy in `lib/` helpers, not at call sites, so it can't be
  forgotten.

## 7. Security

- Secrets come from env vars; never commit them. `.env*` is git-ignored.
- Session cookies: `httpOnly`, `secure` (prod), `sameSite=lax`.
- Hash passwords with `bcrypt` (cost ≥ 12). Never log secrets or PII.
- Rate-limit auth and webhook route handlers.

## 8. Testing

- Unit-test pure logic in `lib/` with Vitest.
- e2e-test user flows with Playwright against a seeded SQLite DB.
- Use a separate `TEST_DATABASE_URL` pointing at a temp SQLite file; reset it
  between runs (`prisma migrate reset --force`).

## 9. Gotchas

- **`prisma generate` after every schema change**, or types go stale.
- **Server Actions can't be called from non-React code** — use route handlers
  there.
- **Don't import server-only `lib/` code into client components.**
- **SQLite writes serialize.** Long transactions block writers; keep them
  short.
- **Timezones:** store UTC (`DateTime`), format at the edge.

## 10. When in Doubt

1. Match the nearest existing pattern in the repo.
2. Run `npm run typecheck && npm run lint && npm run test` before declaring
   done.
3. If a change touches the schema, include the migration and update this file.
