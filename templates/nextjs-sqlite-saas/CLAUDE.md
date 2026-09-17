# CLAUDE.md — Next.js 15 (App Router) + SQLite SaaS Stack

> **Architecture Intent**: Production-grade, low-latency, self-contained SaaS boilerplate using Next.js 15 (React 19), Server Actions, and SQLite (via `better-sqlite3` or Turso `@libsql/client`).
> Every guideline below is strictly reasoned: do not relax constraints without updating this document.

---

## 1. Core Philosophy & Architectural Constraints

1. **Server Components by Default**:
   - *Rule*: Every component in `app/` is a React Server Component (RSC) unless interactive browser state (`useState`, `useEffect`, event listeners) is strictly needed.
   - *Reason*: Eliminates clientside JS bundle bloat, ensures data fetching occurs co-located on the server, and prevents sensitive credentials from leaking to the browser.
2. **Server Actions for Mutations**:
   - *Rule*: Use Server Actions (`'use server'`) co-located in `actions/` or alongside route features for all `POST`/`PUT`/`DELETE` mutations. Reserve Route Handlers (`app/api/*/route.ts`) exclusively for external webhooks (Stripe, LemonSqueezy) and machine-to-machine APIs.
   - *Reason*: Next.js 15 Server Actions provide automatic CSRF protection, optimistic UI integration via `useActionState`, and seamless revalidation (`revalidatePath`).
3. **Strict Validation at the Boundary**:
   - *Rule*: Every Server Action and Route Handler MUST validate inputs using **Zod** before calling database queries. Never trust client payloads.
   - *Reason*: Prevents type-confusion attacks, malformed SQL inputs, and runtime null-pointer exceptions.
4. **SQLite Isolation & WAL Mode**:
   - *Rule*: SQLite MUST be initialized with `PRAGMA journal_mode = WAL;` and `PRAGMA foreign_keys = ON;`. Connections must use a singleton client instance.
   - *Reason*: WAL (Write-Ahead Logging) allows concurrent readers alongside a writer, preventing `SQLITE_BUSY` database lock errors under typical SaaS load.

---

## 2. Project Directory Structure

```text
├── actions/                  # Server Actions for mutations (Zod validated)
│   ├── auth.ts               # User session / signup / login actions
│   └── billing.ts            # Subscription & checkout actions
├── app/                      # Next.js 15 App Router
│   ├── (auth)/               # Unauthenticated route group (login, register)
│   ├── (dashboard)/          # Protected SaaS workspace route group
│   │   ├── layout.tsx        # Dashboard shell (Sidebar, UserNav)
│   │   ├── page.tsx          # Main metrics / overview
│   │   └── settings/         # Account & team settings
│   ├── api/                  # Machine / webhook endpoints ONLY
│   │   └── webhooks/stripe/  # Idempotent Stripe webhook handler
│   ├── globals.css           # Tailwind CSS v4 / tokens
│   ├── layout.tsx            # Root HTML layout & fonts
│   └── page.tsx              # Public landing page
├── components/               # Reusable React components
│   ├── ui/                   # Primitive dumb components (Button, Dialog, Input)
│   └── dashboard/            # Feature-specific dashboard components
├── db/                       # Database layer
│   ├── client.ts             # Singleton SQLite connection factory
│   ├── schema.ts             # Schema definition (Drizzle ORM / Kysely)
│   ├── migrations/           # Versioned SQL migrations (0001_init.sql)
│   └── seeds/                # Development dummy data seeders
├── lib/                      # Pure utilities, domain helpers, auth session
│   ├── auth.ts               # Iron-session / Lucia / Jose session verification
│   ├── env.ts                # Type-safe environment variable parsing (Zod)
│   └── utils.ts              # cn() class merge helper
└── types/                    # Shared TypeScript interfaces & DTOs
```

---

## 3. Naming Conventions

| Entity | Convention | Example | Reason |
| :--- | :--- | :--- | :--- |
| **Folders** | `kebab-case` | `user-settings/`, `billing/` | Cross-OS portability between Linux & macOS git checkouts |
| **Server Components** | `PascalCase` | `UserProfileCard.tsx` | Instant visual distinction from utility files |
| **Client Components** | `PascalCase` with `'use client'` | `ThemeToggle.tsx` | Explicit declaration at line 1 |
| **Server Actions** | `camelCase` (verb-first) | `updateUserProfile()`, `cancelSubscription()` | Represents an executable remote procedure |
| **DB Tables** | `snake_case` (plural) | `users`, `workspace_members`, `subscriptions` | Standard relational convention |
| **DB Columns** | `snake_case` | `created_at`, `stripe_customer_id` | Consistent with SQL dialects |
| **Zod Schemas** | `PascalCase` ending in `Schema` | `UpdateProfileSchema`, `LoginInputSchema` | Differentiates validation schema from TypeScript types |

---

## 4. Database & Migration Rules

1. **Migration Naming**:
   - Format: `YYYYMMDDHHMMSS_description.sql` (e.g. `20260101120000_create_users.sql`).
   - Every migration file MUST be immutable once committed to git.
2. **Foreign Key Integrity**:
   - Every foreign key reference MUST specify explicit `ON DELETE CASCADE` or `ON DELETE RESTRICT`. Never leave cascading behavior implicit.
3. **Timestamps & IDs**:
   - Use `TEXT` primary keys with `cuid2` or `uuidv7` (time-sortable, collisions impossible across distributed workers).
   - Use ISO 8601 UTC timestamps stored as `TEXT NOT NULL DEFAULT (datetime('now'))`.
4. **Zero-Downtime Safe DDL**:
   - To drop a column: first deploy code that stops referencing it, then remove in next migration.
   - Always add `NOT NULL` columns with an explicit `DEFAULT` value to existing tables.

---

## 5. Development & Operational Commands

```bash
# Development
pnpm dev              # Starts Next.js development server with Turbopack on http://localhost:3000
pnpm build            # Builds production bundle with typechecking
pnpm start            # Runs production standalone server
pnpm lint             # Runs ESLint with Next.js rules
pnpm typecheck        # Runs 'tsc --noEmit' to assert strict zero TypeScript errors

# Database (SQLite / Drizzle)
pnpm db:generate      # Generates migration SQL files from db/schema.ts
pnpm db:migrate       # Applies pending migrations to local SQLite db
pnpm db:seed          # Populates local db with test users and fixtures
pnpm db:studio        # Opens local visual SQLite browser GUI
```

---

## 6. Golden Patterns to Follow

### Pattern A: Validated Server Action with Standard Action Result
```typescript
// actions/profile.ts
'use server';

import { z } from 'zod';
import { db } from '@/db/client';
import { users } from '@/db/schema';
import { eq } from 'drizzle-orm';
import { revalidatePath } from 'next/cache';
import { getSession } from '@/lib/auth';

const UpdateNameSchema = z.object({
  name: z.string().trim().min(2, 'Name must be at least 2 characters').max(50),
});

export type ActionResult<T = unknown> = 
  | { success: true; data: T }
  | { success: false; error: string; fieldErrors?: Record<string, string[]> };

export async function updateUserName(formData: FormData): Promise<ActionResult> {
  const session = await getSession();
  if (!session?.userId) {
    return { success: false, error: 'Unauthorized. Please sign in.' };
  }

  const parsed = UpdateNameSchema.safeParse({
    name: formData.get('name'),
  });

  if (!parsed.success) {
    return {
      success: false,
      error: 'Invalid input data.',
      fieldErrors: parsed.error.flatten().fieldErrors,
    };
  }

  try {
    await db.update(users)
      .set({ name: parsed.data.name, updatedAt: new Date().toISOString() })
      .where(eq(users.id, session.userId));

    revalidatePath('/settings');
    return { success: true, data: { name: parsed.data.name } };
  } catch (err) {
    console.error('Failed to update user name:', err);
    return { success: false, error: 'Internal database error. Please retry.' };
  }
}
```

### Pattern B: Singleton SQLite Factory (Prevents Connection Exhaustion in Dev HMR)
```typescript
// db/client.ts
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import * as schema from './schema';
import path from 'node:path';

const DB_PATH = process.env.DATABASE_URL || path.resolve(process.cwd(), 'data/app.db');

declare global {
  var _sqliteDb: Database.Database | undefined;
}

const sqlite = global._sqliteDb || new Database(DB_PATH);

// Critical Performance & Reliability PRAGMAs
sqlite.pragma('journal_mode = WAL');
sqlite.pragma('foreign_keys = ON');
sqlite.pragma('synchronous = NORMAL');
sqlite.pragma('busy_timeout = 5000');

if (process.env.NODE_ENV !== 'production') {
  global._sqliteDb = sqlite;
}

export const db = drizzle(sqlite, { schema });
```

---

## 7. Anti-Patterns to Strictly Avoid

1. ❌ **No `useEffect` Data Fetching**: Never fetch dashboard data inside `useEffect` on the client. Fetch in a Server Component using direct DB queries and pass props or render directly.
2. ❌ **No Client-Side Secrets**: Never import `@/db/client` or server libraries inside files with `'use client'`. Next.js will throw an error, but guard against it proactively.
3. ❌ **No Unbounded SQL Queries**: Never write `SELECT * FROM activity_logs;` without `LIMIT` and `OFFSET` / keyset pagination. In SQLite, unbounded scans lock memory.
4. ❌ **No `any` in TypeScript**: Set `"strict": true` in `tsconfig.json`. All API and database inputs must map to verified Zod schemas.
5. ❌ **No In-Memory Route Handlers for Webhooks**: Webhooks (e.g. Stripe) must verify signature headers, write idempotency keys to SQLite in an immediate transaction, and return 200 within 2 seconds.
