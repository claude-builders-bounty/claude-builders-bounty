# Next.js 15 + SQLite SaaS Engineering Standards (`CLAUDE.md`)

> **Role & Mission:** You are a senior full-stack engineer building a high-performance, edge-ready B2B SaaS application. You write type-safe, minimal, and secure code following these non-negotiable architectural standards.

---

## 1. Tech Stack & Version Constraints

- **Framework:** Next.js 15 (App Router only, React 19, TypeScript strict mode)
- **Database:** SQLite via LibSQL (`@libsql/client`) & Turso (local dev uses embedded file `local.db`, production connects to Turso replica)
- **ORM / Migrations:** Drizzle ORM (`drizzle-orm` + `drizzle-kit`)
- **Validation:** Zod v3
- **Styling & Components:** Tailwind CSS v4, shadcn/ui (Radix primitives), Lucide React
- **Auth:** Auth.js (NextAuth v5) or Clerk with session cookies
- **Testing:** Vitest for unit tests, Playwright for E2E

---

## 2. Directory & Architecture Structure

```text
├── app/
│   ├── (auth)/                  # Auth route group (login, register, forgot-password)
│   ├── (dashboard)/             # Authenticated SaaS dashboard shell
│   │   ├── layout.tsx           # Dashboard layout with sidebar navigation
│   │   ├── page.tsx             # Main metrics overview
│   │   └── settings/            # Organization & user profile settings
│   ├── api/                     # Minimal external webhooks (e.g. stripe, github)
│   ├── layout.tsx               # Root layout (fonts, providers, metadata)
│   └── globals.css              # Tailwind global variables & utility directives
├── components/
│   ├── ui/                      # Primitive atomic components (button, dialog, input)
│   └── dashboard/               # Domain-specific composite views
├── db/
│   ├── index.ts                 # Database client singleton export (`db`)
│   ├── schema/                  # Modular Drizzle schemas
│   │   ├── users.ts             # User & account definitions
│   │   ├── organizations.ts     # Multi-tenant workspace tables
│   │   └── index.ts             # Schema barrel export
│   └── migrations/              # Generated SQL migrations (committed to git)
├── server/
│   ├── actions/                 # Mutative Next.js Server Actions ('use server')
│   │   ├── auth.actions.ts
│   │   └── org.actions.ts
│   └── queries/                 # Read-only data loaders (called by Server Components)
│       └── org.queries.ts
├── lib/
│   ├── utils.ts                 # cn() class merge utility
│   ├── env.ts                   # Type-safe validated environment config (t3-env or zod)
│   └── errors.ts                # AppError domain classes
├── drizzle.config.ts            # Drizzle Kit configuration
└── tsconfig.json
```

---

## 3. SQLite & Database Conventions

### 3.1 Primary Keys & Types
- **IDs:** Use prefixed nanoid or ULID strings (`usr_01j7...`, `org_01j7...`) instead of auto-incrementing integers. This avoids enumeration attacks and simplifies distributed replication.
- **Timestamps:** Store timestamps as integer Unix epoch milliseconds (`integer({ mode: 'timestamp_ms' })`) to guarantee timezone-agnostic sorting.
- **Foreign Keys:** Always declare explicit `references(() => targetTable.id, { onDelete: 'cascade' })`.
- **Booleans:** SQLite represents booleans as `integer({ mode: 'boolean' })` (0 or 1).

### 3.2 Migrations Rule
- **Never modify existing migration files.**
- Always run `npm run db:generate` to generate a versioned timestamped migration.
- Review the generated SQL in `db/migrations/` before running `npm run db:migrate`.
- For greenfield local prototyping, `npm run db:push` is permitted, but production runs strict migrations.

### 3.3 Query Optimization
- Every `SELECT` query in SaaS dashboards must have an explicit `.limit()` or pagination cursor. Never execute unbounded `SELECT * FROM table`.
- Index every foreign key column (`organizationId`, `userId`) and frequently filtered status columns.

---

## 4. Component & Data Fetching Patterns

### 4.1 React Server Components (RSC) by Default
- All pages (`page.tsx`) and layouts (`layout.tsx`) are Server Components.
- Fetch data directly in Server Components using async queries from `server/queries/`.
- Do **not** wrap Server Components in `try/catch` for HTTP errors; rely on `error.tsx` boundaries.

### 4.2 Client Components at Leaf Nodes
- Add `'use client'` strictly to interactive leaf components (forms, modal dialog triggers, dropdown menus).
- Never fetch data via client-side `useEffect()` on mount. Pass data down as serializable props from RSC.

### 4.3 Server Actions for Mutations
- All state modifications (inserts, updates, deletes) live in `server/actions/*.actions.ts` marked with `'use server'`.
- Every action must validate input arguments with a Zod schema before accessing the database:
```typescript
'use server';
import { z } from 'zod';
import { db } from '@/db';
import { organizations } from '@/db/schema';
import { revalidatePath } from 'next/cache';

const CreateOrgSchema = z.object({
  name: z.string().min(2).max(50),
});

export async function createOrganizationAction(input: unknown) {
  const result = CreateOrgSchema.safeParse(input);
  if (!result.success) {
    return { success: false, errors: result.error.flatten().fieldErrors };
  }
  
  const [created] = await db.insert(organizations).values({
    name: result.data.name,
  }).returning();

  revalidatePath('/dashboard');
  return { success: true, data: created };
}
```

---

## 5. Development Workflow Commands

```bash
# Development server (Turbopack)
npm run dev

# Type check & Lint
npm run typecheck
npm run lint

# Database tooling
npm run db:generate    # Generate Drizzle migration from schema changes
npm run db:migrate     # Apply pending migrations to local SQLite
npm run db:studio      # Open Drizzle visual database browser GUI

# Testing
npm run test           # Run Vitest test suite
npm run test:e2e       # Run Playwright integration tests
```

---

## 6. What We DON'T Do (Anti-Patterns & Why)

1. **NO Route Handlers for internal CRUD (`app/api/*/route.ts`)**:
   - *Why:* Server Actions provide type-safety, automatic CSRF protection, and co-located cache revalidation without REST boilerplate. Use API routes only for external third-party webhooks (Stripe, GitHub).
2. **NO `any` or loose casting (`as unknown as T`)**:
   - *Why:* Strict TypeScript ensures SQLite types mirror database constraints and prevents runtime undefined errors.
3. **NO raw string concatenation in SQL queries**:
   - *Why:* Always use Drizzle's `sql` template tag or query builder to prevent SQL injection vulnerabilities.
4. **NO Secret leaks in client bundles**:
   - *Why:* Never prefix server credentials (`TURSO_AUTH_TOKEN`, `STRIPE_SECRET_KEY`) with `NEXT_PUBLIC_`. Use `lib/env.ts` with runtime validation.
5. **NO Unindexed Multi-tenant queries**:
   - *Why:* In SQLite, querying `WHERE organization_id = ?` without an index triggers full table scans that degrade performance as data grows.
