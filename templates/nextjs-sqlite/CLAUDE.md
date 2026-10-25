# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

This document establishes the architecture, conventions, and operational rules for this repository. Follow these standards strictly; do not ask clarifying questions when conventions specified here apply.

---

## 1. Stack & Versions

- **Framework**: Next.js 15.x (App Router, Turbopack enabled)
- **Language**: TypeScript 5.x (Strict mode enabled, `noImplicitAny: true`)
- **Runtime / DB**: SQLite 3 via `better-sqlite3` (WAL mode enabled) or `@libsql/client` (Turso compatible)
- **ORM**: Drizzle ORM (Zero-overhead, pure SQL dialect mapping, schema-first)
- **Styling**: Tailwind CSS v4 + `clsx` + `tailwind-merge`
- **UI Components**: Radix UI primitives + Lucide Icons
- **Auth**: Lucia Auth or NextAuth with Drizzle SQLite adapter
- **Validation**: Zod for server action and API request payload validation
- **Package Manager**: `pnpm` (required; lockfile `pnpm-lock.yaml`)

---

## 2. Essential Dev Commands

```bash
# Development
pnpm dev              # Start Turbopack dev server on http://localhost:3000
pnpm build            # Production typecheck & build
pnpm start            # Start production server
pnpm lint             # Run ESLint validation
pnpm typecheck        # tsc --noEmit

# Database & Migrations
pnpm db:generate      # Generate SQL migration files from src/db/schema.ts
pnpm db:migrate       # Apply pending migrations to local SQLite database
pnpm db:studio        # Open Drizzle Studio web GUI at http://local.drizzle.studio
pnpm db:seed          # Run database seeder (src/db/seed.ts)

# Testing
pnpm test             # Run Vitest test suite
pnpm test:e2e         # Run Playwright end-to-end tests
```

---

## 3. Folder & File Structure

```
.
├── src/
│   ├── app/                      # Next.js App Router pages and route handlers
│   │   ├── (auth)/               # Route group: login, signup, reset-password
│   │   ├── (dashboard)/          # Route group: authenticated SaaS dashboard
│   │   │   ├── layout.tsx        # Dashboard shell (sidebar, navigation, user menu)
│   │   │   └── page.tsx          # Dashboard home
│   │   ├── api/                  # API endpoints (webhooks, health checks only)
│   │   ├── layout.tsx            # Root layout (fonts, providers, metadata)
│   │   └── page.tsx              # Public landing page
│   ├── components/
│   │   ├── ui/                   # Reusable atomic UI (Button, Input, Modal, Card)
│   │   └── forms/                # Form components with Zod validation
│   ├── db/
│   │   ├── schema/               # Drizzle table schemas (auth.ts, users.ts, teams.ts)
│   │   ├── migrations/           # Generated SQL migrations (0000_init.sql, ...)
│   │   ├── index.ts              # SQLite singleton connection & Drizzle client
│   │   └── migrate.ts            # Migration runner script
│   ├── lib/
│   │   ├── auth.ts               # Session verification & authentication helpers
│   │   ├── utils.ts              # Shared utility functions (cn, formatters)
│   │   └── validations.ts        # Zod validation schemas
│   └── actions/                  # Next.js Server Actions (user, team, billing actions)
├── drizzle.config.ts             # Drizzle Kit configuration
├── next.config.ts                # Next.js configuration
├── package.json
├── tsconfig.json
└── CLAUDE.md
```

---

## 4. SQL & Migration Conventions

### 4.1. SQLite Connection Pragma Rules
SQLite requires explicit pragmas for concurrency, data integrity, and foreign keys. The connection factory in `src/db/index.ts` must always configure:

```typescript
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';

const sqlite = new Database(process.env.DATABASE_URL || 'sqlite.db');

// Mandatory SQLite performance and integrity pragmas:
sqlite.pragma('journal_mode = WAL');       // Write-Ahead Logging for high concurrency
sqlite.pragma('synchronous = NORMAL');     // Balanced durability and throughput
sqlite.pragma('foreign_keys = ON');         // Enforce foreign key constraints
sqlite.pragma('busy_timeout = 5000');      // Prevent SQLITE_BUSY under parallel writes

export const db = drizzle(sqlite);
```

### 4.2. Schema Design Rules
- Primary keys must be typed `text` using `cuid2` or `crypto.randomUUID()` to support distributed IDs and client-side optimistic UI.
- All timestamps must store integer epoch timestamps (`integer('created_at', { mode: 'timestamp' })`).
- Column names use `snake_case` in SQL and `camelCase` in TypeScript mappings.
- Always index columns used in `WHERE`, `JOIN`, and `ORDER BY` clauses.

### 4.3. Migration Workflow
1. Never edit existing applied migration files in `src/db/migrations/`.
2. Update schema definitions in `src/db/schema/`.
3. Run `pnpm db:generate` to generate a forward-only numbered migration.
4. Run `pnpm db:migrate` to execute.

---

## 5. Component & Data Fetching Patterns

### 5.1. Default to React Server Components (RSC)
- Fetch data directly inside `async` React Server Components using Drizzle queries.
- Do NOT use `useEffect` or client-side fetching libraries (React Query/SWR) for initial page loads.

### 5.2. Mutations via Server Actions
- All form mutations must use Server Actions placed in `src/actions/`.
- Validate all incoming payloads with Zod before running database mutations.
- Revalidate paths explicitly with `revalidatePath('/dashboard')` or `revalidateTag()`.

```typescript
'use server';

import { db } from '@/db';
import { projects } from '@/db/schema';
import { createProjectSchema } from '@/lib/validations';
import { revalidatePath } from 'next/cache';

export async function createProjectAction(rawInput: unknown) {
  const result = createProjectSchema.safeParse(rawInput);
  if (!result.success) {
    return { error: result.error.flatten().fieldErrors };
  }
  
  await db.insert(projects).values(result.data);
  revalidatePath('/dashboard/projects');
  return { success: true };
}
```

### 5.3. Client Components Boundary
- Add `'use client'` strictly at leaf nodes requiring DOM event listeners, React state (`useState`), or browser APIs.
- Keep Client Components lean; pass data down from Server Components as serializable props.

---

## 6. What We Don't Do (and Why)

| Anti-Pattern | Why We Avoid It | What We Do Instead |
|---|---|---|
| **No Prisma ORM** | Heavy query engine binary, cold start latency on serverless, poor WAL concurrency control in SQLite. | Use **Drizzle ORM** (zero-overhead, lightweight, native SQLite bindings). |
| **No Client `useEffect` Data Fetching** | Causes network waterfalls, layout shifts (CLS), and exposes API endpoints unnecessarily. | Fetch data directly in **React Server Components**. |
| **No Raw Unparameterized SQL** | Severe SQL injection vulnerability. | Use Drizzle query builder or parameterized queries (`db.run(sql`...`)`). |
| **No Plain Numeric Auto-Increment IDs** | Guessable URLs, enumeration attacks, difficult multi-tenant isolation. | Use **UUIDv4** or **CUID2** strings for primary keys. |
| **No Default Exports for Utilities/Components** | Degrades refactoring tooling and autocomplete precision. | Use **Named Exports** (`export function Button(...)`). |
| **No `any` Types** | Bypasses TypeScript safety guarantees. | Use strict types or `unknown` with runtime Zod parsing. |
