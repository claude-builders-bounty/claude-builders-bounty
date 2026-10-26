# CLAUDE.md — Next.js 15 App Router + SQLite (Turso / better-sqlite3) Architecture Guide

This document defines the strict engineering standards, architectural decisions, and operational guidelines for this SaaS project. Every change, contribution, and code generation MUST adhere to these rules without exception.

---

## 1. Stack & Versions

- **Framework:** Next.js 15.x (App Router, Server Actions, React 19 canary / GA)
- **Language:** TypeScript 5.x (`strict: true`, no implicit `any`)
- **Database Engine:** SQLite (Local development: `better-sqlite3`, Production Edge / Serverless: `@libsql/client` Turso)
- **ORM / Query Builder:** Drizzle ORM (`drizzle-orm` + `drizzle-kit`)
- **Authentication:** Auth.js v5 (NextAuth.js `@auth/core`) with database session adapter
- **Styling:** Tailwind CSS v4, Lucide React icons, shadcn/ui primitives (Radix UI)
- **Validation:** Zod 3.x for schema contracts, server action input validation, and environment parsing
- **Testing:** Vitest for unit/integration tests, Playwright for E2E user flows
- **Package Manager:** `pnpm` (Corepack enabled)

---

## 2. Folder Structure

```text
├── src/
│   ├── app/                               # Next.js 15 App Router
│   │   ├── (auth)/                        # Authentication routes group (login, register, verify)
│   │   ├── (dashboard)/                   # Protected tenant dashboard routes
│   │   │   ├── settings/
│   │   │   │   ├── page.tsx
│   │   │   │   └── loading.tsx
│   │   │   ├── layout.tsx                 # Dashboard sidebar and layout
│   │   │   └── page.tsx                   # Dashboard overview
│   │   ├── api/                           # Webhooks and external REST integrations only
│   │   │   └── webhooks/
│   │   │       └── stripe/route.ts
│   │   ├── error.tsx                      # Root client error boundary
│   │   ├── layout.tsx                     # Global root layout (fonts, providers)
│   │   ├── not-found.tsx                  # 404 handler
│   │   └── page.tsx                       # Public marketing landing page
│   ├── components/                        # Reusable component library
│   │   ├── ui/                            # Primitives (button, dialog, input, card)
│   │   ├── layout/                        # Navigation bar, sidebar, footer
│   │   └── domain/                        # Feature-specific components (e.g., billing-card.tsx)
│   ├── db/                                # SQLite & Drizzle ORM layer
│   │   ├── migrations/                    # Auto-generated SQL migrations
│   │   ├── schema/                        # Modular database schemas
│   │   │   ├── auth.ts                    # Users, accounts, sessions
│   │   │   ├── subscriptions.ts           # Billing, plans, organizations
│   │   │   └── index.ts                   # Unified schema barrel export
│   │   ├── client.ts                      # Singleton database connection (Turso / better-sqlite3)
│   │   └── seed.ts                        # Local test seed script
│   ├── lib/                               # Core business logic & server actions
│   │   ├── actions/                       # Next.js Server Actions ('use server')
│   │   │   ├── auth.ts
│   │   │   └── org.ts
│   │   ├── auth/                          # Auth config and server session helpers
│   │   ├── env.ts                         # Zod-validated environment variables
│   │   ├── utils.ts                       # Common utilities (cn, date formatters)
│   │   └── validations/                   # Zod schemas shared across client & server
│   └── types/                             # Global TypeScript definitions
├── drizzle.config.ts                      # Drizzle Kit migration configuration
├── next.config.ts                         # Next.js 15 config
├── tailwind.config.ts                     # Tailwind styling config
└── tsconfig.json                          # Strict TypeScript config
```

---

## 3. SQL & Migration Conventions (SQLite / Turso)

1. **Connection Singleton & Mode:**
   - Always connect using the client factory in `src/db/client.ts`.
   - SQLite connections MUST enforce:
     - `PRAGMA foreign_keys = ON;` (Guarantees referential integrity).
     - `PRAGMA journal_mode = WAL;` (Write-Ahead Logging for high concurrent read performance).
     - `PRAGMA busy_timeout = 5000;` (Prevents immediate `SQLITE_BUSY` lock crashes under concurrency).
2. **Migration Files:**
   - Never write manual unversioned SQL migrations in production.
   - Migrations are generated via `pnpm db:generate` into `src/db/migrations/XXXX_name.sql`.
   - Every table MUST have:
     - Primary key: `id text primary key` (using CUID2 or UUIDv7 for distributed sortable IDs).
     - Audit timestamps: `created_at integer not null default (unixepoch())`, `updated_at integer not null default (unixepoch())`.
     - Soft delete column where applicable: `deleted_at integer null`.
3. **Indexing Standards:**
   - Create explicit indexes on all Foreign Keys (`fk_user_id`, `fk_org_id`).
   - Create unique composite indexes on lookup fields: `create unique index idx_users_org_email on users(org_id, email);`.
   - SQLite handles `INTEGER PRIMARY KEY` as rowid aliases; avoid secondary indices on rowid.

---

## 4. Component & Server Action Patterns

1. **Server Components by Default:**
   - Every file in `src/app/**` is a React Server Component (RSC) unless explicitly prefixed with `'use client'`.
   - Perform direct database reads inside RSCs using Drizzle queries. No internal `fetch('/api/...')` waterfalls.
2. **Client Components:**
   - Mark with `'use client'` only when attaching DOM event listeners (`onClick`), using React state hooks (`useState`, `useReducer`), or browser APIs.
   - Keep client components at the leaves of the render tree; pass server data down as props or `children`.
3. **Server Actions for Mutations:**
   - Place all data writes in `src/lib/actions/*.ts` marked with `'use server'`.
   - Always validate inputs through Zod before database operations:
     ```typescript
     'use server';
     import { db } from '@/db/client';
     import { orgs } from '@/db/schema';
     import { createOrgSchema } from '@/lib/validations/org';
     import { auth } from '@/lib/auth';
     import { revalidatePath } from 'next/cache';

     export async function createOrganization(formData: FormData) {
       const session = await auth();
       if (!session?.user?.id) throw new Error('Unauthorized');

       const parsed = createOrgSchema.safeParse(Object.fromEntries(formData));
       if (!parsed.success) return { error: parsed.error.flatten().fieldErrors };

       await db.insert(orgs).values({
         id: crypto.randomUUID(),
         name: parsed.data.name,
         ownerId: session.user.id,
       });

       revalidatePath('/dashboard');
       return { success: true };
     }
     ```
4. **Streaming & Skeletons:**
   - Wrap slow asynchronous RSC queries with `<Suspense fallback={<SkeletonCard />}>`.
   - Use collocated `loading.tsx` for route-level streaming transitions.

---

## 5. What We Don't Do (And Why)

- ❌ **DO NOT use Prisma with serverless SQLite:**
  - *Why:* Prisma's query engine binary introduces cold-start latency and connection contention on serverless/edge environments (e.g., Cloudflare Workers, Vercel). We use Drizzle ORM for zero-overhead, type-safe SQL with native `@libsql/client`.
- ❌ **DO NOT fetch data on client-side (`useEffect` / SWR) for initial page renders:**
  - *Why:* Client-side initial fetching causes network waterfalls, layout shift (CLS), and SEO degradation. Read directly in Server Components and stream via Suspense.
- ❌ **DO NOT write unparameterized raw SQL (`db.run("SELECT * FROM users WHERE id = '" + id + "'")`):**
  - *Why:* Direct SQL injection risk. Always use Drizzle query builders or parameterized queries (`sql\`SELECT * FROM users WHERE id = ${id}\``).
- ❌ **DO NOT use Route Handlers (`/api/...`) for basic web app form submissions:**
  - *Why:* Next.js Server Actions provide seamless progressive enhancement, type safety, automatic CSRF protection, and collocated revalidation. Reserve Route Handlers strictly for incoming external webhooks (e.g., Stripe, Clerk).
- ❌ **DO NOT disable SQLite WAL mode or foreign key constraints:**
  - *Why:* In SQLite, omitting `PRAGMA foreign_keys = ON;` permits orphaned database rows and silent data corruption. Omitting WAL mode causes severe lock contention under concurrent writes.

---

## 6. Developer Commands

```bash
# Development
pnpm dev              # Starts Next.js 15 dev server with Turbo (http://localhost:3000)
pnpm build            # Compiles Next.js production bundle with typechecking
pnpm start            # Runs production standalone server
pnpm lint             # Runs ESLint with Next.js core web vitals rules
pnpm typecheck        # Runs tsc --noEmit to verify TypeScript contracts

# Database (SQLite & Drizzle)
pnpm db:generate      # Generates new SQL migration files from src/db/schema/*
pnpm db:migrate       # Applies pending SQLite migrations to local or Turso database
pnpm db:studio        # Launches Drizzle Studio GUI for visual database management
pnpm db:seed          # Populates local SQLite database with test tenants & seed data

# Testing
pnpm test             # Runs Vitest unit & integration test suite
pnpm test:e2e         # Runs Playwright end-to-end tests
```
