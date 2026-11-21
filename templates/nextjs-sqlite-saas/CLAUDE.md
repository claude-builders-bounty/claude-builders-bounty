# CLAUDE.md — Next.js 15 App Router + SQLite SaaS Production Blueprint

This document is the authoritative engineering constitution for this project. Claude Code MUST follow these conventions without asking clarifying questions.

---

## 1. Stack & Locked Versions

| Layer | Technology | Version / Mode | Rationale |
| :--- | :--- | :--- | :--- |
| **Framework** | Next.js (App Router) | `15.x` (`react@19`) | Server Components by default; zero client bundle overhead for read paths. |
| **Language** | TypeScript | `5.7+` (`strict: true`, `noUncheckedIndexedAccess: true`) | Prevents null/index runtime crashes across DB and Server Action boundaries. |
| **Database** | SQLite (`better-sqlite3` locally / LibSQL Turso in prod) | WAL Mode + `FOREIGN_KEYS=ON` | Single-node sub-millisecond reads with concurrent read + serialized write safety. |
| **ORM / Query** | Drizzle ORM + `drizzle-kit` | `0.38+` | Zero-overhead SQL generation, strict TypeScript inference, and deterministic SQL migrations. |
| **Validation** | Zod | `3.24+` | Mandatory input validation at every Server Action and Route Handler boundary. |
| **Styling** | Tailwind CSS | `4.x` | Utility-first styling with zero runtime CSS-in-JS cost. |
| **Auth** | Session Cookie (`httpOnly`, `SameSite=Lax`, HMAC-SHA256) | Custom DAL (`src/lib/auth/dal.ts`) | Eliminates third-party auth vendor lock-in and works identically in local SQLite. |

---

## 2. Folder Structure & Naming Conventions

```text
.
├── CLAUDE.md
├── drizzle.config.ts
├── drizzle/
│   └── migrations/              # Forward-only numbered SQL migrations (0001_init.sql)
├── data/
│   └── app.sqlite               # Local SQLite database file (gitignored, WAL-enabled)
├── src/
│   ├── app/
│   │   ├── (marketing)/         # Public SSR pages
│   │   ├── (dashboard)/         # Authenticated app routes (guarded in layout + DAL)
│   │   └── api/
│   │       ├── health/route.ts  # Readiness + SQLite WAL checkpoint probe
│   │       └── webhooks/        # External webhooks (Stripe, etc.)
│   ├── components/
│   │   ├── ui/                  # Stateless atomic UI primitives (PascalCase.tsx)
│   │   └── features/            # Domain components grouped by feature
│   ├── db/
│   │   ├── index.ts             # Singleton SQLite connection with mandatory PRAGMAs
│   │   └── schema/              # Drizzle table schemas (kebab-case.schema.ts)
│   ├── lib/
│   │   ├── auth/dal.ts          # Data Access Layer (verifySession, requireTenantMember)
│   │   └── errors.ts            # Typed AppError classes
│   └── server/
│       ├── actions/             # Mutating Server Actions (*.actions.ts)
│       └── queries/             # Pure server-side read queries (*.queries.ts)
└── tests/                       # Vitest integration tests against in-memory/temp SQLite
```

### Naming Rules
- **Files**:
  - React Components: `PascalCase.tsx` (`BillingPlanCard.tsx`). Each button and page lives in its own dedicated file.
  - Drizzle Schemas: `kebab-case.schema.ts` (`billing-subscriptions.schema.ts`).
  - Server Actions: `kebab-case.actions.ts` (`workspace.actions.ts`).
  - Server Queries: `kebab-case.queries.ts` (`workspace.queries.ts`).
- **Database Identifiers**:
  - Tables: plural `snake_case` (`workspaces`, `workspace_members`, `api_keys`).
  - Columns: `snake_case` (`workspace_id`, `created_at`, `deleted_at`).
  - Primary Keys: `id TEXT PRIMARY KEY` using prefix-tagged ULIDs (`usr_01J...`, `wks_01J...`) so IDs are sortable and self-identifying in logs.
  - Timestamps: Integer Unix epoch milliseconds (`INTEGER NOT NULL`) via `Date.now()` — avoids SQLite string timezone parsing bugs.
  - Money / Currency: Integer minor units (`amount_cents INTEGER NOT NULL`) — never `REAL` or floating-point.

---

## 3. SQLite Connection & Migration Conventions

### Mandatory Connection Initialization (`src/db/index.ts`)
Every SQLite connection MUST execute these PRAGMAs immediately upon opening:

```ts
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';

const sqlite = new Database(process.env.DATABASE_URL ?? './data/app.sqlite');
sqlite.pragma('journal_mode = WAL');
sqlite.pragma('synchronous = NORMAL');
sqlite.pragma('busy_timeout = 5000');
sqlite.pragma('foreign_keys = ON');
sqlite.pragma('cache_size = -64000'); // 64MB page cache

export const db = drizzle(sqlite);
```

**Why**: Without `journal_mode = WAL` and `busy_timeout = 5000`, concurrent Next.js SSR requests and Server Actions throw `SQLITE_BUSY: database is locked`. Without `foreign_keys = ON`, SQLite silently ignores foreign key constraints.

### Migration Rules
1. **Generate, Never Push in Production**: Always run `npm run db:generate` to emit versioned SQL under `drizzle/migrations/`, review the generated SQL, and apply with `npm run db:migrate`.
2. **Forward-Only & Expand-Contract**: Never edit an already-committed migration file. Because SQLite has limited `ALTER TABLE` support, destructive column changes must follow expand-contract (add nullable column -> backfill in transaction -> switch reads -> drop old column in a new migration).
3. **Transactions for Multi-Statement Writes**: Wrap multi-step writes in `db.transaction((tx) => { ... })`. Never `await` external network calls (Stripe, emails, LLMs) inside a SQLite transaction because SQLite locks the single writer for the duration of the transaction.

---

## 4. Component & Data Access Patterns

1. **Server Components by Default**:
   - Pages and layouts fetch data directly via `src/server/queries/*.queries.ts`.
   - Add `'use client'` ONLY to leaf interactive components that use `useState`, `useEffect`, or browser event handlers.
2. **Next.js 15 Async Request APIs**:
   - In Next.js 15, `params`, `searchParams`, `cookies()`, and `headers()` are **asynchronous Promises** and MUST be awaited (`const { slug } = await params;`).
3. **Centralized Data Access Layer (DAL)**:
   - Never rely solely on `middleware.ts` for security. Every query in `src/server/queries/` and every mutation in `src/server/actions/` MUST call `await requireWorkspaceAccess(workspaceId)` from `src/lib/auth/dal.ts` and scope all SQL `WHERE` clauses by `workspace_id`.
4. **Server Action Contract**:
   - Every Server Action validates input with Zod, checks authorization via the DAL, executes a synchronous/transactional SQLite write, calls `revalidatePath()`, and returns a typed result `{ ok: true, data } | { ok: false, error: string }` instead of throwing unhandled exceptions to the client.

---

## 5. What We Don't Do (And Why)

- **NO `db.select()` inside Client Components or importing `src/db` into `'use client'` files**
  *Why*: Leaks server schema details and breaks the webpack/Turbopack client build because `better-sqlite3` is a native C++ addon.
- **NO `await fetch(...)` inside `db.transaction(...)`**
  *Why*: SQLite allows only one active writer at a time. Holding a write transaction open across network I/O starves all other users and triggers `SQLITE_BUSY`.
- **NO `REAL`/`FLOAT` columns for prices, balances, or credits**
  *Why*: IEEE-754 floating-point rounding causes penny discrepancies. Store all currency in integer cents (`amount_cents INTEGER NOT NULL`).
- **NO `SELECT *` on tables with JSON blobs or audit payloads in list views**
  *Why*: Explicit column selection keeps SQLite page reads inside covering indexes and prevents large memory allocations during SSR.
- **NO unindexed Foreign Keys**
  *Why*: SQLite does NOT automatically create indexes on foreign key columns. Every `*_id` foreign key column MUST declare an explicit index (`index('idx_members_workspace_id').on(table.workspaceId)`), or parent deletes and tenant joins will perform full table scans.

---

## 6. Development & Verification Commands

```bash
npm run dev            # Start Next.js 15 dev server on port 3000
npm run db:generate    # Generate SQL migration from src/db/schema/*.schema.ts
npm run db:migrate     # Apply pending migrations in drizzle/migrations/
npm run db:studio      # Launch Drizzle Studio on local SQLite database
npm run lint           # Run ESLint + TypeScript typecheck (tsc --noEmit)
npm run test           # Run Vitest suite against isolated temp SQLite DB
npm run build          # Production build verification
```
