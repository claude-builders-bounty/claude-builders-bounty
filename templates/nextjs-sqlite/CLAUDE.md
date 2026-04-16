# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> **Stack**: Next.js 15 (App Router) · SQLite (better-sqlite3 / Turso) · TypeScript · TailwindCSS v4

---

## Project Overview

This is a **multi-tenant SaaS** application built for speed, simplicity, and operational sanity. Every decision below exists because we learned it the hard way.

**Non-negotiable principles:**
- SQLite is the database. No Postgres. No migrations at 2 AM.
- Server Components by default. Client components only when you need interactivity.
- One `app/` directory. No `pages/` router coexistence.
- Auth via server-side sessions or JWTs stored in httpOnly cookies. Never localStorage tokens.

## Stack & Versions

| Component | Version | Why |
|-----------|---------|-----|
| Next.js | 15.x | App Router only |
| React | 19.x | Server Actions for mutations |
| TypeScript | 5.x | Strict mode enabled |
| Database | better-sqlite3 OR Turso (libsql) | Single-file or edge-ready |
| ORM | Drizzle ORM | Type-safe, zero-abstraction SQL |
| Styling | TailwindCSS v4 | Utility-first, no CSS files |
| Auth | Lucia Auth or NextAuth v5 | Session-based |

## Folder Structure

```
src/
├── app/                    # Next.js App Router (ALL routes live here)
│   ├── (auth)/              # Route group: login, register, forgot-password
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/         # Route group: authenticated views
│   │   ├── layout.tsx       # Sidebar + nav wrapper
│   │   ├── page.tsx         # Dashboard home
│   │   ├── settings/
│   │   └── [organization]/
│   ├── api/                 # API routes (only when clients need direct access)
│   │   └── webhooks/
│   ├── layout.tsx           # Root layout (providers, fonts, toasts)
│   ├── globals.css          # Tailwind imports ONLY
│   └── not-found.tsx
├── components/              # Reusable UI components
│   ├── ui/                  # Dumb presentational atoms (Button, Input, Modal)
│   ├── features/            # Domain-specific molecules (InvoiceForm, TeamSelector)
│   └── layouts/             # Shell components (Sidebar, Topbar, PageHeader)
├── lib/                    # Application logic (NO React here)
│   ├── db.ts                # Database client singleton
│   ├── auth.ts              # Auth helper functions
│   ├── utils.ts             # Pure utility functions
│   ├── validations/         # Zod schemas
│   └── constants.ts         # App-wide constants
├── server/                  # Server-only utilities
│   ├── actions/             # Server Actions (mutations)
│   ├── queries/             # Data fetching functions (cached)
│   └── middleware.ts        # Auth checks, rate limits
├── drizzle/                 # Drizzle schema & migrations
│   ├── schema.ts            # ALL table definitions in ONE file
│   └── migrations/          # Auto-generated, NEVER hand-edit
└── config/                  # External service configs
    └── stripe.ts
```

**Rules:**
- **Never** import from `lib/` into `components/ui/` — UI is framework-agnostic.
- **Never** put business logic in `app/` page files — delegate to `server/actions/`.
- **Always** use `(route-group)` folders for shared layouts — no prop drilling layouts.

## Naming Conventions

| What | Convention | Example |
|------|-----------|---------|
| Files | kebab-case | `invoice-form.tsx` |
| Components | PascalCase | `<InvoiceForm />` |
| DB tables | snake_case | `subscription_plans` |
| Drizzle relations | camelCase | `subscriptionPlans` |
| Env vars | SCREAMING_SNAKE | `DATABASE_URL` |
| Server actions | camelCase verb + noun | `createOrganization` |
| Zod schemas | camelCase + Schema | `createOrgSchema` |
| API routes | kebab-case | `app/api/webhooks/stripe/route.ts` |

## Database Rules (SQLite)

### Schema (`drizzle/schema.ts`)
- **One file.** All tables defined here. No splitting across files — SQLite doesn't care and neither should you.
- **Always** use `$tableName()` function pattern for table references.
- **Always** define relations with `relations()` export.

### Migrations
```bash
npm run db:generate    # Generate migration from schema changes
npm run db:migrate     # Apply pending migrations
npm run db:studio      # Open Drizzle Studio (browser GUI)
```

**Rules:**
- **Never** edit generated migration files directly.
- **Never** use `DROP COLUMN` in production — add deprecation markers instead.
- **Always** add indexes on foreign keys and frequently queried columns.
- **Never** store JSON blobs in text columns — use proper tables with relations.
- **Always** include `created_at` and `updated_at` timestamps on every table.

### Query Patterns

```typescript
// GOOD: Server-side data fetch with cache
import { cache } from 'react'
export const getOrg = cache(async (orgId: string) =>
  db.query.organizations.findFirst({ where: eq(organizations.id, orgId) })
)

// BAD: Fetching inside a component - NO! Use server action/query instead

// GOOD: Mutation via Server Action
'use server'
export async function createOrg(name: string) {
  const validated = createOrgSchema.parse({ name })
  return db.insert(organizations).values(validated).returning()
}
```

### Connection Management
```typescript
// lib/db.ts - Singleton pattern (better-sqlite3)
import Database from 'better-sqlite3'
import { drizzle } from 'drizzle-orm/better-sqlite3'

const sqlite = new Database('data.db')
sqlite.pragma('journal_mode = WAL')        // Enable concurrent reads
sqlite.pragma('foreign_keys = ON')           // Enforce referential integrity
export const db = drizzle(sqlite)
```

For Turso/LibSQL:
```typescript
// lib/db.ts - Edge-compatible
import { createClient } from '@libsql/client'
import { drizzle } from 'drizzle-orm/libsql'

const turso = createClient({
  url: process.env.DATABASE_URL!,
  authToken: process.env.DATABASE_AUTH_TOKEN,
})
export const db = drizzle(turso)
```

### Migration Checklist

Before shipping a schema change:

1. Generate the migration from schema code, do not hand-write SQL first.
2. Check whether the change needs a data backfill or a default value.
3. Verify indexes exist for every new foreign key and every new unique lookup path.
4. Run the migration against a copy of production-like data if the table is already large.
5. Document any destructive follow-up steps as a separate deploy note instead of hiding them in the migration.

## Component Patterns

### Server Components (default)
```typescript
// Default: async server component
export default async function DashboardPage() {
  const user = await requireUser()
  const orgs = await getOrganizations(user.id)
  return <Dashboard orgs={orgs} />
}
```

### Client Components (only when needed)
```typescript
'use client'
// Only add this when you need: useState, useEffect, event handlers, browser APIs
// Keep them small. Extract logic to hooks if >50 lines.
export function SearchInput({ onSearch }: { onSearch: (q: string) => void }) {
  return (
    <input onChange={(e) => onSearch(e.target.value)}
      placeholder="Search..." className="w-full border rounded px-3 py-2"
    />
  )
}
```

### Forms (always use Server Actions + Zod)
```typescript
// server/actions/create-org.ts
'use server'
import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'
import { createOrgSchema } from '@/lib/validations/org'

export async function createOrganization(prev: FormData, form: FormData) {
  const validated = createOrgSchema.safeParse(Object.fromEntries(form))
  if (!validated.success) return { errors: validated.error.flatten().fieldErrors }
  await db.insert(organizations).values(validated.data).returning()
  revalidatePath('/dashboard')
  redirect('/dashboard')
}
```

## Commands

```
dev          Start dev server (port 3000)
build        Production build
start        Start production server
lint         ESLint + Prettier check
db:generate  Generate Drizzle migration
db:migrate   Run migrations
db:studio    Open Drizzle Studio browser GUI
type-check   TypeScript strict mode check
test         Vitest (unit + integration)
```

## Greenfield Smoke Test

If Claude Code follows this file correctly, it should be able to:

- add a new dashboard route under `src/app/(dashboard)/...`,
- create a Drizzle table plus migration without asking where schema files live,
- implement a server action form with Zod validation, and
- keep database, auth, and UI logic in the right layers.

## What We DON'T Do (and Why)

| Anti-pattern | Reason | Alternative |
|-------------|--------|-------------|
| useEffect for data fetching | Race conditions, waterfall requests, SSR breaks | Server Components / cache() from React |
| Prisma | Heavy, slow startup, poor SQLite support, hidden query overhead | Drizzle ORM (lightweight, type-safe, SQL-transparent) |
| localStorage for auth tokens | XSS vulnerable, no server access, SSR breaks | httpOnly cookies + server-side session validation |
| API routes for everything | Unnecessary serialization layer, no streaming benefits | Server Actions for mutations, Server Components for reads |
| CSS modules / styled-components / emotion | Bundle bloat, runtime cost, context switching | TailwindCSS utility classes only |
| Redux / Zustand for server state | Over-engineered, stale data headaches | React Server Components + cache() |
| Middleware auth on every route | Complexity explosion, hard to debug | Layout-level auth check in (dashboard)/layout.tsx |
| Environment variables in client code | Exposes secrets to browser bundle | Server-side only env vars, props for client needs |
| Hand-written SQL strings (raw) | Injection risk, no type safety | Drizzle query builder or sql template tag with param queries |
| any types anywhere | Defeats purpose of TypeScript | unknown -> narrow explicitly, or proper generic typing |

## Environment Variables

Required `.env.local`:
```
DATABASE_URL=file:./data.db                    # better-sqlite3 local
# DATABASE_URL=libsql://your-db.turso.io        # Turso remote
# DATABASE_AUTH_TOKEN=your-turso-token
SESSION_SECRET=<random-64-chars-here>
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

## Testing Strategy

- Unit tests: vitest for pure functions in lib/
- Integration tests: test against real SQLite in-memory DB
- E2E tests: Playwright for critical flows (login, checkout)
- Component tests: NOT a priority -- Server Components are tested via integration tests

## Performance Rules

- Always use revalidatePath / revalidateTag after mutations -- never router.refresh().
- Always stream slow pages with Suspense boundaries.
- Never fetch the same data twice in one request tree -- use cache() from React.
- Always generate static params for dynamic routes where possible (generateStaticParams).
- Never put heavy libraries (charting, rich text editors) in initial bundle -- dynamically import them.
