# CLAUDE.md — Next.js 15 (App Router) + SQLite Production SaaS Architecture

> **Purpose**: Authoritative architectural and coding instructions for Claude Code working in this repository. Follow every rule below strictly before creating, modifying, or reviewing files.

---

## 1. Stack & Exact Versions

| Layer | Technology | Pinned Version | Notes |
| :--- | :--- | :--- | :--- |
| **Runtime** | Node.js LTS | `>= 22.11.0` | Native `fetch`, `--env-file`, ESM support |
| **Framework** | Next.js (App Router) | `15.2.x` | React 19 Server Components (`async` params/headers/cookies) |
| **UI & Styling** | React + Tailwind CSS + shadcn/ui | `React 19.0.x`, `Tailwind 4.0.x` | Server-first components; client islands only when interactive |
| **Database Engine** | SQLite (`better-sqlite3` / LibSQL) | `better-sqlite3@^11.8.0` | Local WAL-mode single-file DB (`/data/app.db`) or Turso replica |
| **ORM & Query Builder** | Drizzle ORM + Drizzle Kit | `drizzle-orm@^0.39.0`, `drizzle-kit@^0.30.0` | Zero-overhead typed SQL; schema-as-code in `src/db/schema.ts` |
| **Authentication** | Better-Auth / Lucia Session Cookies | `better-auth@^1.2.0` | Database-backed HTTP-only session cookies (`sessions` table in SQLite) |
| **Validation** | Zod | `zod@^3.24.0` | Shared validation schemas for Server Actions and Route Handlers |
| **Billing** | Stripe Webhook + Customer Portal | `stripe@^17.5.0` | Idempotent webhook processor synced to SQLite `subscriptions` table |
| **Testing** | Vitest + Playwright | `vitest@^3.0.0`, `@playwright/test@^1.50.0` | In-memory `:memory:` SQLite per unit test suite |

---

## 2. Folder Structure

```text
.
├── CLAUDE.md                        # This file — read before every task
├── drizzle.config.ts                # Drizzle Kit migration config pointing to src/db/schema.ts
├── next.config.ts                   # Next.js 15 config (serverExternalPackages: ['better-sqlite3'])
├── data/                            # Git-ignored runtime SQLite files (app.db, app.db-wal, app.db-shm)
├── drizzle/                         # Committed, sequential SQL migration files (0000_init.sql, ...)
└── src/
    ├── app/                         # Next.js 15 App Router routes ONLY (thin routing layer)
    │   ├── (marketing)/             # Public landing, pricing, legal pages
    │   ├── (auth)/                  # Sign-in, sign-up, password reset routes
    │   ├── (dashboard)/             # Authenticated tenant workspace routes
    │   │   ├── layout.tsx           # Server layout verifying session via requireAuth()
    │   │   └── settings/page.tsx    # Async Server Component (reads DB directly via src/server/queries)
    │   └── api/
    │       ├── health/route.ts      # Readiness probe (SELECT 1 + WAL checkpoint status)
    │       └── webhooks/stripe/route.ts  # Raw-body Stripe webhook handler
    ├── components/
    │   ├── ui/                      # Stateless primitives (Button, Dialog, Input, Table)
    │   └── features/                # Domain components (billing-card.tsx, project-form.tsx)
    ├── db/
    │   ├── index.ts                 # Singleton SQLite connection + PRAGMA initialization
    │   ├── schema.ts                # Single source of truth for tables, indexes, and relations
    │   └── migrate.ts               # Programmatic migration runner executed on boot
    ├── server/
    │   ├── auth.ts                  # Session validation helpers: getCurrentUser(), requireUser()
    │   ├── queries/                 # Read-only data loaders wrapped in React `cache()`
    │   └── actions/                 # Mutating Server Actions (Zod parse -> Auth check -> DB tx -> revalidatePath)
    └── lib/
        ├── env.ts                   # Zod-validated environment variables (DATABASE_URL, STRIPE_SECRET_KEY)
        ├── errors.ts                # Typed ActionResult<T> = { ok: true; data: T } | { ok: false; error: string }
        └── validators/              # Shared Zod schemas imported by both Server Actions and Client Forms
```

---

## 3. SQLite & Migration Conventions (CRITICAL)

### 3.1 Connection & Mandatory PRAGMAs (`src/db/index.ts`)
SQLite in production SaaS **requires** Write-Ahead Logging (`WAL`) and a busy timeout so concurrent web requests never throw `SQLITE_BUSY`:

```typescript
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema";

const sqlite = new Database(process.env.DATABASE_URL ?? "./data/app.db");

// Mandatory production PRAGMAs — never remove these:
sqlite.pragma("journal_mode = WAL");
sqlite.pragma("synchronous = NORMAL");
sqlite.pragma("busy_timeout = 5000");
sqlite.pragma("foreign_keys = ON");
sqlite.pragma("temp_store = MEMORY");
sqlite.pragma("cache_size = -64000"); // 64MB page cache

export const db = drizzle(sqlite, { schema });
export { sqlite };
```

### 3.2 Schema & Migration Rules
1. **Never edit generated SQL files in `drizzle/` by hand** after they have been committed. Modify `src/db/schema.ts` and run `npm run db:generate`.
2. **Timestamps**: Store all timestamps as **Unix epoch milliseconds (`integer("created_at", { mode: "timestamp_ms" }).notNull()`)** or ISO-8601 UTC strings. Never rely on local server timezone.
3. **Monetary values**: Store all prices, balances, and invoice amounts as **integer cents (`integer("amount_cents").notNull()`)** — never `REAL` or floating-point numbers.
4. **Primary Keys**: Use prefixed ULIDs or UUIDv7 (`text("id").primaryKey()`) so IDs are k-sortable (`usr_01J...`, `org_01J...`).
5. **Multi-Tenancy**: Every tenant-owned table (`projects`, `api_keys`, `invoices`) **must** have a non-nullable `org_id` column with a composite index `(org_id, created_at)`.
6. **Transactions**: Because `better-sqlite3` is synchronous, keep transactions strictly CPU/SQL-bound (`db.transaction((tx) => { ... })`). **Never `await` a network call (Stripe, email, LLM) inside a SQLite transaction**, as doing so locks the write connection.

---

## 4. Next.js 15 & Component Patterns

1. **Next.js 15 Async Request APIs**:
   In Next.js 15, `params`, `searchParams`, `cookies()`, and `headers()` are **Promises**. Always `await` them:
   ```typescript
   export default async function ProjectPage({ params }: { params: Promise<{ id: string }> }) {
     const { id } = await params;
     const project = await getProjectById(id);
     ...
   }
   ```
2. **Server Components by Default**:
   - Every component is a Server Component unless it uses browser APIs, `useState`, `useEffect`, or event handlers (`onClick`, `onChange`).
   - Place `"use client"` at the **leaf component** level (e.g., `ProjectForm.tsx`), never on a page or layout.
3. **Data Fetching vs. Mutations**:
   - **Reads**: Call functions in `src/server/queries/*.ts` directly from Server Components. Do **not** create internal `/api/...` routes just to `fetch()` them from a Server Component.
   - **Writes**: Use Next.js **Server Actions** in `src/server/actions/*.ts`. Every Server Action must follow this exact 4-step pipeline:
     1. Validate input with `schema.safeParse(rawInput)`.
     2. Authenticate & authorize tenant scope with `const user = await requireUser()`.
     3. Execute synchronous Drizzle/SQLite mutation (`db.transaction(...)`).
     4. Call `revalidatePath(...)` and return `ActionResult<T>` (never throw raw database errors to the client).

---

## 5. What We DO NOT Do (and Why)

| Anti-Pattern | Why It Is Banned in This Codebase | What to Do Instead |
| :--- | :--- | :--- |
| **Using Prisma in Next.js Edge Middleware** | `better-sqlite3` is a native C++ addon and cannot run in the V8 Edge Runtime. | Run auth session checks in Node.js runtime layouts/actions or use lightweight JWT cookie pre-checks in `middleware.ts`. |
| **`await fetch(...)` inside `db.transaction()`** | SQLite allows only **one writer at a time**. Holding a transaction open across network I/O blocks all other writes and triggers `SQLITE_BUSY`. | Fetch external APIs (Stripe/OpenAI) *before* or *after* the synchronous `db.transaction()` block, using an idempotency state column. |
| **Using `SELECT *` without `WHERE org_id = ?`** | Causes cross-tenant data leaks in a multi-tenant SaaS. | Always require `orgId` as the first parameter in every query helper in `src/server/queries/`. |
| **Storing blobs/uploads in SQLite** | Bloats `/data/app.db`, degrades WAL checkpoint latency, and slows backups. | Store files in S3/Cloudflare R2 and store only the object key and SHA-256 hash in SQLite. |
| **Throwing unhandled exceptions in Server Actions** | Next.js masks unhandled production errors with a generic digest, breaking form error UI. | Return `{ ok: false, error: "Human-readable message", fieldErrors }` using `ActionResult<T>`. |

---

## 6. Essential Commands (`package.json`)

```bash
# Development
npm run dev              # Start Next.js 15 dev server with Turbopack (http://localhost:3000)
npm run typecheck        # Run tsc --noEmit (must pass with 0 errors before finishing any task)
npm run lint             # Run ESLint + Next.js core-web-vitals rules

# Database (Drizzle + SQLite)
npm run db:generate      # Generate SQL migration in ./drizzle from src/db/schema.ts
npm run db:migrate       # Apply pending SQL migrations to ./data/app.db
npm run db:studio        # Launch Drizzle Studio GUI to inspect ./data/app.db
npm run db:seed          # Seed deterministic local tenant, user, and sample projects

# Testing & Verification
npm run test             # Run Vitest unit & integration suites against in-memory SQLite (:memory:)
npm run test:e2e         # Run Playwright end-to-end flows
npm run build            # Full production build verification
```

