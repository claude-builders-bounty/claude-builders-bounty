# CLAUDE.md — Next.js 15 + SQLite SaaS Template

> Production-grade, highly opinionated system instructions for building SaaS applications with **Next.js 15 (App Router)**, **React 19**, and **SQLite (better-sqlite3 / Turso)**.

---

## 1. Stack & Versions

- **Framework**: Next.js 15+ (App Router, Turbopack default)
- **Runtime / Language**: Node.js 20+ LTS / TypeScript 5.5+ (Strict Mode)
- **UI & Styling**: React 19, Tailwind CSS v4, Lucide React icons, Radix UI primitives
- **Database**: SQLite with `better-sqlite3` (local/dedicated) or `@libsql/client` (Turso edge replication)
- **ORM / Schema**: Drizzle ORM (`drizzle-orm` + `drizzle-kit`) for type-safe migrations and zero-overhead queries
- **Validation**: Zod v3 (`z.infer`, safeParse on all I/O boundaries)
- **Authentication**: Session-based auth via secure HTTP-only cookies and Argon2id / Lucia patterns
- **Package Manager**: `pnpm` (strictly enforced)

---

## 2. Dev Commands & Scripts

Always run commands via `pnpm`:

```bash
# Development
pnpm dev                 # Start Next.js with Turbopack (http://localhost:3000)
pnpm build               # Build production bundle with type checking
pnpm start               # Start production standalone server
pnpm lint                # Run ESLint across app and lib
pnpm typecheck           # Run tsc --noEmit

# Database & Migrations
pnpm db:generate         # Generate SQL migrations from src/db/schema.ts
pnpm db:migrate          # Apply pending migrations to local/production SQLite database
pnpm db:seed             # Seed database with initial plans and demo data
pnpm db:studio           # Open Drizzle Studio UI to inspect SQLite tables locally
pnpm db:vacuum           # Optimize SQLite storage and defragment database file

# Testing
pnpm test                # Run Vitest unit & integration test suites
pnpm test:watch          # Run Vitest in interactive watch mode
pnpm test:e2e            # Run Playwright end-to-end tests
```

---

## 3. Project & Folder Structure

We enforce a feature-first, layered architecture isolating server data from client presentation:

```
├── .env.example
├── CLAUDE.md
├── drizzle.config.ts
├── next.config.ts
├── package.json
├── tsconfig.json
├── src/
│   ├── app/
│   │   ├── (auth)/             # Auth routes (login, register, forgot-password)
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── (dashboard)/        # Authenticated SaaS application routes
│   │   │   ├── layout.tsx      # Dashboard shell (sidebar, tenant switcher, user nav)
│   │   │   ├── page.tsx        # Main metrics / overview
│   │   │   ├── settings/       # Account, team, billing settings
│   │   │   └── loading.tsx     # Route-level Suspense fallback
│   │   ├── api/
│   │   │   ├── auth/           # OAuth callbacks & session refresh
│   │   │   └── webhooks/       # Stripe / payment provider webhook handlers
│   │   ├── error.tsx           # Global error boundary
│   │   ├── layout.tsx          # Root layout (fonts, providers, metadata)
│   │   └── page.tsx            # Public marketing landing page
│   ├── actions/                # Server Actions (mutations with Zod validation)
│   │   ├── auth.actions.ts
│   │   ├── user.actions.ts
│   │   └── billing.actions.ts
│   ├── components/
│   │   ├── ui/                 # Headless / atomic UI primitives (button, dialog, input)
│   │   ├── dashboard/          # Domain-specific components for dashboard
│   │   └── shared/             # Reusable shared components across views
│   ├── db/
│   │   ├── index.ts            # SQLite client instance (singleton, WAL configuration)
│   │   ├── schema.ts           # Drizzle schema definitions & relations
│   │   └── migrations/         # Version-controlled SQL migration scripts
│   ├── lib/
│   │   ├── auth/               # Session creation, cookie validation, password hashing
│   │   ├── billing/            # Stripe integration and webhook parsers
│   │   ├── errors/             # Standardized domain error classes
│   │   └── utils.ts            # Classnames helper (clsx, tailwind-merge)
│   └── types/
│       └── index.ts            # Shared DTOs and environment variable interfaces
```

---

## 4. SQLite Conventions & Best Practices

SQLite requires explicit connection configuration for maximum reliability and concurrency in web services.

### 4.1 Connection Configuration (`src/db/index.ts`)
1. **Enable WAL Mode**: Always execute `PRAGMA journal_mode = WAL;` upon initialization. This permits concurrent readers while a write transaction is executing.
2. **Enable Foreign Key Enforcement**: SQLite turns off foreign keys by default. Always execute `PRAGMA foreign_keys = ON;`.
3. **Busy Timeout**: Set `PRAGMA busy_timeout = 5000;` to avoid immediate lock errors under concurrent writes.
4. **Synchronous Mode**: Use `PRAGMA synchronous = NORMAL;` in WAL mode for 10x write performance without sacrificing durability against app crashes.

```typescript
// src/db/index.ts
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import * as schema from './schema';

const sqlitePath = process.env.DATABASE_URL || './sqlite.db';

const globalForDb = globalThis as unknown as { sqlite: Database.Database | undefined };

const sqlite = globalForDb.sqlite ?? new Database(sqlitePath);
sqlite.pragma('journal_mode = WAL');
sqlite.pragma('foreign_keys = ON');
sqlite.pragma('busy_timeout = 5000');
sqlite.pragma('synchronous = NORMAL');

if (process.env.NODE_ENV !== 'production') globalForDb.sqlite = sqlite;

export const db = drizzle(sqlite, { schema });
```

### 4.2 Migration Rules
- Never manually edit production SQLite schemas.
- Update `src/db/schema.ts` using Drizzle ORM definitions.
- Run `pnpm db:generate` to produce timestamped SQL migration files.
- Inspect the generated migration before running `pnpm db:migrate`.
- All tables must have:
  - `id`: Primary key (`text` with CUID2 or UUIDv7).
  - `created_at`: Integer timestamp (`unixepoch()`).
  - `updated_at`: Integer timestamp (`unixepoch()`).

---

## 5. Component Patterns & Data Fetching

### 5.1 Server Components (Default)
- Direct DB access is permitted and encouraged in React Server Components (`RSC`).
- Never wrap RSC in `useEffect` or client-side fetchers.
- Use `React.Suspense` with targeted `loading.tsx` skeletons.

```typescript
// src/app/(dashboard)/page.tsx
import { db } from '@/db';
import { projects } from '@/db/schema';
import { eq } from 'drizzle-orm';
import { requireAuth } from '@/lib/auth';

export default async function DashboardPage() {
  const user = await requireAuth();
  const userProjects = await db.query.projects.findMany({
    where: eq(projects.userId, user.id),
    limit: 50,
  });

  return (
    <div>
      <h1>Your Projects</h1>
      <ProjectList initialProjects={userProjects} />
    </div>
  );
}
```

### 5.2 Server Actions for Mutations
- All state mutations must use Server Actions (`'use server'`).
- Validate every input using Zod before executing SQL.
- Return structured result objects `{ success: boolean; data?: T; error?: string }`.
- Revalidate paths with `revalidatePath()` or `revalidateTag()` immediately after mutation.

```typescript
// src/actions/project.actions.ts
'use server';

import { db } from '@/db';
import { projects } from '@/db/schema';
import { requireAuth } from '@/lib/auth';
import { revalidatePath } from 'next/cache';
import { z } from 'zod';

const createProjectSchema = z.object({
  name: z.string().trim().min(2).max(64),
});

export async function createProjectAction(input: z.infer<typeof createProjectSchema>) {
  const user = await requireAuth();
  const parsed = createProjectSchema.safeParse(input);
  if (!parsed.success) {
    return { success: false, error: parsed.error.issues[0].message };
  }

  const [newProject] = await db.insert(projects).values({
    name: parsed.data.name,
    userId: user.id,
  }).returning();

  revalidatePath('/dashboard');
  return { success: true, data: newProject };
}
```

---

## 6. What We Don't Do (And Why)

1. **NO Prisma**: Prisma introduces heavy binary engines, higher memory overhead, and cold-start latency. Drizzle with `better-sqlite3` provides raw SQLite speed, zero dependencies, and instant compilation.
2. **NO Client-Side Fetching for Initial Renders**: Never use `useEffect()` or TanStack Query to fetch data required for first paint. Fetch in Server Components to eliminate client waterfalls and deliver pure HTML.
3. **NO Unbounded Queries**: Never write `SELECT * FROM table` without an explicit `LIMIT` and index-backed cursor. Unbounded reads exhaust SQLite memory buffers under high volume.
4. **NO Raw Unchecked SQL in Actions**: Never concatenate parameters into raw queries. Always use Drizzle prepared statements or parameterized queries to eliminate SQL injection.
5. **NO Global State for Server Data**: Avoid Redux / Zustand for server-persisted data. Keep server state on the server (RSC + cache tags) and UI filters in URL `searchParams`.
6. **NO Ambiguous String Dates**: Do not store date strings like `MM/DD/YYYY`. Always store timestamps as UTC unix epoch integers (`timestampMs`) or ISO-8601 strings.
7. **NO Hard Deletions on Critical User Data**: Use soft deletes (`deleted_at: integer`) on billing, audit, and user tables to preserve transaction integrity.
