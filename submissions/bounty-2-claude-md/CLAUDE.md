# CLAUDE.md — Next.js 15 + SQLite SaaS

Opinionated defaults for a greenfield B2B SaaS on **Next.js 15 App Router** and **SQLite** (better-sqlite3 locally, Turso/libSQL in production).

## Stack & versions

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15 App Router | Server Components + colocated routes; no Pages router |
| Language | TypeScript strict | Catches schema drift at compile time |
| DB (dev) | better-sqlite3 | Fast local file DB, no Docker required |
| DB (prod) | Turso / libSQL | SQLite-compatible, edge-replicated, same SQL dialect |
| ORM | Drizzle | Type-safe queries, migration files in repo |
| Auth | Auth.js v5 (NextAuth) | Session cookies, OAuth, fits App Router |
| Styling | Tailwind + shadcn/ui | Copy-paste components, no design-system lock-in |
| Validation | Zod | Shared between API routes and forms |
| Testing | Vitest + Playwright | Unit for lib/, e2e for critical flows |

Pin versions in `package.json`; do not use `latest` ranges.

## Folder structure

```
app/
  (marketing)/          # Public pages — no auth
  (dashboard)/          # Authenticated shell + layout
    dashboard/
      page.tsx
      settings/
        page.tsx
  api/
    [...]/route.ts      # Route handlers only — thin wrappers
components/
  ui/                   # shadcn primitives — never import from app/
  features/             # Domain components (InvoiceTable, PlanCard)
lib/
  db/
    schema.ts           # Drizzle schema — single source of truth
    client.ts           # DB singleton
    migrations/         # SQL migration files (see below)
  auth/
    session.ts
  validators/           # Zod schemas shared by server + client
server/
  actions/              # Server Actions — mutations only
  queries/              # Read-only data access (RSC callers)
types/
  index.ts              # Shared TS types not inferable from Drizzle
```

**Rule:** `app/` pages compose; they do not contain SQL or business rules. Put reads in `server/queries/`, writes in `server/actions/`.

## Naming conventions

| Artifact | Pattern | Example |
|----------|---------|---------|
| React components | PascalCase file + export | `components/features/BillingCard.tsx` |
| Server actions | verb + noun, `Action` suffix | `createWorkspaceAction` |
| Query functions | `get` / `list` prefix | `getWorkspaceById` |
| DB tables | snake_case plural | `workspaces`, `billing_events` |
| Route segments | kebab-case | `app/(dashboard)/billing-history/page.tsx` |
| Env vars | `SCREAMING_SNAKE`, prefixed | `DATABASE_URL`, `AUTH_SECRET` |

## SQL & migration conventions

1. **Migrations are forward-only.** Never edit a merged migration; add a new file.
2. **File naming:** `lib/db/migrations/YYYYMMDDHHMMSS_description.sql`
3. **Every table** has `id TEXT PRIMARY KEY` (UUID v7 or cuid2), `created_at`, `updated_at`.
4. **Soft deletes** use `deleted_at INTEGER` (unix epoch), not boolean flags.
5. **Foreign keys** enabled: `PRAGMA foreign_keys = ON` on every connection.
6. **Indexes** on every FK column and every column used in `WHERE` for list endpoints.
7. **No raw SQL in components.** Drizzle only, except migration files.

```ts
// lib/db/client.ts — singleton pattern
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';

const sqlite = new Database(process.env.DATABASE_URL!.replace('file:', ''));
sqlite.pragma('foreign_keys = ON');

export const db = drizzle(sqlite);
```

Turso production: swap `client.ts` driver to `@libsql/client` + `drizzle-orm/libsql`; keep schema identical.

## Component patterns

- **Server Components by default.** Add `'use client'` only for interactivity.
- **Forms:** React Hook Form + Zod resolver + Server Action for submit.
- **Loading:** `loading.tsx` per route segment; skeletons match final layout.
- **Errors:** `error.tsx` per segment; log to observability, show safe message.
- **Data fetching:** RSC calls `server/queries/*` directly — no `useEffect` fetch.

```tsx
// app/(dashboard)/dashboard/page.tsx
import { getDashboardStats } from '@/server/queries/dashboard';

export default async function DashboardPage() {
  const stats = await getDashboardStats();
  return <DashboardView stats={stats} />;
}
```

## Dev commands

```bash
pnpm dev              # Next dev server
pnpm db:migrate       # Apply pending SQL migrations
pnpm db:studio        # Drizzle Studio (local only)
pnpm test             # Vitest unit tests
pnpm test:e2e         # Playwright
pnpm lint && pnpm typecheck
```

Add these scripts to `package.json` on day one.

## Auth & multi-tenancy

- Every dashboard route checks session in `app/(dashboard)/layout.tsx`.
- **Row-level tenancy:** all queries filter by `workspace_id` from session — never trust client-supplied workspace IDs.
- API routes return `401` / `403`; never redirect from API handlers.

## What we don't do (and why)

| Anti-pattern | Why we avoid it |
|--------------|-----------------|
| Pages Router | App Router is the default; mixing routers confuses RSC boundaries |
| Prisma | Heavier than needed; Drizzle matches SQLite + edge deployments |
| `useEffect` data fetching in dashboard | Causes waterfalls and loading flashes; use RSC |
| Global Redux/Zustand for server data | Server state belongs on the server; client stores for UI only |
| `any` or `@ts-ignore` | Fix the type; SaaS codebases rot without strict TS |
| Storing secrets in `NEXT_PUBLIC_*` | Public env vars ship to the browser |
| `DELETE` without `WHERE` in scripts | Use soft deletes; hard deletes only in migrations with review |
| Monolithic `lib/utils.ts` | Split by domain under `lib/` and `server/` |

## Environment files

```
.env.local          # gitignored — local secrets
.env.example        # committed — keys only, no values
```

Required keys: `DATABASE_URL`, `AUTH_SECRET`, `AUTH_URL`, OAuth provider keys.

## PR checklist (Claude should enforce)

- [ ] Migration added if schema changed
- [ ] Zod schema updated if input shape changed
- [ ] `workspace_id` filter present on new queries
- [ ] No `'use client'` unless necessary
- [ ] Unit test for non-trivial `lib/` or `server/` logic

## First prompt smoke test

After pasting this file, Claude Code should be able to scaffold `createWorkspaceAction`, add a `workspaces` table migration, and wire a dashboard page **without asking** which router, ORM, or auth library to use.