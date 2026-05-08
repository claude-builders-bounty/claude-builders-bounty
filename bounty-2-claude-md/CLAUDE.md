# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> This file gives Claude Code full context for this project. Every rule exists because we learned the hard way.

---

## Stack & Versions

| Layer | Choice | Version | Why |
|-------|--------|---------|-----|
| Framework | Next.js (App Router) | 15.x | Server Components + streaming by default |
| Runtime | Node.js | 20 LTS | Required by Next.js 15 |
| Language | TypeScript | 5.x strict | No `any`, no excuses |
| Database | SQLite via better-sqlite3 | latest | Zero-config, file-based, fast enough for SaaS scale |
| ORM | Drizzle ORM | latest | Type-safe, SQL-like, no magic |
| Auth | NextAuth.js v5 | beta | App Router native, Edge-compatible |
| Styling | Tailwind CSS | 4.x | Utility-first, no CSS files |
| UI Components | shadcn/ui | latest | Copy-paste, not a dependency |
| Validation | Zod | 3.x | Infer types from schemas, single source of truth |
| Testing | Vitest + React Testing Library | latest | Vite-native, fast |
| Package manager | pnpm | 9.x | Strict hoisting, fast installs |

---

## Folder Structure

```
src/
├── app/                    # Next.js App Router — routes ONLY
│   ├── (auth)/             # Auth route group (no layout leakage)
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/        # Protected route group
│   │   ├── layout.tsx      # Dashboard shell (sidebar + header)
│   │   ├── page.tsx        # /dashboard
│   │   ├── settings/
│   │   └── billing/
│   ├── api/                # Route handlers (REST, not tRPC)
│   │   └── webhooks/
│   ├── layout.tsx          # Root layout — fonts, providers
│   ├── page.tsx            # Landing page
│   └── globals.css         # Tailwind directives ONLY
├── components/
│   ├── ui/                 # shadcn/ui primitives (Button, Dialog, etc.)
│   ├── forms/              # Form components tied to Zod schemas
│   └── shared/             # App-specific shared components
├── lib/
│   ├── db/                 # Database layer
│   │   ├── schema.ts       # Drizzle table definitions (SINGLE file)
│   │   ├── migrate.ts      # Migration runner script
│   │   ├── client.ts       # DB connection singleton
│   │   └── queries/        # Named query functions
│   │       ├── users.ts
│   │       └── subscriptions.ts
│   ├── auth.ts             # NextAuth config + helpers
│   ├── stripe.ts           # Stripe client + webhook handlers
│   └── validators.ts       # Zod schemas for API inputs
├── hooks/                  # Custom React hooks
├── types/                  # Shared TypeScript types (prefer Zod inference)
├── constants.ts            # Feature flags, plan limits, static data
└── middleware.ts           # NextAuth middleware (route protection)

drizzle/                    # Generated migration SQL files
public/                     # Static assets
```

### Why this structure?

- **Route groups** `(auth)` and `(dashboard)` prevent layout coupling — auth pages never load dashboard layout.
- **`lib/db/queries/`** keeps SQL out of route handlers. Every DB call goes through a named function.
- **Single `schema.ts`** — Drizzle works best with one schema file. Don't split by feature.
- **`components/ui/`** is reserved for shadcn. Never put app logic here.

---

## SQL / Migration Conventions

### Schema Rules

1. **One file**: All tables live in `src/lib/db/schema.ts`. Drizzle needs a single schema export for migrations.
2. **Naming**: `snake_case` for columns and tables. TypeScript maps to `camelCase` automatically via Drizzle's `casing: 'snake_case'` config.
3. **Every table gets**:
   - `id` — `text` primary key using `nanoid()` (not auto-increment, not UUID)
   - `created_at` — `integer` Unix timestamp, default `sql\`(unixepoch())\``
   - `updated_at` — `integer` Unix timestamp, updated via trigger or app code
4. **Foreign keys**: Always `text` referencing the parent `id`. Always `onDelete: 'cascade'` unless the child must survive.
5. **Booleans**: Store as `integer` (0/1). SQLite has no native boolean.
6. **JSON**: Store as `text`, parse in application code. Don't use SQLite's JSON functions in queries.

### Migration Rules

1. **Generate**: `pnpm drizzle-kit generate` — creates a new SQL file in `drizzle/`
2. **Never edit** generated migration files. If the migration is wrong, drop it and regenerate.
3. **Apply**: `pnpm drizzle-kit migrate` — runs pending migrations
4. **No down migrations**: We move forward. If you need to revert, write a new migration that undoes the change.
5. **Seed data** goes in `src/lib/db/seed.ts`, not in migrations.
6. **Migration naming**: Drizzle auto-generates names like `0003_add_stripe_customer_id.sql`. Don't rename them.

### Query Rules

1. **No raw SQL in route handlers.** Put every query in `src/lib/db/queries/`.
2. **Query functions are named by action**: `getUserById()`, `createSubscription()`, `updateUserPlan()`.
3. **Use Drizzle's query builder**, not raw `sql` tagged strings, unless performance demands it.
4. **Always select specific columns.** Never use `SELECT *` in production queries.

```typescript
// ✅ Good — named query, specific columns
export function getUserByEmail(email: string) {
  return db
    .select({ id: users.id, name: users.name, email: users.email })
    .from(users)
    .where(eq(users.email, email))
    .get();
}

// ❌ Bad — raw SQL in a route handler
export async function GET(req: Request) {
  const user = db.run('SELECT * FROM users WHERE email = ?', [email]);
}
```

---

## Component Patterns

### Server Components by Default

Every component is a Server Component unless it needs:
- `useState`, `useEffect`, or browser APIs → `"use client"`
- Event handlers (`onClick`, `onChange`) → `"use client"`
- Context consumers → `"use client"`

If you're not sure, start without `"use client"`. You'll know when you need it.

### File Naming

| Type | Convention | Example |
|------|-----------|---------|
| Pages | `page.tsx` | `app/(dashboard)/settings/page.tsx` |
| Layouts | `layout.tsx` | `app/(dashboard)/layout.tsx` |
| Loading states | `loading.tsx` | `app/(dashboard)/loading.tsx` |
| Error boundaries | `error.tsx` | `app/(dashboard)/error.tsx` |
| Server actions | `actions.ts` | `app/(dashboard)/settings/actions.ts` |
| Client components | `PascalCase.tsx` | `components/shared/UserAvatar.tsx` |
| Hooks | `camelCase.ts` | `hooks/useDebounce.ts` |
| Utilities | `camelCase.ts` | `lib/formatCurrency.ts` |

### Server Actions

- Place in `actions.ts` next to the page that uses them.
- Always validate input with Zod at the action boundary.
- Always revalidate the relevant cache after mutations.
- Return `{ success: true }` or `{ error: string }` — never throw.

```typescript
// app/(dashboard)/settings/actions.ts
'use server';

import { z } from 'zod';
import { revalidatePath } from 'next/cache';
import { updateUser } from '@/lib/db/queries/users';

const updateNameSchema = z.object({
  name: z.string().min(1).max(100),
});

export async function updateName(formData: FormData) {
  const parsed = updateNameSchema.safeParse({ name: formData.get('name') });
  if (!parsed.success) {
    return { error: 'Invalid name' };
  }
  await updateUser(parsed.data.name);
  revalidatePath('/settings');
  return { success: true };
}
```

### Data Fetching

- **Server Components**: Fetch directly with Drizzle queries. No `fetch()`, no API routes.
- **Client Components**: Use Server Actions or SWR for real-time data. No `fetch()` to your own API routes.
- **Never use `useEffect` for data fetching.** This is a Server Component architecture, not a SPA.

---

## Dev Commands

```bash
# Install
pnpm install

# Development
pnpm dev              # Start dev server (http://localhost:3000)

# Database
pnpm db:generate      # Generate migration from schema changes
pnpm db:migrate       # Apply pending migrations
pnpm db:studio        # Open Drizzle Studio (DB GUI)
pnpm db:seed          # Seed the database

# Build & Deploy
pnpm build            # Production build
pnpm start            # Start production server

# Linting & Formatting
pnpm lint             # ESLint
pnpm format           # Prettier (write)

# Testing
pnpm test             # Run all tests
pnpm test:watch       # Watch mode
pnpm test:coverage    # With coverage report
```

---

## Patterns to Follow

1. **Co-locate related code.** A feature's queries, actions, and components should be discoverable from its route folder.
2. **Validate at the boundary.** Zod schemas validate incoming data at API routes and Server Actions. Internal code trusts the types.
3. **Prefer composition over props drilling.** Use React context sparingly. Pass props explicitly up to 3 levels.
4. **Error handling**: Use `error.tsx` boundaries. Never catch and silently swallow errors.
5. **Loading states**: Always add `loading.tsx` for data-fetching pages. Use Next.js Suspense streaming.
6. **Environment variables**: Prefix with `NEXT_PUBLIC_` only if needed in the browser. Everything else stays server-only.
7. **Import aliases**: Use `@/` for `src/`. Never use relative paths that go up more than one level (`../../`).

---

## What We Don't Do (and Why)

| Don't | Why |
|-------|-----|
| Use Prisma | Drizzle generates better SQL, has no Rust engine to compile, and works natively with SQLite |
| Use `any` type | TypeScript strict mode exists for a reason. If the type is unknown, use `unknown` and narrow it |
| Store files in the database | SQLite is for structured data. Use S3/R2 for file storage |
| Use tRPC | REST route handlers are simpler, don't require a separate server, and are easier to debug |
| Use `getServerSideProps` or Pages Router | We're all-in on App Router. No legacy patterns |
| Write CSS files | Tailwind utilities only. Custom CSS goes in `globals.css` with `@apply` sparingly |
| Use Redux or Zustand | Server Components + Server Actions handle state. Local UI state uses `useState` |
| Auto-increment IDs | `nanoid()` is URL-safe, predictable length, and works offline |
| Store passwords | NextAuth handles credential hashing. Never touch `bcrypt` directly |
| Use SQLite in production at scale | SQLite handles ~100K reads/sec fine. For >1M users, migrate to Turso or PostgreSQL |
| Put business logic in components | Components render. Logic lives in `lib/` or Server Actions |
| Use `useEffect` for data fetching | This is a server-rendered app, not a SPA. Fetch in Server Components |
| Create API routes for internal data | Server Components and Actions access the DB directly. API routes are for webhooks and external integrations only |
| Split Drizzle schema into multiple files | Drizzle's migration generator works best with a single schema file. Keep it in one place |

---

## Database Schema Example

This is the typical starting schema for a SaaS project:

```typescript
// src/lib/db/schema.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';
import { sql } from 'drizzle-orm';

export const users = sqliteTable('users', {
  id: text('id').primaryKey(),
  email: text('email').notNull().unique(),
  name: text('name').notNull(),
  hashedPassword: text('hashed_password'),  // null for OAuth users
  plan: text('plan').notNull().default('free'),  // free | pro | enterprise
  stripeCustomerId: text('stripe_customer_id'),
  createdAt: integer('created_at').notNull().default(sql`(unixepoch())`),
  updatedAt: integer('updated_at').notNull().default(sql`(unixepoch())`),
});

export const sessions = sqliteTable('sessions', {
  id: text('id').primaryKey(),
  userId: text('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  token: text('token').notNull().unique(),
  expiresAt: integer('expires_at').notNull(),
  createdAt: integer('created_at').notNull().default(sql`(unixepoch())`),
});

export const subscriptions = sqliteTable('subscriptions', {
  id: text('id').primaryKey(),
  userId: text('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  stripeSubscriptionId: text('stripe_subscription_id').notNull().unique(),
  stripePriceId: text('stripe_price_id').notNull(),
  status: text('status').notNull(),  // active | past_due | canceled
  currentPeriodEnd: integer('current_period_end').notNull(),
  createdAt: integer('created_at').notNull().default(sql`(unixepoch())`),
  updatedAt: integer('updated_at').notNull().default(sql`(unixepoch())`),
});
```

---

## Quick Reference

- **New page**: Create folder in `app/(dashboard)/`, add `page.tsx`
- **New API route**: Create folder in `app/api/`, add `route.ts`
- **New DB table**: Add to `schema.ts`, run `pnpm db:generate && pnpm db:migrate`
- **New component**: `components/shared/ComponentName.tsx` (or `components/ui/` if it's a primitive)
- **New query**: Add to `lib/db/queries/` in the relevant domain file
- **Protect a route**: Add path to `middleware.ts` matcher

---

*This CLAUDE.md is designed to be pasted into a greenfield Next.js 15 + SQLite project. Claude Code will understand the project context without asking clarifying questions.*
