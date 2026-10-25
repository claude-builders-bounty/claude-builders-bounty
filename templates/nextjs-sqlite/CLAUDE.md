# CLAUDE.md - Next.js 15 + SQLite SaaS Architecture Guide

> **Role & Mental Model:** You are a senior full-stack engineer building a production-grade, high-performance SaaS application. The architecture prioritizes zero-latency queries, strict type safety, predictable schema migrations, and zero-compromise security.

---

## 🛠️ Stack & Recommended Versions

| Layer | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Framework** | Next.js (App Router) | `^15.1.0` | React Server Components, Server Actions, Route Handlers |
| **Runtime / Library** | React | `^19.0.0` | Actions, `useActionState`, `useOptimistic`, Form status |
| **Language** | TypeScript | `^5.6.0` | Strict type checking (`strict: true`) |
| **Database** | SQLite (`better-sqlite3` / `@libsql/client`) | `latest` | Embedded zero-latency relational storage |
| **ORM & Migrations** | Drizzle ORM + Drizzle Kit | `^0.38.0` | Type-safe SQL builder & declarative migrations |
| **Validation** | Zod | `^3.24.0` | Input validation for Server Actions & API routes |
| **Styling** | Tailwind CSS | `^4.0.0` | Utility-first styling with design tokens |
| **Icons & UI** | Lucide React | `^0.460.0` | Accessible iconography |

---

## 📁 Opinionated Folder Structure

```text
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Authentication route group (unauthenticated layout)
│   │   ├── login/page.tsx
│   │   └── signup/page.tsx
│   ├── (dashboard)/              # Protected SaaS route group
│   │   ├── layout.tsx            # Authenticated session boundary & sidebar
│   │   ├── dashboard/page.tsx    # High-level metrics & overview
│   │   └── settings/page.tsx     # Account & billing settings
│   ├── api/                      # Webhooks & public REST endpoints only
│   │   └── webhooks/stripe/route.ts
│   ├── error.tsx                 # Global boundary for uncaught route errors
│   ├── layout.tsx                # Root HTML/Body layout with theme providers
│   └── page.tsx                  # Public landing / marketing page
├── components/
│   ├── ui/                       # Primitive design system elements (Button, Dialog, Input)
│   └── shared/                   # Domain composite components (UserNav, StatCard, EmptyState)
├── db/
│   ├── migrations/               # Auto-generated SQL migration files (drizzle-kit)
│   ├── schema.ts                 # Authoritative table definitions & relations
│   └── index.ts                  # Singleton database connection & pragmas
├── lib/
│   ├── actions/                  # Modular, Zod-validated Server Actions
│   │   ├── auth.ts
│   │   └── organization.ts
│   ├── auth/                     # Session validation & password hashing
│   └── utils.ts                  # Tailwind merger (`cn`) & common formatters
├── drizzle.config.ts             # Drizzle Kit migration configuration
├── next.config.ts                # Next.js configuration
├── package.json
├── tsconfig.json
└── CLAUDE.md                     # This architectural specification
```

---

## ⚡ SQLite Database & Migration Conventions

### 1. Mandatory Pragmas for Production Performance
Every SQLite connection **must** initialize the following pragmas in `db/index.ts`:

```typescript
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import * as schema from './schema';

const sqlite = new Database(process.env.DATABASE_URL || 'sqlite.db');

// Mandatory SQLite production settings:
sqlite.pragma('journal_mode = WAL');       // Write-Ahead Logging for high concurrency
sqlite.pragma('synchronous = NORMAL');     // Faster commits without data corruption in WAL mode
sqlite.pragma('foreign_keys = ON');        // Enforce referential integrity & cascading deletes
sqlite.pragma('busy_timeout = 5000');      // Prevent "database is locked" errors under load
sqlite.pragma('cache_size = -64000');      // 64MB memory cache for hot queries

export const db = drizzle(sqlite, { schema });
```

### 2. Schema Definition Standards (`db/schema.ts`)
- Use **UUIDv4** or **ULID/CUID2** for all primary keys to prevent enumeration attacks.
- Explicitly declare `createdAt` and `updatedAt` timestamps with integer unix seconds or text ISO strings.
- Always add `.index()` on foreign key columns.

```typescript
import { sqliteTable, text, integer, index } from 'drizzle-orm/sqlite-core';

export const users = sqliteTable('users', {
  id: text('id').primaryKey(),
  email: text('email').notNull().unique(),
  name: text('name'),
  role: text('role', { enum: ['user', 'admin'] }).default('user').notNull(),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
});

export const organizations = sqliteTable('organizations', {
  id: text('id').primaryKey(),
  name: text('name').notNull(),
  ownerId: text('owner_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
}, (table) => [
  index('org_owner_idx').on(table.ownerId),
]);
```

### 3. Database Lifecycle Commands
```bash
npm run db:generate   # Generate SQL migrations from schema diffs
npm run db:migrate    # Apply pending migrations to the SQLite instance
npm run db:studio     # Launch local Drizzle visual browser
```

---

## 🧩 Component & Data Mutation Patterns

### 1. Server Components as First-Class Default
- Fetch data directly in Server Components using `await db.query...`.
- Never fetch data inside `useEffect` on the client.

### 2. Standardized Server Action Flow
All state mutations must follow the triple-guard pattern:
1. Authenticate caller.
2. Validate inputs with Zod.
3. Wrap write operations in `db.transaction()` if multi-table.

```typescript
'use server';

import { z } from 'zod';
import { db } from '@/db';
import { organizations } from '@/db/schema';
import { revalidatePath } from 'next/cache';

const CreateOrgSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters').max(50),
});

export type ActionState = {
  success: boolean;
  data?: unknown;
  error?: string;
};

export async function createOrganization(prevState: ActionState, formData: FormData): Promise<ActionState> {
  const parsed = CreateOrgSchema.safeParse({
    name: formData.get('name'),
  });

  if (!parsed.success) {
    return { success: false, error: parsed.error.issues[0].message };
  }

  try {
    const orgId = crypto.randomUUID();
    await db.insert(organizations).values({
      id: orgId,
      name: parsed.data.name,
      ownerId: 'CURRENT_USER_ID', // Replace with validated session ID
    });

    revalidatePath('/dashboard');
    return { success: true, data: { id: orgId } };
  } catch (err) {
    return { success: false, error: 'Database write error occurred.' };
  }
}
```

---

## 🚫 What We DON'T Do (and Why)

| Anti-Pattern | Why We Avoid It | What We Do Instead |
| :--- | :--- | :--- |
| **Direct Client DB Access** | Exposes raw secrets and locks SQLite instances. | Use Server Actions (`'use server'`) exclusively for database interactions. |
| **`useEffect` Data Fetching** | Causes client-side waterfalls, layout shifts, and SEO loss. | Fetch asynchronously in React Server Components. |
| **Unindexed Foreign Keys** | Forces full table scans during joins and cascade deletions in SQLite. | Always add explicit `index()` decorators on all relational references. |
| **Ad-Hoc SQL String Concatenation** | Introduces SQL injection vectors and circumvents TypeScript type inference. | Use Drizzle ORM query builders or parameterized prepared statements. |
| **Global Client State for Server Data** | Redux/Zustand for server data leads to cache invalidation bugs. | Rely on Next.js `revalidatePath` / `revalidateTag` for server-truth synchronization. |
| **Multi-Statement Writes Without Transactions** | Interrupted operations leave orphaned records in SQLite. | Wrap related operations in `db.transaction(async (tx) => ...)`. |

---

## 🚀 Greenfield Project Checklist

1. Initialize Next.js: `npx create-next-app@latest my-saas --ts --tailwind --app --eslint`
2. Install SQLite & ORM: `npm i better-sqlite3 drizzle-orm zod lucide-react && npm i -D @types/better-sqlite3 drizzle-kit`
3. Copy this `CLAUDE.md` to project root.
4. Run `npm run db:generate && npm run db:migrate` to scaffold initial database schema.
