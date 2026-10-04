# CLAUDE.md - Next.js 15 + SQLite Production SaaS Blueprint

> This file provides authoritative context and engineering rules for Claude Code. Follow these conventions strictly. Do not deviate without explicit user instructions.

---

## 1. Stack & Versions

- **Framework**: Next.js 15.2+ (App Router only, React 19)
- **Language**: TypeScript 5.7+ (Strict mode, no `any`, `noImplicitAny: true`)
- **Database Engine**: SQLite via `better-sqlite3` (Local / VPS) or `@libsql/client` (Turso edge/cloud)
- **ORM / Query Builder**: Drizzle ORM (`drizzle-orm` + `drizzle-kit`)
- **Styling**: Tailwind CSS v4 (`@tailwindcss/postcss`) + `shadcn/ui` components
- **Validation**: Zod 3.24+ (Schema-first validation across server actions and APIs)
- **Authentication**: Auth.js / NextAuth v5 (Database session strategy with SQLite adapter)
- **Package Manager**: `pnpm` (Preferred) or `npm`

---

## 2. Folder Structure & Organization

```text
├── src/
│   ├── app/                          # Next.js App Router (Routes & Pages)
│   │   ├── (auth)/                   # Route group: login, signup, verify
│   │   ├── (dashboard)/              # Route group: protected app shell
│   │   │   ├── layout.tsx            # Authenticated sidebar & header
│   │   │   └── page.tsx              # Dashboard home
│   │   ├── api/                      # Webhooks & public REST endpoints only
│   │   │   └── webhooks/stripe/      # Stripe webhook handler
│   │   ├── globals.css               # Tailwind CSS root imports
│   │   └── layout.tsx                # Root HTML/Body & global providers
│   ├── actions/                      # Server Actions ("use server")
│   │   ├── auth.actions.ts           # Authentication mutations
│   │   ├── billing.actions.ts        # Stripe checkout & billing portal
│   │   └── teams.actions.ts          # Core domain mutations
│   ├── components/                   # Reusable UI Components
│   │   ├── ui/                       # Primitive design system (shadcn/ui)
│   │   └── forms/                    # Form components with React Hook Form
│   ├── db/                           # Database layer
│   │   ├── schema/                   # Drizzle schema definitions
│   │   │   ├── auth.ts               # Users, sessions, accounts
│   │   │   ├── subscriptions.ts      # Plans, customer IDs, status
│   │   │   └── index.ts              # Aggregated schema export
│   │   ├── migrations/               # Auto-generated SQL migration files
│   │   ├── client.ts                 # SQLite connection singleton & pragmas
│   │   └── migrate.ts                # Migration runner script
│   ├── lib/                          # Shared utilities
│   │   ├── auth.ts                   # Auth.js configuration & session helpers
│   │   ├── env.ts                    # T3-style Zod environment variable check
│   │   └── utils.ts                  # cn() class merger helper
│   └── types/                        # Global domain types & Drizzle inferred types
├── drizzle.config.ts                 # Drizzle Kit CLI configuration
├── next.config.ts                    # Next.js configuration
├── package.json                      # Dependency declarations
└── tsconfig.json                     # Strict TypeScript config
```

---

## 3. SQL & SQLite Conventions

### 3.1 Connection Pragmas (Mandatory for Performance & Concurrency)
SQLite must be initialized with production concurrency pragmas in `src/db/client.ts`:

```typescript
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import * as schema from './schema';

const sqlite = new Database(process.env.DATABASE_URL || 'sqlite.db');

// Rationale: WAL mode allows concurrent readers while a writer commits.
sqlite.pragma('journal_mode = WAL');
// Rationale: Prevents database locked errors under moderate server load.
sqlite.pragma('busy_timeout = 5000');
// Rationale: Enforces foreign key constraint integrity.
sqlite.pragma('foreign_keys = ON');
// Rationale: NORMAL synchronous is safe in WAL mode and drastically speeds up writes.
sqlite.pragma('synchronous = NORMAL');

export const db = drizzle(sqlite, { schema });
```

### 3.2 Schema & Column Conventions
- **Table Names**: Snake_case pluralized (`users`, `teams`, `subscription_tiers`).
- **IDs**: Prefix-based string IDs via nanoid or ulid (e.g. `usr_123`, `org_456`) or ULID. Do NOT expose auto-increment integer IDs to clients.
- **Timestamps**: Integer epoch milliseconds (`integer('created_at', { mode: 'timestamp_ms' })`) for portable time comparisons.
- **Indexes**: Explicitly index all foreign keys (`team_id`, `user_id`) and status columns used in WHERE filters.

### 3.3 Migrations
- Never manually edit raw database files.
- Always generate migrations via `npm run db:generate`.
- Apply migrations via `npm run db:migrate`.
- For rapid local prototyping: `npm run db:push`.

---

## 4. Component & Architecture Patterns

### 4.1 Server Components by Default
- All pages and layouts in `src/app/` are **React Server Components (RSC)**.
- Fetch data directly in Server Components using `await db.query...`.
- Never use client-side `useEffect` or React Query for initial page data loading.

### 4.2 Client Components Leaf-Only
- Mark files with `'use client'` only at the leaves of the render tree when user interaction (state, event listeners, hooks) is needed.
- Pass pre-fetched server data down via props.

### 4.3 Server Actions for All Data Mutations
- Place mutations in `src/actions/*.actions.ts`.
- Every action must start with `'use server'`.
- Validate all payloads with a Zod schema before database operations.
- Always authenticate user session inside the action.
- Return structured result objects `{ success: boolean, data?: T, error?: string }` instead of throwing raw exceptions.

Example Action Pattern:
```typescript
'use server';

import { z } from 'zod';
import { auth } from '@/lib/auth';
import { db } from '@/db/client';
import { teams } from '@/db/schema';
import { revalidatePath } from 'next/cache';

const CreateTeamSchema = z.object({
  name: z.string().min(2).max(50),
});

export async function createTeamAction(input: z.infer<typeof CreateTeamSchema>) {
  const session = await auth();
  if (!session?.user?.id) {
    return { success: false, error: 'Unauthorized' };
  }

  const parsed = CreateTeamSchema.safeParse(input);
  if (!parsed.success) {
    return { success: false, error: parsed.error.issues[0].message };
  }

  const newTeam = await db.insert(teams).values({
    id: `team_${crypto.randomUUID()}`,
    name: parsed.data.name,
    ownerId: session.user.id,
  }).returning();

  revalidatePath('/dashboard/teams');
  return { success: true, data: newTeam[0] };
}
```

---

## 5. Standard Dev Commands

```bash
# Development
npm run dev               # Start Next.js dev server on localhost:3000
npm run build             # Build optimized production bundle
npm run start             # Start production server
npm run lint              # ESLint & type check

# Database (Drizzle Kit)
npm run db:generate       # Generate SQL migration from schema diffs
npm run db:migrate        # Execute pending migrations against database
npm run db:push           # Push schema directly to SQLite (DEV ONLY)
npm run db:studio         # Launch visual Drizzle Studio GUI on localhost:4983

# Testing
npm run test              # Execute Vitest test suite
```

---

## 6. What We DON'T Do (and Why)

| Anti-Pattern | Why We Avoid It | What We Do Instead |
|---|---|---|
| **No `any` or loose types** | Defeats TypeScript compile safety; leads to runtime null errors. | Infer Drizzle types: `type User = typeof users.$inferSelect;`. |
| **No client-side SQL or API routes for simple CRUD** | Redundant latency, extra boilerplate, and CORS vulnerabilities. | Use Server Actions directly invoked from UI forms. |
| **No unindexed Foreign Keys in SQLite** | SQLite does not auto-index foreign keys; causes full-table scans on JOINs. | Add `.index()` on all foreign key definitions in Drizzle schema. |
| **No floating Promises** | Unhandled async errors drop silently in Node.js / Next.js. | Always `await` async calls or handle with `.catch()`. |
| **No storing dates as raw strings in SQLite** | Inconsistent date formatting breaks SQL range queries. | Use integer timestamps: `{ mode: 'timestamp_ms' }`. |
| **No dynamic routes without loading skeletons** | White screen flashes during streaming data fetch. | Include `loading.tsx` in route folders. |
| **No exposing DB file in public directory** | Security vulnerability: anyone could download the SQLite file. | Keep database at project root or dedicated `/data/` volume. |

---

