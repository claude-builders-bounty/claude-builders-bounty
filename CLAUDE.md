# CLAUDE.md — Next.js 15 + SQLite SaaS Template

> Opinionated guide for building production-ready SaaS with Next.js 15 App Router and SQLite (better-sqlite3 or Turso).
> Every rule has a reason. Follow them unless you have a good excuse.

---

## Project Structure

```
├── app/                    # Next.js App Router pages (use folders, not flat routes)
│   ├── (auth)/             # Route group: auth pages (login, register, etc.)
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/        # Route group: authenticated pages
│   │   ├── layout.tsx      # Dashboard layout with sidebar
│   │   ├── page.tsx        # Dashboard home
│   │   └── settings/
│   ├── api/                # API routes only
│   │   └── [...path]/      # Catch-all for complex routes
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Marketing landing page
├── components/             # Shared React components
│   ├── ui/                 # Primitives (Button, Input, Card — shadcn/ui style)
│   ├── forms/              # Complex form components
│   └── layout/             # Shell components (Navbar, Sidebar, Footer)
├── lib/                    # Core business logic (zero React imports)
│   ├── db/                 # Database layer
│   │   ├── index.ts        # DB singleton (Connection to singleton pattern)
│   │   ├── schema.ts       # Drizzle schema definitions
│   │   └── migrations/     # Drizzle migration files
│   ├── auth/               # Auth utilities (session, password hashing)
│   └── services/           # Business logic (order processing, billing, etc.)
├── hooks/                  # Custom React hooks (useUser, useSubscription)
├── scripts/                # One-off scripts (seed, migrate, fix-data)
├── drizzle/                # Drizzle config and migration runner
└── drizzle.config.ts       # Drizzle configuration
```

**Why this structure?**
- Route groups `(auth)` and `(dashboard)` organize auth vs app pages without URL changes
- `lib/` has no React imports — pure TypeScript, easy to test
- `components/ui/` holds primitives; don't mix with business components

---

## Naming Conventions

### Files
- **Pages/Routes**: `kebab-case` — `app/dashboard/settings/page.tsx`
- **Components**: `PascalCase` — `UserProfileCard.tsx`
- **Utilities/Hooks**: `camelCase` — `useAuth.ts`, `formatCurrency.ts`
- **Config**: `kebab-case` — `drizzle.config.ts`, `next.config.js`
- **Database migrations**: `YYYYMMDDHHMMSS_description.sql`

### Variables & Functions
- Use descriptive names: `const userSubscription = ...` not `const sub = ...`
- Functions are verbs: `createUser()`, `generateInvoice()`, `cancelSubscription()`
- Boolean flags start with `is`, `has`, `should`: `isLoading`, `hasSubscription`, `shouldRedirect`
- Database columns: `snake_case` (SQLite convention)

### TypeScript Types
- Prefix with entity name: `UserRow`, `SubscriptionRow`, `InvoiceInsert`
- DTOs: `CreateUserDto`, `UpdateSubscriptionDto`
- API Response: `ApiResponse<T>`, `PaginatedResponse<T>`

**Why?**
- Consistency across team members
- IDE autocomplete is predictable
- Easy grep for specific patterns

---

## Database Migrations

### Rules

1. **Use Drizzle ORM** — Never write raw SQL for schema changes
2. **Migrations are sacred** — Treat migration files like source code
3. **Never mutate existing columns** — Create new ones, migrate, drop old
4. **Always add NOT NULL constraints in a separate migration** — After backfilling data
5. **Keep migrations small** — One logical change per migration

### Migration Workflow

```bash
# 1. Edit schema (lib/db/schema.ts)
# 2. Generate migration
npm run db:generate

# 3. Review the generated SQL in drizzle/migrations/
# 4. Apply to local DB
npm run db:migrate

# 5. If correct, commit the migration file
git add drizzle/migrations/
```

### Schema Rules

```typescript
// ✅ DO: Explicit defaults, clear relations
export const users = sqliteTable('users', {
  id: text('id').primaryKey(), // UUID, not auto-increment
  email: text('email').notNull().unique(),
  passwordHash: text('password_hash').notNull(),
  createdAt: integer('created_at', { mode: 'timestamp' })
    .notNull()
    .default(sql`CURRENT_TIMESTAMP`),
});

// ❌ DON'T: Ambiguous types, missing constraints
export const usersBad = sqliteTable('users', {
  id: integer('id').primaryKey(), // Auto-increment is an anti-pattern
  email: text('email'),           // Missing NOT NULL
  createdAt: text('created_at'),  // Should be timestamp
});
```

### Why UUID primary keys?
- Security: Can't enumerate users via `/api/users/1`, `/api/users/2`
- Merging data across environments is safe
- Distributed systems don't clash on auto-increment

### Why integer timestamps?
- SQLite doesn't have a native DATETIME type
- Store as Unix seconds (integer) — not ISO strings
- Easier to sort, compare, and index
- Use `sql\`CURRENT_TIMESTAMP\`` for DB-level defaults

---

## Dev Commands

```bash
# Development
npm run dev              # Start Next.js dev server (http://localhost:3000)
npm run build            # Production build
npm run start            # Start production server

# Database
npm run db:generate      # Generate Drizzle migration from schema changes
npm run db:migrate       # Apply pending migrations
npm run db:studio        # Open Drizzle Studio (visual DB explorer)
npm run db:seed          # Run seed script (dev only)

# Code Quality
npm run lint             # ESLint
npm run typecheck        # TypeScript type checking
npm run test             # Vitest unit tests

# Deployment
npm run db:push          # Push schema to Turso (development)
npm run db:deploy        # Deploy migrations to production Turso
```

**Environment Variables Required:**
```bash
# .env.local
DATABASE_URL=file:./local.db          # Local SQLite (better-sqlite3)
TURSO_DATABASE_URL=file:./prod.db     # Production SQLite
TURSO_AUTH_TOKEN=your-token-here      # Turso auth (production only)
```

---

## Patterns to Follow

### 1. Server Components by default
```typescript
// app/dashboard/page.tsx — Server Component (default)
// Can directly query DB, no client state needed
export default async function DashboardPage() {
  const user = await getServerUser();
  const subscription = await db.query.subscriptions.findFirst({
    where: eq(subscriptions.userId, user.id),
  });
  return <Dashboard subscription={subscription} />;
}
```

### 2. Client Components only when needed
```typescript
// components/SubscriptionBadge.tsx
'use client'; // Only add when you need useState, useEffect, or browser APIs

import { useSubscription } from '@/hooks/useSubscription';

export function SubscriptionBadge() {
  const { data, isLoading } = useSubscription();
  // ...
}
```

### 3. Async DB operations in Server Components
```typescript
// lib/db/index.ts — Connection singleton pattern
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';

const sqlite = new Database(process.env.DATABASE_URL!);
export const db = drizzle(sqlite);

// Usage in route handlers
export async function POST(request: Request) {
  const body = await request.json();
  const [user] = await db.insert(users).values(body).returning();
  return Response.json(user);
}
```

### 4. Validation with Zod
```typescript
import { z } from 'zod';

export const CreateUserSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  name: z.string().min(1).max(100),
});

export const UpdateSubscriptionSchema = z.object({
  tier: z.enum(['free', 'pro', 'enterprise']),
  billingCycle: z.enum(['monthly', 'annual']),
});

// In API route
const parsed = CreateUserSchema.safeParse(await request.json());
if (!parsed.success) {
  return Response.json({ error: parsed.error }, { status: 400 });
}
```

### 5. Secure password hashing
```typescript
import { hash, verify } from '@node-rs/argon2';

export async function hashPassword(password: string): Promise<string> {
  return hash(password, {
    memoryCost: 19456,
    timeCost: 2,
    parallelism: 1,
  });
}

export async function verifyPassword(hash: string, password: string): Promise<boolean> {
  return verify(hash, password);
}
```

### 6. API route structure
```typescript
// app/api/users/route.ts — Consistent structure
export async function GET(request: Request) {
  // Auth check
  const user = await getServerUser();
  if (!user) return Response.json({ error: 'Unauthorized' }, { status: 401 });

  // Query with pagination
  const url = new URL(request.url);
  const limit = Math.min(Number(url.searchParams.get('limit') ?? 20), 100);
  const offset = Number(url.searchParams.get('offset') ?? 0);

  const results = await db.query.users.findMany({
    where: eq(users.organizationId, user.organizationId),
    limit,
    offset,
  });

  return Response.json({ data: results, limit, offset });
}
```

---

## Anti-Patterns to Avoid

### ❌ Don't use `new Database()` in every request
```typescript
// ❌ BAD — Creates new connection per request
export async function GET() {
  const db = new Database('db.sqlite'); // Connection leak!
  const users = await db.select().from(usersTable);
}
```
```typescript
// ✅ GOOD — Singleton connection
import { db } from '@/lib/db';
export async function GET() {
  const users = await db.select().from(usersTable);
}
```

### ❌ Don't use `any` types in DB operations
```typescript
// ❌ BAD — Loses type safety
const user = await db.query.users.findFirst({ where: { id: params.id as any } });

// ✅ GOOD — Proper typing
const user = await db.query.users.findFirst({
  where: eq(users.id, params.id),
});
```

### ❌ Don't commit migration files blindly
```bash
# ❌ BAD — Ignored generated files
git add . && git commit -m "update"

# ✅ GOOD — Explicit about what changed
git add drizzle/migrations/00000000000000_new_migration.sql
```
Migrations can destroy data. Review them before committing.

### ❌ Don't use Server Actions for mutations that need validation
```typescript
// ❌ BAD — No input validation in Server Action
export async function updateUser(formData: FormData) {
  await db.update(users).set({ name: formData.get('name') });
}

// ✅ GOOD — Use Zod + API route for complex mutations
// Or validate in Server Action with Zod
export async function updateUser(formData: FormData) {
  const parsed = UpdateUserSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) throw new Error('Invalid input');
  await db.update(users).set(parsed.data);
}
```

### ❌ Don't store passwords in plain text
```typescript
// ❌ BAD — Plain text storage
await db.insert(users).values({ password: plainTextPassword });

// ✅ GOOD — Argon2 hashed
const hash = await hashPassword(plainTextPassword);
await db.insert(users).values({ passwordHash: hash });
```

### ❌ Don't use auto-increment IDs as public identifiers
```typescript
// ❌ BAD — Predictable IDs
const invoice = await db.insert(invoices).values({...});
return Response.json({ id: invoice.id }); // 1, 2, 3...

// ✅ GOOD — UUID-based public IDs
const invoice = await db.insert(invoices).values({
  id: crypto.randomUUID(),
  ...
});
```

### ❌ Don't run migrations on every deploy
```typescript
// ❌ BAD — Migrations in startup code
// app/layout.tsx
const { error } = await migrate(); // Every server start!

// ✅ GOOD — Migrations are part of deployment pipeline
// Run once during deployment, not at runtime
```

---

## Authentication Strategy

For Next.js + SQLite SaaS:

1. **Sessions via encrypted cookies** — No JWT, no external deps
2. **Password hashing via Argon2** — Not bcrypt/scrypt
3. **Rate limiting on auth endpoints** — Prevent brute force
4. **CSRF protection** — Next.js built-in for Server Actions

```typescript
// lib/auth/session.ts
import { cookies } from 'next/headers';

export async function getServerUser() {
  const sessionCookie = (await cookies()).get('session');
  if (!sessionCookie?.value) return null;

  const session = await decryptSession(sessionCookie.value);
  if (!session?.userId) return null;

  const user = await db.query.users.findFirst({
    where: eq(users.id, session.userId),
  });

  return user ?? null;
}
```

---

## Environment-Specific DB Configuration

### Local Development (better-sqlite3)
```typescript
// lib/db/index.ts
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';

const sqlite = new Database(process.env.DATABASE_URL!);
export const db = drizzle(sqlite);
```

### Production (Turso)
```typescript
// lib/db/index.ts — Runtime detection
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';

const sqlite = new Database(process.env.TURSO_DATABASE_URL!);
export const db = drizzle(sqlite);
```

> **Note**: better-sqlite3 is synchronous but SQLite only allows one writer at a time. Use write transactions for bulk operations.

---

## Testing Strategy

```typescript
// __tests__/lib/services/billing.test.ts
import { describe, it, expect } from 'vitest';
import { calculateProratedAmount } from '@/lib/services/billing';

describe('calculateProratedAmount', () => {
  it('handles mid-cycle upgrades correctly', () => {
    const result = calculateProratedAmount('pro', 'enterprise', 15, 30);
    expect(result).toBe(50); // Half month at enterprise rate
  });
});
```

- Test business logic in `lib/` — pure functions, easy to test
- Mock DB with `drizzle-mock` for integration tests
- E2E test critical flows (signup, checkout, cancel)

---

## Deployment Checklist

Before deploying:

- [ ] All migrations applied (`npm run db:migrate`)
- [ ] `TURSO_AUTH_TOKEN` set in production env
- [ ] `DATABASE_URL` points to production DB
- [ ] Passwords are hashed with Argon2 (not plain text)
- [ ] Auth endpoints rate-limited
- [ ] No `console.log` in production
- [ ] Environment variables validated at startup

---

## Why These Rules?

- **UUIDs** — Security through obscurity is bad, but predictable enumeration is worse
- **Drizzle over raw SQL** — Type safety prevents a whole class of runtime errors
- **Server Components default** — Reduces bundle size, better performance
- **Argon2 over bcrypt** — Better memory hardness, modern standard
- **No auto-increment IDs** — Predictable IDs are a security risk in public APIs

---

*This CLAUDE.md assumes Next.js 15, Drizzle ORM, better-sqlite3/Turso, and TypeScript. Adjust accordingly for other stacks.*