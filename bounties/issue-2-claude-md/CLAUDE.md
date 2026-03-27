# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

> This file tells Claude Code exactly how this project works. Read it before touching any file.
> Every rule has a reason. If you disagree with a rule, ask before breaking it.

---

## 1. Stack & Exact Versions

| Tool | Version | Why |
|------|---------|-----|
| Node.js | 20 LTS | `fetch` built-in, no polyfills needed |
| Next.js | 15.x | App Router stable, Server Actions stable |
| TypeScript | 5.x strict | `strict: true` — no escape hatches |
| SQLite driver | `better-sqlite3` ^9 (local) or `@libsql/client` ^0.14 (Turso) | Synchronous API for better-sqlite3 eliminates async bugs in DB layer |
| ORM | Drizzle ORM ^0.30 | Type-safe queries, SQL-first, no magic |
| Auth | NextAuth.js v5 (Auth.js) | App Router native, built-in adapter for Drizzle |
| Validation | Zod ^3 | Schema = type + runtime validator, one source of truth |
| Forms | react-hook-form ^7 + `@hookform/resolvers` | Uncontrolled by default = no re-render on keystroke |
| Styling | Tailwind CSS ^3 + shadcn/ui | Copy-paste components, no dependency hell |
| Testing | Vitest + `@testing-library/react` | Same config as Vite, no Jest quirks with ESM |
| Email | Resend | Minimal API, React Email templates |

**Never upgrade major versions mid-sprint.** Pin `package.json` with exact versions in CI.

---

## 2. Folder Structure

```
/
├── app/                          # Next.js App Router ONLY — no logic here
│   ├── layout.tsx                # Root layout: fonts, providers, metadata
│   ├── page.tsx                  # Marketing/landing page
│   ├── globals.css               # Tailwind base only, no custom CSS rules
│   ├── (auth)/                   # Route group — no URL segment
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   └── layout.tsx            # Auth-specific layout (centered card)
│   ├── (dashboard)/              # Protected routes group
│   │   ├── layout.tsx            # Sidebar + header — check session here
│   │   ├── page.tsx              # Dashboard home
│   │   ├── settings/page.tsx
│   │   └── [id]/page.tsx         # Dynamic segments
│   └── api/
│       ├── auth/[...nextauth]/route.ts   # Auth.js handler
│       └── webhooks/
│           └── stripe/route.ts   # Webhook endpoints (raw body required)
│
├── components/
│   ├── ui/                       # shadcn/ui primitives — NEVER edit these
│   ├── forms/                    # Form components with built-in validation
│   │   └── LoginForm.tsx
│   └── features/                 # Domain-specific components
│       ├── billing/
│       └── dashboard/
│
├── lib/
│   ├── db/
│   │   ├── index.ts              # DB singleton — import from here only
│   │   ├── schema.ts             # Drizzle schema — source of truth for types
│   │   └── migrations/           # Raw SQL files, numbered sequentially
│   │       ├── 0001_initial.sql
│   │       └── 0002_add_teams.sql
│   ├── auth.ts                   # Auth.js config + session helpers
│   ├── validations.ts            # Zod schemas shared across server/client
│   └── utils.ts                  # Pure functions: cn(), formatDate(), slugify()
│
├── hooks/                        # Client-side hooks ONLY
│   └── use-debounce.ts
│
├── server/                       # Server-only code (never imported by client)
│   ├── queries/                  # DB queries by domain
│   │   ├── users.ts
│   │   └── subscriptions.ts
│   └── actions/                  # Server Actions by domain
│       ├── auth.ts
│       └── billing.ts
│
├── types/
│   └── index.ts                  # Shared TypeScript types (not DB types — those come from schema.ts)
│
├── drizzle.config.ts
├── middleware.ts                  # Auth protection — route matching only
└── next.config.ts
```

**Why this structure:**
- `app/` only handles routing and rendering. No business logic.
- `server/` directory is enforced as server-only via `import 'server-only'` at top of each file. If a Client Component accidentally imports it, Next.js throws at build time — not at runtime in prod.
- `lib/db/` is a singleton. Every module imports from `lib/db/index.ts`. Never create a second DB connection.
- `components/ui/` is owned by shadcn. Run `npx shadcn@latest add button` to update, never hand-edit.

---

## 3. Dev Commands

```bash
# Start dev server (port 3000)
npm run dev

# Run migrations (apply all pending)
npm run db:migrate

# Open Drizzle Studio (visual DB inspector)
npm run db:studio

# Generate migration file from schema changes
npm run db:generate

# Type check (no emit)
npx tsc --noEmit

# Run tests (watch mode)
npx vitest

# Run tests (CI mode)
npx vitest run

# Lint
npm run lint

# Format
npx prettier --write .

# Build + check for type errors (always run before PR)
npm run build
```

**`package.json` scripts must include these exact names** so Claude can run them without asking:
```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "db:generate": "drizzle-kit generate",
    "db:migrate": "tsx lib/db/migrate.ts",
    "db:studio": "drizzle-kit studio"
  }
}
```

---

## 4. Database — SQLite Rules

### 4.1 Schema (Drizzle)

Define all tables in `lib/db/schema.ts`. This file is the **single source of truth** for both TypeScript types and SQL structure.

```typescript
// lib/db/schema.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';
import { createId } from '@paralleldrive/cuid2';

export const users = sqliteTable('users', {
  id: text('id').primaryKey().$defaultFn(() => createId()),
  email: text('email').notNull().unique(),
  name: text('name'),
  role: text('role', { enum: ['user', 'admin'] }).notNull().default('user'),
  createdAt: integer('created_at', { mode: 'timestamp' })
    .notNull()
    .$defaultFn(() => new Date()),
  updatedAt: integer('updated_at', { mode: 'timestamp' })
    .notNull()
    .$defaultFn(() => new Date()),
});

// Inferred types — use these everywhere, never write manual interfaces for DB rows
export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;
```

**Rules:**
- IDs: use `cuid2`, not UUID (shorter, URL-safe, k-sortable)
- Timestamps: store as `INTEGER` Unix timestamps. Never `TEXT` dates.
- Enums: use `text` with `{ enum: [...] }` — SQLite has no native enum type
- `NOT NULL` is the default intent — explicitly mark optional fields `.nullable()`

### 4.2 Migration Conventions

**Rule: one migration file per schema change. Never edit an existing migration.**

Files live in `lib/db/migrations/` and are numbered: `0001_initial.sql`, `0002_add_teams.sql`.

```sql
-- lib/db/migrations/0003_add_subscriptions.sql
-- Purpose: Add subscriptions table for billing
-- Affects: users (FK), new subscriptions table
-- Created: 2026-03-27
-- Author: claude / [dev name]

-- ⬆ UP
CREATE TABLE IF NOT EXISTS subscriptions (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  stripe_customer_id TEXT UNIQUE,
  plan TEXT NOT NULL CHECK(plan IN ('free', 'pro', 'enterprise')) DEFAULT 'free',
  status TEXT NOT NULL CHECK(status IN ('active', 'canceled', 'past_due')) DEFAULT 'active',
  current_period_end INTEGER,  -- Unix timestamp
  created_at INTEGER NOT NULL DEFAULT (unixepoch()),
  updated_at INTEGER NOT NULL DEFAULT (unixepoch())
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);

-- ⬇ DOWN (run manually if needed — never auto-rolled back)
-- DROP TABLE IF EXISTS subscriptions;
```

Migration runner in `lib/db/migrate.ts`:
```typescript
import { migrate } from 'drizzle-orm/better-sqlite3/migrator';
import { db } from './index';

migrate(db, { migrationsFolder: './lib/db/migrations' });
console.log('Migrations applied');
```

### 4.3 Query Patterns

```typescript
// server/queries/users.ts
import 'server-only'; // fails at build if imported by client
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';
import { eq, and, desc } from 'drizzle-orm';
import type { User } from '@/lib/db/schema';

// ✅ Parameterized — always use Drizzle's eq/and/etc., never string interpolation
export async function getUserByEmail(email: string): Promise<User | undefined> {
  return db.select().from(users).where(eq(users.email, email)).get();
}

// ✅ Transactions for multi-table writes
export async function createUserWithProfile(data: { email: string; name: string }) {
  return db.transaction((tx) => {
    const user = tx.insert(users).values(data).returning().get();
    // tx.insert(profiles)... 
    return user;
  });
}

// ❌ Never do this — SQL injection vector
export async function badQuery(email: string) {
  return db.run(`SELECT * FROM users WHERE email = '${email}'`); // NEVER
}
```

### 4.4 Turso (Production SQLite)

Switch from `better-sqlite3` to Turso by changing `lib/db/index.ts`:

```typescript
// lib/db/index.ts — Turso version
import { drizzle } from 'drizzle-orm/libsql';
import { createClient } from '@libsql/client';

const client = createClient({
  url: process.env.TURSO_DATABASE_URL!,
  authToken: process.env.TURSO_AUTH_TOKEN!,
});

export const db = drizzle(client);
```

The rest of the codebase doesn't change — schema and queries are identical.

---

## 5. Component Patterns

### 5.1 Server vs Client — Decision Rule

```
Does it need useState / useEffect / browser APIs / event listeners?
  YES → 'use client' — keep it as a leaf, not a wrapper
  NO  → Server Component (default)
```

```typescript
// ✅ Server Component — fetches data, no interactivity
// app/(dashboard)/page.tsx
import { getUser } from '@/server/queries/users';
import { UserCard } from '@/components/features/dashboard/UserCard';

export default async function DashboardPage() {
  const user = await getUser(); // direct DB call — no fetch, no API
  return <UserCard user={user} />;
}

// ✅ Client Component — only the interactive part
// components/features/dashboard/ThemeToggle.tsx
'use client';
import { useState } from 'react';

export function ThemeToggle() {
  const [dark, setDark] = useState(false);
  return <button onClick={() => setDark(!dark)}>Toggle</button>;
}
```

### 5.2 File Naming

| Type | Convention | Example |
|------|-----------|---------|
| Page | `page.tsx` (Next.js required) | `app/dashboard/page.tsx` |
| Layout | `layout.tsx` | `app/(dashboard)/layout.tsx` |
| Component | `PascalCase.tsx` | `UserAvatar.tsx` |
| Server Action file | `camelCase.ts` in `server/actions/` | `billing.ts` |
| Hook | `use-kebab-case.ts` | `use-debounce.ts` |
| Query file | `camelCase.ts` in `server/queries/` | `users.ts` |
| Utility | `camelCase.ts` | `formatDate.ts` |

### 5.3 Server Actions

Server Actions replace REST endpoints for form submissions and mutations:

```typescript
// server/actions/auth.ts
'use server';
import { z } from 'zod';
import { redirect } from 'next/navigation';
import { createUser } from '@/server/queries/users';

const RegisterSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  name: z.string().min(1),
});

export async function registerAction(formData: FormData) {
  // 1. Validate
  const result = RegisterSchema.safeParse(Object.fromEntries(formData));
  if (!result.success) {
    return { error: result.error.flatten().fieldErrors };
  }

  // 2. Execute
  try {
    await createUser(result.data);
  } catch (e) {
    if (e instanceof Error && e.message.includes('UNIQUE')) {
      return { error: { email: ['Email already registered'] } };
    }
    throw e; // Let Next.js error boundary handle unexpected errors
  }

  // 3. Redirect (outside try/catch — redirect() throws internally)
  redirect('/dashboard');
}
```

### 5.4 Form Handling

```typescript
// components/forms/RegisterForm.tsx
'use client';
import { useActionState } from 'react'; // Next.js 15 hook
import { registerAction } from '@/server/actions/auth';

export function RegisterForm() {
  const [state, action, pending] = useActionState(registerAction, null);

  return (
    <form action={action}>
      <input name="email" type="email" required />
      {state?.error?.email && <p className="text-red-500">{state.error.email[0]}</p>}
      
      <input name="password" type="password" required minLength={8} />
      <input name="name" type="text" required />

      <button type="submit" disabled={pending}>
        {pending ? 'Creating account...' : 'Register'}
      </button>
    </form>
  );
}
```

**Why `useActionState` not `useFormStatus`:** `useActionState` gives you the return value of the action, which carries validation errors. Use `useFormStatus` only for the pending indicator inside a nested component.

### 5.5 Data Fetching Hierarchy

```
Server Component (page.tsx)
  → direct DB call via server/queries/
  → pass data as props to child Server Components
  → pass data as props to Client Components (serializable only)

Client Component
  → receive initial data as props (from server)
  → SWR/TanStack Query for client-side updates/polling
  → Server Actions for mutations
```

Never fetch from a Client Component on mount (`useEffect(() => { fetch('/api/...') })`). This pattern causes layout shift, loading spinners, and double-fetching.

---

## 6. API Routes — When to Use Them

Use `app/api/` route handlers **only** for:
- Webhooks (Stripe, GitHub, etc.) that require raw body access
- Endpoints consumed by third parties or mobile apps
- OAuth callbacks (handled by Auth.js automatically)

For internal UI data fetching: use Server Components + Server Actions.

```typescript
// app/api/webhooks/stripe/route.ts
import { headers } from 'next/headers';
import Stripe from 'stripe';

export async function POST(req: Request) {
  const body = await req.text(); // raw body for signature verification
  const sig = (await headers()).get('stripe-signature')!;

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(body, sig, process.env.STRIPE_WEBHOOK_SECRET!);
  } catch (e) {
    return new Response('Invalid signature', { status: 400 });
  }

  switch (event.type) {
    case 'customer.subscription.updated':
      await handleSubscriptionUpdate(event.data.object as Stripe.Subscription);
      break;
  }

  return new Response('OK', { status: 200 });
}
```

---

## 7. Auth — Session & Protection

```typescript
// lib/auth.ts
import NextAuth from 'next-auth';
import { DrizzleAdapter } from '@auth/drizzle-adapter';
import GitHub from 'next-auth/providers/github';
import { db } from '@/lib/db';

export const { handlers, auth, signIn, signOut } = NextAuth({
  adapter: DrizzleAdapter(db),
  providers: [GitHub],
  callbacks: {
    session({ session, user }) {
      session.user.id = user.id; // always expose user.id on session
      return session;
    },
  },
});
```

```typescript
// middleware.ts — protect routes, no business logic here
import { auth } from '@/lib/auth';
import { NextResponse } from 'next/server';

export default auth((req) => {
  const isLoggedIn = !!req.auth;
  const isDashboard = req.nextUrl.pathname.startsWith('/dashboard');

  if (isDashboard && !isLoggedIn) {
    return NextResponse.redirect(new URL('/login', req.url));
  }
});

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
```

**Row-level security:** Every query in `server/queries/` that touches user data must filter by `userId`. Never return data without a user scope check.

```typescript
// ✅ Always scope to current user
export async function getUserSubscription(userId: string) {
  return db.select().from(subscriptions)
    .where(eq(subscriptions.userId, userId)) // userId from session, not URL param
    .get();
}

// ❌ Never trust URL parameters alone
export async function getSubscriptionById(id: string) {
  return db.select().from(subscriptions).where(eq(subscriptions.id, id)).get();
  // Attacker can enumerate other users' subscriptions
}
```

---

## 8. Environment Variables

Required in `.env.local` (never commit this file):
```bash
# DB — local development
DATABASE_URL="./data/local.db"

# DB — production (Turso)
TURSO_DATABASE_URL="libsql://your-db.turso.io"
TURSO_AUTH_TOKEN="your-token"

# Auth
AUTH_SECRET="generate with: openssl rand -base64 32"
AUTH_GITHUB_ID="..."
AUTH_GITHUB_SECRET="..."

# Email
RESEND_API_KEY="re_..."

# Billing
STRIPE_SECRET_KEY="sk_live_..."
STRIPE_WEBHOOK_SECRET="whsec_..."
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY="pk_live_..."
```

Validate env vars at startup — fail fast before accepting requests:
```typescript
// lib/env.ts
import { z } from 'zod';

const EnvSchema = z.object({
  DATABASE_URL: z.string().min(1),
  AUTH_SECRET: z.string().min(32),
  RESEND_API_KEY: z.string().startsWith('re_'),
});

export const env = EnvSchema.parse(process.env);
// If missing, throws at startup with clear message — not a cryptic runtime error
```

---

## 9. Error Handling

### Server Actions
- Return `{ error: string | FieldErrors }` for expected errors (validation, conflicts)
- `throw` for unexpected errors — Next.js error boundary catches them
- Never return stack traces to the client

### API Routes
```typescript
// Standard error response shape
type ApiError = { error: string; code?: string };

export function errorResponse(message: string, status: number): Response {
  return Response.json({ error: message } satisfies ApiError, { status });
}
```

### Database Errors
```typescript
// Detect SQLite constraint violations
function isUniqueViolation(e: unknown): boolean {
  return e instanceof Error && e.message.includes('UNIQUE constraint failed');
}
```

---

## 10. What We DON'T Do (And Why)

### ❌ No Pages Router
This project uses App Router exclusively. Never create files in `pages/`. If you see `pages/`, it's a mistake.

### ❌ No `useEffect` for Data Fetching
`useEffect` + `fetch('/api/data')` causes: 1) double requests in React StrictMode, 2) no deduplication, 3) loading flicker. Use Server Components instead.

### ❌ No Raw SQL String Interpolation
`db.run(\`SELECT * FROM users WHERE id = '${id}'\`)` is a SQL injection vector. Always use Drizzle's parameterized API.

### ❌ No `any` Type
TypeScript strict mode is enabled. `any` means "I gave up." Use `unknown` + type guards, or fix the upstream type.

### ❌ No Business Logic in `app/`
Pages and layouts are routing artifacts. Logic goes in `server/queries/`, `server/actions/`, or `lib/`. If a page file exceeds 50 lines, something is wrong.

### ❌ No Client Components as Page Roots
```typescript
// ❌ Wrong — entire page is now client-side JS bundle
'use client';
export default function DashboardPage() { ... }

// ✅ Right — page is server, interactive widget is client leaf
export default async function DashboardPage() {
  const data = await getData();
  return <DashboardShell data={data}><InteractiveWidget /></DashboardShell>;
}
```

### ❌ No Unscoped DB Queries in Request Handlers
Every DB query must include a `userId` filter derived from the authenticated session, not from URL params or request body. Users must never be able to read or modify another user's data.

### ❌ No `.env` Committed to Git
`.env.local` is gitignored. Provide `.env.example` with placeholder values. If secrets appear in git history, rotate them immediately.

### ❌ No Drizzle `push` in Production
`drizzle-kit push` syncs schema directly — it drops columns without warning. Use `drizzle-kit generate` + `npm run db:migrate` in production. `push` is only for local dev iteration.

### ❌ No `console.log` in Production Code
Use a structured logger (e.g., `pino`) or remove logs before merging. `console.log` in Server Components leaks to server logs which may be visible in your hosting dashboard.

---

## 11. TypeScript Configuration

```json
// tsconfig.json (required settings)
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

`noUncheckedIndexedAccess` is non-negotiable — it catches `array[0]` being `undefined` at compile time instead of runtime.

---

## 12. Testing Conventions

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./test/setup.ts'],
  },
  resolve: {
    alias: { '@': path.resolve(__dirname, '.') },
  },
});
```

**What to test:**
- `lib/validations.ts` — Zod schemas: valid input, invalid input, edge cases
- `server/queries/` — Use an in-memory SQLite DB (`:memory:`), not mocks
- `server/actions/` — Integration tests with real DB
- Components — Only test behavior, not markup

**What NOT to test:**
- shadcn/ui components (they're tested upstream)
- Next.js routing (framework responsibility)
- Type correctness (that's TypeScript's job)

---

## 13. Git Conventions

```
feat(auth): add GitHub OAuth provider
fix(db): handle unique constraint on email registration  
chore(deps): bump next to 15.2.1
refactor(queries): extract user lookup to server/queries/users.ts
```

Format: `type(scope): lowercase description`  
Types: `feat`, `fix`, `chore`, `refactor`, `docs`, `test`  
Never commit: `node_modules/`, `.env.local`, `*.db`, `.next/`

---

## 14. Deployment Checklist

Before deploying to production:
- [ ] `npm run build` passes (no type errors, no missing env vars)
- [ ] All migrations applied on prod DB (`npm run db:migrate`)  
- [ ] `AUTH_SECRET` is a 32+ char random string (not the dev default)
- [ ] Stripe webhook endpoint registered and `STRIPE_WEBHOOK_SECRET` set
- [ ] `.env.example` updated with new variable names (not values)
- [ ] `noStore()` or `cache: 'no-store'` on any route that reads user-specific data

---

*This CLAUDE.md was designed to give Claude Code full project context without follow-up questions. If something in the codebase contradicts this file, follow this file and flag the discrepancy.*
