# CLAUDE.md — Next.js 15 + SQLite SaaS

This file tells Claude Code exactly how this project is built and what conventions to follow.
Every rule here has a reason. Follow them precisely — don't ask for clarification on covered topics.

---

## Stack & Versions

| Layer | Technology | Version |
|---|---|---|
| Framework | Next.js App Router | 15.x |
| Runtime | Node.js | 22 LTS |
| Database | SQLite via better-sqlite3 | 9.x |
| ORM / Query | Raw SQL (no ORM) | — |
| Auth | better-auth | 1.x |
| Styling | Tailwind CSS | 4.x |
| Components | shadcn/ui | latest |
| Payments | Stripe | 17.x |
| Email | Resend | 4.x |
| Validation | Zod | 3.x |
| Package manager | pnpm | 9.x |
| TypeScript | strict mode | 5.x |

**Why no ORM?** SQLite with better-sqlite3 is synchronous and fast. Raw SQL is explicit, debuggable, and forces intentional schema design. ORMs add abstraction that fights SQLite's simplicity.

---

## Folder Structure

```
.
├── app/                        # Next.js App Router pages and layouts
│   ├── (auth)/                 # Auth routes — login, register, reset-password
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/            # Protected routes — authenticated users only
│   │   ├── layout.tsx          # Checks session, redirects if unauthenticated
│   │   └── settings/page.tsx
│   ├── api/                    # Route handlers
│   │   ├── auth/[...all]/route.ts   # better-auth catch-all handler
│   │   ├── stripe/webhook/route.ts
│   │   └── ...
│   ├── layout.tsx              # Root layout — fonts, providers
│   └── page.tsx                # Marketing home page (public)
│
├── components/
│   ├── ui/                     # shadcn/ui primitives (auto-generated, never edited manually)
│   └── app/                    # Application-specific components
│       ├── auth/               # AuthForm, LoginButton, etc.
│       ├── billing/            # PricingCard, SubscriptionBanner, etc.
│       └── shared/             # Navbar, Footer, Sidebar
│
├── db/
│   ├── index.ts                # Singleton Database instance (better-sqlite3)
│   ├── schema.sql              # Source-of-truth schema (all CREATE TABLE statements)
│   └── migrations/
│       ├── 001_initial.sql
│       ├── 002_add_subscriptions.sql
│       └── runner.ts           # Migration runner — runs on app start
│
├── lib/
│   ├── auth.ts                 # better-auth server instance and config
│   ├── auth-client.ts          # better-auth browser client
│   ├── stripe.ts               # Stripe singleton
│   ├── email.ts                # Resend wrapper
│   └── utils.ts                # cn() and other pure utilities
│
├── queries/                    # All SQL queries, organized by domain
│   ├── users.ts                # getUserById(), updateUserPlan(), etc.
│   ├── subscriptions.ts
│   └── ...
│
├── actions/                    # Next.js Server Actions (mutations only)
│   ├── auth.ts
│   ├── billing.ts
│   └── ...
│
├── types/
│   └── index.ts                # Shared TypeScript types (not Zod schemas)
│
├── middleware.ts               # Session check — protects (dashboard) routes
├── next.config.ts
├── tailwind.config.ts
└── .env.local                  # Never committed — see .env.example
```

**Why this structure?**
- Route groups `(auth)` and `(dashboard)` keep layouts clean without affecting URL paths.
- `queries/` keeps all SQL out of components and actions — testable and reusable.
- `components/ui/` is hands-off (shadcn generates it); `components/app/` is ours.

---

## Dev Commands

```bash
pnpm dev              # Start dev server (localhost:3000)
pnpm build            # Production build
pnpm start            # Start production server
pnpm lint             # ESLint check
pnpm typecheck        # tsc --noEmit (run before every PR)
pnpm db:migrate       # Run pending migrations
pnpm db:studio        # Open Drizzle Studio (read-only inspection, no schema edits)
pnpm db:reset         # Drop and recreate DB from schema.sql (dev only)
```

**Always run `pnpm typecheck` before declaring a feature done.** TypeScript errors in CI are blocking.

---

## Database: SQLite Conventions

### Connection Singleton

```typescript
// db/index.ts
import Database from 'better-sqlite3';
import path from 'path';

const DB_PATH = process.env.DB_PATH ?? path.join(process.cwd(), 'data', 'app.db');

export const db = new Database(DB_PATH, {
  // Enable WAL mode for concurrent reads alongside writes
  // Never disable this — it prevents read/write contention in Next.js
});

db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');  // Always enforce FK constraints
db.pragma('busy_timeout = 5000'); // 5s timeout instead of immediate SQLITE_BUSY
```

**Why WAL?** Next.js concurrent requests hit SQLite simultaneously. WAL allows one writer and multiple concurrent readers without blocking.

### Schema Conventions

```sql
-- db/schema.sql

CREATE TABLE IF NOT EXISTS users (
  id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  email       TEXT NOT NULL UNIQUE,
  name        TEXT,
  plan        TEXT NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'pro', 'enterprise')),
  created_at  INTEGER NOT NULL DEFAULT (unixepoch()),
  updated_at  INTEGER NOT NULL DEFAULT (unixepoch())
);

-- Always use INTEGER for timestamps (Unix epoch seconds, not milliseconds)
-- Always use TEXT for IDs (UUIDs are TEXT in SQLite)
-- Always use CHECK constraints for enums — never rely on app-layer validation alone
-- Always add created_at / updated_at to every table
```

Rules:
- IDs: `TEXT`, generated with `lower(hex(randomblob(16)))` — produces a 32-char hex UUID.
- Timestamps: `INTEGER` (Unix epoch seconds). Use `unixepoch()` as default. In TypeScript, multiply by 1000 for `Date` objects.
- Booleans: `INTEGER` (0 or 1). SQLite has no boolean type.
- Enums: `TEXT` with `CHECK` constraint. Document the allowed values.
- Foreign keys: Always declare them. `PRAGMA foreign_keys = ON` must be set at connection time.

### Migrations

**Never edit existing migration files.** Migrations are append-only history.

```sql
-- db/migrations/001_initial.sql
-- Filename format: NNN_description.sql
-- NNN is zero-padded to 3 digits

CREATE TABLE IF NOT EXISTS users ( ... );
CREATE TABLE IF NOT EXISTS sessions ( ... );
```

```typescript
// db/migrations/runner.ts
// The runner reads all .sql files in order and applies ones not yet in
// the `migrations` tracking table. Runs synchronously on app startup.
// Never skip this — schema drift kills prod.
```

**Migration rules:**
1. One concern per migration file. Don't mix unrelated changes.
2. To rename a column: add new column → backfill → drop old column (3 separate migrations).
3. To drop a table: deprecate (stop writing) → verify no reads → drop (2 deploys minimum).
4. Always wrap destructive migrations in a transaction.

### Query Layer

All SQL lives in `queries/`. Never write SQL inside Server Actions, route handlers, or components.

```typescript
// queries/users.ts
import { db } from '@/db';

export interface User {
  id: string;
  email: string;
  name: string | null;
  plan: 'free' | 'pro' | 'enterprise';
  created_at: number;
  updated_at: number;
}

export function getUserById(id: string): User | undefined {
  return db.prepare<[string], User>(
    'SELECT * FROM users WHERE id = ?'
  ).get(id);
}

export function updateUserPlan(id: string, plan: User['plan']): void {
  db.prepare(
    'UPDATE users SET plan = ?, updated_at = unixepoch() WHERE id = ?'
  ).run(plan, id);
}
```

Rules:
- Always type the query parameters and row type explicitly on `prepare<Params, Row>()`.
- Use `.get()` for single row, `.all()` for multiple rows, `.run()` for mutations.
- For transactions, use `db.transaction(() => { ... })()`.
- Parameterize every value. No string interpolation. Ever.

---

## Component Patterns

### Server vs Client Components

Default to Server Components. Mark `'use client'` only when you need:
- `useState` / `useReducer`
- `useEffect`
- Browser APIs (`window`, `document`, `localStorage`)
- Event handlers that can't be Server Actions

```typescript
// ✅ Good — server component fetches data directly
// app/(dashboard)/settings/page.tsx
import { getSession } from '@/lib/auth';
import { getUserById } from '@/queries/users';

export default async function SettingsPage() {
  const session = await getSession();
  const user = getUserById(session.userId);
  return <SettingsForm user={user} />;
}

// ✅ Good — client component handles only UI state
// components/app/settings/SettingsForm.tsx
'use client';
import { updateProfileAction } from '@/actions/auth';

export function SettingsForm({ user }: { user: User }) {
  return (
    <form action={updateProfileAction}>
      <input name="name" defaultValue={user.name ?? ''} />
      <button type="submit">Save</button>
    </form>
  );
}
```

### Server Actions

Server Actions handle all mutations. They replace API routes for form submissions and button clicks.

```typescript
// actions/auth.ts
'use server';

import { z } from 'zod';
import { getSession } from '@/lib/auth';
import { updateUserPlan } from '@/queries/users';
import { revalidatePath } from 'next/cache';

const UpdateProfileSchema = z.object({
  name: z.string().min(1).max(100),
});

export async function updateProfileAction(formData: FormData) {
  const session = await getSession();
  if (!session) throw new Error('Unauthorized');

  const parsed = UpdateProfileSchema.safeParse({
    name: formData.get('name'),
  });

  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors };
  }

  updateUserName(session.userId, parsed.data.name);
  revalidatePath('/settings');
}
```

Rules:
- Every action starts with session check. No exceptions.
- Every action validates input with Zod before touching the database.
- Return `{ error: ... }` for validation errors; `throw` for system errors.
- Call `revalidatePath()` after mutations that affect displayed data.

### Naming Conventions

| Entity | Convention | Example |
|---|---|---|
| Pages | `page.tsx` in route folder | `app/(dashboard)/billing/page.tsx` |
| Layouts | `layout.tsx` | `app/(dashboard)/layout.tsx` |
| Server components | PascalCase | `SettingsPage`, `BillingLayout` |
| Client components | PascalCase + `'use client'` | `PricingCard`, `AuthForm` |
| Server Actions | camelCase + `Action` suffix | `updateProfileAction`, `cancelSubscriptionAction` |
| Query functions | camelCase, verb-noun | `getUserById`, `listActiveSubscriptions` |
| DB columns | snake_case | `created_at`, `stripe_customer_id` |
| TS types | PascalCase | `User`, `Subscription`, `PlanType` |
| Env vars | SCREAMING_SNAKE_CASE | `DATABASE_URL`, `STRIPE_SECRET_KEY` |

---

## What We Don't Do (and Why)

### ❌ No ORM (Prisma, Drizzle, etc.)
SQLite + better-sqlite3 is already an excellent low-level API. ORMs add generated query overhead, migration abstraction leaks, and type-generation steps that slow the dev loop. Raw SQL is readable, explicit, and grep-able.

### ❌ No `useEffect` for data fetching
Server Components fetch data directly. Client Components receive data as props. `useEffect` for fetching means waterfall requests, loading states in every component, and duplicated cache logic.

### ❌ No API routes for internal mutations
Server Actions handle mutations with less boilerplate, built-in CSRF protection, and direct access to server-side session. API routes are only for external webhooks (Stripe, etc.).

### ❌ No `any` in TypeScript
Strict mode is on. A single `any` defeats the type system in that callpath. Use `unknown` and narrow, or fix the upstream type.

### ❌ No `process.env` directly in components
All env access goes through `lib/env.ts` which validates at startup:
```typescript
// lib/env.ts
import { z } from 'zod';

const EnvSchema = z.object({
  DATABASE_URL: z.string().min(1),
  BETTER_AUTH_SECRET: z.string().min(32),
  STRIPE_SECRET_KEY: z.string().startsWith('sk_'),
  RESEND_API_KEY: z.string().startsWith('re_'),
});

export const env = EnvSchema.parse(process.env);
```
If a required env var is missing, the app crashes at startup with a clear error — not at runtime during a user request.

### ❌ No direct DB access in components or layouts
All DB reads go through `queries/`. This keeps SQL testable and prevents n+1 queries hiding in JSX.

### ❌ No `Date` objects for DB storage
Store timestamps as `INTEGER` Unix epoch seconds. Convert to `Date` only at the display layer:
```typescript
const createdAt = new Date(user.created_at * 1000); // ✅
```

### ❌ No inline styles or magic numbers in Tailwind
If a design value appears more than once, extract it into a component or CSS variable. Tailwind's `theme.extend` in `tailwind.config.ts` is the right place for brand values.

---

## Auth: better-auth Setup

```typescript
// lib/auth.ts (server)
import { betterAuth } from 'better-auth';
import { db } from '@/db';

export const auth = betterAuth({
  database: { db, type: 'sqlite' },
  emailAndPassword: { enabled: true },
  session: {
    cookieCache: { enabled: true, maxAge: 60 * 5 }, // 5 min cache
  },
});

export async function getSession() {
  const { headers } = await import('next/headers');
  return auth.api.getSession({ headers: await headers() });
}
```

```typescript
// lib/auth-client.ts (browser)
import { createAuthClient } from 'better-auth/react';
export const authClient = createAuthClient({ baseURL: process.env.NEXT_PUBLIC_APP_URL });
```

---

## Stripe Integration

Stripe webhook events are the source of truth for subscription state — never trust client-reported plan data.

```typescript
// app/api/stripe/webhook/route.ts
import Stripe from 'stripe';
import { stripe } from '@/lib/stripe';
import { updateUserPlan } from '@/queries/users';

export async function POST(req: Request) {
  const body = await req.text();
  const sig = req.headers.get('stripe-signature')!;

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(body, sig, process.env.STRIPE_WEBHOOK_SECRET!);
  } catch {
    return new Response('Webhook signature verification failed', { status: 400 });
  }

  switch (event.type) {
    case 'customer.subscription.created':
    case 'customer.subscription.updated': {
      const sub = event.data.object as Stripe.Subscription;
      const userId = sub.metadata.userId;
      const plan = sub.status === 'active' ? 'pro' : 'free';
      updateUserPlan(userId, plan);
      break;
    }
    case 'customer.subscription.deleted': {
      const sub = event.data.object as Stripe.Subscription;
      updateUserPlan(sub.metadata.userId, 'free');
      break;
    }
  }

  return new Response('OK', { status: 200 });
}
```

---

## Environment Variables

```bash
# .env.example (committed — no secrets)

# App
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Database
DB_PATH=./data/app.db

# Auth
BETTER_AUTH_SECRET=                    # min 32 chars, generate with: openssl rand -base64 32

# Stripe
STRIPE_SECRET_KEY=                     # sk_test_... or sk_live_...
STRIPE_WEBHOOK_SECRET=                 # whsec_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=    # pk_test_... or pk_live_...

# Email
RESEND_API_KEY=                        # re_...
EMAIL_FROM=noreply@yourdomain.com
```

---

## Pre-Commit Checklist (run before every PR)

```bash
pnpm typecheck   # Must pass — zero errors
pnpm lint        # Must pass — zero warnings
pnpm build       # Must succeed — no build errors
```

Claude: if the user says "ship it" or "commit", run these three commands and only proceed if all pass.
