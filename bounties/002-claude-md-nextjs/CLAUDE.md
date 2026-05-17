# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated, production-ready. Every rule has a reason.

## Stack & Versions

- **Next.js 15** (App Router) — server components by default, `'use client'` only when needed
- **SQLite** via `better-sqlite3` — zero-config, single-file, perfect for SaaS until >100k users
- **TypeScript** strict mode — no `any` without a comment explaining why
- **Tailwind CSS** — utility-first, no custom CSS files unless Tailwind can't express it
- **Auth** — lucia-auth (v3+) with session tokens in httpOnly cookies, never localStorage
- **Migrations** — plain `.sql` files in `db/migrations/`, applied via `better-sqlite3` directly
- **Payments** — Stripe Checkout (redirect flow, no custom UI) + webhooks for fulfillment

## Folder Structure

```
src/
  app/                    # Next.js App Router pages
    (auth)/               # Route group: auth pages (login, register)
    (dashboard)/          # Route group: authenticated pages
    api/                  # API routes (REST, never tRPC)
  components/
    ui/                   # Reusable UI primitives (Button, Input, Modal)
    forms/                # Form components (LoginForm, SettingsForm)
  lib/
    db.ts                 # Database singleton (import once, reuse)
    auth.ts               # Auth helpers (getSession, requireAuth)
    stripe.ts             # Stripe client (server-only)
    email.ts              # Email sending (Resend or similar)
  types/
    db.ts                 # Generated types or manual table interfaces
db/
  migrations/
    001_create_users.sql  # Numbered, descriptive, never edited after deploy
    002_add_billing.sql
  seed.ts                 # Development seed data (optional)
```

### Why this structure?

- `(auth)` and `(dashboard)` route groups let you apply different layouts without repeating code
- `lib/` over `utils/` — "lib" signals "this is core infrastructure, don't touch lightly"
- `db.ts` as singleton: SQLite is single-connection, so you MUST share one instance. No connection pools.
- `components/ui/` vs `components/forms/` — UI primitives are pure and testable; forms contain business logic

## Database Conventions

### Table naming

- **Plural, snake_case**: `users`, `api_keys`, `billing_events`
- **Join tables**: `team_members` (not `user_teams` or `teams_users`)
- **Timestamps**: `created_at` and `updated_at` on every table. Use `CURRENT_TIMESTAMP` defaults.
- **Soft delete**: `deleted_at TIMESTAMP NULL` — never hard-delete user data

### Migration rules

1. Number files sequentially: `001_`, `002_`, etc.
2. **Never edit a migration after it's deployed.** Create a new migration instead.
3. Migrations are plain SQL, no ORM. `better-sqlite3` handles them directly.
4. Always wrap in a transaction. If your migration needs multiple statements, they either all succeed or all fail.
5. Test migrations on a copy of production data before deploying.

### Query patterns

```typescript
// ✅ Good: parameterized, single-purpose
const user = db.prepare('SELECT * FROM users WHERE id = ?').get(userId);

// ✅ Good: multi-row with pagination
const posts = db.prepare(
  'SELECT * FROM posts WHERE author_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?'
).all(authorId, limit, offset);

// ❌ Bad: string interpolation
const user = db.prepare(`SELECT * FROM users WHERE id = ${userId}`).get(); // SQL injection!
```

### Why no ORM?

SQLite's strength is simplicity. An ORM adds 100KB+ of abstraction for queries you can write in 3 lines of SQL. `better-sqlite3` is synchronous and fast — you don't need connection management, async overhead, or query builders. Write SQL, it works.

## Component Patterns

### Server Components (default)

Assume every component is a server component. Only add `'use client'` when you need:
- `useState`, `useEffect`, or any React hook
- Event handlers (`onClick`, `onChange`)
- Browser APIs (`window`, `localStorage`, `navigator`)

```typescript
// ✅ Server component (no 'use client' directive)
import { db } from '@/lib/db';

export default async function UserList() {
  const users = db.prepare('SELECT id, name FROM users LIMIT 20').all();
  return (
    <ul>
      {users.map(u => <li key={u.id}>{u.name}</li>)}
    </ul>
  );
}
```

### Client Components

```typescript
// ✅ Client component (minimal, imports Server Actions or API calls)
'use client';

import { useState } from 'react';
import { updateName } from './actions';

export function NameEditor({ initialName }: { initialName: string }) {
  const [name, setName] = useState(initialName);
  return (
    <input
      value={name}
      onChange={e => setName(e.target.value)}
      onBlur={() => updateName(name)}
    />
  );
}
```

### Form handling

Use **Server Actions** for mutations. Never build a REST endpoint for a form unless you need external API access.

```typescript
// app/(dashboard)/settings/actions.ts
'use server';

import { db } from '@/lib/db';
import { requireAuth } from '@/lib/auth';
import { revalidatePath } from 'next/cache';

export async function updateName(formData: FormData) {
  const user = await requireAuth();
  const name = formData.get('name') as string;
  db.prepare('UPDATE users SET name = ? WHERE id = ?').run(name, user.id);
  revalidatePath('/settings');
}
```

### Loading & Error states

Every async page needs `loading.tsx` and `error.tsx` in the same directory. Next.js handles the Suspense boundary automatically.

```
app/(dashboard)/posts/
  page.tsx        # Main content (async server component)
  loading.tsx     # Skeleton shown while page.tsx loads
  error.tsx       # Error boundary fallback ('use client')
```

## Auth Rules

1. **Session tokens in httpOnly cookies** — never localStorage, never JWT in JS
2. Use `lucia-auth` v3+ — it handles token rotation, expiry, and CSRF
3. `requireAuth()` throws if no valid session — call it at the top of every authenticated route/action
4. Rate-limit login attempts: 5 per minute per IP, tracked in SQLite

## API Routes

### When to use API routes vs Server Actions

- **Server Actions**: mutations triggered by form submissions or button clicks
- **API routes** (`route.ts`): endpoints called by external services (webhooks, cron jobs, third parties)

```typescript
// app/api/stripe/webhook/route.ts
export async function POST(req: Request) {
  const sig = req.headers.get('stripe-signature')!;
  const event = stripe.webhooks.constructEvent(body, sig, secret);
  // ... handle event
  return Response.json({ received: true });
}
```

## What We Don't Do (and Why)

| Anti-pattern | Why not | Do instead |
|---|---|---|
| `useEffect` for data fetching | Extra round-trip, no SSR | Server Components + async/await |
| `useState(initialData)` with empty initial | Hydration mismatch | Pass data as props from server |
| ORM (Prisma, Drizzle, Kysely) | Overkill for SQLite's feature set | `better-sqlite3` + raw SQL |
| API routes for form submissions | Unnecessary REST layer | Server Actions |
| JWT in localStorage | XSS vulnerability | httpOnly session cookies |
| `any` type | Loses all type safety | Proper interface or `unknown` + narrowing |
| `npm run dev` in production | No optimization, no error handling | `npm run build && npm start` |
| Multiple DB connections | SQLite is single-writer | Singleton pattern in `lib/db.ts` |

## Dev Commands

```bash
npm run dev          # Start dev server (turbopack)
npm run build        # Production build
npm run start        # Start production server
npm run lint         # ESLint + TypeScript check
npm run db:migrate   # Apply pending migrations
npm run db:seed      # Seed development data
npm run db:studio    # Open SQLite browser (optional)
npm run stripe:listen # Stripe CLI webhook forwarding
```

## Testing

- **Unit tests**: `vitest` for pure functions and utilities
- **Integration tests**: `vitest` + `better-sqlite3` with `:memory:` database
- **E2E**: `playwright` for critical flows (signup, payment, upgrade)
- Test files co-located: `__tests__/` next to the code they test

## Deployment

- **Production**: any Node.js host that supports Next.js (Vercel, Railway, Fly.io)
- **SQLite**: persists on a volume. Backup regularly with `litestream` for point-in-time recovery
- **Environment variables**: `.env.local` for dev, platform env vars for production. Never commit `.env*` files.
- **Health check**: `GET /api/health` returns `{ status: 'ok', db: 'connected' }`

## First-Time Setup (for this project)

```bash
npm install
cp .env.example .env.local  # Fill in required vars
npm run db:migrate
npm run db:seed              # Optional
npm run dev
```

---

*This CLAUDE.md was built for the [Claude Builders Bounty #2](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2).*

*Last updated: 2026-05-17*
