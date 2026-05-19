# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated project guide for Claude Code. Follow these patterns.

## Project Structure

```
src/
├── app/                    # Next.js 15 App Router (RSC by default)
│   ├── (auth)/            # Route group: login, register, reset
│   │   ├── login/page.tsx
│   │   └── layout.tsx
│   ├── (dashboard)/       # Route group: authenticated pages
│   │   ├── layout.tsx     # Shared dashboard shell
│   │   └── settings/page.tsx
│   ├── api/               # Route handlers (no RSC)
│   │   └── webhooks/stripe/route.ts
│   └── layout.tsx         # Root layout
├── lib/
│   ├── db.ts              # SQLite connection singleton
│   ├── db/                # Migration runner + queries
│   │   ├── migrate.ts
│   │   └── schema.ts      # Table definitions
│   └── auth.ts            # Lucia / Auth.js config
├── components/
│   ├── ui/                # shadcn/ui primitives
│   └── features/          # Domain components (BillingForm, TeamPicker)
├── hooks/                 # Client hooks (useMediaQuery, useDebounce)
├── types/                 # Shared TypeScript types
└── middleware.ts           # Auth guard, rate-limit, i18n
```

## Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Server Components (file) | `page.tsx`, `layout.tsx` | `app/dashboard/page.tsx` |
| Client Components | `ComponentName.client.tsx` or `"use client"` at top | `SignUpForm.tsx` |
| Route Handlers | `route.ts` | `app/api/users/route.ts` |
| DB queries | `getX`, `createX`, `updateX`, `deleteX` | `getUserByEmail` |
| Actions | `action.ts` per feature | `app/checkout/action.ts` |
| Types | `PascalCase` interfaces | `UserProfile`, `CreateTeamInput` |
| Environment vars | `UPPER_SNAKE_CASE` | `DATABASE_URL`, `STRIPE_SECRET_KEY` |

## Tech Stack

- **Framework:** Next.js 15 (App Router, RSC)
- **Database:** SQLite via `better-sqlite3` (single-file, zero-config)
- **ORM:** Drizzle ORM (lightweight, type-safe)
- **Auth:** Lucia Auth v3 (session-based) or NextAuth v5
- **UI:** Tailwind CSS + shadcn/ui
- **Payments:** Stripe Checkout + Webhooks
- **Email:** Resend (React.Email templates)
- **Validation:** Zod (shared client/server)
- **Testing:** Vitest + Playwright
- **CI/CD:** GitHub Actions → Vercel

## Database Rules

```typescript
// Always use the singleton pattern for SQLite
// lib/db.ts
import Database from 'better-sqlite3';

let db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!db) {
    db = new Database(process.env.DATABASE_URL || './data/app.db');
    db.pragma('journal_mode = WAL');
    db.pragma('foreign_keys = ON');
  }
  return db;
}
```

- **Never** create multiple DB connections
- **Always** use parameterized queries (never string interpolation)
- **Always** wrap writes in transactions
- **Never** use SQLite in edge runtime — mark route handlers `export const runtime = 'nodejs'`

## API Design

```typescript
// Route handlers return proper status codes
// app/api/users/route.ts
import { NextResponse } from 'next/server';
import { z } from 'zod';

const createUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(2).max(100),
});

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const parsed = createUserSchema.safeParse(body);
    
    if (!parsed.success) {
      return NextResponse.json(
        { error: parsed.error.flatten() },
        { status: 400 }
      );
    }
    
    const user = await createUser(parsed.data);
    return NextResponse.json(user, { status: 201 });
  } catch (error) {
    console.error('POST /api/users', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

- **Always** validate input with Zod
- **Always** return consistent `{ data, error }` shape
- **Never** leak internal errors to the client
- **Always** `export const runtime = 'nodejs'` when using SQLite
- **Always** use `NextResponse.json()` — never `Response`

## Server Actions

```typescript
// app/checkout/action.ts
'use server';

import { revalidatePath } from 'next/cache';
import { auth } from '@/lib/auth';
import { getDb } from '@/lib/db';

export async function checkout(planId: string) {
  const session = await auth();
  if (!session?.user) throw new Error('Unauthorized');
  
  const db = getDb();
  const txn = db.transaction(() => {
    const subscription = db.prepare(
      'INSERT INTO subscriptions (user_id, plan_id, status) VALUES (?, ?, ?)'
    ).run(session.user.id, planId, 'active');
    
    db.prepare(
      'UPDATE users SET plan_id = ? WHERE id = ?'
    ).run(planId, session.user.id);
    
    return subscription;
  });
  
  txn();
  revalidatePath('/dashboard');
}
```

- **Always** check auth at the top
- **Always** wrap DB writes in transactions
- **Always** `revalidatePath` after mutations
- **Never** pass sensitive data to client components

## Component Patterns

```typescript
// Server Component (default)
// app/dashboard/page.tsx
import { auth } from '@/lib/auth';
import { getUserStats } from '@/lib/db/queries';
import { StatsCard } from './StatsCard'; // Client component

export default async function DashboardPage() {
  const session = await auth();
  const stats = await getUserStats(session.user.id);
  
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {stats.map(stat => (
        <StatsCard key={stat.id} {...stat} />
      ))}
    </div>
  );
}

// Client Component
// app/dashboard/StatsCard.tsx
'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/card';

export function StatsCard({ title, value, trend }: StatsCardProps) {
  const [expanded, setExpanded] = useState(false);
  // ...
}
```

- Server Components fetch data directly (no useEffect)
- Client Components start with `"use client"` directive
- Push client interactivity to leaf nodes
- Use `loading.tsx` and `error.tsx` for boundaries

## Testing

```bash
# Unit tests (Vitest)
pnpm test -- --coverage

# E2E (Playwright)
pnpm test:e2e
```

- Unit tests: `*.test.ts` next to the file
- Integration: `*.integration.test.ts`
- E2E: `e2e/*.spec.ts`
- Use `vitest` for everything — no Jest

## Git Workflow

```
main          # Production (auto-deploys to Vercel)
├── staging   # Pre-prod
├── feat/*    # Feature branches
├── fix/*     # Bug fixes
└── chore/*   # Deps, config, cleanup
```

- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`
- PR title must match commit convention
- Squash merge to main

## Environment Variables

```bash
# .env.local (never committed)
DATABASE_URL="./data/app.db"
STRIPE_SECRET_KEY="sk_live_..."
STRIPE_WEBHOOK_SECRET="whsec_..."
RESEND_API_KEY="re_..."
NEXT_PUBLIC_APP_URL="http://localhost:3000"

# .env.example (committed, no secrets)
DATABASE_URL="./data/app.db"
NEXT_PUBLIC_APP_URL="http://localhost:3000"
```

## Common Mistakes

- ❌ Using `crypto.randomUUID()` in Server Components (not available)
- ❌ Importing `better-sqlite3` in edge routes
- ❌ `fetch()` to internal API routes (use direct function calls)
- ❌ Forgetting `revalidatePath` after Server Action mutations
- ❌ Client components wrapping Server Components (data fetching breaks)
- ❌ Passing Date objects from Server to Client components (serialize first)
