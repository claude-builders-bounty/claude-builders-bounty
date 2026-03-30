# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions

- **Runtime**: Node.js 20+ (App Router required)
- **Framework**: Next.js 15 (App Router, React 19)
- **Database**: SQLite via `better-sqlite3` (local dev) / [Turso](https://turso.tech) (production)
- **ORM**: [Drizzle ORM](https://orm.drizzle.team) — thin, type-safe, SQL-first
- **Auth**: NextAuth.js v5 with credentials + OAuth
- **Styling**: Tailwind CSS — utility-first, no CSS-in-JS
- **Deployment**: Vercel (frontend) + Turso (edge SQLite)

## Project Structure

```
/
├── app/                    # Next.js App Router — every subfolder = a route
│   ├── (auth)/            # Route group: auth pages (no layout shared with main)
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/       # Route group: authenticated pages
│   │   ├── layout.tsx    # Auth guard + sidebar layout
│   │   └── [org]/        # Multi-tenant: org-scoped routes
│   │       ├── settings/
│   │       └── page.tsx
│   ├── api/               # Route handlers only — no business logic here
│   │   └── auth/
│   ├── page.tsx           # Landing / marketing
│   └── layout.tsx         # Root layout: fonts, providers, metadata
├── components/            # React components
│   ├── ui/                # Primitive UI (Button, Input, Card — shadcn/ui)
│   ├── forms/             # Form components bound to schemas
│   └── features/          # Business-domain components (InvoiceTable, etc.)
├── db/                    # Database layer
│   ├── schema.ts          # Drizzle schema — single source of truth
│   ├── index.ts           # DB client singleton
│   └── migrations/        # Drizzle migration files (committed)
├── lib/                   # Pure utilities — no React, no DB
│   ├── utils.ts           # cn(), formatCurrency(), etc.
│   └── validators.ts      # Zod schemas for API inputs
├── scripts/               # One-off scripts (seed, migrate, sync)
└── drizzle/               # Drizzle config (drizzle.config.ts)
```

**Rules:**
- `app/` = routes + server components only
- `components/features/` = client components, co-located with domain
- Never put business logic in `app/api/` — delegate to `lib/` or `db/`
- Never import server-only code into client components

## Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Files | kebab-case | `user-settings.ts` |
| React components | PascalCase | `InvoiceTable.tsx` |
| Database tables | snake_case plural | `users`, `invoices` |
| Columns | snake_case | `created_at`, `user_id` |
| API routes | kebab-case | `app/api/billing-hooks/route.ts` |
| Variables | camelCase | `isLoading`, `userData` |
| Constants | SCREAMING_SNAKE | `MAX_FILE_SIZE` |
| CSS classes | Tailwind only | No `.module.css` |

## Database Conventions

### Schema (Drizzle)

```typescript
// db/schema.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core'

export const users = sqliteTable('users', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  email: text('email').notNull().unique(),
  name: text('name').notNull(),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull()
    .$defaultFn(() => new Date()),
  // Always use bigint('id') for foreign keys, integer for local PKs
})

// Multi-tenant: always include orgId
export const invoices = sqliteTable('invoices', {
  id: text('id').primaryKey(), // UUID, never auto-increment for business entities
  orgId: text('org_id').notNull(),
  amount: integer('amount').notNull(), // Always store money in cents (integer)
  currency: text('currency').notNull().default('USD'),
  status: text('status', { enum: ['draft','sent','paid'] }).notNull().default('draft'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull(),
})
```

### Migrations

```bash
# Generate migration from schema changes
npx drizzle-kit generate

# Apply migrations (run once on deploy, not on every request)
npx drizzle-kit migrate

# Push schema (dev only — prefer migrations in prod)
npx drizzle-kit push
```

**Rules:**
- Migrations are committed to git — never auto-migrate in production
- Money always stored as INTEGER cents — never floats
- Timestamps always as Unix ms integers — never ISO strings
- UUIDs for business entity IDs, auto-increment for lookup tables only
- Always include `createdAt` and `updatedAt` on tables
- Use `orgId` as first column after PK for multi-tenant tables

## Component Patterns

### Server Components (default)

```tsx
// app/(dashboard)/invoices/page.tsx — Server Component
import { db } from '@/db'
import { invoices } from '@/db/schema'
import { InvoiceTable } from '@/components/features/invoice-table'

export default async function InvoicesPage({ params }: { params: Promise<{ orgId: string }> }) {
  const { orgId } = await params
  const data = await db.select().from(invoices).where(eq(invoices.orgId, orgId))
  return <InvoiceTable invoices={data} />
}
```

### Client Components ('use client')

```tsx
// components/features/invoice-table.tsx — Client Component
'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { useInvoiceMutations } from '@/lib/hooks/use-invoice-mutations'

export function InvoiceTable({ invoices }: { invoices: Invoice[] }) {
  const [selected, setSelected] = useState<string[]>([])
  const { payInvoice, isPaying } = useInvoiceMutations()

  return (
    <div className="space-y-4">
      {invoices.map(invoice => (
        <InvoiceRow
          key={invoice.id}
          invoice={invoice}
          onSelect={setSelected}
        />
      ))}
    </div>
  )
}
```

**Rules:**
- Server Components by default; add `'use client'` only when needed
- No `useState`/`useEffect` in Server Components
- Pass data as props, not through context for async data
- Use TanStack Query (`@tanstack/react-query`) for client-side async state

## Anti-Patterns — What We Don't Do

### ❌ No direct DB writes in API routes

```tsx
// WRONG — business logic in route handler
export async function POST(req: Request) {
  const body = await req.json()
  db.insert(users).values(body) // buried here
}
```

```tsx
// RIGHT — thin API route, logic in service layer
export async function POST(req: Request) {
  const body = await req.json()
  const result = await userService.createUser(body)
  return Response.json(result)
}
```

### ❌ No inline SQL strings

```tsx
// WRONG
const users = await db.raw('SELECT * FROM users WHERE email = ?', [email])
```

```tsx
// RIGHT
const users = await db.select().from(users).where(eq(users.email, email))
```

### ❌ No floats for money

```tsx
// WRONG — floating point errors
const price = 19.99
```

```tsx
// RIGHT — integer cents
const priceCents = 1999
```

### ❌ No mixing auth strategies

Pick one: either all API routes use NextAuth session, or all use API keys. Never both in the same handler.

## Environment Variables

```
# Required
DATABASE_URL=file:./data/app.db          # SQLite path (local)
TURSO_DATABASE_URL=https://xxx.turso.io  # Turso (prod)
TURSO_AUTH_TOKEN=                         # Turso auth (prod)
NEXTAUTH_SECRET=                         # openssl rand -base64 32
NEXTAUTH_URL=http://localhost:3000       # No trailing slash

# Optional
ANALYTICS_ID=                            # Plausible / Posthog
```

## Dev Commands

```bash
npm run dev          # Start dev server (localhost:3000)
npm run build        # Production build
npm run db:studio    # Open Drizzle Studio (db browser)
npm run db:migrate   # Apply pending migrations
npm run db:seed      # Run seed script (only in dev)
npm run typecheck     # tsc --noEmit (run before PR)
npm run lint         # ESLint + Prettier
```

## Multi-Tenancy

Every database query MUST filter by `orgId`. Never rely on user ID alone.

```typescript
// WRONG — cross-tenant data leak
const data = await db.select().from(invoices).where(eq(invoices.userId, session.user.id))

// RIGHT — org-scoped
const data = await db.select().from(invoices).where(
  and(eq(invoices.orgId, orgId), eq(invoices.userId, session.user.id))
)
```

Row-Level Security (RLS) via Turso is the backup; app-level filtering is the primary defense.
