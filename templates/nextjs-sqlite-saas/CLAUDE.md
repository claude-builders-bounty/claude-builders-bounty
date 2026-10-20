# CLAUDE.md — Next.js 15 App Router + SQLite SaaS Architecture Contract

## 1. Stack & Pinned Versions
- **Runtime**: Node.js `>=22.0.0` (LTS)
- **Framework**: Next.js `15.2.x` (**App Router only** — `src/app/`, React 19 Server Components + Server Actions)
- **Database**: SQLite via `better-sqlite3` (`^11.8.0`) in local/single-node production (WAL mode enabled) or `@libsql/client` (Turso) with Drizzle ORM (`drizzle-orm ^0.39.0`, `drizzle-kit ^0.30.0`)
- **Validation**: `zod ^3.24.0` at every Server Action and Route Handler boundary
- **Auth**: Session cookies (`httpOnly`, `sameSite=lax`, `secure`) backed by SQLite `sessions` table
- **Styling**: Tailwind CSS v4 + Radix Primitives (`src/components/ui/`)

## 2. Folder Structure
```text
src/
├── app/                        # Next.js 15 App Router routes & layouts
│   ├── (marketing)/            # Public landing & pricing pages
│   ├── (auth)/                 # /login, /signup, /verify
│   ├── (dashboard)/            # Authenticated tenant routes
│   └── api/webhooks/           # External webhooks ONLY (Stripe, etc.)
├── db/
│   ├── index.ts                # Singleton SQLite connection (WAL + busy_timeout)
│   ├── schema.ts               # Canonical Drizzle SQLite schema
│   └── migrations/             # Sequential SQL migrations (0001_*.sql)
├── actions/                    # Server Actions ("use server"), 1 file per domain
├── queries/                    # Read-only typed DB queries (`server-only`)
└── components/
    ├── ui/                     # Stateless design-system primitives
    └── features/               # Domain components
```

## 3. SQL & Migration Conventions (Strict Rules)
1. **Always Enable WAL & Pragmas on Connection Init (`src/db/index.ts`)**:
   - `PRAGMA journal_mode = WAL;`
   - `PRAGMA synchronous = NORMAL;`
   - `PRAGMA foreign_keys = ON;`
   - `PRAGMA busy_timeout = 5000;`
   *Why*: Default SQLite locking fails under concurrent Next.js Server Component reads + Server Action writes.
2. **Never Edit Applied Migrations**:
   - Generate migrations via `npm run db:generate` (`drizzle-kit generate`) and apply via `npm run db:migrate`.
   - Every table MUST have `id TEXT PRIMARY KEY` (ULID/UUIDv7), `tenant_id TEXT NOT NULL`, `created_at INTEGER NOT NULL` (Unix ms), and `updated_at INTEGER NOT NULL`.
3. **Tenant Isolation**:
   - Every query in `src/queries/` and mutation in `src/actions/` MUST filter by `eq(table.tenantId, session.tenantId)`.

## 4. Component & Data Flow Patterns
- **Reads**: Fetch directly inside async Server Components using functions from `src/queries/*` (marked `import "server-only"`). Never create `/api/*` routes just to fetch data for your own UI.
- **Writes**: Mutate exclusively via Server Actions in `src/actions/*` validated with `zod`, followed by `revalidatePath()`.
- **Transactions**: Wrap multi-statement SQLite writes in `db.transaction((tx) => { ... })` synchronously (`better-sqlite3` transactions are synchronous — never `await` inside `db.transaction`).

## 5. Development Commands
- `npm run dev` — Start Next.js 15 with Turbopack (`next dev --turbopack`)
- `npm run db:generate` — Generate SQL migration from `src/db/schema.ts`
- `npm run db:migrate` — Apply pending SQLite migrations
- `npm run typecheck` — Run `tsc --noEmit`
- `npm test` — Run Vitest against an in-memory/temp-file SQLite database

## 6. What We Don't Do (And Why)
- **No `pages/` router**: Mixing Pages and App Router duplicates bundling and breaks RSC layouts.
- **No `await` inside `better-sqlite3` transactions**: `better-sqlite3` runs synchronously on the main thread; yielding to the event loop inside a transaction throws `Transaction function cannot return a promise`.
- **No `SELECT *` in list views**: Always project explicit columns to keep RSC payload serialization small.
- **No raw `Date` strings in SQLite**: Store timestamps as `INTEGER` (Unix epoch ms) for deterministic indexing and range queries.
