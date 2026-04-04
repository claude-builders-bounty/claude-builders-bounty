# CLAUDE.md — Next.js 15 + SQLite SaaS

This file gives you everything you need to work in this codebase without asking questions. Read it once. Then build.

## Stack

| Layer | Choice | Version |
|---|---|---|
| Framework | Next.js App Router | 15.x |
| Runtime | Node.js | 20+ |
| Database | SQLite via better-sqlite3 | 9.x |
| ORM | None — raw SQL only | — |
| Auth | next-auth v5 | 5.x |
| Styling | Tailwind CSS | 3.x |
| Deployment | Vercel or self-hosted Node | — |

No ORMs. No query builders. Raw SQL with explicit column names. If you're reaching for Prisma, stop.

---

## Folder Structure

```
/
├── app/                        # Next.js App Router pages
│   ├── (auth)/                 # Route group: auth flows (login, register)
│   ├── (dashboard)/            # Route group: authenticated app
│   │   ├── layout.tsx          # Dashboard shell + nav
│   │   └── [feature]/
│   │       ├── page.tsx        # Server Component — fetch + render
│   │       └── actions.ts      # Server Actions for mutations
│   ├── api/                    # API routes (webhooks, external integrations only)
│   └── layout.tsx              # Root layout
│
├── lib/
│   ├── db.ts                   # Single DB connection (singleton)
│   ├── db/
│   │   ├── schema.sql          # Source of truth for schema
│   │   ├── migrations/         # Numbered migration files: 001_init.sql, 002_add_x.sql
│   │   └── queries/            # Query modules per domain: users.ts, subscriptions.ts
│   ├── auth.ts                 # next-auth config
│   └── utils.ts                # Pure utility functions only
│
├── components/
│   ├── ui/                     # Primitives: Button, Input, Modal, etc.
│   └── [feature]/              # Feature-scoped components
│
└── types/
    └── index.ts                # Shared TypeScript types (DB row types live here)
```

---

## Database Rules

### Connection — `lib/db.ts`

One connection. Singleton. Never import `better-sqlite3` anywhere else.

```typescript
import Database from 'better-sqlite3';
import path from 'path';

const DB_PATH = process.env.DATABASE_URL ?? path.join(process.cwd(), 'data', 'app.db');

let db: Database.Database;

function getDb(): Database.Database {
  if (!db) {
    db = new Database(DB_PATH);
    db.pragma('journal_mode = WAL');
    db.pragma('foreign_keys = ON');
    db.pragma('synchronous = NORMAL');
  }
  return db;
}

export default getDb;
```

### Schema — `lib/db/schema.sql`

This file is the truth. The running database must match this file. Always.

```sql
CREATE TABLE IF NOT EXISTS users (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  email       TEXT NOT NULL UNIQUE,
  name        TEXT,
  created_at  INTEGER NOT NULL DEFAULT (unixepoch()),
  updated_at  INTEGER NOT NULL DEFAULT (unixepoch())
);

-- Indexes are explicit, never automatic
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
```

Rules:
- All timestamps: `INTEGER` (Unix epoch). Not `DATETIME`. Not `TEXT`.
- All IDs: `INTEGER PRIMARY KEY AUTOINCREMENT`.
- Explicit `NOT NULL` on every column that must have a value.
- Foreign keys always have a matching index.

### Migrations — `lib/db/migrations/`

Name: `001_init.sql`, `002_add_stripe_customer.sql`, etc.

Migrations are append-only. Never edit a migration that has been run in production. Write a new one.

Apply migrations at startup — `getDb()` can run pending migrations on init, or use a one-shot `npm run migrate` script.

### Queries — `lib/db/queries/users.ts`

```typescript
import getDb from '@/lib/db';
import type { User } from '@/types';

export function getUserByEmail(email: string): User | undefined {
  return getDb()
    .prepare('SELECT id, email, name, created_at FROM users WHERE email = ?')
    .get(email) as User | undefined;
}

export function createUser(email: string, name: string): User {
  const stmt = getDb().prepare(
    'INSERT INTO users (email, name) VALUES (?, ?) RETURNING id, email, name, created_at'
  );
  return stmt.get(email, name) as User;
}
```

Rules:
- Always name the columns in SELECT. Never `SELECT *`.
- Use `.get()` for single rows, `.all()` for multiple, `.run()` for mutations that don't return rows.
- Wrap multi-step mutations in a transaction: `db.transaction(() => { ... })()`.
- Put queries in the domain module, not in Server Components.

---

## Component Patterns

### Server Components fetch their own data

```typescript
// app/(dashboard)/billing/page.tsx
import { getSubscription } from '@/lib/db/queries/subscriptions';
import { auth } from '@/lib/auth';

export default async function BillingPage() {
  const session = await auth();
  const subscription = getSubscription(session!.user.id);

  return <BillingView subscription={subscription} />;
}
```

### Server Actions handle mutations

```typescript
// app/(dashboard)/billing/actions.ts
'use server';

import { revalidatePath } from 'next/cache';
import { auth } from '@/lib/auth';
import { cancelSubscription } from '@/lib/db/queries/subscriptions';

export async function cancelSubscriptionAction() {
  const session = await auth();
  if (!session) throw new Error('Unauthorized');

  cancelSubscription(session.user.id);
  revalidatePath('/billing');
}
```

Client components call Server Actions directly. No API routes for internal mutations.

### Client Components are for interactivity only

```typescript
'use client';

import { useTransition } from 'react';
import { cancelSubscriptionAction } from './actions';

export function CancelButton() {
  const [isPending, startTransition] = useTransition();

  return (
    <button
      disabled={isPending}
      onClick={() => startTransition(() => cancelSubscriptionAction())}
    >
      {isPending ? 'Canceling...' : 'Cancel subscription'}
    </button>
  );
}
```

---

## Dev Commands

```bash
npm run dev          # Start dev server (localhost:3000)
npm run build        # Production build
npm run migrate      # Run pending DB migrations
npm run db:seed      # Seed dev data (never runs in production)
npm run typecheck    # tsc --noEmit
npm run lint         # eslint
```

---

## Naming Conventions

| Thing | Convention | Example |
|---|---|---|
| Components | PascalCase | `UserCard.tsx` |
| Server Actions files | `actions.ts` | `app/(dashboard)/settings/actions.ts` |
| DB query files | camelCase plural | `subscriptions.ts` |
| DB columns | snake_case | `created_at`, `stripe_customer_id` |
| TypeScript types | PascalCase | `type User`, `type Subscription` |
| Environment variables | SCREAMING_SNAKE | `DATABASE_URL`, `NEXTAUTH_SECRET` |

---

## What We Don't Do

**No ORM.**
ORMs add a translation layer between your mental model and the database. SQLite is simple. SQL is readable. The indirection costs more than it saves.

**No API routes for internal mutations.**
Server Actions are the right primitive. `app/api/` is for webhooks, OAuth callbacks, and external integrations only.

**No `SELECT *`.**
Schema changes silently break queries that use `*`. Always name your columns.

**No datetime strings in the database.**
`INTEGER` Unix epochs compare with `<` and `>`, sort correctly, and never have timezone bugs.

**No client-side data fetching for initial page data.**
Server Components load data on the server. SWR/React Query belong in dashboards with live updates, not in every page.

**No global state management libraries.**
Server Components + URL state + Server Actions cover 95% of cases. Reach for Zustand only when you genuinely need shared client state across unrelated components.

---

## Environment Variables

```bash
# Required
DATABASE_URL=./data/app.db        # Path to SQLite file
NEXTAUTH_SECRET=<random-32-bytes> # next-auth encryption key
NEXTAUTH_URL=http://localhost:3000 # Full URL of your app

# Optional (add as needed)
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

Never commit `.env.local`. It's in `.gitignore`. It stays there.

---

## TypeScript Types

Row types live in `types/index.ts` and match the database schema exactly.

```typescript
// types/index.ts
export type User = {
  id: number;
  email: string;
  name: string | null;
  created_at: number; // Unix epoch
};

export type Subscription = {
  id: number;
  user_id: number;
  plan: 'free' | 'pro' | 'enterprise';
  status: 'active' | 'canceled' | 'past_due';
  stripe_subscription_id: string | null;
  current_period_end: number; // Unix epoch
  created_at: number;
};
```

---

## Checklist Before Shipping

- [ ] `DATABASE_URL` points to a persistent path in production (not `/tmp`)
- [ ] SQLite file is excluded from deployments (`.gitignore` or `.vercelignore`)
- [ ] WAL mode enabled (it's in `getDb()` — verify it ran)
- [ ] Foreign keys enabled (same)
- [ ] All migrations applied in production
- [ ] `NEXTAUTH_SECRET` is a real random value, not a placeholder
- [ ] No `console.log` with user data in production paths
