# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Stack & Versions

```
Next.js: 15.x (App Router, React 19)
Database: SQLite via better-sqlite3 (sync) or @libsql/client (async/Turso)
ORM: Drizzle ORM (type-safe, SQL-like, lightweight)
Runtime: Node.js 20+ LTS
Package Manager: npm (lockfile v3)
TypeScript: 5.x (strict mode, no suppressions)
Styling: CSS Modules + Tailwind CSS 4.x utility classes
Auth: NextAuth.js v5 (Auth.js) with credentials or OAuth
Validation: Zod (schema-first, used everywhere)
Testing: Vitest + Playwright
Deployment: Vercel (Edge) or Node adapter for self-hosted
```

**Why Drizzle over Prisma?** Prisma generates a client that hides SQL. Drizzle gives you raw SQL power with type safety — you write SQL, you own SQL. For SQLite where every query counts, this matters.

**Why better-sqlite3 over libsql?** Synchronous queries work perfectly in Server Components and Route Handlers. No async overhead for simple CRUD. Use `@libsql/client` only if you need Turso remote replication.

---

## Folder Structure

```
/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (auth)/             # Auth route group (login, register, forgot-password)
│   │   ├── (dashboard)/        # Protected route group (requires session)
│   │   ├── api/                # API Route Handlers
│   │   │   ├── auth/[...nextauth]/  # NextAuth handlers
│   │   │   └── [resource]/     # RESTful API routes
│   │   ├── layout.tsx          # Root layout
│   │   └── page.tsx            # Landing/marketing page
│   ├── components/
│   │   ├── ui/                 # Primitive UI components (Button, Input, Card)
│   │   ├── forms/              # Form components with react-hook-form + zod
│   │   └── features/           # Feature-specific components
│   ├── lib/
│   │   ├── db/
│   │   │   ├── index.ts        # Database connection singleton
│   │   │   ├── schema.ts       # Drizzle schema (tables, relations)
│   │   │   └── migrations/     # SQL migration files
│   │   ├── auth.ts             # NextAuth configuration
│   │   ├── validators.ts       # Shared Zod schemas
│   │   └── utils.ts            # Utility functions
│   └── types/
│       └── index.ts            # Shared TypeScript types
├── public/                     # Static assets
├── drizzle/                    # Drizzle config (drizzle.config.ts)
├── tests/
│   ├── unit/                   # Vitest unit tests
│   └── e2e/                    # Playwright E2E tests
├── .env.local                  # Local env vars (NEVER commit)
├── .env.example                # Env var template (COMMIT this)
└── package.json
```

**Key conventions:**
- `src/` prefix — explicit source root, not everything is "src"
- Route groups `(auth)`, `(dashboard)` — no URL prefix, logical grouping only
- Feature folders `components/features/` — co-locate with the feature, not type
- `lib/db/` — db-only concerns live here, not in `utils/`

---

## SQL / Migration Conventions

### Schema Definition (Drizzle)

```typescript
// src/lib/db/schema.ts
import { sqliteTable, text, integer, real } from 'drizzle-orm/sqlite-core';

export const users = sqliteTable('users', {
  id: text('id').primaryKey(), // nanoid() — not auto-increment
  email: text('email').notNull().unique(),
  passwordHash: text('password_hash').notNull(),
  name: text('name'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull(),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull(),
});

export const sessions = sqliteTable('sessions', {
  id: text('id').primaryKey(),
  userId: text('user_id').notNull().references(() => users.id),
  expiresAt: integer('expires_at', { mode: 'timestamp' }).notNull(),
});
```

**Rules:**
- Use `text('id').primaryKey()` with `nanoid()` — never auto-increment. UUIDs create serialization issues; integer AI is fine for SQLite but nanoid plays better with distributed systems and URL-safe IDs.
- Always define `createdAt` and `updatedAt` as Unix timestamps (integer, mode: 'timestamp')
- Foreign keys are optional in SQLite — enforce referential integrity in application code, not DB constraints
- No `ON DELETE CASCADE` — handle deletions explicitly in application code

### Migration Workflow

```bash
# 1. Edit src/lib/db/schema.ts
# 2. Generate migration
npx drizzle-kit generate

# 3. Review the generated SQL in drizzle/migrations/
# 4. Apply to local DB
npx drizzle-kit migrate

# 5. Apply to production (run migrations before deploying new code)
npx drizzle-kit push  # for development only; use migrate for prod
```

**Migration rules:**
- Every migration must be reviewed before running — never auto-apply
- Never modify a migration after it's been applied to any environment
- If a migration is destructive, write a rollback migration alongside it
- Use `drizzle-kit push` for local dev, `drizzle-kit migrate` for staged/prod

### Query Patterns

```typescript
// ✅ CORRECT: Prepared statements, explicit columns
const db = getDb();
const result = db.select({
  id: users.id,
  email: users.email,
  name: users.name,
}).from(users).where(eq(users.id, userId));

// ✅ CORRECT: Transactions for multi-step writes
const db = getDb();
await db.transaction(async (tx) => {
  await tx.insert(sessions).values({ id: nanoid(), userId, expiresAt });
  await tx.update(users).set({ updatedAt: new Date() }).where(eq(users.id, userId));
});

// ❌ WRONG: Select *
const result = db.select().from(users).where(eq(users.id, userId));

// ❌ WRONG: String interpolation in queries
const result = db.raw(`SELECT * FROM users WHERE id = '${userId}'`);
```

---

## Component Patterns

### Server vs Client Components

```typescript
// ✅ Server Component (default) — for data fetching, SEO, static content
// src/app/(dashboard)/settings/page.tsx
export default async function SettingsPage() {
  const user = await getSession();
  // Direct DB access — no API call needed
  const profile = await db.select().from(users).where(eq(users.id, user.id));
  return <ProfileForm profile={profile} />;
}

// ✅ Client Component — for interactivity, useState, event handlers
// src/components/forms/ProfileForm.tsx
'use client';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { profileSchema } from '@/lib/validators';

export function ProfileForm({ profile }) {
  const form = useForm({ resolver: zodResolver(profileSchema), defaultValues: profile });
  // ...
}

// ❌ WRONG: Client Component importing Server Component
// ❌ WRONG: 'use client' at the top of a file that does only data fetching
```

**Rules:**
- Default to Server Components. Add `'use client'` only when you need browser APIs, event handlers, or state.
- Never import a Server Component into a Client Component
- Pass Server Component output to Client Components as props or children
- Use React Server Actions for form submissions instead of API routes when possible

### Form Components

```typescript
// src/components/forms/SignupForm.tsx
'use client';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { signupSchema } from '@/lib/validators';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { FormField, FormLabel, FormMessage } from '@/components/ui/Form';

export function SignupForm() {
  const form = useForm({ resolver: zodResolver(signupSchema) });

  async function onSubmit(data) {
    const res = await fetch('/api/auth/signup', { method: 'POST', body: JSON.stringify(data) });
    if (!res.ok) { form.setError('root', { message: await res.text() }); return; }
    router.push('/dashboard');
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      <FormField control={form.control} name="email">
        <FormLabel>Email</FormLabel>
        <Input {...form.register('email')} type="email" />
        <FormMessage />
      </FormField>
      <Button type="submit" loading={form.formState.isSubmitting}>Sign Up</Button>
    </form>
  );
}
```

**Rules:**
- Always use `react-hook-form` + `zod` for form validation
- Never use `useState` for form values — let react-hook-form own the state
- Display validation errors inline, per field
- Show a root-level error for API failures
- Disable submit button while `isSubmitting`

### API Route Handlers

```typescript
// src/app/api/users/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';
import { eq } from 'drizzle-orm';
import { userCreateSchema } from '@/lib/validators';
import { z } from 'zod';

export async function POST(req: NextRequest) {
  const body = await req.json();
  const parsed = userCreateSchema.safeParse(body);
  if (!parsed.success) return NextResponse.json(parsed.error, { status: 400 });

  const existing = await db.select().from(users).where(eq(users.email, parsed.data.email));
  if (existing.length) return NextResponse.json({ error: 'Email taken' }, { status: 409 });

  const [user] = await db.insert(users).values({ id: nanoid(), ...parsed.data }).returning();
  return NextResponse.json(user, { status: 201 });
}
```

**Rules:**
- Always validate request body with Zod before processing
- Return appropriate HTTP status codes: 201 created, 400 bad request, 401 unauthorized, 404 not found, 409 conflict, 500 server error
- Never expose internal error details in production responses
- Use `NextResponse.json()` for all responses — no `res.send()`

---

## Anti-Patterns to Avoid

### 1. No `any` types
```typescript
// ❌ WRONG
const data: any = fetchData();

// ✅ CORRECT
const data = z.array(userSchema).parse(await fetchData());
```

### 2. No inline styles
```typescript
// ❌ WRONG
<div style={{ padding: '1rem', color: 'red' }}>

// ✅ CORRECT
<div className={styles.card}>
```

### 3. No `console.log` in production code
```typescript
// ❌ WRONG
console.log('User:', user);

// ✅ CORRECT — use a proper logger
import { logger } from '@/lib/logger';
logger.info('User fetched', { userId: user.id });
```

### 4. No secrets in client-side code
```typescript
// ❌ WRONG — DATABASE_URL in browser bundle
const db = createClient(process.env.DATABASE_URL);

// ✅ CORRECT — db connection only in server code
// src/lib/db/index.ts (never imported in client components)
```

### 5. No magic numbers
```typescript
// ❌ WRONG
if (user.tokenCount > 1000) { ... }

// ✅ CORRECT
const FREE_TIER_TOKEN_LIMIT = 1000;
if (user.tokenCount > FREE_TIER_TOKEN_LIMIT) { ... }
```

### 6. No fetching in Client Components for initial data
```typescript
// ❌ WRONG — Client Component fetching its own initial data
'use client';
export function UserProfile() {
  const { data } = useSWR('/api/user');
  ...
}

// ✅ CORRECT — Pass data from Server Component
export default async function ProfilePage() {
  const user = await getSession();
  return <UserProfile user={user} />;
}
```

### 7. No database queries in Client Components
```typescript
// ❌ WRONG — DB access from browser
'use client';
const users = await db.select().from(users); // NEVER

// ✅ CORRECT — API route or Server Component only
```

### 8. No synchronous `localStorage` / `sessionStorage` in Server Components
```typescript
// ❌ WRONG
const token = localStorage.getItem('token'); // localStorage is not available on server

// ✅ CORRECT — use cookies for server-readable auth state
import { cookies } from 'next/headers';
const session = cookies().get('session');
```

---

## Dev Commands

```bash
# Install dependencies
npm install

# Database
npx drizzle-kit generate          # Generate migrations from schema changes
npx drizzle-kit migrate           # Apply migrations to database
npx drizzle-kit studio             # Visual DB editor (http://localhost:4983)
npx drizzle-kit push               # Push schema (dev only — overwrites!)
npx drizzle-kit check              # Verify migrations match schema

# Development
npm run dev                        # Next.js dev server (http://localhost:3000)
npm run build                      # Production build
npm run start                     # Start production server

# Code quality
npm run lint                      # ESLint
npm run typecheck                 # TypeScript (tsc --noEmit)
npm run format                     # Prettier format

# Testing
npm run test                       # Vitest unit tests
npm run test:watch                 # Watch mode
npm run test:e2e                   # Playwright E2E tests
npm run test:e2e:ui                # Playwright UI mode

# Deployment prep
npm run db:migrate:prod             # Run migrations on production DB
```

---

## Shared Zod Schemas (validate at boundary, reuse everywhere)

```typescript
// src/lib/validators.ts
import { z } from 'zod';

export const userCreateSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8).regex(/[A-Z]/, 'Must contain uppercase'),
  name: z.string().min(1).max(100).optional(),
});

export const userUpdateSchema = userCreateSchema.partial();

export const idSchema = z.string().min(1); // nanoid

// API request/response schemas
export const apiResponseSchema = z.object({
  data: z.unknown().optional(),
  error: z.string().optional(),
});
```

**Rule:** Define Zod schemas once in `src/lib/validators.ts`. Use them in:
- API route handlers (request validation)
- Form components (client-side validation)
- Test fixtures (factory function input validation)

---

## Environment Variables

```bash
# .env.example — commit this file
DATABASE_URL=file:./data/app.db
NEXTAUTH_SECRET=your-secret-here
NEXTAUTH_URL=http://localhost:3000

# .env.local — never commit, added by developer
DATABASE_URL=file:./data/app.db
NEXTAUTH_SECRET=generate-with-openssl-rand-base64-32
NEXTAUTH_URL=http://localhost:3000
```

**Rule:** All secrets go in `.env.local`. Use `.env.example` for template — must be committed.

---

## Testing Conventions

```typescript
// tests/unit/db.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';
import { eq } from 'drizzle-orm';

describe('User queries', () => {
  beforeEach(() => {
    // Reset DB to clean state
    db.delete(users).run();
  });

  it('creates a user with valid data', async () => {
    const [user] = await db.insert(users).values({
      id: nanoid(),
      email: 'test@example.com',
      passwordHash: await hash('Password123'),
    }).returning();
    expect(user.email).toBe('test@example.com');
  });
});
```

**Rules:**
- Use Vitest for unit tests, Playwright for E2E
- Test at the API boundary, not internal implementation details
- Never mock the database — use a test DB file (copy schema, run migrations)
- Coverage gate: minimum 80% for critical paths (auth, payments, data mutations)

---

## Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Files | kebab-case | `user-profile.tsx`, `api-helpers.ts` |
| Components | PascalCase | `UserProfile.tsx`, `DashboardLayout.tsx` |
| Functions | camelCase | `createUser`, `getUserByEmail` |
| DB Tables | snake_case (plural) | `users`, `user_sessions` |
| DB Columns | snake_case | `created_at`, `password_hash` |
| Variables | camelCase | `userId`, `isLoading` |
| Constants | SCREAMING_SNAKE | `MAX_RETRY_COUNT`, `FREE_TIER_LIMIT` |
| CSS Classes | kebab-case | `user-card`, `submit-button` |
| URL paths | kebab-case | `/api/users`, `/user-settings` |
| Env vars | SCREAMING_SNAKE | `DATABASE_URL`, `NEXTAUTH_SECRET` |
| Zod schemas | camelCase | `userCreateSchema`, `loginSchema` |
