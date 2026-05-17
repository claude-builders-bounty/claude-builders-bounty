# CLAUDE.md 鈥?Next.js 15 + SQLite SaaS Starter

> **Why this file exists:** This project is a SaaS built with Next.js 15 App Router + SQLite (Turso/better-sqlite3). This document tells Claude Code exactly how we work, so it can contribute without asking clarifying questions. Every rule below has a reason.

---

## Stack & Versions

| Layer | Choice | Reason |
|---|---|---|
| Framework | Next.js 15 (App Router) | RSC + streaming = fast, no client-side JS bloat |
| Language | TypeScript 5 | Type safety at edges (API, DB, forms) |
| Database | SQLite via `better-sqlite3` (dev) / Turso (prod) | Zero-ops, embedded, ACID, fast for SaaS workloads |
| ORM | **None** 鈥?raw SQL with `better-sqlite3` + `@libsql/client` | ORMs add abstraction we don't need; SQL is portable |
| Styling | Tailwind CSS 4 | Utility-first, no CSS files to maintain |
| Auth | Better Auth | Open-source, Next.js-native, supports multi-tenant orgs |
| Payments | Stripe SDK | Industry standard for SaaS billing |
| Deployment | Vercel | Zero-config for Next.js, Edge Middleware support |
| Testing | Vitest + @testing-library/react | Fast, JSDOM-free for RSC |

**Why NOT Prisma / Drizzle?**
- Prisma: heavy, client-side bundle, WASM overhead
- Drizzle: good, - **Raw SQL wins:** explicit, debuggable, portable between better-sqlite3 and Turso

---

## Folder Structure

```
src/
鈹溾攢鈹€ app/                    # Next.js App Router
鈹?  鈹溾攢鈹€ (auth)/             # Route group: login, register, forgot-password
鈹?  鈹?  鈹溾攢鈹€ login/page.tsx
鈹?  鈹?  鈹斺攢鈹€ register/page.tsx
鈹?  鈹溾攢鈹€ (dashboard)/        # Protected routes (layout checks auth)
鈹?  鈹?  鈹溾攢鈹€ layout.tsx     # Auth guard + org switcher
鈹?  鈹?  鈹溾攢鈹€ page.tsx       # /dashboard
鈹?  鈹?  鈹斺攢鈹€ settings/
鈹?  鈹溾攢鈹€ api/                # Route Handlers (API routes)
鈹?  鈹?  鈹溾攢鈹€ auth/[...all]/route.ts   # Better Auth handler
鈹?  鈹?  鈹溾攢鈹€ trpc/[trpc]/route.ts     # (optional) tRPC
鈹?  鈹?  鈹斺攢鈹€ webhooks/stripe/route.ts
鈹?  鈹溾攢鈹€ layout.tsx          # Root layout: fonts, providers, Toaster
鈹?  鈹斺攢鈹€ page.tsx            # Landing page (/)
鈹溾攢鈹€ components/             # Shared UI components (Server + Client)
鈹?  鈹溾攢鈹€ ui/                 # Base: Button, Input, Modal, etc.
鈹?  鈹溾攢鈹€ forms/              # Form components with react-hook-form + zod
鈹?  鈹斺攢鈹€ layouts/            # Shell, Sidebar, Navbar
鈹溾攢鈹€ lib/                    # Pure logic (no React)
鈹?  鈹溾攢鈹€ db.ts              # SQLite connection + query helpers
鈹?  鈹溾攢鈹€ auth.ts            # Better Auth config + session helpers
鈹?  鈹溾攢鈹€ stripe.ts          # Stripe client + webhook handlers
鈹?  鈹斺攢鈹€ validations.ts     # Zod schemas (shared with forms)
鈹溾攢鈹€ core/                   # Business logic (never import from React)
鈹?  鈹溾攢鈹€ users/
鈹?  鈹?  鈹溾攢鈹€ queries.ts     # SQL: getUserById, updateUser, etc.
鈹?  鈹?  鈹斺攢鈹€ actions.ts    # Server Actions (called from forms)
鈹?  鈹溾攢鈹€ orgs/
鈹?  鈹?  鈹溾攢鈹€ queries.ts
鈹?  鈹?  鈹斺攢鈹€ actions.ts
鈹?  鈹斺攢鈹€ subscriptions/
鈹?      鈹溾攢鈹€ queries.ts
鈹?      鈹斺攢鈹€ actions.ts
鈹溾攢鈹€ types/                  # TypeScript types (generated from DB schema)
鈹?  鈹溾攢鈹€ database.ts         # Generated: User, Org, Subscription, etc.
鈹?  鈹斺攢鈹€ api.ts             # API request/response types
鈹溾攢鈹€ hooks/                  # Client-side React hooks
鈹?  鈹溾攢鈹€ useUser.ts
鈹?  鈹斺攢鈹€ useSubscription.ts
鈹斺攢鈹€ middleware.ts           # Next.js Middleware: auth, org routing, rate-limit
```

### Rules

- **`src/core/*/queries.ts`** 鈥?ONLY raw SQL + type casting. No React imports.
- **`src/core/*/actions.ts`** 鈥?Next.js Server Actions. Always `use server`.
- **`src/lib/db.ts`** 鈥?Single source of DB connection. Never import `better-sqlite3` anywhere else.
- **`src/types/database.ts`** 鈥?Auto-generated from `migrations/*.sql`. Never edit manually.

---

## SQL / Migration Conventions

### Database File

```
migrations/
鈹溾攢鈹€ 0001_initial_schema.sql
鈹溾攢鈹€ 0002_add_orgs.sql
鈹溾攢鈹€ 0003_add_subscriptions.sql
鈹斺攢鈹€ 0004_add_audit_logs.sql
```

### Rules

1. **Every migration is additive.** Never use `ALTER TABLE DROP COLUMN` or `DROP TABLE`. If you need to remove a column, add a new table and migrate data.
   - *Reason:* SQLite doesn't support `DROP COLUMN` in older versions; additive migrations are reversible.

2. **Migration files are numbered sequentially.** Format: `NNNN_description.sql`.
   - *Reason:* Deterministic ordering; no timestamp conflicts in PRs.

3. **Every table has `id` (TEXT, primary key, cuid()), `created_at`, `updated_at`.**
   ```sql
   CREATE TABLE users (
     id TEXT PRIMARY KEY DEFAULT(cuid()),
     email TEXT UNIQUE NOT NULL,
     name TEXT NOT NULL,
     created_at INTEGER DEFAULT(unixepoch()) NOT NULL,
     updated_at INTEGER DEFAULT(unixepoch()) NOT NULL
   );
   ```
   - *Reason:* `cuid()` = URL-safe, collision-free, sortable by time. `INTEGER` timestamps = SQLite-native, works in Turso.

4. **Foreign keys are `TEXT` matching `cuid()` of parent.** Always add `ON DELETE CASCADE`.
   ```sql
   CREATE TABLE subscriptions (
     id TEXT PRIMARY KEY DEFAULT(cuid()),
     user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
     plan_id TEXT NOT NULL,
     status TEXT NOT NULL DEFAULT('active'),
     created_at INTEGER DEFAULT(unixepoch()) NOT NULL
   );
   ```

5. **No enums.** Use `TEXT` with a `CHECK` constraint.
   ```sql
   status TEXT NOT NULL DEFAULT('active') CHECK(status IN ('active', 'canceled', 'past_due'))
   ```
   - *Reason:* SQLite doesn't have native enums; CHECK constraints are portable to Turso.

6. **Indexes on all foreign keys + frequently queried columns.**
   ```sql
   CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
   CREATE INDEX idx_subscriptions_status ON subscriptions(status);
   ```

7. **Queries use parameterized SQL. Never concatenate strings.**
   ```typescript
   // 鉁?GOOD
   const user = db.prepare('SELECT * FROM users WHERE email = ?').get(email) as User;
   
   // 鉂?BAD 鈥?SQL injection risk
   const user = db.prepare(`SELECT * FROM users WHERE email = '${email}'`).get();
   ```

8. **Transactions wrap multi-row writes.**
   ```typescript
   const result = db.transaction(() => {
     const user = db.prepare('INSERT INTO users (email, name) VALUES (?, ?) RETURNING id').get(email, name);
     db.prepare('INSERT INTO subscriptions (user_id, plan_id) VALUES (?, ?)').run(user.id, 'free');
     return user;
   })();
   ```

---

## Component Patterns

### Server Components (Default)

```typescript
// src/app/(dashboard)/page.tsx
import { getUsers } from '@/core/users/queries';
import { UsersTable } from '@/components/UsersTable';

export default async function DashboardPage() {
  const users = getUsers(); // Direct SQL call, no API round-trip
  
  return (
    <main>
      <h1>Users</h1>
      <UsersTable users={users} />
    </main>
  );
}
```

- *Reason:* RSC = zero client JS. Data fetched on server. Fast.

### Client Components (Only When Needed)

```typescript
'use client';

// src/components/forms/CreateUserForm.tsx
import { useActionState } from 'react';
import { createUser } from '@/core/users/actions';

export function CreateUserForm() {
  const [state, formAction, pending] = useActionState(createUser, null);
  
  return (
    <form action={formAction}>
      <input name="email" type="email" required />
      <input name="name" type="text" required />
      <button disabled={pending}>Create</button>
    </form>
  );
}
```

- *Rule:* Always use `useActionState` (React 19) for forms. Never `onSubmit` + `fetch`.

### Layouts

```typescript
// src/app/(dashboard)/layout.tsx
import { auth } from '@/lib/auth';
import { redirect } from 'next/navigation';

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const session = await auth();
  if (!session) redirect('/login');
  
  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
```

---

## What We Don't Do (And Why)

| Don't | Why |
|---|---|
| 鉂?Use ORM (Prisma, Drizzle) | Raw SQL is explicit, debuggable, portable |
| 鉂?Use `useEffect` for data fetching | RSC + Server Actions = no client-side data fetching |
| 鉂?Use Redux / Zustand | Server state lives in RSC; client state is local (`useState`) |
| 鉂?Use `any` type | TypeScript is free; use it |
| 鉂?Concatenate SQL strings | Parameterized queries only 鈥?prevent injection |
| 鉂?Mutate `process.env` | Next.js env vars are frozen at build time |
| 鉂?Use `next/router` (pages router) | We're App Router only |
| 鉂?Add ESLint plugins beyond defaults | More plugins = more bikeshedding |
| 鉂?Write unit tests for components | Vitest + @testing-library/react for logic; E2E with Playwright |
| 鉂?Use `async/await` with better-sqlite3 | It's synchronous by design; use `.get()` / `.all()` / `.run()` |

---

## Dev Commands

```bash
# Install
npm install

# Dev server (with Turso local dev server or better-sqlite3)
npm run dev

# Run migrations
npm run db:migrate

# Generate TypeScript types from schema
npm run db:generate-types

# Lint + format
npm run lint
npm run format

# Test
npm run test          # Vitest (unit + integration)
npm run test:e2e      # Playwright (optional)

# Build (production check)
npm run build
```

### Environment Variables

```bash
# .env.local (never commit)
DATABASE_URL=file:./dev.db          # better-sqlite3 (dev)
# or
TURSO_URL=libsql://...              # Turso (prod)
TURSO_AUTH_TOKEN=...

BETTER_AUTH_SECRET=...              # openssl rand -base64 32
BETTER_AUTH_URL=http://localhost:3000

STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

---

## Patterns to Follow

### Server Actions (Preferred Over API Routes)

```typescript
// src/core/users/actions.ts
'use server';

import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';
import { db } from '@/lib/db';
import { createUserSchema } from '@/lib/validations';

export async function createUser(prevState: any, formData: FormData) {
  const validated = createUserSchema.parse({
    email: formData.get('email'),
    name: formData.get('name'),
  });
  
  const user = db.prepare(`
    INSERT INTO users (email, name) 
    VALUES (?, ?) 
    RETURNING id
  `).get(validated.email, validated.name) as { id: string };
  
  revalidatePath('/dashboard/users');
  redirect(`/dashboard/users/${user.id}`);
}
```

### Error Handling

```typescript
// Always return structured errors from Server Actions
export async function createUser(prevState: any, formData: FormData) {
  try {
    const validated = createUserSchema.parse({...});
    // ... do work
    return { success: true, data: user };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { success: false, errors: error.flatten().fieldErrors };
    }
    return { success: false, errors: { _form: ['Something went wrong'] } };
  }
}
```

---

## Anti-Patterns to Avoid

```typescript
// 鉂?DON'T: Fetch data in Client Component
'use client';
useEffect(() => { fetch('/api/users').then(...) }, []);  // Use RSC instead

// 鉂?DON'T: Use `any`
const user: any = getData();  // Use types/database.ts instead

// 鉂?DON'T: Ignore error handling in Server Actions
export async function createUser(...) {
  db.prepare('...').run();  // What if it throws? Return error state!
}

// 鉂?DON'T: Put business logic in Route Handlers
// Route Handlers are for external APIs (webhooks, third-party integrations)
// Use Server Actions for first-party forms/data mutations

// 鉂?DON'T: Import `db.ts` in Client Components
// It only works on the server (better-sqlite3 is Node-only)
```

---

## Testing Strategy

```typescript
// src/core/users/queries.test.ts
import { describe, it, expect } from 'vitest';
import { db } from '@/lib/db';
import { getUserById } from './queries';

describe('getUserById', () => {
  it('returns user when found', () => {
    const user = getUserById('test-cuid');
    expect(user).toBeDefined();
    expect(user.email).toBe('test@example.com');
  });
  
  it('returns null when not found', () => {
    const user = getUserById('non-existent');
    expect(user).toBeNull();
  });
});
```

- Test **logic** (`src/core/*/queries.ts`, `src/lib/*`).
- Don't test **components** 鈥?they're just JSX.
- Use **Playwright** for E2E if needed (critical paths only: signup 鈫?create org 鈫?subscribe).

---

## How to Use This Document

1. Copy this file as `CLAUDE.md` in your project root.
2. Run `claude` in the project directory.
3. Claude will read this file and understand:
   - What stack you use and why
   - How to structure new features
   - What SQL patterns to follow
   - What to avoid
4. No need to explain your conventions 鈥?Claude already knows.

---

**Last updated:** 2025-01-01  
**Maintainer:** Your Team  
**License:** MIT (same as your project)
