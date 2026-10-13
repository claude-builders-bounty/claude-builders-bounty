# CLAUDE.md — Next.js 15 App Router + SQLite (better-sqlite3 / Turso) SaaS Architecture

## 1. Core Stack & Non-Negotiable Principles
- **Framework**: Next.js 15 (App Router only; `pages/` directory is strictly forbidden).
- **Database**: SQLite in WAL mode via `better-sqlite3` (local/single-node) or `@libsql/client` (Turso edge).
- **Query Layer**: Drizzle ORM with strict TypeScript schema definitions in `src/db/schema.ts`.
- **Server Mutations**: Next.js Server Actions (`src/actions/*.ts`) validated with `zod` before touching the database.

## 2. Opinionated Project Structure
```
src/
├── app/                    # Next.js 15 App Router routes & layouts
│   ├── (marketing)/        # Public SSG/ISR landing & pricing pages
│   ├── (dashboard)/        # Authenticated tenant routes
│   └── api/webhooks/       # Stripe / LemonSqueezy webhooks ONLY
├── actions/                # Server Actions (1 file per domain: billing.ts, projects.ts)
├── db/
│   ├── index.ts            # Singleton connection + WAL pragma initialization
│   ├── schema.ts           # Single source of truth Drizzle tables
│   └── migrations/         # Numbered SQL migrations (0001_init.sql)
└── lib/
    ├── auth.ts             # Session validation helper
    └── validators/         # Shared Zod schemas
```

## 3. Database & SQLite Rules (Why: Prevent `SQLITE_BUSY` & Data Corruption)
1. **Mandatory PRAGMAs on Connection Startup** (`src/db/index.ts`):
   ```sql
   PRAGMA journal_mode = WAL;
   PRAGMA synchronous = NORMAL;
   PRAGMA foreign_keys = ON;
   PRAGMA busy_timeout = 5000;
   ```
   *Reason*: Without `WAL` and `busy_timeout`, concurrent read/write requests in Next.js Server Components will throw `SQLITE_BUSY`.
2. **Migration Discipline**:
   - Never run `drizzle-kit push` in production. Always generate deterministic SQL migrations (`npm run db:generate`) and apply via `npm run db:migrate`.
   - Every table MUST have `id TEXT PRIMARY KEY` (ULID/UUIDv7, never auto-increment integers that leak tenant volume), `created_at INTEGER NOT NULL`, and `updated_at INTEGER NOT NULL` (Unix epoch ms).

## 4. Development Commands
- `npm run dev`: Start Next.js 15 with Turbopack (`next dev --turbo`)
- `npm run db:generate`: Generate SQL migration from `src/db/schema.ts`
- `npm run db:migrate`: Apply pending migrations to local SQLite
- `npm run typecheck`: Run `tsc --noEmit`
- `npm run test`: Run Vitest against an in-memory SQLite instance (`:memory:`)

## 5. Patterns to Follow vs. Anti-Patterns to Avoid
- **DO**: Fetch data directly inside async Server Components using `src/db` queries filtered by `tenant_id`.
- **DO NOT**: Create `/api/*` REST routes for internal UI data fetching (use Server Components for reads and Server Actions for writes).
- **DO NOT**: Import `src/db` inside any file marked with `"use client"`.
- **DO NOT**: Use `SELECT *` without a `LIMIT` clause on multi-tenant tables.
