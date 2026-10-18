# CLAUDE.md — Next.js 15 + SQLite SaaS Stack Guide

> **Stack**: Next.js 15 (App Router, React 19) · TypeScript 5.6+ (Strict) · SQLite (better-sqlite3 / @libsql/client) · Drizzle ORM · Tailwind CSS · Zod

---

## 1. Development & Build Commands

```bash
# Development
npm run dev              # Turbopack dev server on http://localhost:3000
npm run build            # Production build with type & lint verification
npm run start            # Run production build

# Database & Migrations
npm run db:generate      # Generate Drizzle migration SQL files from schema
npm run db:migrate       # Apply pending migrations to local SQLite database
npm run db:studio        # Open Drizzle Studio UI on http://localhost:4983
npm run db:seed          # Seed development database with deterministic test data

# Quality & Verification
npm run typecheck        # tsc --noEmit (strict typecheck)
npm run lint             # ESLint verification
npm run test             # Vitest unit & integration tests
npm run test:watch       # Vitest interactive watcher
```

---

## 2. Project Architecture & Directory Layout

```
src/
├── app/                        # Next.js App Router routes & layouts
│   ├── (auth)/                 # Route group: login, register, reset-password
│   ├── (dashboard)/            # Route group: authenticated application core
│   │   ├── dashboard/page.tsx
│   │   └── settings/page.tsx
│   ├── api/                    # Route handlers (webhooks & public REST only)
│   ├── layout.tsx              # Root HTML & body shell, fonts, global providers
│   ├── page.tsx                # Public marketing landing page
│   └── globals.css             # Tailwind imports & CSS custom properties
├── actions/                    # Server Actions (colocated by business domain)
│   ├── auth.ts                 # Login, session termination, password flows
│   ├── billing.ts              # Subscription management, invoice retrieval
│   └── user.ts                 # Profile mutations & preferences
├── components/
│   ├── ui/                     # Primitives (buttons, inputs, dialogs, badges)
│   ├── layout/                 # Shell components (navbar, sidebar, mobile nav)
│   └── dashboard/              # Domain-specific composite widgets
├── db/
│   ├── schema/                 # Drizzle schema definitions by domain table
│   │   ├── users.ts            # Users, accounts, sessions
│   │   └── subscriptions.ts    # Plans, customer IDs, subscription status
│   ├── index.ts                # Database connection singleton & client export
│   └── migrations/             # Generated SQL migration history files
├── lib/
│   ├── auth/                   # Session verification & permission guards
│   ├── env.ts                  # Type-safe validated environment variables (Zod)
│   ├── errors.ts               # Structured domain error hierarchy & codes
│   └── utils.ts                # General pure helper functions (cn, formatters)
└── types/                      # Global ambient & shared domain types
```

---

## 3. Database Conventions (SQLite & Drizzle)

### Connection Singleton
- Use WAL (Write-Ahead Logging) mode on local SQLite instances:
  ```ts
  import Database from 'better-sqlite3';
  import { drizzle } from 'drizzle-orm/better-sqlite3';

  const sqlite = new Database(process.env.DATABASE_URL || 'sqlite.db');
  sqlite.pragma('journal_mode = WAL');
  sqlite.pragma('foreign_keys = ON');
  export const db = drizzle(sqlite);
  ```
- **Turso / libSQL**: When connecting over HTTP/WebSocket, use `@libsql/client` with the same Drizzle schema definitions.

### Schema & Modeling Rules
1. **Primary Keys**: Always use lowercase prefixed cuid2/nanoid strings (`usr_...`, `sub_...`, `org_...`) or autoincrement integer IDs. Never use raw random v4 UUIDs without index consideration.
2. **Timestamps**: Store all timestamps as integer unix epochs in seconds (`integer({ mode: 'timestamp' })` or milliseconds). Do not use varying string format dates in SQL columns.
3. **Foreign Keys**: Always specify `onDelete: 'cascade'` or `onDelete: 'restrict'` explicitly on relations. Never rely on SQLite default no-op.
4. **Boolean Flags**: Store as integer `0` / `1` with explicit default values (`integer({ mode: 'boolean' }).default(false).notNull()`).

---

## 4. Component & Server Action Patterns

### Server Components by Default
- Treat every component as a **React Server Component (RSC)** unless it requires interactive DOM state, browser event listeners (`onClick`, `onChange`), or browser APIs.
- Keep Client Components at the leaves of your component tree. Push `'use client'` down to the smallest interactive widget (e.g., `<FavoriteButton>`, not `<UserProfilePage>`).

### Server Actions Architecture
- Server Actions belong in `src/actions/` or alongside route domains.
- Every Server Action must validate inputs with a **Zod** schema.
- Return structured result objects `{ success: true, data }` or `{ success: false, error: string }`. Never let raw database errors bubble unhandled to clients.

```ts
'use server';

import { z } from 'zod';
import { db } from '@/db';
import { users } from '@/db/schema/users';
import { eq } from 'drizzle-orm';
import { revalidatePath } from 'next/cache';

const UpdateProfileSchema = z.object({
  name: z.string().min(2).max(50),
  bio: z.string().max(280).optional(),
});

export async function updateProfile(userId: string, input: z.infer<typeof UpdateProfileSchema>) {
  const parsed = UpdateProfileSchema.safeParse(input);
  if (!parsed.success) {
    return { success: false, error: parsed.error.flatten().fieldErrors };
  }

  try {
    await db.update(users).set(parsed.data).where(eq(users.id, userId));
    revalidatePath('/dashboard/settings');
    return { success: true };
  } catch (err) {
    return { success: false, error: 'Database update failed' };
  }
}
```

---

## 5. What We Don't Do (Anti-Patterns & Why)

1. **DON'T put `'use client'` at the top of page files**:
   - *Why*: Disables server-side streaming, inflates client JavaScript bundle size, and forces data fetching to waterfall through client-side requests.
2. **DON'T call external API route handlers from Server Components**:
   - *Why*: Calling `fetch('http://localhost:3000/api/...')` from a Server Component introduces unnecessary network loopback overhead and breaks cookie propagation. Call database functions or services directly.
3. **DON'T use `any` in TypeScript**:
   - *Why*: Breaks type inference across Drizzle query results and Server Action payloads. Use `InferSelectModel` and `InferInsertModel` from Drizzle schema.
4. **DON'T perform unindexed table scans on SQLite**:
   - *Why*: While SQLite is extremely fast in-memory and on SSDs, unindexed scans block the single-writer WAL pipeline under concurrent user sessions. Always index query predicates (`where`, `join`, `orderBy`).
5. **DON'T bypass input validation**:
   - *Why*: Client validation is cosmetic. Every Server Action and API Route Handler must validate incoming payloads through Zod schemas before touching the database.
