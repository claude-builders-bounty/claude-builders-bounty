# CLAUDE.md — Next.js 15 App Router + SQLite SaaS Architecture Guide

> **Purpose**: Authoritative architectural contract for Claude Code operating in this
> Next.js 15 + SQLite SaaS repository. Follow these conventions without asking clarifying
> questions unless a requirement directly contradicts an explicit rule below.

---

## 1. Stack & Pinned Versions

| Layer | Technology | Version | Rationale |
| :--- | :--- | :--- | :--- |
| **Framework** | Next.js (App Router, Turbopack) | `15.2.x` | Async Request APIs (`cookies()`, `headers()`, `params`), React 19 Server Actions, native Server Components |
| **UI Runtime** | React | `19.0.x` | Native `useActionState`, `useOptimistic`, and Server Component streaming |
| **Language** | TypeScript (`strict: true`, `noUncheckedIndexedAccess: true`) | `5.7.x` | Prevents unchecked `undefined` on SQLite row lookups and dynamic route params |
| **Database Engine** | SQLite via `better-sqlite3` (local/single-node) or `@libsql/client` (Turso edge/replicas) | `11.x` / `0.14.x` | Synchronous C++ binding in Node.js runtime eliminates connection-pool exhaustion; zero-latency local reads |
| **Query & Schema Layer** | Drizzle ORM + `drizzle-kit` | `0.39.x` | Zero-overhead SQL builder, 1:1 SQLite dialect mapping, deterministic `.sql` migration output |
| **Validation** | Zod | `3.24.x` | Shared runtime parsing at Server Action and Route Handler boundaries |
| **Authentication** | Custom HTTP-only signed session cookies (`jose` + SHA-256 session tokens in SQLite) | `5.9.x` | Sub-millisecond session validation via local SQLite index without third-party auth vendor latency |
| **Billing** | Stripe SDK (`stripe`) + idempotent webhook ledger in SQLite | `17.x` | Webhook events are deduplicated in SQLite before mutating subscription state |
| **Styling** | Tailwind CSS + Radix UI primitives | `4.0.x` | Utility-first CSS with zero runtime JS overhead |
| **Testing** | Vitest (unit/DB integration with `:memory:` SQLite) + Playwright (E2E) | `3.x` / `1.50.x` | Real SQLite schema execution in <10ms per test without mocking SQL |

---

## 2. Development & Database Commands

Always run verification commands after modifying schema, queries, or Server Actions:

```bash
# Development server (Next.js 15 with Turbopack)
pnpm dev

# Type-checking & Linting (MUST pass with 0 warnings before finishing a task)
pnpm typecheck          # tsc --noEmit
pnpm lint               # next lint --max-warnings=0

# Database lifecycle (SQLite + Drizzle Kit)
pnpm db:generate        # Generate numbered SQL migration from src/db/schema/*.ts
pnpm db:migrate         # Apply pending migrations in src/db/migrations/ to SQLite DB
pnpm db:seed            # Seed local dev database with deterministic tenant/user fixtures
pnpm db:studio          # Launch Drizzle Studio against local SQLite file

# Testing
pnpm test               # Run Vitest unit + in-memory SQLite integration tests
pnpm test:watch         # Run Vitest in watch mode
pnpm test:e2e           # Run Playwright end-to-end suite
```

---

## 3. Folder Structure & Boundary Rules

```text
.
├── data/                         # Git-ignored local SQLite database files (app.db, app.db-wal, app.db-shm)
├── src/
│   ├── app/                      # Next.js 15 App Router (routing, layouts, RSC pages, route handlers ONLY)
│   │   ├── (marketing)/          # Public pages (pricing, landing, legal)
│   │   ├── (auth)/               # Login, signup, password reset routes
│   │   ├── (dashboard)/          # Authenticated tenant routes (enforced by layout + DAL session check)
│   │   │   └── [orgSlug]/        # Multi-tenant organization scope
│   │   └── api/
│   │       ├── webhooks/stripe/  # Raw body webhooks (ONLY place Route Handlers are used for mutations)
│   │       └── health/           # Liveness check (verifies SQLite read/write pragma state)
│   ├── components/
│   │   ├── ui/                   # Stateless design-system primitives (Button, Dialog, Input)
│   │   └── features/             # Domain-scoped client/server components (billing/, projects/, members/)
│   ├── db/
│   │   ├── index.ts              # Singleton SQLite connection + mandatory PRAGMA initialization
│   │   ├── migrate.ts            # Programmatic migration runner with advisory file lock
│   │   ├── migrations/           # Committed, sequential SQL files (0000_init.sql, 0001_add_orgs.sql)
│   │   └── schema/               # Drizzle table definitions split by domain (users.ts, orgs.ts, billing.ts)
│   ├── server/                   # Strictly server-only business logic (`import "server-only"` at top of every file)
│   │   ├── actions/              # Next.js Server Actions (input validation -> auth check -> service call -> revalidate)
│   │   ├── queries/              # Read-only Data Access Layer (DAL) functions wrapped in React `cache()`
│   │   └── services/             # Transactional domain logic (Stripe sync, org provisioning, RBAC checks)
│   └── lib/                      # Isomorphic pure utilities, Zod schemas, constants, error classes
└── tests/
    ├── helpers/test-db.ts        # Creates isolated in-memory SQLite instance per test with migrations applied
    ├── integration/              # Service & DAL tests against real in-memory SQLite
    └── e2e/                      # Playwright browser specs
```

### Architectural Boundaries (Strict)
1. **No direct `db` imports inside `src/app/` or `src/components/`**:
   - Pages (`page.tsx`) and Server Components read data exclusively via `src/server/queries/*`.
   - Client Components (`"use client"`) mutate data exclusively via `src/server/actions/*`.
2. **Every file in `src/db/` and `src/server/` MUST start with `import "server-only";`**:
   - This guarantees `better-sqlite3` native bindings are never accidentally bundled into client chunks.
3. **Node.js Runtime Enforcement**:
   - Never set `export const runtime = "edge"` on any route or layout that touches `better-sqlite3`. Native C++ addons require the Node.js runtime (`export const runtime = "nodejs"`).

---

## 4. Naming Conventions

| Artifact | Convention | Example | Reason |
| :--- | :--- | :--- | :--- |
| **Files & Directories** | `kebab-case` | `src/server/queries/org-members.ts` | Case-sensitive Linux filesystem safety across macOS/Linux deploys |
| **React Components** | `PascalCase` export | `export function BillingUsageCard()` | Standard JSX component resolution |
| **Server Actions** | `camelCase` verb + noun, suffixed with `Action` | `createProjectAction`, `updateMemberRoleAction` | Distinguishes network-crossing RPC mutations from local functions |
| **DAL Read Queries** | `get*` or `list*` prefix | `getOrganizationBySlug`, `listActiveSubscriptions` | Makes read-only semantics explicit at call sites |
| **SQLite Tables** | `snake_case`, plural | `organizations`, `organization_members`, `webhook_events` | Avoids SQL reserved-word collisions (`user`, `order`, `group`) |
| **SQLite Columns** | `snake_case` | `created_at`, `stripe_customer_id`, `amount_cents` | Matches raw SQLite pragma and migration output |
| **Primary Keys** | Prefixed ULID/nanoid text (`id`) | `usr_01J9X...`, `org_01J9X...` | Sortable by creation time, URL-safe, prevents sequential ID enumeration |
| **Foreign Keys** | `<singular_table>_id` | `organization_id`, `user_id` | Unambiguous join target |
| **Indexes** | `idx_<table>_<columns>` | `idx_org_members_org_id_user_id` | Immediately identifiable in `EXPLAIN QUERY PLAN` |
| **Unique Constraints** | `uq_<table>_<columns>` | `uq_organizations_slug` | Deterministic error parsing on `SQLITE_CONSTRAINT_UNIQUE` |

---

## 5. SQLite & Migration Conventions

### 5.1 Mandatory Connection Pragmas (`src/db/index.ts`)
Every SQLite connection MUST execute these pragmas immediately upon opening:

```ts
import "server-only";
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema";

const sqlite = new Database(process.env.DATABASE_URL ?? "./data/app.db");

// Mandatory production pragmas — DO NOT REMOVE
sqlite.pragma("journal_mode = WAL");          // Concurrent reads during writes
sqlite.pragma("synchronous = NORMAL");        // Full durability in WAL mode without fsync stall on every commit
sqlite.pragma("busy_timeout = 5000");         // Wait up to 5s on write lock contention instead of immediate SQLITE_BUSY
sqlite.pragma("foreign_keys = ON");           // SQLite disables FK enforcement by default; must be enabled per connection
sqlite.pragma("temp_store = MEMORY");         // Keep temporary sort/index tables in RAM
sqlite.pragma("cache_size = -64000");         // 64MB page cache
sqlite.pragma("mmap_size = 268435456");       // 256MB memory-mapped I/O

export const db = drizzle(sqlite, { schema });
export type DbClient = typeof db;
```

### 5.2 Data Types & Schema Rules
1. **Timestamps**: Store as `INTEGER` Unix epoch milliseconds (`mode: "timestamp_ms"`) and always default to `(unixepoch('subsec') * 1000)`. Reason: Integer comparisons and range indexes are faster and timezone-bug-free compared to mixed ISO strings.
2. **Booleans**: Store as `INTEGER` (`0` or `1`, Drizzle `{ mode: "boolean" }`).
3. **Monetary Values**: Store as `INTEGER` in the smallest currency unit (`amount_cents`, e.g., `$19.00` -> `1900`). **Never use `REAL`/`FLOAT` for money.**
4. **JSON Columns**: Only use `TEXT` (`{ mode: "json" }`) for unstructured audit metadata or external webhook payloads. Never store relational foreign keys inside JSON arrays.
5. **Multi-Tenant Isolation**: Every tenant-owned table MUST include `organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE` and a composite index starting with `organization_id`.

### 5.3 Migration Rules
1. **Never hand-edit applied migration files** in `src/db/migrations/`. Migrations are append-only.
2. **Never use `drizzle-kit push` in production or CI**: Always generate explicit SQL via `pnpm db:generate`, inspect the generated `.sql` file, and commit it to git.
3. **SQLite `ALTER TABLE` awareness**: Adding a `NOT NULL` column to an existing table requires a `DEFAULT` value, or a 12-step table rebuild inside a transaction with `PRAGMA foreign_keys = OFF` outside the transaction.
4. **Transactions are synchronous in `better-sqlite3`**:
   - Inside `db.transaction((tx) => { ... })`, **never `await` a Promise** (no `fetch()`, no Stripe API calls, no async crypto). `better-sqlite3` transactions run synchronously on the main thread; yielding to the event loop inside a transaction will throw or interleave statements from other requests.
   - Perform all external network I/O (Stripe, email, LLM calls) *before* or *after* the synchronous SQLite transaction, using an outbox/idempotency record if two-phase consistency is needed.

---

## 6. Component, DAL & Server Action Patterns

### 6.1 Next.js 15 Async Request APIs
In Next.js 15, `params`, `searchParams`, `cookies()`, and `headers()` are **always Promises**. Always `await` them:

```tsx
// Correct Next.js 15 Page signature
export default async function ProjectPage({
  params,
  searchParams,
}: {
  params: Promise<{ orgSlug: string; projectId: string }>;
  searchParams: Promise<{ tab?: string }>;
}) {
  const { orgSlug, projectId } = await params;
  const { tab = "overview" } = await searchParams;
  // ...
}
```

### 6.2 Authenticated Data Access Layer (`src/server/queries/`)
Authenticate and authorize inside the query function itself (never rely solely on `middleware.ts`):

```ts
import "server-only";
import { cache } from "react";
import { and, eq } from "drizzle-orm";
import { db } from "@/db";
import { projects } from "@/db/schema";
import { requireOrgMember } from "@/server/services/auth";

export const getProjectById = cache(async (orgSlug: string, projectId: string) => {
  const { org } = await requireOrgMember(orgSlug);
  return db.query.projects.findFirst({
    where: and(eq(projects.id, projectId), eq(projects.organizationId, org.id)),
  });
});
```

### 6.3 Server Action Pattern (`src/server/actions/`)
All Server Actions MUST return a discriminated union `ActionResult<T>` rather than throwing expected validation/domain errors across the client boundary:

```ts
export type ActionResult<T = void> =
  | { ok: true; data: T }
  | { ok: false; error: string; fieldErrors?: Record<string, string[]> };
```

Every Server Action follows this exact 5-step pipeline:
1. Parse input with a Zod schema (`schema.safeParse`).
2. Verify session and tenant role via `requireOrgMember(orgSlug, ["owner", "admin"])`.
3. Execute synchronous SQLite mutation (`db.transaction(...)`).
4. Call `revalidatePath` / `revalidateTag`.
5. Return `{ ok: true, data }`.

---

## 7. What We Don't Do (And Why)

| Anti-Pattern | What We Do Instead | Why |
| :--- | :--- | :--- |
| **No `async/await` inside `db.transaction()`** | Run external API calls outside the transaction; keep `db.transaction((tx) => ...)` 100% synchronous | `better-sqlite3` is synchronous. Yielding to the Node.js event loop mid-transaction holds the single SQLite write lock across I/O latency, causing `SQLITE_BUSY` across all concurrent users |
| **No `middleware.ts` database queries** | Validate session tokens in `src/server/services/auth.ts` (cached per request with React `cache()`) | Next.js middleware runs before route rendering and historically defaults to Edge constraints; keeping auth + RBAC in the Node.js DAL ensures single-hop SQLite reads and defense-in-depth |
| **No `/api/*` Route Handlers for internal UI mutations** | Use typed Server Actions in `src/server/actions/` | Route Handlers require manual `fetch()` boilerplate, duplicate Zod type definitions, and manual client cache invalidation. Reserve `/api/*` strictly for external webhooks (Stripe) and healthchecks |
| **No `SELECT *` without `organization_id` filter** | Every query on tenant data includes `eq(table.organizationId, org.id)` | Prevents Cross-Tenant Insecure Direct Object Reference (IDOR) vulnerabilities |
| **No ORM "magic" auto-migrations on boot** | Run `pnpm db:migrate` as an explicit pre-start step (`node dist/migrate.js && next start`) | Running schema migrations lazily inside request handlers causes race conditions during rolling restarts |
| **No `useEffect` data fetching for initial page state** | Fetch in Server Components and pass serializable props (or stream via `<Suspense>`) | Eliminates client-server network waterfalls and layout shift; SQLite reads on the same machine take <0.2ms |
| **No floating-point currency (`REAL`) or unindexed FKs** | Use integer cents (`INTEGER`) and explicit `index("idx_...")` on every foreign key | SQLite does not automatically index foreign keys; missing FK indexes cause full table scans on `ON DELETE CASCADE` and joins |
