# CLAUDE.md — Next.js 15 + SQLite SaaS

Opinionated instructions for working on this codebase. Every rule has a reason.
Follow these without asking for clarification on new features or bug fixes.

---

## Stack

| Layer | Choice | Version | Why this, not the alternative |
|---|---|---|---|
| Framework | Next.js App Router | 15.x | Server Components eliminate client-side data-fetching boilerplate; PPR for instant shells |
| Language | TypeScript | 5.x strict | Strict null checks prevent the majority of runtime errors in DB-heavy code |
| Database | SQLite via `better-sqlite3` | 9.x | Synchronous API fits Next.js Server Components naturally; zero-infra for indie SaaS |
| DB (cloud) | Turso (libSQL) | latest | Use when deploying to edge or multi-region; API-compatible with `better-sqlite3` |
| Auth | `better-auth` | 1.x | Built for Next.js App Router; supports OAuth + magic link without a separate service |
| Validation | Zod | 3.x | Single schema used for both DB input and API boundary validation |
| Payments | Stripe | latest | Webhook-driven; never trust client-side success callbacks |
| Styles | Tailwind CSS | 4.x | Utility-first keeps components self-contained; no CSS files to maintain |
| Testing | Vitest + Playwright | latest | Vitest is faster than Jest for TS projects; Playwright for auth/payment flows |
| Runtime | Node.js | 22.x LTS | Required for `better-sqlite3` native bindings; do not use edge runtime for DB routes |

---

## Folder Structure

```
src/
├── app/
│   ├── (auth)/                 # Login, register, reset-password (unauthenticated)
│   ├── (dashboard)/            # Protected pages — always wrap in auth check
│   │   ├── layout.tsx          # Single auth guard here — never repeat in child pages
│   │   └── settings/
│   ├── api/                    # Route handlers only — no business logic here
│   │   ├── webhooks/
│   │   │   └── stripe/route.ts # Must verify Stripe signature before any DB write
│   │   └── ...
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── ui/                     # Primitives (Button, Input, Modal) — no data fetching
│   └── features/               # Feature components — may accept server-fetched props
├── lib/
│   ├── db/
│   │   ├── client.ts           # Singleton DB connection — import this, never open raw
│   │   ├── migrations/         # SQL files only, numbered, never modified after merge
│   │   └── queries/            # Typed query functions — one file per domain
│   ├── auth/
│   │   └── config.ts           # better-auth config — auth logic lives only here
│   ├── stripe/
│   │   └── client.ts           # Stripe SDK singleton + webhook helpers
│   ├── schemas/                # Zod schemas shared between server and client
│   └── utils/                  # Pure functions, no side effects, no imports from lib/db
├── scripts/
│   ├── migrate.ts              # Run with: pnpm db:migrate
│   └── seed.ts                 # Run with: pnpm db:seed (dev only)
└── types/
    └── index.ts                # Global type augmentations (e.g. Session extension)
```

**Rules:**
- `app/api/` route handlers call `lib/db/queries/` — never call `lib/db/client.ts` directly from a route handler.
- `components/ui/` must never import from `lib/db/` or `lib/auth/`.
- `lib/utils/` must never import from `lib/db/`, `lib/auth/`, or `lib/stripe/`.

---

## Dev Commands

```bash
pnpm dev           # Next.js dev server (http://localhost:3000)
pnpm build         # Production build
pnpm lint          # ESLint
pnpm typecheck     # tsc --noEmit
pnpm test          # Vitest unit + integration
pnpm test:e2e      # Playwright end-to-end
pnpm db:migrate    # Apply all pending migrations
pnpm db:seed       # Seed dev data (never run in production)
pnpm db:studio     # Open Drizzle Studio / sqlite-web for DB inspection
pnpm stripe:listen # Forward Stripe webhooks to localhost (requires Stripe CLI)
```

Always run `pnpm typecheck` before committing changes that touch `lib/` or `app/api/`.

---

## Database & Migration Rules

### Connection singleton (`lib/db/client.ts`)

```typescript
import Database from 'better-sqlite3';
import path from 'path';

const DB_PATH = process.env.DATABASE_URL ?? path.join(process.cwd(), 'data', 'app.db');

// Module-level singleton — Next.js HMR can re-evaluate modules; guard against
// opening multiple connections in development.
const globalForDb = global as unknown as { db: Database.Database };

export const db = globalForDb.db ?? new Database(DB_PATH);

if (process.env.NODE_ENV !== 'production') globalForDb.db = db;

// Always on — SQLite defers FK checks by default.
db.pragma('foreign_keys = ON');
// WAL mode: readers don't block writers; required for concurrent Server Actions.
db.pragma('journal_mode = WAL');
```

**Why the global singleton pattern:** Next.js hot-reloads modules in development,
which would open a new file handle on every save without this guard.

### Migration files

- Location: `lib/db/migrations/`
- Naming: `NNNN_snake_case_description.sql` (e.g., `0001_create_users.sql`)
- **Never modify a migration file after it has been merged to main.** Create a new one.
- Every migration must be idempotent: use `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`.
- Include both `-- migrate:up` and `-- migrate:down` sections.

```sql
-- migrate:up
CREATE TABLE IF NOT EXISTS users (
  id          TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  email       TEXT NOT NULL UNIQUE,
  name        TEXT,
  plan        TEXT NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'pro', 'enterprise')),
  stripe_customer_id TEXT UNIQUE,
  created_at  INTEGER NOT NULL DEFAULT (unixepoch()),
  updated_at  INTEGER NOT NULL DEFAULT (unixepoch())
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id ON users(stripe_customer_id);

-- migrate:down
DROP TABLE IF EXISTS users;
```

**Why `INTEGER` for timestamps, not `DATETIME`:** SQLite stores DATETIME as text,
which makes range queries, ordering, and arithmetic awkward. `unixepoch()` is an
integer; convert to `Date` in the query layer.

**Why `lower(hex(randomblob(16)))` for IDs:** Produces a 32-char hex UUID-equivalent
without requiring an extension. Avoids auto-increment IDs leaking row counts to clients.

### Query functions (`lib/db/queries/`)

One file per domain (e.g., `users.ts`, `subscriptions.ts`). All DB access goes here.
Return typed objects — never return raw SQLite row objects to calling code.

```typescript
// lib/db/queries/users.ts
import { db } from '../client';
import { z } from 'zod';

const UserSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  name: z.string().nullable(),
  plan: z.enum(['free', 'pro', 'enterprise']),
  stripe_customer_id: z.string().nullable(),
  created_at: z.number().transform(ts => new Date(ts * 1000)),
  updated_at: z.number().transform(ts => new Date(ts * 1000)),
});
export type User = z.infer<typeof UserSchema>;

export function getUserByEmail(email: string): User | null {
  const row = db.prepare('SELECT * FROM users WHERE email = ?').get(email);
  if (!row) return null;
  return UserSchema.parse(row);
}

export function createUser(data: { email: string; name?: string }): User {
  const stmt = db.prepare(
    'INSERT INTO users (email, name) VALUES (?, ?) RETURNING *'
  );
  const row = stmt.get(data.email, data.name ?? null);
  return UserSchema.parse(row);
}
```

**Why validate on read:** SQLite doesn't enforce column types. A Zod parse on read
surfaces schema drift immediately instead of crashing in a React component.

---

## Authentication Rules

Auth is handled entirely by `better-auth`. Do not implement custom JWT logic.

```typescript
// lib/auth/config.ts
import { betterAuth } from 'better-auth';
import { db } from '../db/client';

export const auth = betterAuth({
  database: { db, type: 'sqlite' },
  emailAndPassword: { enabled: true },
  socialProviders: {
    github: {
      clientId: process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_CLIENT_SECRET!,
    },
  },
});
```

- **Always call `auth.api.getSession()` in Server Components** to get the current user.
  Never read the session from client-side cookies directly.
- **Auth guard goes in the dashboard layout** (`app/(dashboard)/layout.tsx`), not in
  individual pages. Redirect to `/login` if no session.
- **Never expose `stripe_customer_id` or `password_hash` in Server Component props**
  passed to Client Components.

---

## Stripe & Billing Rules

- **Always verify the webhook signature** before reading `event.data`.
  Unverified webhooks are a privilege-escalation vector.
- **Plan upgrades come from webhooks only.** When a checkout succeeds, the client
  redirects to a success page, but the DB plan update happens in the webhook handler
  (`customer.subscription.updated`), not on success page load.
- **Never trust `?session_id` on the success page** to grant access. It's informational only.

```typescript
// app/api/webhooks/stripe/route.ts
import Stripe from 'stripe';
import { headers } from 'next/headers';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

export async function POST(req: Request) {
  const body = await req.text();
  const sig = (await headers()).get('stripe-signature')!;

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(body, sig, process.env.STRIPE_WEBHOOK_SECRET!);
  } catch {
    return new Response('Invalid signature', { status: 400 });
  }

  if (event.type === 'customer.subscription.updated') {
    // update plan in DB here
  }

  return new Response('ok');
}
```

---

## Component Patterns

### Server Components (default)

Use Server Components for anything that reads from the DB or needs the session.
Do not add `'use client'` unless the component needs browser APIs or event handlers.

```typescript
// app/(dashboard)/settings/page.tsx
import { auth } from '@/lib/auth/config';
import { getUserByEmail } from '@/lib/db/queries/users';
import { headers } from 'next/headers';

export default async function SettingsPage() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect('/login');

  const user = getUserByEmail(session.user.email);
  return <SettingsForm user={user} />;
}
```

### Server Actions (mutations)

All form submissions use Server Actions. No separate API routes for form handling.

```typescript
// lib/actions/profile.ts
'use server';
import { auth } from '@/lib/auth/config';
import { updateUser } from '@/lib/db/queries/users';
import { revalidatePath } from 'next/cache';
import { z } from 'zod';

const UpdateProfileSchema = z.object({
  name: z.string().min(1).max(100),
});

export async function updateProfile(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) throw new Error('Unauthorized');

  const { name } = UpdateProfileSchema.parse({
    name: formData.get('name'),
  });

  updateUser(session.user.id, { name });
  revalidatePath('/dashboard/settings');
}
```

- **Always re-authenticate in Server Actions.** Never trust a user ID passed from
  the client in form data — always derive the user ID from the server-side session.
- **Validate with Zod before any DB write.**

---

## What We Don't Do (and Why)

| Pattern | Why we avoid it |
|---|---|
| `useEffect` for data fetching | Server Components fetch data — no loading spinners, no waterfalls |
| API routes for form submissions | Server Actions are colocated, type-safe, and don't need `fetch()` |
| Client-side plan/entitlement checks | Trivially bypassable; always check on the server |
| ORM (Prisma, Drizzle) | Adds a migration layer we don't need; raw SQL is explicit and auditable |
| `any` in TypeScript | Defeats the point of strict mode; use `unknown` + narrowing |
| Auto-increment integer PKs | Leaks row counts; use `randomblob(16)` hex IDs |
| `DATETIME` columns in SQLite | Use `INTEGER` (unix epoch); range queries and ordering are correct |
| `DELETE FROM table` without WHERE | Never. Use `WHERE id = ?`. The query layer enforces this. |
| Storing JWTs in localStorage | XSS-exposed; `better-auth` uses `HttpOnly` cookies |
| Trust Stripe checkout redirect for plan upgrade | Webhooks are authoritative; redirects are informational |
| `process.env` in Client Components | Leaks secrets; only `NEXT_PUBLIC_` vars go to the client |
| Modifying merged migrations | Create a new migration instead; existing data may depend on the original |

---

## Environment Variables

```bash
# .env.local (never commit)
DATABASE_URL=./data/app.db          # Omit for default path

BETTER_AUTH_SECRET=                 # 32+ random bytes: openssl rand -base64 32
BETTER_AUTH_URL=http://localhost:3000

GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

**Rules:**
- `NEXT_PUBLIC_` prefix: only for values that must be readable in the browser.
- Never add `STRIPE_SECRET_KEY` or `BETTER_AUTH_SECRET` with a `NEXT_PUBLIC_` prefix.
- `.env.local` is gitignored. Use `.env.example` (committed, no real values) as the reference.

---

## Testing

### Unit tests (Vitest)

Test query functions against an in-memory SQLite database:

```typescript
// lib/db/queries/users.test.ts
import Database from 'better-sqlite3';
import { vi, beforeEach, it, expect } from 'vitest';

vi.mock('../client', () => ({ db: new Database(':memory:') }));

beforeEach(() => {
  // run migrations against in-memory DB
});

it('returns null for unknown email', () => {
  expect(getUserByEmail('nobody@example.com')).toBeNull();
});
```

### E2E tests (Playwright)

Cover the three critical paths: sign-up, upgrade to paid plan, and login after
password reset. Mock Stripe webhooks using `stripe trigger` in beforeAll.

---

## Naming Conventions

- **Files**: `kebab-case.ts` / `kebab-case.tsx`
- **Components**: `PascalCase`
- **Functions / variables**: `camelCase`
- **DB columns**: `snake_case`
- **Environment variables**: `SCREAMING_SNAKE_CASE`; app-specific vars prefixed with nothing (not `APP_`)
- **Migration files**: `NNNN_description.sql` where NNNN is zero-padded (0001, 0002, …)
- **Server Actions**: exported async functions in `lib/actions/*.ts`, named by operation (`updateProfile`, `cancelSubscription`)

---

## Git Conventions

- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`
- One migration per PR when possible — easier to roll back
- Do not commit `data/` (SQLite file) — it is gitignored
- Do not commit `.env.local` — use `.env.example`
