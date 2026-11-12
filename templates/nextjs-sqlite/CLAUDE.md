# CLAUDE.md — Next.js 15 + SQLite SaaS Architecture Guide

> **Project Archetype**: Production B2B/B2C SaaS Web Application  
> **Core Philosophy**: Zero client waterfalls, type-safe SQL, sub-millisecond local latency, and deterministic Server Actions. Every rule in this document exists for a concrete reliability, security, or performance reason.

---

## 1. Stack & Versions

| Layer | Pinned Technology | Version | Rationale |
| :--- | :--- | :--- | :--- |
| **Framework** | Next.js App Router | `15.x` (React 19) | Server Components by default; async request APIs (`await params`, `await searchParams`); streaming SSR. |
| **Language** | TypeScript (Strict) | `5.6+` | `strict: true`, `noUncheckedIndexedAccess: true`, `exactOptionalPropertyTypes: true`. No unchecked property access. |
| **Database** | SQLite (Embedded / Edge) | `better-sqlite3` (single node) / `@libsql/client` (Turso edge replicas) | Embedded file-based performance (<0.5ms reads); zero external connection pool bottlenecks; trivial backups. |
| **ORM / Query Builder** | Drizzle ORM | `0.35+` with `drizzle-kit` | SQL-like query mental model, zero runtime overhead, generate type-safe migrations with zero magic. |
| **Schema Validation** | Zod | `3.23+` | Strict boundary validation on all Server Action inputs, env vars, and route payloads. |
| **Styling** | Tailwind CSS v4 + shadcn/ui | Latest | Atomic utility classes, accessible Radix primitives, zero runtime CSS-in-JS bundle overhead. |
| **Testing** | Vitest + Playwright | `2.x` / `1.48+` | In-memory SQLite (`:memory:`) for instant isolated unit/integration tests; Playwright for critical auth & checkout E2E. |

---

## 2. Folder Structure

```text
├── drizzle/                     # Drizzle SQL migration files and metadata
│   ├── migrations/              # Generated SQL migrations (0000_..., 0001_...)
│   └── meta/                    # Drizzle migration journal
├── src/
│   ├── app/                     # Next.js 15 App Router pages and layouts
│   │   ├── (auth)/              # Route group: login, signup, verify-email
│   │   ├── (dashboard)/         # Route group: authenticated SaaS tenant dashboard
│   │   ├── (marketing)/         # Route group: public marketing, pricing, docs
│   │   ├── api/                 # Webhooks (Stripe, Resend) & public REST endpoints
│   │   ├── layout.tsx           # Global root layout (fonts, providers)
│   │   └── page.tsx             # Public landing page
│   ├── components/              # React components
│   │   ├── ui/                  # Primitives from shadcn/ui (button, dialog, input)
│   │   └── shared/              # Reusable app-specific components (navbar, sidebar)
│   ├── db/                      # Database configuration & schemas
│   │   ├── index.ts             # SQLite connection instance (WAL pragma, client export)
│   │   └── schema/              # Table definitions by domain
│   │       ├── users.ts         # User, session, and credential tables
│   │       ├── organizations.ts # Multitenancy & org memberships
│   │       └── subscriptions.ts # Billing tiers, customer IDs, usage metrics
│   ├── lib/                     # Utilities & shared helpers
│   │   ├── env.ts               # Validated environment variables (T3 Env / Zod)
│   │   ├── utils.ts             # Tailwind cn() helper and formatting
│   │   └── id.ts                # Prefixed NanoID / UUIDv7 generator (e.g., usr_123)
│   ├── server/                  # Server-only logic (never imported by client components)
│   │   ├── actions/             # Server Actions ('use server') for mutations
│   │   ├── queries/             # Data fetchers for React Server Components
│   │   └── auth/                # Session parsing, password hashing (scrypt/argon2id)
│   └── types/                   # Global TypeScript type declarations
├── tests/                       # Automated test suites
│   ├── unit/                    # Vitest unit tests (DB schemas, utilities)
│   └── e2e/                     # Playwright integration & browser tests
├── drizzle.config.ts            # Drizzle Kit CLI configuration
├── next.config.ts               # Next.js compiler & bundle configuration
└── package.json                 # Dependency manifests
```

---

## 3. SQL & Migration Conventions

### Mandatory SQLite PRAGMAs
Every database connection **must** configure these SQLite PRAGMAs on startup (in `src/db/index.ts`):
```typescript
db.run(sql`PRAGMA journal_mode = WAL;`);          // Write-Ahead Logging for concurrent reads
db.run(sql`PRAGMA foreign_keys = ON;`);          // Enforce relational foreign key constraints
db.run(sql`PRAGMA busy_timeout = 5000;`);        // 5s lock retry to prevent SQLITE_BUSY crashes
db.run(sql`PRAGMA synchronous = NORMAL;`);       // Safe durability with 3x higher write throughput
```

### Schema Rules
1. **Primary Keys**: Use string IDs with type prefixes (e.g. `usr_01H...`, `org_01H...`) using UUIDv7 or NanoID.  
   *Why*: Prevents enumeration attacks, simplifies multi-tenant partitioning, and keeps b-trees balanced by insertion timestamp.
2. **Timestamps**: Store all timestamps as integers (`timestamp_ms` or `mode: 'timestamp'` in Drizzle) in UTC.  
   *Why*: Avoids timezone drift, leap second parsing failures, and string format ambiguities.
3. **Foreign Keys**: Always specify `onDelete: 'cascade'` or `onDelete: 'restrict'` explicitly. Never rely on SQLite implicit cascade defaults.
4. **Indexes**: Place explicit indexes on all foreign keys (`organization_id`, `user_id`) and columns used in `WHERE`, `ORDER BY`, or `GROUP BY` queries.

---

## 4. Component & Server Action Patterns

### React Server Components (RSC) by Default
- All components in `src/app/` are React Server Components unless explicitly annotated with `'use client'`.
- Fetch data directly in RSC using server queries from `src/server/queries/*.ts`. Never use client-side `useEffect` or `fetch()` for initial page data.
- Push `'use client'` to the leaves of the tree (e.g., interactive dropdowns, submit buttons, modals).

### Server Actions for Mutations
All state modifications must use Server Actions (`'use server'`) located in `src/server/actions/`:
```typescript
'use server';

import { z } from 'zod';
import { revalidatePath } from 'next/cache';
import { requireAuth } from '@/server/auth';
import { db } from '@/db';
import { projects } from '@/db/schema';

const CreateProjectSchema = z.object({
  name: z.string().trim().min(2).max(64),
  description: z.string().trim().max(256).optional(),
});

export type ActionResponse<T> = 
  | { success: true; data: T }
  | { success: false; error: string; fieldErrors?: Record<string, string[]> };

export async function createProjectAction(input: unknown): Promise<ActionResponse<{ id: string }>> {
  const session = await requireAuth();
  
  const parsed = CreateProjectSchema.safeParse(input);
  if (!parsed.success) {
    return {
      success: false,
      error: 'Invalid input parameters.',
      fieldErrors: parsed.error.flatten().fieldErrors,
    };
  }

  try {
    const [created] = await db.insert(projects).values({
      name: parsed.data.name,
      description: parsed.data.description,
      organizationId: session.organizationId,
      createdBy: session.userId,
    }).returning({ id: projects.id });

    revalidatePath('/dashboard/projects');
    return { success: true, data: { id: created.id } };
  } catch (err) {
    console.error('Failed to create project:', err);
    return { success: false, error: 'Database operation failed. Please try again.' };
  }
}
```

---

## 5. What We DON'T Do (and Why)

1. **DON'T use `any` or `@ts-ignore`**:  
   *Why*: Untyped values bypass runtime boundaries and propagate `undefined` crashes into production. Use `unknown` and narrow with Zod or type guards.
2. **DON'T perform client-side data fetching for initial renders**:  
   *Why*: Causes layout shifts, flash of unstyled content (FOUC), multiple roundtrips, and exposes query internals to client bundles. Fetch in RSC directly.
3. **DON'T write raw SQL string concatenations**:  
   *Why*: Leaves the database wide open to SQL injection attacks. Always use Drizzle ORM query builders or `sql` tagged template literals.
4. **DON'T expose secret env vars with `NEXT_PUBLIC_`**:  
   *Why*: Any variable starting with `NEXT_PUBLIC_` is baked into client JavaScript bundles and readable by any browser. Only client-safe configs (e.g. app URL) may use this prefix.
5. **DON'T catch and swallow errors (`catch {}` without logging)**:  
   *Why*: Hides production outages and silent data corruption. Always log errors on the server with request context.
6. **DON'T mutate database state in `GET` route handlers or Server Components**:  
   *Why*: Next.js aggressively pre-renders and caches RSCs and GET requests. Writes must only occur in `POST`/`PUT`/`DELETE` Route Handlers or Server Actions.
7. **DON'T disable SQLite foreign key enforcement**:  
   *Why*: SQLite defaults to `foreign_keys = OFF` for backward compatibility. Leaving it off results in orphaned records and corrupt referential integrity.

---

## 6. Development & Migration Commands

```bash
# Development server (Turbopack)
npm run dev

# Typechecking & linting
npm run typecheck       # tsc --noEmit
npm run lint            # next lint

# Database operations (Drizzle Kit)
npm run db:generate     # drizzle-kit generate (creates SQL migration files)
npm run db:migrate      # tsx src/db/migrate.ts (applies migrations)
npm run db:studio       # drizzle-kit studio (visual database browser)

# Testing
npm run test            # vitest run (in-memory SQLite test suite)
npm run test:watch      # vitest watch
npm run test:e2e        # playwright test (end-to-end user flows)

# Production build & verification
npm run build           # next build
npm run start           # next start
```

---

## 7. Naming Conventions

- **Files & Directories**: `kebab-case` (e.g., `user-profile.tsx`, `auth-session.ts`).
- **React Components**: `PascalCase` (e.g., `ProjectCard`, `DashboardSidebar`).
- **Database Tables**: `snake_case` in plural form (e.g., `users`, `organization_memberships`, `audit_logs`).
- **Database Columns**: `snake_case` (e.g., `created_at`, `organization_id`, `stripe_customer_id`).
- **Server Actions**: `camelCase` ending in `Action` (e.g., `createProjectAction`, `deleteWorkspaceAction`).
- **TypeScript Types & Interfaces**: `PascalCase` (e.g., `SessionUser`, `ProjectWithMembers`).
