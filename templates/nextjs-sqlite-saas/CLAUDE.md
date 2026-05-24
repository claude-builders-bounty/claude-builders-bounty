# CLAUDE.md — Next.js 15 + SQLite SaaS

Opinionated project guide for a greenfield SaaS using **Next.js 15 App Router** and **SQLite** (Turso libSQL or local `better-sqlite3`).

## Stack & versions

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15 (App Router) | Server Components + Route Handlers reduce client bundle size |
| Language | TypeScript strict | Catch data-shape bugs at compile time |
| Database | SQLite via Drizzle ORM | Typed queries, lightweight migrations, works local + Turso |
| Auth | Auth.js v5 (NextAuth) | Session cookies, no custom auth wheel |
| Styling | Tailwind CSS | Utility-first, no CSS-in-JS runtime |
| Validation | Zod | Shared schemas for forms + API |

**We do not** use Pages Router, Prisma, or MongoDB in new code.

## Folder structure

```
src/
  app/                 # App Router routes only
    (marketing)/       # Public pages (no auth)
    (dashboard)/       # Authenticated app shell
    api/               # Route Handlers (REST-ish JSON)
  components/
    ui/                # Dumb presentational components
    features/          # Feature-specific composed components
  db/
    schema.ts          # Drizzle table definitions
    migrations/        # SQL migration files (generated)
    client.ts          # DB connection singleton
  lib/                 # Pure helpers (no React imports)
  server/              # Server-only services (queries, auth guards)
tests/
  unit/                # Vitest unit tests
  e2e/                 # Playwright (critical paths only)
```

**Rule:** UI components never import `db/client.ts`. Data access lives in `src/server/`.

## Dev commands

```bash
pnpm install
pnpm dev              # http://localhost:3000
pnpm db:generate      # drizzle-kit generate after schema change
pnpm db:migrate       # apply migrations
pnpm test             # vitest
pnpm lint             # eslint + tsc --noEmit
```

## SQL & migration conventions

1. **One migration per logical change** — never edit an applied migration file.
2. Table names: `snake_case`, plural (`users`, `billing_events`).
3. Primary keys: `id TEXT` (UUID v7 string) or `INTEGER PRIMARY KEY AUTOINCREMENT` for internal tables only.
4. Timestamps: `created_at`, `updated_at` as `INTEGER` Unix ms or `TEXT` ISO — pick one project-wide (default: INTEGER ms).
5. Soft deletes: `deleted_at INTEGER NULL` — never hard-delete user-owned rows in app code.
6. Foreign keys: always declare in Drizzle schema; enable `PRAGMA foreign_keys = ON` on every connection.

```typescript
// src/db/client.ts pattern
import { drizzle } from "drizzle-orm/libsql";
import { createClient } from "@libsql/client";

const client = createClient({ url: process.env.DATABASE_URL! });
export const db = drizzle(client);
```

## Component patterns

- **Server Components by default** — add `"use client"` only for interactivity.
- **Colocate feature code** — `src/components/features/billing/` not a giant `components/` dump.
- **Route Handlers** return `NextResponse.json()` with Zod-validated bodies.
- **Errors:** throw `Response` with status in Route Handlers; use `error.tsx` boundaries in UI routes.

## Auth & tenancy

- Session read: `auth()` in Server Components / Route Handlers.
- Every multi-tenant query filters by `organization_id` from the session — no optional org filter.
- Admin routes live under `src/app/(dashboard)/admin/` with a shared `requireAdmin()` guard.

## What we don't do (and why)

| Anti-pattern | Why |
|--------------|-----|
| Fetch in `useEffect` for initial page data | Use Server Components + direct DB calls |
| Global Redux/MobX | React Server Components + URL state cover our needs |
| Raw SQL strings in components | Drizzle + `src/server` repositories only |
| `any` or `@ts-ignore` | Fix the type or narrow with Zod |
| Environment secrets in client bundles | Only `NEXT_PUBLIC_*` crosses the wire |
| Force-push to `main` | PR + CI required |

## PR checklist

- [ ] Schema change includes migration + updated Drizzle schema
- [ ] New Route Handler has Zod input validation
- [ ] No secrets or PII in logs
- [ ] `pnpm lint && pnpm test` pass locally

## When Claude is unsure

1. Prefer **server-side data fetching** over client fetch.
2. Prefer **explicit types + Zod** over inference from external APIs.
3. Ask before adding a new dependency — keep the stack table authoritative.
