# CLAUDE.md — Next.js 15 + SQLite SaaS Architecture Guide

> **Project Target**: Modern, type-safe SaaS application built with Next.js 15 (App Router), React 19, TypeScript 5, and SQLite (via `better-sqlite3` locally and LibSQL / Turso at edge).

---

## 1. Stack & Versions

- **Framework**: Next.js 15.x (App Router only, React Server Components by default)
- **UI & Runtime**: React 19.x, TypeScript 5.x (`strict: true`)
- **Styling**: Tailwind CSS 4.x + `shadcn/ui` components (Radix UI primitives)
- **Database**: SQLite (via `better-sqlite3` for high-throughput node runtime, LibSQL / `@libsql/client` compatible)
- **ORM / Query Builder**: Drizzle ORM (`drizzle-orm` + `drizzle-kit`) for zero-overhead compile-time type safety
- **Validation**: Zod 3.x (`z.infer` for all input boundary validation)
- **Authentication**: Lucia Auth / Auth.js with SQLite session adapter

---

## 2. Dev & Operational Commands

```bash
# Development server (Turbopack enabled)
pnpm dev

# Type-check and lint
pnpm typecheck
pnpm lint

# Database schema management
pnpm db:generate    # Generates SQL migration files in /drizzle
pnpm db:migrate     # Applies pending migrations to SQLite database
pnpm db:studio      # Opens local Drizzle Studio GUI for visual schema inspection
pnpm db:seed        # Populates baseline seed data (development only)

# Production build and run
pnpm build
pnpm start

# Automated test suite
pnpm test           # Runs Vitest unit and integration test suite
```

---

## 3. Directory & Folder Structure

```
├── drizzle/                    # Generated SQL migration history files
├── src/
│   ├── actions/                # Server Actions (Mutations & business logic)
│   │   ├── auth.ts             # Auth sign-in / sign-up / logout actions
│   │   └── workspace.ts        # Domain-specific mutation procedures
│   ├── app/                    # Next.js 15 App Router
│   │   ├── (auth)/             # Route group: /login, /register (standalone layout)
│   │   ├── (dashboard)/        # Route group: Protected app workspace (/dashboard, /settings)
│   │   ├── api/                # Public REST Webhooks only (e.g. Stripe, GitHub webhooks)
│   │   ├── layout.tsx          # Global root layout (fonts, providers, metadata)
│   │   └── page.tsx            # Marketing homepage
│   ├── components/
│   │   ├── ui/                 # Reusable atomic design primitives (buttons, inputs, dialogs)
│   │   └── modules/            # Feature-specific composite components
│   ├── db/
│   │   ├── client.ts           # SQLite connection pool & Drizzle client instance
│   │   ├── schema.ts           # Drizzle schema definitions & relations
│   │   └── migrations.ts       # Migration execution runner
│   ├── lib/
│   │   ├── auth.ts             # Session validation helpers & password hashing
│   │   └── utils.ts            # Class merges (clsx + twMerge), string helpers
│   └── types/                  # Global shared TypeScript interface definitions
├── drizzle.config.ts           # Drizzle Kit configuration
└── tsconfig.json               # Strict TypeScript configuration
```

---

## 4. SQL & SQLite Database Conventions

### SQLite PRAGMA Standards (Mandatory in `src/db/client.ts`)
Always execute these PRAGMAs upon opening any SQLite connection:
```sql
PRAGMA journal_mode = WAL;          -- Write-Ahead Logging allows concurrent reads during write transactions
PRAGMA busy_timeout = 5000;         -- 5-second backoff prevents "database is locked" errors under load
PRAGMA foreign_keys = ON;           -- Enforce relational referential integrity at the database engine level
PRAGMA synchronous = NORMAL;        -- Safe and performant balance when using WAL mode
```

### Schema & Column Standards
1. **Primary Keys**: Always use UUIDv4 or `text('id').primaryKey()` with nanoid/cuid2. Never expose auto-incrementing sequential integers in public URLs to prevent enumeration attacks.
2. **Timestamps**: Every table must contain:
   ```typescript
   createdAt: integer('created_at', { mode: 'timestamp_ms' }).notNull().$defaultFn(() => new Date()),
   updatedAt: integer('updated_at', { mode: 'timestamp_ms' }).notNull().$defaultFn(() => new Date()),
   ```
3. **Foreign Keys**: Always specify `onDelete: 'cascade'` or `onDelete: 'restrict'` explicitly. Never leave delete behavior implicit.

---

## 5. Architectural & Component Patterns

### React Server Components (RSC) by Default
- Data fetching occurs exclusively in Server Components using direct Drizzle queries.
- Do not make HTTP fetch calls to internal Next.js `/api` endpoints from Server Components. Call the database layer directly.

### Client Components Only When Required
- Add `'use client'` only at the lowest leaf component level requiring browser state (`useState`, `useEffect`, or event listeners).
- Never make entire page wrappers client components.

### Server Actions for All Data Mutations
All mutations must follow this strict signature:
```typescript
'use server'

import { z } from 'zod';
import { db } from '@/db/client';

export type ActionResult<T> =
  | { success: true; data: T }
  | { success: false; error: string };

export async function createItemAction(input: unknown): Promise<ActionResult<{ id: string }>> {
  // 1. Zod input validation
  const parsed = inputSchema.safeParse(input);
  if (!parsed.success) {
    return { success: false, error: parsed.error.issues[0].message };
  }

  // 2. Auth session verification
  const session = await getSession();
  if (!session) {
    return { success: false, error: 'Unauthorized' };
  }

  // 3. Database mutation inside try/catch
  try {
    const [inserted] = await db.insert(items).values({ ...parsed.data, userId: session.userId }).returning();
    return { success: true, data: { id: inserted.id } };
  } catch (err: any) {
    return { success: false, error: 'Failed to create item' };
  }
}
```

---

## 6. What We DO NOT Do (and Why)

| Anti-Pattern | Why We Avoid It | What We Do Instead |
|--------------|-----------------|--------------------|
| **Prisma ORM** | Heavy Rust engine binary overhead, slow cold starts on serverless, suboptimal SQLite concurrency. | Use **Drizzle ORM** (zero-overhead, raw SQL speed, compile-time type inference). |
| **Internal `/api` REST routes for CRUD** | Introduces serialization overhead, redundant HTTP roundtrips, and endpoint sprawl. | Use **Server Actions** directly called from React forms or UI triggers. |
| **Client-Side Data Fetching (SWR/React Query) for initial renders** | Leads to layout shifts, request waterwalls, and larger JavaScript bundles sent to the client. | Fetch directly in **React Server Components** before HTML streaming. |
| **`any` TypeScript types** | Bypasses compiler safety and creates latent runtime bugs in production. | Strict typing with `z.infer<typeof Schema>` across all boundaries. |
| **Database file in public directory** | Security vulnerability exposing the raw `.sqlite` file over HTTP. | Store `.sqlite` database outside the `public/` web root, typically in `.data/app.db`. |
| **Direct untransactional multi-table writes** | Can leave database in an inconsistent corrupted state if an operation fails halfway. | Wrap multi-table operations in `db.transaction(async (tx) => { ... })`. |

---

## 7. Quality Checklist Before Merging Code

- [ ] `pnpm typecheck` returns zero TypeScript diagnostics.
- [ ] All inputs validated via Zod schemas before hitting DB queries.
- [ ] All database foreign keys have explicit delete constraints (`cascade` or `restrict`).
- [ ] No secrets or private keys leaked in client-facing components (`NEXT_PUBLIC_` prefix audited).
- [ ] Server actions return standard `{ success, data, error }` pattern.
