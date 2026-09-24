# CLAUDE.md — Next.js 15 App Router + SQLite SaaS Blueprint

This document defines architecture, style, database conventions, and rules for Claude Code when working in this repository. Follow these conventions strictly. Do not ask clarifying questions when conventions explicitly resolve ambiguity.

---

## 1. Stack & Pinned Versions

- **Framework**: Next.js 15 (App Router with React 19 Server Components)
- **Language**: TypeScript 5.6+ (strict mode enabled, no `any`, explicit return types on exports)
- **Database Engine**: SQLite 3 via `better-sqlite3` (synchronous, in-process, sub-millisecond local queries)
  - *Production Cloud SQLite Alternative*: `@libsql/client` (Turso) via the same unified database interface
- **ORM / Query Builder**: Drizzle ORM (`drizzle-orm` + `drizzle-kit`)
- **Styling**: Tailwind CSS v4 + `shadcn/ui` (Radix primitives)
- **Icons**: `lucide-react`
- **Validation**: `zod` v3.23+ (schemas used for Server Actions, API routes, and DB record validation)
- **Package Manager**: `pnpm` (required; lockfile is `pnpm-lock.yaml`)

---

## 2. Dev Commands & Tooling

```bash
pnpm dev              # Start dev server with Turbopack (http://localhost:3000)
pnpm build            # Production compilation and type checking
pnpm start            # Run production build
pnpm lint             # Run ESLint check
pnpm typecheck        # Run tsc --noEmit
pnpm test             # Run Vitest unit & integration test suites
pnpm db:generate      # Generate Drizzle SQL migration files from schema
pnpm db:migrate       # Apply pending migrations to local SQLite database
pnpm db:push          # Fast schema push during early local prototyping
pnpm db:studio        # Open Drizzle web inspector (http://local.drizzle.studio)
pnpm db:seed          # Seed development database with deterministic mock users & plans
```

---

## 3. Directory & File Organization

```text
├── app/
│   ├── (auth)/             # Route group: login, signup, reset-password
│   ├── (dashboard)/        # Route group: authenticated SaaS dashboard
│   │   ├── layout.tsx      # Sidebar, workspace context, user nav
│   │   ├── page.tsx        # Main dashboard overview (Server Component)
│   │   └── settings/       # Account, billing, team settings
│   ├── api/
│   │   └── webhooks/       # Stripe/LemonSqueezy webhook handlers
│   ├── layout.tsx          # Root HTML layout, font loader, theme provider
│   └── globals.css         # Tailwind base styles & theme tokens
├── components/
│   ├── ui/                 # Atomic design primitives (Button, Dialog, Input - shadcn)
│   ├── forms/              # Controlled client forms with react-hook-form + zod
│   └── shared/             # Header, Footer, EmptyState, PageHeader
├── lib/
│   ├── db/
│   │   ├── schema/         # Modular Drizzle schemas (users.ts, teams.ts, subscriptions.ts)
│   │   ├── client.ts       # Database singleton instance with WAL mode config
│   │   └── index.ts        # Re-exported database handle & schema
│   ├── actions/            # Next.js Server Actions ("use server" mutations)
│   │   ├── auth.ts
│   │   └── billing.ts
│   ├── auth/               # Session management & password hashing (Argon2id/bcrypt)
│   └── utils.ts            # cn() class utility, formatting helpers
├── migrations/             # Generated SQL migration files (tracked in git)
├── drizzle.config.ts       # Drizzle CLI configuration
└── tests/                  # Vitest integration tests (in-memory SQLite db per test)
```

---

## 4. SQLite & Database Conventions

### Pragmas & Concurrency
All SQLite connections MUST be initialized with these production pragmas in `lib/db/client.ts`:
1. `PRAGMA journal_mode = WAL;` (Write-Ahead Logging allows concurrent readers alongside a writer)
2. `PRAGMA synchronous = NORMAL;` (Safe with WAL mode; eliminates disk sync bottlenecks)
3. `PRAGMA foreign_keys = ON;` (Strict referential integrity enforcement)
4. `PRAGMA busy_timeout = 5000;` (Prevents "database is locked" crashes during bursts by queuing writes)

```typescript
// lib/db/client.ts
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import * as schema from "./schema";

const sqlite = new Database(process.env.DATABASE_URL || "sqlite.db");
sqlite.pragma("journal_mode = WAL");
sqlite.pragma("synchronous = NORMAL");
sqlite.pragma("foreign_keys = ON");
sqlite.pragma("busy_timeout = 5000");

export const db = drizzle(sqlite, { schema });
```

### Table Conventions
- Primary keys: Prefer UUIDv7 (time-ordered) or NanoID strings over sequential auto-increment integers to prevent ID enumeration attacks:
  `id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID())`
- Timestamps: Always store `created_at` and `updated_at` as integer UNIX timestamps (`mode: "timestamp"`) or ISO strings.
- Foreign keys: Always specify `onDelete: "cascade"` or `onDelete: "restrict"`. Never leave cascading behavior undefined.

---

## 5. Component & Data Fetching Patterns

### Server Components First
- Treat all pages and layouts as **Server Components** by default.
- Fetch data directly in Server Components using `await db.query...`.
- Never wrap simple reads in an internal HTTP `fetch('/api/...')` call inside Server Components — query SQLite directly.

### Mutations via Server Actions
- Write all mutations as Server Actions (`"use server"`) in `lib/actions/`.
- Validate all incoming parameters with a Zod schema before database execution.
- Return structured result tuples: `{ success: true, data: T }` or `{ success: false, error: string }`.
- Call `revalidatePath()` or `revalidateTag()` immediately after successful writes.

```typescript
// Example: lib/actions/teams.ts
"use server";
import { z } from "zod";
import { db } from "@/lib/db";
import { teams } from "@/lib/db/schema";
import { revalidatePath } from "next/cache";

const CreateTeamSchema = z.object({
  name: z.string().min(2).max(50),
});

export async function createTeamAction(input: z.infer<typeof CreateTeamSchema>) {
  const parsed = CreateTeamSchema.safeParse(input);
  if (!parsed.success) {
    return { success: false, error: parsed.error.issues[0].message };
  }
  
  const [created] = await db.insert(teams).values({ name: parsed.data.name }).returning();
  revalidatePath("/dashboard/teams");
  return { success: true, data: created };
}
```

---

## 6. Anti-Patterns: What We Don't Do (And Why)

| Anti-Pattern | Why We Avoid It | What To Do Instead |
| :--- | :--- | :--- |
| **`useEffect` data fetching** | Causes layout shift, waterfall network chains, and exposes private database models to the client. | Fetch on the server in Server Components; stream with `<Suspense>` skeletons. |
| **Client-side DB imports** | Bundles server/native binaries into the browser, causing build failures and security leaks. | Keep `better-sqlite3` and `db` strictly inside server files (`lib/actions/*`, `lib/db/*`, Server Components). |
| **Heavy ORMs (Prisma Engine)** | Prisma spawns an external query-engine Rust binary which bloats cold starts and slows down SQLite. | Use Drizzle ORM — zero-overhead, thin TypeScript wrapper over raw SQL. |
| **Raw SQL String Interpolation** | Causes critical SQL injection vulnerabilities (`SELECT * FROM users WHERE id = '${id}'`). | Always use Drizzle prepared statements or parameterized templates: `sql`tag`. |
| **Unbounded List Queries** | Running `SELECT *` without limits causes memory leaks as database tables grow. | Always append `.limit(pageSize).offset(...)` with cursor pagination. |

---

## 7. Testing Strategy
- Tests live in `tests/` using **Vitest**.
- Unit tests for Server Actions execute against an in-memory SQLite database (`new Database(":memory:")`) to guarantee complete test isolation and zero disk contamination.
- Test suites must pass with zero warnings before deploying to main.
