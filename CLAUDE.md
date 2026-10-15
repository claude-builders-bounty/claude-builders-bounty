# CLAUDE.md - Next.js 15 App Router + SQLite SaaS Blueprint

> Production-ready guidelines and architectural invariants for Claude Code pair programming on this repository.
> Follow every convention strictly. Zero unnecessary abstractions. Pragmatic, type-safe craftsmanship.

---

## 1. Stack & Pinned Versions

- **Framework**: Next.js 15 (React 19 RC / Stable, App Router exclusively).
- **Language**: TypeScript 5.5+ (`strict: true`, no implicit `any`, `skipLibCheck: true`).
- **Database Engine**: SQLite via `better-sqlite3` (embedded local dev) or `@libsql/client` (Turso edge replication).
- **Query Builder / ORM**: Drizzle ORM (type-safe SQL dialect, zero runtime query generation overhead).
- **Styling**: Tailwind CSS v3.4+ / v4 with `clsx` and `tailwind-merge` (`cn` helper).
- **Validation**: Zod v3 (mandatory for all Server Action inputs and route parameters).
- **Icons**: Lucide React.
- **Runtime**: Node.js 20+ or Bun 1.1+.

---

## 2. Dev Commands & Tooling

```bash
# Development
npm run dev              # Launch Next.js dev server with Turbopack (next dev --turbo)
npm run build            # Typecheck and build production bundle
npm run start            # Run production standalone build

# Database Operations (Drizzle + SQLite)
npm run db:generate      # Generate deterministic SQL migration scripts from schema
npm run db:migrate       # Apply pending SQL migrations to local SQLite (WAL mode)
npm run db:push          # Push schema changes directly (prototyping only)
npm run db:studio        # Open local Drizzle Studio GUI for inspection
npm run db:seed          # Seed deterministic development records

# Quality & Verification
npm run lint             # ESLint analysis with Next.js core web vitals rules
npm run typecheck        # tsc --noEmit
npm test                 # Run Vitest unit & integration test matrix
```

---

## 3. Directory & Folder Conventions

```
├── src/
│   ├── app/                    # Next.js App Router (pages, layouts, route handlers)
│   │   ├── (auth)/             # Route group: login, signup, reset password
│   │   ├── (dashboard)/        # Route group: authenticated SaaS tenant dashboard
│   │   │   ├── settings/
│   │   │   └── page.tsx
│   │   ├── api/                # External webhooks & third-party integrations only
│   │   ├── layout.tsx          # Root HTML layout with font and theme providers
│   │   ├── page.tsx            # Public marketing landing page
│   │   └── globals.css         # Tailwind directives and CSS variables
│   ├── components/             # Reusable UI primitives
│   │   ├── ui/                 # Headless / atomic buttons, inputs, modals
│   │   └── forms/              # Controlled form components
│   ├── db/                     # Database access layer
│   │   ├── schema/             # Drizzle table schemas (users.ts, orgs.ts, billing.ts)
│   │   ├── migrations/         # Immutable numbered SQL migration files
│   │   ├── client.ts           # Singleton SQLite connection instance with WAL mode
│   │   └── migrate.ts          # Migration executor script
│   ├── actions/                # Server Actions ('use server') partitioned by domain
│   │   ├── auth.ts
│   │   └── workspace.ts
│   └── lib/                    # Shared pure utilities
│       ├── validation/         # Zod schemas for forms and actions
│       ├── session.ts          # Auth session validation helpers
│       └── utils.ts            # Class merging (cn) and formatting
├── drizzle.config.ts           # Drizzle Kit configuration
└── CLAUDE.md                   # This instruction file
```

---

## 4. SQLite & Database Conventions

### Pragmas & Concurrency
Always enable **Write-Ahead Logging (WAL)** and foreign key constraints on connection initialization:
```typescript
// src/db/client.ts
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import * as schema from './schema';

const sqlite = new Database(process.env.DATABASE_URL || 'sqlite.db');
sqlite.pragma('journal_mode = WAL');
sqlite.pragma('foreign_keys = ON');
sqlite.pragma('busy_timeout = 5000');

export const db = drizzle(sqlite, { schema });
```

### Migration Rules
- **Never mutate applied migrations**: Migrations in `src/db/migrations/` are immutable once applied. Always generate a forward migration (`npm run db:generate`).
- **Strict Snake Case for SQL**: Tables and columns must be `snake_case` in SQLite (`created_at`, `org_id`). TypeScript models map via Drizzle.
- **Always Include Audit Timestamps**: Every table must have `created_at` (default `CURRENT_TIMESTAMP`) and `updated_at`.
- **Soft Deletes**: Use `deleted_at INTEGER` timestamp instead of raw `DELETE` for billing, org, and user tables.
- **Type Inference**: Never write manual interface duplicates. Always use `typeof table.$inferSelect` and `typeof table.$inferInsert`.

---

## 5. Next.js 15 App Router & Component Patterns

### Server vs. Client Boundary
- **Server Components by Default**: Every component in `src/app/` is a Server Component unless interactive browser state is required.
- **Push `'use client'` to the Leaves**: Never mark an entire page or layout with `'use client'`. Extract only the button, form, or dropdown that needs browser events into a separate leaf component.
- **Server Actions for Mutations**: All mutations use Server Actions located in `src/actions/`.
  - Always validate input with Zod inside the Server Action before executing database queries.
  - Return typed result objects `{ success: true, data } | { success: false, error: string }`.
  - Always call `revalidatePath()` or `revalidateTag()` after successful database writes.

```typescript
// src/actions/workspace.ts
'use server';

import { db } from '@/db/client';
import { workspaces } from '@/db/schema';
import { createWorkspaceSchema } from '@/lib/validation/workspace';
import { revalidatePath } from 'next/cache';

export async function createWorkspaceAction(rawInput: unknown) {
  const result = createWorkspaceSchema.safeParse(rawInput);
  if (!result.success) {
    return { success: false, error: result.error.flatten().fieldErrors };
  }

  try {
    const [created] = await db.insert(workspaces).values(result.data).returning();
    revalidatePath('/dashboard');
    return { success: true, data: created };
  } catch (err: any) {
    return { success: false, error: 'Failed to create workspace.' };
  }
}
```

---

## 6. What We DON'T Do (And Why)

| Anti-Pattern | Why We Avoid It | Preferred Alternative |
| :--- | :--- | :--- |
| **`useEffect` for data fetching** | Causes waterfall cascades, layout thrashing, and hydration mismatches. | Async Server Components with direct `await db.query...`. |
| **API Route Handlers for internal CRUD** | Adds redundant HTTP serialization overhead and cookie passing complexity. | Next.js Server Actions (`'use server'`). Route handlers are reserved for external webhooks (e.g. Stripe). |
| **Heavy ORMs (Prisma, TypeORM)** | Heavy runtime engine, massive bundle, complex binary engine dependencies in serverless/containers. | Drizzle ORM: Zero runtime footprint, plain SQL semantics, instant cold starts. |
| **Unindexed Foreign Keys** | SQLite does not auto-index foreign keys; causes full-table scans on `JOIN` queries. | Always declare an explicit index on foreign keys (`user_id`, `org_id`). |
| **In-Memory SQLite without persistence** | Data is erased when server restarts or recompiles. | Persistent file database (`sqlite.db` in WAL mode). |
| **Catch-All Error Silencing (`catch (e) {}`)** | Masks database constraints, deadlocks, and validation bugs during execution. | Log errors explicitly with context and return typed error feedback to the client. |
| **Raw Unparameterized SQL** | Introduces SQL injection vulnerabilities and breaks Drizzle type guarantees. | Use Drizzle query builder or tagged template literals `sql```. |

---

## 7. Context & Verification Checklist for Claude Code

When generating or editing code in this repository:
1. **Never write raw `any` types**: Infer from Drizzle schema `typeof table.$inferSelect` or Zod schemas.
2. **Always revalidate cache**: Call `revalidatePath()` or `revalidateTag()` after successful database mutations.
3. **Verify SQLite type alignment**: SQLite stores booleans as `INTEGER (0/1)` and timestamps as ISO strings or Unix milliseconds.
4. **Zero Clarifying Questions**: Follow the established directory layout and naming conventions directly without halting the user.
