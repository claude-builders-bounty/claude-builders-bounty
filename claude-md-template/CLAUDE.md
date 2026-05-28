# CLAUDE.md — Next.js + SQLite SaaS

> Opinionated project context for Claude Code. Every rule exists for a reason.

## Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15 (App Router) | Server Components, streaming, layouts |
| Database | SQLite via better-sqlite3 | Zero-latency reads, single-file deploys |
| Auth | Better Auth | Type-safe, SQLite-native, session-based |
| Styling | Tailwind CSS 4 | Utility-first, zero runtime CSS |
| Validation | Zod | Runtime + static types from one schema |
| ORM | Drizzle ORM | SQL-first, SQLite-first, type-safe |
| Testing | Vitest | Fast, ESM-native, compatible with Vite |
| Package Manager | pnpm | Fast, disk-efficient, strict hoisting |

## Folder Structure

```
src/
  app/                    # Next.js App Router (routes only)
    (auth)/               # Auth group: login, register, forgot-password
    (dashboard)/          # Protected dashboard group
      layout.tsx          # Auth check, sidebar, nav
      page.tsx            # Dashboard home
    api/                  # Route handlers (thin — delegate to services)
      auth/[...all]/      # Better Auth catch-all
      webhooks/           # Stripe, etc.
  components/
    ui/                   # Generic UI primitives (Button, Input, Card)
    features/             # Feature-specific components (UserTable, BillingCard)
  lib/
    db/
      schema.ts           # Drizzle schema (all tables)
      migrate.ts          # Migration runner
      index.ts            # DB singleton export
    auth.ts               # Better Auth config
    stripe.ts             # Stripe client
    utils.ts              # Pure utility functions
  services/               # Business logic (called by route handlers + actions)
    user.ts
    billing.ts
  types/                  # Shared TypeScript types
public/
  fonts/                  # Self-hosted fonts only
```

## Database Rules

### Migrations

- **Never** edit generated migration files after they've been applied
- **Always** use `drizzle-kit generate` then `drizzle-kit migrate` — never raw SQL in production
- **One migration per feature branch** — squash before merge if needed
- Migration files live in `drizzle/migrations/`

### Schema Conventions

```typescript
// ✅ DO: Explicit, typed, with defaults
export const users = sqliteTable('users', {
  id: text('id').primaryKey().$defaultFn(() => createId()),
  email: text('email').notNull().unique(),
  name: text('name').notNull(),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
})

// ❌ DON'T: Use auto-increment IDs (bad for distributed systems)
// ❌ DON'T: Use REAL for money (use integer cents)
// ❌ DON'T: Nullable columns without a reason (prefer defaults)
```

### Query Patterns

```typescript
// ✅ DO: Use transactions for multi-step writes
db.transaction((tx) => {
  const user = tx.insert(users).values(data).returning().get()
  tx.insert(subscriptions).values({ userId: user.id, plan: 'free' }).run()
})

// ❌ DON'T: Chain multiple .get() calls outside a transaction
// ❌ DON'T: Use db.all() for single-row queries (use .get())
```

## Component Patterns

### Server Components (default)

```typescript
// ✅ DO: Fetch data directly in Server Components
export default async function UserList() {
  const users = await getUsers() // Direct DB call — no API needed
  return <UserTable users={users} />
}
```

### Client Components

```typescript
// ✅ DO: Mark explicitly, keep minimal
'use client'

import { useState } from 'react'

export function UserForm({ onSubmit }: { onSubmit: (data: FormData) => Promise<void> }) {
  // Form state, optimistic UI, interactions
}
```

### Rules

- **Default to Server Components** — only add `'use client'` for interactivity
- **Never** fetch data in Client Components via useEffect — use Server Components or React Query
- **Colocate** feature components with their route when possible
- **UI primitives** go in `components/ui/` — they accept props, never fetch data

## API Route Handlers

```typescript
// ✅ DO: Thin handlers that delegate to services
export async function POST(req: Request) {
  const body = await req.json()
  const data = createPaymentSchema.parse(body) // Zod validation
  const result = await createPayment(data)      // Service call
  return NextResponse.json(result)
}

// ❌ DON'T: Put business logic in route handlers
// ❌ DON'T: Skip validation — always Zod parse
```

## Auth Rules

- **Every dashboard route** is protected by the `(dashboard)` layout's auth check
- **API routes** that need auth use `getSession(req)` from `lib/auth.ts`
- **Never** trust client-side auth state for server decisions
- **Session cookies** are httpOnly, secure, sameSite=lax

## What We Don't Do (and Why)

| Anti-pattern | Why not |
|-------------|---------|
| Prisma | Overhead for SQLite; Drizzle is leaner and more SQL-native |
| ORMs with migrations that auto-apply | Dangerous in production; we generate + review + migrate |
| CSS-in-JS | Runtime cost; Tailwind is zero-runtime |
| React state for server data | Use Server Components; client state is for UI-only |
| `any` type | Eliminate with `unknown` + type guards |
| Barrel exports (index.ts re-exports) | Tree-shaking is imperfect; import directly |
| Monolithic components | Split into container (data) + presentational (UI) |
| Environment variables in client code | Only `NEXT_PUBLIC_*` prefixes; everything else is server-only |

## Dev Commands

```bash
pnpm dev              # Start dev server (localhost:3000)
pnpm build            # Production build
pnpm test             # Run tests (Vitest)
pnpm test:watch       # Tests in watch mode
pnpm lint             # ESLint + Prettier check
pnpm db:generate      # Generate Drizzle migration
pnpm db:migrate       # Apply migrations
pnpm db:studio        # Open Drizzle Studio (DB inspector)
```

## Testing Conventions

```typescript
// ✅ DO: Test behavior, not implementation
it('creates a user with a free subscription', async () => {
  const user = await createUser({ email: 'test@example.com', name: 'Test' })
  const sub = await getSubscription(user.id)
  expect(sub.plan).toBe('free')
})

// ❌ DON'T: Test internal state or mock everything
// ❌ DON'T: Use snapshot tests for UI (fragile)
```

- **Unit tests** for services and utilities
- **Integration tests** for API routes (test the full request cycle)
- **No E2E tests** unless specifically needed (Playwright only if so)
- Test files: `*.test.ts` colocated with the source file

## Git Conventions

- **Conventional commits**: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`
- **One feature per branch** — squash on merge
- **PR descriptions** must include: what changed, why, how to test
- **No force pushes** on main

## Deployment

- **Target**: Vercel (or any edge-compatible host)
- **SQLite file**: Persisted via volume mount or Turso (remote SQLite)
- **Migrations**: Run as part of build step (`pnpm db:migrate`)
- **Environment**: All secrets via `.env.local` (never committed)

## Performance Rules

- **Server Components** for data fetching (no client waterfalls)
- **Suspense boundaries** for streaming slow queries
- **Image optimization**: Always use `next/image` with explicit width/height
- **Font loading**: Self-hosted fonts in `public/fonts/`, loaded via `next/font`
- **Bundle analysis**: Run `pnpm build && pnpm analyze` before merging large changes
