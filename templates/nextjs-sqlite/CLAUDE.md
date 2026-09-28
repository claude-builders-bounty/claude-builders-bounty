# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

> **Scope:** This file is the single source of truth for Claude Code in this repo. Follow every rule below without asking clarifying questions. Each rule states its `reason:` — do not change a rule until you understand the reason. Paste this file unchanged into any greenfield `create-next-app@15` + `better-sqlite3` project and it must work.

---

## 1. Stack & Pinned Versions

| Layer | Choice | Reason |
|---|---|---|
| Framework | **Next.js 15** (App Router, Turbopack) | React 19 Server Components by default; least JS shipped to browser. |
| Language | **TypeScript 5.6+** `strict: true`, no `any` | `unknown` + narrowing instead of `any`; `any` leaks through props. |
| DB (local) | **better-sqlite3 12.x** (synchronous, in-process) | Sub-ms queries, zero network hop, WAL supports concurrent reads + 1 writer. |
| DB (prod) | **Turso / @libsql/client** | Same SQLite dialect; swap is one connection-string change. |
| ORM | **Drizzle ORM + drizzle-kit** | Zero-runtime magic, SQL-readable migrations, typed queries, no Rust binary. |
| Styling | **Tailwind CSS v4 + shadcn/ui** | Utility-first + Radix primitives; no CSS-in-JS runtime. |
| Validation | **zod 3.23+** | One schema validates form, Server Action, and API route. |
| Auth | **Auth.js / Lucia + Argon2id** | Session cookie, not JWT-in-localStorage — immune to XSS token theft. |
| Tests | **Vitest + Playwright** | Vitest for unit/integration (in-memory SQLite per test), Playwright for auth/billing e2e. |
| Package mgr | **pnpm** (lockfile `pnpm-lock.yaml`) | Strictest peer-deps, fastest installs, reproducible CI cache. |
| Node | **22 LTS** | Native `node:sqlite` available but `better-sqlite3` still faster for sync writes. |

**Version pinning rule:** Do not bump major versions without updating `migrations/` pragmas, Drizzle config, and this table together — reason: SQLite pragmas and Drizzle dialects are version-coupled.

---

## 2. Dev Commands

```bash
pnpm dev              # Turbopack dev server → http://localhost:3000
pnpm build            # Production build + typecheck (must pass before PR)
pnpm start            # Serve production build
pnpm lint             # ESLint (next/core-web-vitals)
pnpm typecheck        # tsc --noEmit
pnpm test             # Vitest (unit + integration, in-memory SQLite per file)
pnpm test:e2e         # Playwright (auth + billing flows only)
pnpm db:generate      # drizzle-kit generate — creates SQL migration file
pnpm db:migrate       # Apply pending migrations to local dev.db
pnpm db:push          # ⚠️ Local prototyping only — never on a branch that has been pushed
pnpm db:studio        # Drizzle Studio inspector
pnpm db:seed          # Deterministic seed (users, plans) — idempotent
```

**Gate before every commit:** `pnpm lint && pnpm typecheck && pnpm test && pnpm build` — reason: billing and auth regressions cost real money; the build gate catches prerender/env errors that dev never shows.

---

## 3. Folder Structure

```
app/
  (marketing)/               # Route group — no URL segment (landing, pricing, blog)
  (auth)/                    # login, signup, reset-password — unauthenticated layouts
  (dashboard)/               # Authenticated SaaS shell
    layout.tsx               # Sidebar + workspace context + user nav (Server Component)
    page.tsx                 # Overview (Server Component, direct db query)
    settings/                # Account / billing / team
  api/
    webhooks/stripe/route.ts # Stripe webhook only — every other mutation is a Server Action
  layout.tsx                 # Root <html>, font loader, theme provider
  globals.css                # Tailwind base + design tokens

components/
  ui/                        # shadcn primitives — presentational only, no db import
  forms/                     # Client forms: react-hook-form + zodResolver
  shared/                    # Header, Footer, EmptyState, PageHeader

lib/
  db/
    client.ts                # Singleton better-sqlite3 + WAL pragmas (see §4)
    index.ts                 # Re-export db handle + schema
    schema/
      users.ts               # One file per domain table
      teams.ts
      subscriptions.ts
  actions/                   # Server Actions — every mutation lives here
    auth.ts
    teams.ts
    billing.ts
  auth/
    session.ts               # Cookie session helpers
    password.ts              # Argon2id hash / verify
  env.ts                     # zod-parsed process.env — fail-fast on boot
  utils.ts                   # cn(), formatters — no business logic

migrations/                  # Drizzle-generated SQL — committed to git, never edited after merge
  0000_init.sql
  0001_add_teams.sql

drizzle.config.ts            # Points at lib/db/schema + DATABASE_URL
tests/
  setup.ts                   # Creates in-memory SQLite per test file
  factories/                 # Deterministic test data builders
```

**One place per kind of code** — reason: Claude never asks "where does the db live?" and code search is O(1).

---

## 4. SQLite & Migration Rules

### 4.1 Connection — `lib/db/client.ts`

Every SQLite connection **must** set these pragmas at open. No exceptions.

```ts
// lib/db/client.ts
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema";

const sqlite = new Database(process.env.DATABASE_URL ?? "file:./dev.db");
sqlite.pragma("journal_mode = WAL");   // concurrent readers + 1 writer without full file lock
sqlite.pragma("synchronous = NORMAL"); // safe with WAL; avoids fsync bottleneck
sqlite.pragma("foreign_keys = ON");    // enforce FK constraints — SQLite default is OFF
sqlite.pragma("busy_timeout = 5000");  // queue writes 5s instead of throwing "database is locked"

export const db = drizzle(sqlite, { schema });
export { sqlite };
```

Reason for each pragma: WAL prevents `SQLITE_BUSY` on concurrent reads during writes; `NORMAL` is crash-safe only under WAL; `foreign_keys = OFF` by default silently breaks referential integrity; `busy_timeout` converts lock errors into queued retries.

For **Turso** (production):

```ts
import { createClient } from "@libsql/client";
import { drizzle } from "drizzle-orm/libsql";
const client = createClient({ url: process.env.DATABASE_URL!, authToken: process.env.TURSO_AUTH_TOKEN });
export const db = drizzle(client, { schema });
```
Reason: dialect is identical — `DATABASE_URL=file:./dev.db` locally becomes `libsql://…` in prod with zero query changes.

### 4.2 Schema Conventions

| Rule | Example | Reason |
|---|---|---|
| PK: `text` UUID/NanoID, not auto-increment int | `id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID())` | Prevents ID enumeration; lexicographically sortable if UUIDv7. |
| Timestamps: `integer` Unix ms + `mode: "timestamp"` | `createdAt: integer("created_at", { mode: "timestamp" }).notNull()` | Timezone-free, sortable, no string parsing. |
| FK: always explicit `onDelete` | `.references(() => users.id, { onDelete: "cascade" })` | Undefined cascade silently orphans rows. |
| Enums: `text` + zod union, not `check()` | `plan: text("plan").notNull().$type<"free"\|"pro">()` | SQLite has no native enum; zod is the single validator. |
| No `SELECT *` | Enumerate columns in every query | Adding a column breaks no API response shape. |

### 4.3 Migration Discipline

1. **Schema change = new migration file, next sequence number.** Never edit a migration that has been merged to `main` — reason: local/prod drift, lost rollback.
2. **Migrations are SQL files, not TypeScript.** Review the SQL before merging — reason: Drizzle can generate surprising `DROP` statements.
3. `pnpm db:push` is allowed only on local branches never pushed — reason: it skips the migration history and cannot be replayed on prod.
4. `pnpm db:migrate` runs automatically in CI dry-run before build — reason: catches missing `ALTER TABLE` before deploy.
5. Seed lives in `migrations/seed.sql` or `lib/db/seed.ts`, never hardcoded in app code — reason: seed must be idempotent and runnable on any env.

Example migration:

```sql
-- migrations/0001_add_plan.sql
ALTER TABLE users ADD COLUMN plan TEXT NOT NULL DEFAULT 'free';
ALTER TABLE users ADD COLUMN plan_updated_at INTEGER;
```

---

## 5. Naming Conventions

| Target | Convention | Example | Reason |
|---|---|---|---|
| Files & folders | `kebab-case` | `user-card.tsx`, `lib/db/client.ts` | Linux is case-sensitive; macOS is not — kebab avoids deploy-only breakage. |
| Components | `PascalCase` | `UserCard`, `BillingForm` | Matches React convention; grep-friendly. |
| Hooks | `use-kebab` file, `useCamel` export | `use-teams.ts` → `useTeams()` | Instant recognition as hook. |
| DB tables/columns | `snake_case` | `users`, `created_at` | SQLite idiomatic; Drizzle maps to camelCase in TS if desired. |
| Env vars | `SCREAMING_SNAKE` | `DATABASE_URL`, `STRIPE_SECRET_KEY` | 12-factor standard. |
| Route segment | Singular or group | `app/(dashboard)/settings/` | Groups `(…)` do not appear in URL — reason: layout sharing without URL nesting. |

Max **one component per file** (plus its `.test.tsx`), max **two files per feature folder** — reason: file search stays trivial and barrel re-exports stay shallow.

---

## 6. Component & Data-Fetching Patterns

### 6.1 Server Components First

- Every `page.tsx` and `layout.tsx` is a **Server Component** by default. Do not add `"use client"` unless the file needs `useState`, `useEffect`, or browser APIs.
- Fetch inside the Server Component with `await db.query.users.findMany(...)` — never `fetch("/api/users")` from a Server Component — reason: internal fetch adds a network hop to query the same SQLite file on the same machine.
- Stream slow sections with `<Suspense fallback={<Skeleton />}>` — reason: avoids waterfall; fast parts paint immediately.

### 6.2 Mutations via Server Actions

All writes go through Server Actions in `lib/actions/*.ts`:

```ts
// lib/actions/teams.ts
"use server";
import { z } from "zod";
import { db } from "@/lib/db";
import { teams } from "@/lib/db/schema/teams";
import { revalidatePath } from "next/cache";

const CreateTeamSchema = z.object({
  name: z.string().min(2).max(50),
  slug: z.string().regex(/^[a-z0-9-]+$/),
});

export async function createTeamAction(input: unknown) {
  const parsed = CreateTeamSchema.safeParse(input);
  if (!parsed.success) return { success: false as const, error: parsed.error.issues[0].message };
  const [row] = await db.insert(teams).values({ name: parsed.data.name, slug: parsed.data.slug }).returning();
  revalidatePath("/dashboard/teams");
  return { success: true as const, data: row };
}
```

Rules:
- `input: unknown` + `safeParse` — reason: caller is the browser; never trust the shape.
- Return `{ success: true, data } | { success: false, error: string }` — reason: no thrown exceptions cross the RSC boundary cleanly.
- Call `revalidatePath` / `revalidateTag` after every successful write — reason: Next.js caches Server Component output aggressively.
- Never expose `db` to a Client Component — reason: bundles `better-sqlite3` native bindings into the browser and leaks schema.

### 6.3 Forms

Use `react-hook-form` + `zodResolver` on the client, submit to a Server Action:

```tsx
"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { CreateTeamSchema } from "@/lib/validators/team";
import { createTeamAction } from "@/lib/actions/teams";
```

Reason: one zod schema drives client validation, server validation, and type inference end-to-end.

### 6.4 Env Contract

```ts
// lib/env.ts
import { z } from "zod";
export const env = z.object({
  DATABASE_URL: z.string().default("file:./dev.db"),
  TURSO_AUTH_TOKEN: z.string().optional(),
  STRIPE_SECRET_KEY: z.string().min(1),
  NEXT_PUBLIC_APP_URL: z.string().url(),
}).parse(process.env);
```

- Import `env` instead of `process.env` everywhere — reason: crash at boot with a clear zod message beats `undefined` at 2am in production.
- Every new env var must be added to `.env.example` — reason: onboarding breaks silently otherwise.

---

## 7. Auth & Authorization

- Session cookie via `lib/auth/session.ts`; never store tokens in `localStorage` — reason: XSS can steal `localStorage`, but `httpOnly` cookies cannot be read by JS.
- Hash passwords with **Argon2id** (preferred) or `bcrypt` cost 12 — reason: SQLite has no pgcrypto; hashing must happen in Node.
- Every Server Action that mutates data must call `requireUser()` / `requireRole("admin")` first — reason: missing auth check is the #1 SaaS vulnerability.
- Row-level scoping: every query includes `where: eq(table.ownerId, session.userId)` — reason: prevents IDOR (Insecure Direct Object Reference) across tenants.

---

## 8. Testing

```ts
// tests/setup.ts — in-memory SQLite per test file
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import * as schema from "@/lib/db/schema";

export function createTestDb() {
  const sqlite = new Database(":memory:");
  sqlite.pragma("journal_mode = WAL");
  sqlite.pragma("foreign_keys = ON");
  // run migrations against this in-memory instance
  return { sqlite, db: drizzle(sqlite, { schema }) };
}
```

- Unit/integration: Vitest with `createTestDb()` — fresh DB per file, no global state — reason: parallel tests never contaminate each other.
- E2E: Playwright covers only `signup → login → create-resource → billing` — reason: those two flows lose real money when broken; exhaustive e2e is flaky and slow.

---

## 9. What We Don't Do (Anti-Patterns)

| Anti-Pattern | Why We Avoid It | Do This Instead |
|---|---|---|
| `useEffect` for data fetching | Layout shift, waterfalls, exposes DB models to client | Fetch in Server Components; stream with `<Suspense>` |
| Importing `db` / `better-sqlite3` in Client Components | Bundles native bindings into browser, build fails, leaks schema | Keep `db` in `lib/db/*` and Server Actions only |
| `fetch("/api/...")` from a Server Component to self | Extra network hop to query same SQLite file | Call `db.query` or a Server Action directly |
| Heavy ORM (Prisma engine) for <20 tables | Rust binary bloats cold start, overkill for SQLite | Drizzle — zero overhead, SQL-transparent |
| `SELECT *` | Adding a column changes API shape, breaks clients | Enumerate columns explicitly |
| `any` in TypeScript | Spreads through props unchecked, defeats `strict` | `unknown` + narrowing, or precise union types |
| Editing a merged migration | Local/prod schema drift, unrecoverable | New migration with next sequence number |
| `console.log` in merged code | Prod logs need level + context; `log` is noise | `lib/logger.ts` with `info`/`warn`/`error` |
| Storing auth tokens in `localStorage` | XSS steals tokens | `httpOnly` cookie session |
| N+1 queries in a loop | SQLite is fast but N round-trips still scale linearly | Single `JOIN` or `WHERE id IN (…)` batch query |
| Committing `dev.db` / `*.sqlite` | Binary churn in git, merge conflicts, secret leakage | `.gitignore` the DB file; migrations reproduce schema |

---

## 10. When SQLite Is the Wrong Choice

Switch away from a local SQLite file when any of these is true — reason: SQLite allows exactly one writer at a time.

- Horizontal scaling across multiple server instances (use Turso/libSQL or Postgres).
- Write throughput > 1k writes/sec sustained.
- Need row-level write concurrency or `LISTEN/NOTIFY`.
- Compliance requires point-in-time recovery beyond file snapshots.

For this SaaS template the path is: **`better-sqlite3` locally → Turso in prod (same dialect, same Drizzle queries) → Postgres only when write concurrency demands it** — reason: each step keeps the migration format and query style stable.

---

## 11. CI Gate (Must Be Green Before Merge)

```
lint → typecheck → test → db:migrate (dry-run) → build → playwright (signup/login/billing)
```

Reason: billing and auth are the two flows that lose real money when broken — e2e is mandatory for them, optional elsewhere.

---

## 12. Quick Start for Claude Code

1. `pnpm install`
2. Copy `.env.example` → `.env` and fill `DATABASE_URL` (default `file:./dev.db` works locally).
3. `pnpm db:migrate && pnpm db:seed`
4. `pnpm dev`
5. Work only inside `app/`, `components/`, `lib/` as described above. Never create files outside the folder structure in §3.

If a request conflicts with this file, this file wins — do not ask, follow the convention and note the deviation in the PR description.
