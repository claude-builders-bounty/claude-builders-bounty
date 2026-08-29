# Next.js 15 + SQLite SaaS Development Guidelines

This document provides strict, opinionated architectural and coding rules for building scalable SaaS applications with Next.js 15 App Router and SQLite (Drizzle ORM + better-sqlite3 / Turso).

---

## 1. Tech Stack & Core Versions

- **Framework:** Next.js 15.x (App Router, Server Actions, React 19)
- **Language:** TypeScript 5.x (Strict mode enabled, zero `any`)
- **Database:** SQLite with `better-sqlite3` (Local / VPS) or `@libsql/client` (Turso / Edge)
- **ORM & Migrations:** Drizzle ORM (`drizzle-orm`, `drizzle-kit`)
- **Styling:** Tailwind CSS v4, `clsx`, `tailwind-merge`
- **Validation:** Zod v3.x
- **Icons:** `lucide-react`
- **Auth:** Auth.js v5 / Lucia Auth (Session-based, stored in SQLite)

---

## 2. Project Directory Structure

```text
├── app/
│   ├── (auth)/                # Route group: login, register, forgot-password
│   ├── (dashboard)/           # Protected SaaS dashboard routes
│   │   ├── dashboard/page.tsx # Server Component data root
│   │   └── settings/page.tsx
│   ├── api/                   # Webhook endpoints ONLY (Stripe, external integrations)
│   ├── actions/               # Server Actions grouped by domain (auth, billing, teams)
│   ├── layout.tsx             # Root layout with fonts & providers
│   └── page.tsx               # Marketing landing page
├── components/
│   ├── ui/                    # Primitive components (Button, Input, Modal, Badge)
│   ├── dashboard/             # Domain-specific dashboard widgets
│   └── shared/                # Navbar, Footer, UserAvatar
├── db/
│   ├── schema/                # Drizzle schema split by domain (users.ts, orgs.ts, billing.ts)
│   │   └── index.ts           # Re-exports all table definitions
│   ├── migrations/            # Generated SQL migration files (drizzle-kit)
│   ├── client.ts              # SQLite connection instance with WAL mode
│   └── seed.ts                # Database seeding script
├── lib/
│   ├── auth.ts                # Session resolution & permission checks
│   ├── utils.ts               # cn() helper, date formatters, currency helpers
│   └── validation/            # Reusable Zod schemas
└── types/                     # Shared TypeScript interfaces
```

---

## 3. Essential Dev Commands

```bash
pnpm dev              # Start local dev server (Turbopack)
pnpm build            # Production typecheck & Next.js build
pnpm lint             # Run ESLint & Prettier
pnpm test             # Run Vitest unit & integration test suite

# Database & Migration Workflows
pnpm db:generate      # Generate SQL migrations from schema diffs
pnpm db:migrate       # Apply pending migrations to SQLite database
pnpm db:studio        # Open Drizzle visual database manager
pnpm db:seed          # Seed sample users and organizations
```

---

## 4. SQLite Configuration & Migration Rules

1. **Always Enable WAL (Write-Ahead Logging):**
   SQLite must run in WAL mode to allow concurrent reads during writes without table locks:
   ```typescript
   // db/client.ts
   import Database from 'better-sqlite3';
   import { drizzle } from 'drizzle-orm/better-sqlite3';
   import * as schema from './schema';

   const sqlite = new Database(process.env.DATABASE_URL || 'data/app.db');
   sqlite.pragma('journal_mode = WAL');
   sqlite.pragma('busy_timeout = 5000');
   sqlite.pragma('synchronous = NORMAL');
   sqlite.pragma('foreign_keys = ON');

   export const db = drizzle(sqlite, { schema });
   ```

2. **Schema Conventions:**
   - Primary Keys: Use `text('id').primaryKey().$defaultFn(() => crypto.randomUUID())` or `nanoid` (avoids sequential ID enumeration attacks).
   - Timestamps: Always include `createdAt: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date())` and `updatedAt`.
   - Indexing: Explicitly add `.index()` on all foreign key columns and frequently filtered columns (`status`, `org_id`).

3. **Never Edit Generated Migrations Directly:**
   Always modify `db/schema/*.ts` and run `pnpm db:generate` to produce clean migration versions.

---

## 5. Server & Component Architecture Patterns

### Pattern 1: Server Components First (Zero Waterfalls)
* Fetch data directly in Server Components using Drizzle queries.
* Pass data down as props to Client Components.
* Never use `useEffect` + client-side `fetch()` for initial page load data.

```tsx
// app/(dashboard)/dashboard/page.tsx (Server Component)
import { db } from '@/db/client';
import { projects } from '@/db/schema';
import { requireUser } from '@/lib/auth';
import { ProjectList } from '@/components/dashboard/ProjectList';

export default async function DashboardPage() {
  const user = await requireUser();
  const userProjects = await db.query.projects.findMany({
    where: (p, { eq }) => eq(p.userId, user.id),
    orderBy: (p, { desc }) => [desc(p.createdAt)],
  });

  return <ProjectList initialData={userProjects} />;
}
```

### Pattern 2: Server Actions for All Data Mutations
* Place Server Actions in `app/actions/`.
* Always validate inputs with Zod before executing SQL.
* Return a standardized result object: `{ success: boolean, data?: T, error?: string }`.

```typescript
// app/actions/projects.ts
'use server';

import { db } from '@/db/client';
import { projects } from '@/db/schema';
import { requireUser } from '@/lib/auth';
import { createProjectSchema } from '@/lib/validation/projects';
import { revalidatePath } from 'next/cache';

export async function createProjectAction(rawInput: unknown) {
  const user = await requireUser();
  const parsed = createProjectSchema.safeParse(rawInput);
  
  if (!parsed.success) {
    return { success: false, error: parsed.error.issues[0].message };
  }

  const [newProject] = await db.insert(projects).values({
    ...parsed.data,
    userId: user.id,
  }).returning();

  revalidatePath('/dashboard');
  return { success: true, data: newProject };
}
```

### Pattern 3: Leaf-Level Client Components
* Mark components with `'use client'` only when they manage interactive state (forms, dropdowns, dialogs).
* Keep them as small leaves at the bottom of the component tree.

---

## 6. What We DO NOT Do (And Why)

| Anti-Pattern | Why We Avoid It | What We Do Instead |
| :--- | :--- | :--- |
| **No Prisma ORM** | Prisma's Rust query engine binary causes high cold-start latency on serverless/edge and adds memory bloat with SQLite. | Use **Drizzle ORM** (zero-overhead, pure TypeScript query builder). |
| **No API Route Handlers for Mutations** | Creating `app/api/project/route.ts` for internal CRUD operations creates boilerplate and manual type syncing. | Use **Server Actions** (`app/actions/*.ts`) with direct RPC typing. |
| **No `useEffect` Data Fetching** | Client-side fetching creates UI loading flickers and network waterfalls. | Query SQLite directly in async **React Server Components**. |
| **No Sequential Auto-Increment IDs in URLs** | Integer IDs (`/project/1`, `/project/2`) leak business metrics and allow scraping. | Use **UUIDv4** or **nanoids** for entity IDs. |
| **No Hardcoded Environment Variables** | Silent runtime failures when env vars are missing in production. | Validate all environment variables with **Zod (`env.mjs`)** at build time. |
