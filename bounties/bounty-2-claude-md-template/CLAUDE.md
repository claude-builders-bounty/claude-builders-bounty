# CLAUDE.md — Project Guide for Claude Code

## Project Overview

SaaS application built with Next.js 15 (App Router), SQLite via Turso + Drizzle ORM. Multi-tenant, subscription-gated platform with Stripe billing, Resend transactional emails, and NextAuth v5 authentication.

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | Next.js 15 (App Router), React 19, TypeScript 5 |
| Styling | Tailwind CSS v4, shadcn/ui (Radix primitives), class-variance-authority |
| Database | Turso (libSQL) + Drizzle ORM, drizzle-kit for migrations |
| Auth | NextAuth v5 (Auth.js) with credentials + OAuth providers |
| Payments | Stripe (webhooks, checkout), pricing table |
| Email | Resend (React Email templates) |
| Scheduling | Cron jobs via Vercel Cron or inngest |
| Forms | React Hook Form + Zod |
| Testing | Vitest + Testing Library (React Testing Library) |
| Linting | Biome (format + lint) or ESLint + Prettier |

## Build / Run / Test Commands

```bash
npm run dev          # Start dev server (localhost:3000)
npm run build        # Production build (runs type-check + lint)
npm run start        # Start production server
npm test             # Run Vitest (watch mode)
npm run test:run     # Run Vitest once (CI)
npm run lint         # Biome check (or ESLint)
npm run format       # Biome format (or Prettier)
npm run typecheck    # tsc --noEmit (if separate from build)
npm run db:push      # npx drizzle-kit push (apply schema to dev)
npm run db:migrate   # npx drizzle-kit migrate (generate + apply)
npm run db:seed      # Run seed script
npm run db:studio    # npx drizzle-kit studio (open DB browser)
```

## Code Style & Conventions

### General Rules

- **Server Components by default.** Only add `'use client'` when you need browser APIs, `useState`, `useEffect`, event handlers, or context.
- **Server Actions for mutations.** Use `"use server"` functions defined in `actions/` directories or inline in Server Components. Never call Server Actions from Client Components via fetch — import and call them directly.
- **Zod for validation.** Every form input, API route input, and server action parameter must be validated with a Zod schema. Coerce types at the boundary.
- **TypeScript strict mode.** `strict: true` in tsconfig. No `any` — use `unknown` and narrow.
- **Prefer `async/await` over `.then()`.** Always.
- **No barrel exports** (`index.ts` re-exports). They cause circular deps and tree-shaking issues.
- **File naming:** `kebab-case.ts` for utilities, `PascalCase.tsx` for components, `camelCase.ts` for hooks.
- **Imports order:** React → Next → third-party → internal (absolute `@/` alias).

### Component Conventions

```tsx
// app/(marketing)/pricing/page.tsx — Server Component (default)
import { db } from '@/db'
import { plans } from '@/db/schema'
import { PricingCard } from '@/components/pricing-card'

export default async function PricingPage() {
  const allPlans = await db.select().from(plans)
  return (
    <section>
      {allPlans.map(p => <PricingCard key={p.id} plan={p} />)}
    </section>
  )
}
```

```tsx
// components/pricing-card.tsx — Client Component (needs interactivity)
'use client'

import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'

interface Props {
  plan: { id: string; name: string; price: number }
}

export function PricingCard({ plan }: Props) {
  const router = useRouter()
  return <Button onClick={() => router.push(`/checkout?planId=${plan.id}`)}>{plan.name}</Button>
}
```

### Server Action Pattern

```tsx
// app/(dashboard)/settings/actions.ts
'use server'

import { revalidatePath } from 'next/cache'
import { auth } from '@/auth'
import { db } from '@/db'
import { users } from '@/db/schema'
import { eq } from 'drizzle-orm'
import { z } from 'zod'

const updateNameSchema = z.object({
  name: z.string().min(1).max(100),
})

export async function updateName(formData: FormData) {
  const session = await auth()
  if (!session?.user?.id) throw new Error('Unauthorized')

  const parsed = updateNameSchema.safeParse({
    name: formData.get('name'),
  })
  if (!parsed.success) return { error: parsed.error.flatten().fieldErrors }

  await db.update(users)
    .set({ name: parsed.data.name })
    .where(eq(users.id, session.user.id))

  revalidatePath('/settings')
  return { success: true }
}
```

### Data Fetching Pattern

```tsx
// Parallel data fetching in Server Components
export default async function DashboardPage() {
  const [projects, recentActivity, metrics] = await Promise.all([
    db.select().from(projects).where(eq(projects.teamId, session.user.teamId)),
    db.select().from(activity).orderBy(desc(activity.createdAt)).limit(10),
    getMetrics(session.user.teamId),
  ])

  return <DashboardClient projects={projects} activity={recentActivity} metrics={metrics} />
}
```

### Error Handling

```tsx
// app/error.tsx — Catch errors in the segment and its children
'use client'

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div>
      <h2>Something went wrong</h2>
      <p className="text-muted-foreground">{error.message}</p>
      <Button onClick={reset}>Try again</Button>
    </div>
  )
}
```

```tsx
// app/not-found.tsx
import Link from 'next/link'

export default function NotFound() {
  return (
    <div>
      <h2>Not Found</h2>
      <Link href="/">Return home</Link>
    </div>
  )
}
```

### Loading States

```tsx
// app/dashboard/loading.tsx — Shows immediately while the page loads
import { Skeleton } from '@/components/ui/skeleton'

export default function DashboardLoading() {
  return (
    <div className="space-y-4 p-8">
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-64 w-full" />
    </div>
  )
}
```

Use **Streaming** (React Suspense) for independent sections:

```tsx
import { Suspense } from 'react'
import { RecentActivity } from './recent-activity'
import { RecentActivityFallback } from './recent-activity-fallback'

export default function Page() {
  return (
    <div>
      <h1>Dashboard</h1>
      <Suspense fallback={<RecentActivityFallback />}>
        <RecentActivity />
      </Suspense>
    </div>
  )
}
```

## Directory Structure

```
src/
├── app/                          # Next.js App Router
│   ├── (marketing)/              # Route group — public pages
│   │   ├── page.tsx              #  Landing page
│   │   ├── pricing/page.tsx
│   │   └── layout.tsx            #  Public layout (no auth check)
│   ├── (dashboard)/              # Route group — authenticated
│   │   ├── dashboard/
│   │   │   ├── page.tsx
│   │   │   └── loading.tsx
│   │   ├── settings/
│   │   │   ├── page.tsx
│   │   │   └── actions.ts        # Server Actions for settings
│   │   └── layout.tsx            # Dashboard layout (auth guard)
│   ├── api/
│   │   ├── auth/[...nextauth]/route.ts
│   │   ├── webhooks/stripe/route.ts
│   │   └── trpc/[trpc]/route.ts  # If using tRPC
│   ├── (auth)/                   # Route group — auth pages
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   └── layout.tsx
│   ├── error.tsx
│   ├── not-found.tsx
│   ├── layout.tsx                # Root layout (providers, fonts)
│   └── globals.css               # Tailwind imports
├── components/
│   ├── ui/                       # shadcn/ui components (npx shadcn add)
│   ├── forms/                    # Form components
│   ├── layouts/                  # Dashboard sidebar, navbar, etc.
│   └── shared/                   # Shared business-logic components
├── db/
│   ├── index.ts                  # DB client (Turso / libSQL connection)
│   ├── schema/
│   │   ├── index.ts              # Re-exports all tables
│   │   ├── users.ts
│   │   ├── teams.ts
│   │   ├── subscriptions.ts
│   │   └── projects.ts
│   ├── migrations/               # drizzle-kit generates these
│   └── seed.ts                   # Seed data
├── actions/                      # Shared Server Actions
│   ├── auth.ts
│   └── billing.ts
├── lib/
│   ├── utils.ts                  # cn(), formatDate(), etc.
│   ├── constants.ts
│   ├── stripe.ts                 # Stripe client helper
│   ├── resend.ts                 # Resend client helper
│   └── email/                    # React Email templates
├── hooks/                        # Shared React hooks (use debounce, etc.)
├── providers/                    # React context providers (SessionProvider, etc.)
├── styles/                       # Additional styles if needed
├── types/                        # Shared TypeScript types
├── validations/                  # Shared Zod schemas
│   ├── auth.ts
│   ├── team.ts
│   └── project.ts
└── tests/
    ├── setup.ts                  # Vitest setup (clean DB, mocks)
    ├── helpers.ts                # Test utilities (createTestUser, etc.)
    ├── components/               # Component tests
    ├── actions/                  # Server Action tests
    └── db/                       # DB query tests
```

## Route Conventions

```
┌──────────────────────────┬──────────────────────────────────────────────┐
│ Pattern                  │ Use Case                                     │
├──────────────────────────┼──────────────────────────────────────────────┤
│ (marketing)              │ Route group — no layout inheritance          │
│ dashboard/@analytics     │ Parallel route — renders alongside dashboard │
│ settings/(...)details    │ Intercepting route — modal from link         │
│ [teamSlug]/settings      │ Dynamic segment — team scoping              │
│ [...rest]/page.tsx       │ Catch-all — custom 404s, catch-all routes   │
└──────────────────────────┴──────────────────────────────────────────────┘
```

### Auth Guard Pattern

```tsx
// middleware.ts
export { default } from 'next-auth/middleware'

export const config = {
  matcher: ['/dashboard/:path*', '/settings/:path*', '/api/protected/:path*'],
}
```

Or with a custom guard:

```tsx
// app/(dashboard)/layout.tsx
import { auth } from '@/auth'
import { redirect } from 'next/navigation'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await auth()
  if (!session) redirect('/login')
  if (!session.user.teamId) redirect('/onboarding')

  return (
    <div className="flex">
      <Sidebar team={session.user.team} />
      <main>{children}</main>
    </div>
  )
}
```

## Database Migration Workflow

```bash
# 1. Edit schema in src/db/schema/*.ts

# 2. Generate migration SQL
npx drizzle-kit generate

# 3. Review the generated SQL in src/db/migrations/

# 4. Apply to dev database
npx drizzle-kit migrate

# 5. Apply to production (via CI or manual)
#   For Turso: npx drizzle-kit migrate --config=drizzle.prod.config.ts
#   Never push directly to prod — always use migrations.
```

**Schema pattern:**

```ts
// src/db/schema/users.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core'
import { createId } from '@paralleldrive/cuid2'

export const users = sqliteTable('users', {
  id: text('id').primaryKey().$defaultFn(createId),
  email: text('email').notNull().unique(),
  name: text('name'),
  teamId: text('team_id').references(() => teams.id, { onDelete: 'set null' }),
  createdAt: integer('created_at', { mode: 'timestamp' })
    .notNull()
    .$defaultFn(() => new Date()),
  updatedAt: integer('updated_at', { mode: 'timestamp' })
    .notNull()
    .$onUpdateFn(() => new Date()),
})

export type User = typeof users.$inferSelect
export type NewUser = typeof users.$inferInsert
```

## Testing Preferences

```bash
npm test          # Interactive watch mode
npm run test:run  # CI mode (single run)
```

### Structure

```
src/tests/
├── setup.ts           # Global setup (vitest.config.ts references this)
│   ├── clears DB between runs (better-sqlite3 or Turso local replica)
│   └── mocks Stripe, Resend, NextAuth
├── helpers.ts         # createTestUser(), createTestTeam(), etc.
├── components/
│   └── pricing-card.test.tsx
├── actions/
│   └── update-name.test.ts
└── db/
    └── users.test.ts
```

### Key Testing Patterns

```ts
// src/tests/setup.ts
import { beforeAll, afterEach } from 'vitest'
import { db } from '@/db'
import { users, teams } from '@/db/schema'

afterEach(async () => {
  // Clean all tables in dependency order
  await db.delete(users)
  await db.delete(teams)
})

// Mock external services
vi.mock('@/lib/stripe', () => ({
  stripe: { checkout: { sessions: { create: vi.fn() } } },
}))
```

```ts
// src/tests/actions/update-name.test.ts
import { describe, it, expect } from 'vitest'
import { updateName } from '@/app/(dashboard)/settings/actions'

describe('updateName', () => {
  it('rejects empty name', async () => {
    const formData = new FormData()
    formData.set('name', '')
    const result = await updateName(formData)
    expect(result).toHaveProperty('error')
    // Vitest style: no assertions on DOM unless testing components
  })
})
```

```ts
// src/tests/components/pricing-card.test.tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { PricingCard } from '@/components/pricing-card'

describe('PricingCard', () => {
  it('renders plan name and price', () => {
    render(<PricingCard plan={{ id: '1', name: 'Pro', price: 2900 }} />)
    expect(screen.getByText('Pro')).toBeDefined()
  })
})
```

### Testing Rules

- **Vitest** over Jest. Always.
- **React Testing Library** over Enzyme.
- **Query by role/text**, never by test ID (unless unavoidable for dynamic content).
- **Integration tests** for Server Actions (they call the real DB in test — use a local SQLite replica, not Turso remote).
- **Component tests** for client-side interactivity. Server Components are tested via integration/e2e.
- **No snapshot tests** for UI components (too brittle). Use `toHaveTextContent`, `toBeInTheDocument`, etc.
- **No E2E tests** in this repo unless Playwright is explicitly added.

## Environment Variables

```env
# .env.example
DATABASE_URL=libsql://your-db.turso.io
DATABASE_AUTH_TOKEN=
AUTH_SECRET=
AUTH_GITHUB_ID=
AUTH_GITHUB_SECRET=
AUTH_GOOGLE_ID=
AUTH_GOOGLE_SECRET=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=
RESEND_API_KEY=
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

All environment variables are read at runtime (not build time) via `process.env` — unless they need to be public (`NEXT_PUBLIC_`).

## Key Libraries & Versions

```jsonc
// package.json (key dependencies)
{
  "next": "^15.1.0",
  "react": "^19.0.0",
  "@auth/core": "^0.37.0",
  "next-auth": "^5.0.0-beta.25",
  "drizzle-orm": "^0.36.0",
  "@libsql/client": "^0.14.0",
  "drizzle-kit": "^0.28.0",
  "zod": "^3.24.0",
  "react-hook-form": "^7.53.0",
  "@hookform/resolvers": "^3.9.0",
  "stripe": "^17.0.0",
  "resend": "^4.0.0",
  "tailwindcss": "^4.0.0",
  "class-variance-authority": "^0.7.1",
  "vitest": "^2.1.0",
  "@testing-library/react": "^16.1.0",
  "biome": "^1.9.0" // or eslint + prettier
}
```

## Git & PR Conventions

- Branch from `main` with `feat/`, `fix/`, `chore/` prefixes.
- PR title format: `type(scope): description` (e.g., `feat(billing): add annual plan discount`).
- Squash merge into `main`.
- Keep PRs under 400 lines when possible.

## Common Gotchas

1. **Drizzle + SQLite:** SQLite has no `enum` type — use `text()` with Zod runtime validation instead of DB-level enums.
2. **Turso + migrations:** Turso does not support foreign key enforcement in all plans. Use `PRAGMA foreign_keys = ON` and test locally with `better-sqlite3` or Turso local replicas.
3. **NextAuth v5:** Callbacks run on every request. Keep them lean — don't query the database inside `session()` callback if you can pass data via `jwt()`.
4. **Server Actions + revalidation:** Always `revalidatePath` or `revalidateTag` after mutations. Cache invalidation is manual.
5. **Parallel routes + modals:** Intercepting routes (`(..)`) only work with soft navigation (client-side `next/link`). Hard refreshes render the actual page.
