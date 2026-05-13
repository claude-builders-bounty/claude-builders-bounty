# CLAUDE.md — Next.js + SQLite SaaS Project

> Drop this file into the root of any greenfield Next.js 15 + SQLite project.
> Claude Code (or any coding agent) will understand your stack, conventions, and boundaries without asking questions.

---

## Stack & Versions

| Layer | Technology | Version | Why |
|-------|-----------|---------|-----|
| Framework | Next.js (App Router) | 15.x | Server Components, streaming, built-in API routes |
| Runtime | Node.js | 20 LTS | Stability, wide ecosystem |
| Language | TypeScript | 5.x | Type safety is non-negotiable |
| Database | SQLite via better-sqlite3 | 3.x | Zero-config, file-based, fast for SaaS scale |
| ORM | Drizzle ORM | 0.x | Type-safe queries, SQLite-first, lightweight |
| Auth | NextAuth.js v5 | 5.x-beta | App Router native, multi-provider |
| Styling | Tailwind CSS | 4.x | Utility-first, no runtime cost |
| Validation | Zod | 3.x | Runtime + compile-time validation |
| Testing | Vitest + Testing Library | latest | Fast, Vite-native |

**Package manager**: pnpm (strict, fast, disk-efficient).

```bash
# Core commands
pnpm dev          # Start dev server (port 3000)
pnpm build        # Production build
pnpm start        # Serve production build
pnpm lint         # ESLint + TypeScript check
pnpm test         # Run tests
pnpm test:watch   # Watch mode
pnpm db:generate  # Generate migration files from schema
pnpm db:migrate   # Apply pending migrations
pnpm db:studio    # Open Drizzle Studio (DB GUI)
```

---

## Folder Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Auth route group (login, register)
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/       # Protected route group
│   │   ├── layout.tsx     # Dashboard shell (sidebar, header)
│   │   ├── page.tsx       # /dashboard
│   │   ├── settings/
│   │   └── [resource]/    # Dynamic resource CRUD pages
│   ├── api/               # API route handlers
│   │   └── [resource]/
│   │       ├── route.ts   # GET (list), POST (create)
│   │       └── [id]/
│   │           └── route.ts  # GET, PATCH, DELETE
│   ├── layout.tsx         # Root layout (html, body, providers)
│   ├── page.tsx           # Landing/redirect
│   └── globals.css
├── components/
│   ├── ui/                # Primitive UI (Button, Input, Dialog, etc.)
│   └── features/          # Domain-specific composites
│       └── [resource]/
│           ├── table.tsx
│           ├── form.tsx
│           └── detail.tsx
├── lib/
│   ├── db/
│   │   ├── index.ts       # Database connection singleton
│   │   ├── schema.ts      # Drizzle table definitions
│   │   └── migrations/    # Generated SQL migration files
│   ├── auth/
│   │   ├── config.ts      # NextAuth configuration
│   │   └── session.ts     # Session helpers
│   ├── validations/       # Zod schemas (one per resource)
│   └── utils.ts           # Shared utilities (cn, formatDate, etc.)
├── server/
│   ├── queries/           # Data access layer (one file per resource)
│   │   └── [resource].ts  # CRUD functions, accept Drizzle instance
│   └── actions/           # Next.js Server Actions
│       └── [resource].ts  # Mutations with revalidation
├── hooks/                 # Client-side React hooks
├── types/                 # Shared TypeScript types
│   └── index.ts           # Re-export from schema + custom types
└── constants.ts           # App-wide constants
```

### Rules

1. **Every route has a `page.tsx`**. No例外。
2. **Server Components by default**. Only add `"use client"` when you need browser APIs or React hooks (useState, useEffect, etc.).
3. **One file per concern**. A component file does one thing. If it grows past 150 lines, split it.
4. **Colocate related files**. Keep forms, tables, and detail views for a resource in `components/features/[resource]/`.
5. **Never import from `app/` into `lib/` or `server/`**. Dependency direction: `app/` → `components/` → `lib/` → `server/`. Never the reverse.

---

## Database & Migrations

### Schema Definition

All tables are defined in `src/lib/db/schema.ts` using Drizzle's `sqliteTable`.

```typescript
// src/lib/db/schema.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const users = sqliteTable('users', {
  id: text('id').primaryKey(),           // nanoid, NOT auto-increment
  email: text('email').notNull().unique(),
  name: text('name'),
  createdAt: integer('created_at', { mode: 'timestamp' })
    .notNull().default(sql`(unixepoch())`),
});
```

### Conventions

1. **Primary keys**: `text` type, use `nanoid()` (not UUID, not auto-increment). Shorter, URL-safe, sortable.
2. **Timestamps**: Always `integer` with `mode: 'timestamp'`. Store as Unix epoch seconds. Column names: `created_at`, `updated_at`.
3. **Foreign keys**: Always `text` type referencing the parent's `id`. Name them `[parent]_id`.
4. **Soft delete**: Add `deleted_at integer` column. Filter with `isNull(deleted_at)` in queries. Never hard-delete user data.
5. **Boolean fields**: Use `integer` with `mode: 'boolean'` (SQLite has no native boolean).

### Migration Workflow

```bash
# 1. Edit src/lib/db/schema.ts
# 2. Generate migration
pnpm db:generate
# 3. Review the generated SQL in src/lib/db/migrations/
# 4. Apply
pnpm db:migrate
```

**Never edit migration files after they've been committed.** If the migration is wrong, generate a new one that fixes it.

### Query Patterns

```typescript
// src/server/queries/users.ts
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';
import { eq } from 'drizzle-orm';

// All queries go through the db singleton.
// Never import drizzle in page components.

export function getUserById(id: string) {
  return db.query.users.findFirst({
    where: eq(users.id, id),
  });
}

export function createUser(data: NewUser) {
  return db.insert(users).values(data).returning();
}
```

**Rule**: Data access lives in `server/queries/`. API routes and Server Actions call these functions. Never write raw SQL in route handlers.

---

## API Routes

### Pattern

Every resource gets a folder under `app/api/`:

```
app/api/users/
├── route.ts          # GET /api/users (list), POST /api/users (create)
└── [id]/
    └── route.ts      # GET, PATCH, DELETE /api/users/:id
```

### Handler Structure

```typescript
// app/api/users/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { createUser, listUsers } from '@/server/queries/users';
import { createUserSchema } from '@/lib/validations/users';

export async function GET(req: NextRequest) {
  const users = await listUsers();
  return NextResponse.json(users);
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const parsed = createUserSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json(
      { error: 'Validation failed', issues: parsed.error.issues },
      { status: 400 }
    );
  }

  const user = await createUser(parsed.data);
  return NextResponse.json(user, { status: 201 });
}
```

### Rules

1. **Always validate input with Zod** before touching the database. The schema lives in `lib/validations/`.
2. **Return proper HTTP status codes**: 200 (OK), 201 (Created), 400 (Validation), 401 (Auth), 403 (Forbidden), 404 (Not Found), 500 (Server Error).
3. **Never catch and swallow errors silently**. Use `console.error` + return 500.
4. **No business logic in route handlers**. Call `server/queries/` functions.

---

## Server Actions

Use Server Actions for mutations triggered from forms. Keep them in `server/actions/`.

```typescript
// server/actions/users.ts
'use server';

import { revalidatePath } from 'next/cache';
import { createUser } from '@/server/queries/users';
import { createUserSchema } from '@/lib/validations/users';

export async function createUserAction(formData: FormData) {
  const raw = Object.fromEntries(formData);
  const parsed = createUserSchema.safeParse(raw);

  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors };
  }

  await createUser(parsed.data);
  revalidatePath('/dashboard/users');
  return { success: true };
}
```

### Rules

1. **Always `'use server'`** at the top of the file.
2. **Always validate with Zod** before mutating.
3. **Always call `revalidatePath`** after mutations so the UI updates.
4. **Return `{ success: true }` or `{ error: ... }`** — never throw.

---

## Components

### UI Primitives (`components/ui/`)

These are generic, stateless, reusable components. They have **no knowledge of business logic or data models**.

Examples: `Button`, `Input`, `Select`, `Dialog`, `Table`, `Badge`, `Card`.

Pattern:
```typescript
// components/ui/button.tsx
import { cn } from '@/lib/utils';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
}

export function Button({ variant = 'primary', size = 'md', className, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        'rounded-md font-medium transition-colors',
        variant === 'primary' && 'bg-blue-600 text-white hover:bg-blue-700',
        variant === 'secondary' && 'bg-gray-200 text-gray-800 hover:bg-gray-300',
        variant === 'danger' && 'bg-red-600 text-white hover:bg-red-700',
        size === 'sm' && 'px-3 py-1 text-sm',
        size === 'md' && 'px-4 py-2',
        size === 'lg' && 'px-6 py-3 text-lg',
        className
      )}
      {...props}
    />
  );
}
```

### Feature Components (`components/features/`)

These know about business data. They import types from `types/` and call Server Actions or API routes.

```typescript
// components/features/users/user-form.tsx
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { createUserAction } from '@/server/actions/users';

export function UserForm() {
  const [loading, setLoading] = useState(false);

  async function handleSubmit(formData: FormData) {
    setLoading(true);
    await createUserAction(formData);
    setLoading(false);
  }

  return (
    <form action={handleSubmit}>
      <Input name="name" placeholder="Name" required />
      <Input name="email" type="email" placeholder="Email" required />
      <Button type="submit" disabled={loading}>
        {loading ? 'Creating...' : 'Create User'}
      </Button>
    </form>
  );
}
```

---

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Files | kebab-case | `user-form.tsx`, `create-user.ts` |
| Directories | kebab-case | `api/users/`, `components/features/` |
| React components | PascalCase | `UserForm`, `DashboardLayout` |
| Functions | camelCase | `getUserById`, `createUser` |
| Database tables | snake_case, plural | `users`, `projects`, `api_keys` |
| Database columns | snake_case | `created_at`, `user_id` |
| Types/Interfaces | PascalCase | `User`, `CreateUserInput` |
| Zod schemas | camelCase + Schema | `createUserSchema`, `updateProjectSchema` |
| Constants | SCREAMING_SNAKE | `MAX_PAGE_SIZE`, `DEFAULT_TIMEOUT` |
| API routes | lowercase, plural | `/api/users`, `/api/projects` |
| Server actions | camelCase + Action | `createUserAction`, `deleteProjectAction` |
| CSS classes | Tailwind utilities only | No custom class names |

---

## Authentication & Authorization

### Setup

Auth is handled by NextAuth.js v5 with the Credentials provider as default.

```typescript
// lib/auth/config.ts
import NextAuth from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import { verifyPassword } from '@/lib/auth/password';

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Credentials({
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        const user = await getUserByEmail(credentials.email as string);
        if (!user) return null;
        const valid = await verifyPassword(credentials.password as string, user.passwordHash);
        if (!valid) return null;
        return { id: user.id, email: user.email, name: user.name };
      },
    }),
  ],
  pages: {
    signIn: '/login',
  },
});
```

### Rules

1. **Protect routes** using `auth()` in Server Components and middleware.
2. **Never store plaintext passwords**. Use `bcryptjs` with salt rounds of 12.
3. **Session is available via `auth()`** in Server Components and `useSession()` in Client Components.
4. **API routes must check auth**. Every `/api/` route (except `/api/auth/*`) must call `auth()` and return 401 if no session.

---

## What We Don't Do (and Why)

| Anti-pattern | Why we avoid it |
|-------------|----------------|
| **No Prisma** | Prisma adds ~30MB to node_modules and has poor SQLite migration ergonomics. Drizzle is lighter and generates plain SQL. |
| **No Redux/Zustand** | Server Components + Server Actions eliminate most client state. Use React's built-in `useState` for the rest. |
| **No `getServerSideProps` or `getStaticProps`** | Those are Pages Router patterns. We use App Router: `async function` in Server Components. |
| **No raw SQL in components** | All queries go through `server/queries/`. Components don't know about the database. |
| **No environment variables without `NEXT_PUBLIC_` prefix for client** | Next.js enforces this. Server-only vars (DB path, secrets) have no prefix. |
| **No `.env` committed to git** | Use `.env.example` with placeholder values. Real `.env` is gitignored. |
| **No `any` type** | If you need flexibility, use `unknown` and narrow with type guards. |
| **No barrel files (`index.ts` that re-exports everything)** | They break tree-shaking and make imports opaque. Import directly from the source file. |
| **No `console.log` in production code** | Use a logger or remove before commit. |
| **No CSS modules or styled-components** | Tailwind only. One styling system. No exceptions. |
| **No client-side data fetching with `useEffect`** | Use Server Components for data. If you must fetch on the client, use `use()` or SWR — never raw `useEffect` + `fetch`. |
| **No dynamic ORM queries built from user input** | Always use parameterized queries via Drizzle. Never concatenate strings into SQL. |

---

## Error Handling

```typescript
// Server-side: Return Result objects, don't throw
type Result<T> = { ok: true; data: T } | { ok: false; error: string };

export async function createUser(data: NewUser): Promise<Result<User>> {
  try {
    const user = await db.insert(users).values(data).returning();
    return { ok: true, data: user[0] };
  } catch (err) {
    if (err instanceof DatabaseError && err.code === 'SQLITE_CONSTRAINT_UNIQUE') {
      return { ok: false, error: 'Email already exists' };
    }
    console.error('Failed to create user:', err);
    return { ok: false, error: 'Internal server error' };
  }
}
```

### Rules
1. **Never throw in server functions**. Return `Result<T>` types.
2. **Client components handle errors in the UI**. Show toast or inline error message.
3. **Log server errors with context** (function name, input summary, error message).

---

## Testing

### What to test
- **Server logic**: `server/queries/` functions (CRUD operations)
- **Validation**: Zod schema edge cases
- **API routes**: Request → Response with mocked DB

### What NOT to test
- UI components (too brittle, low value)
- Drizzle ORM itself (it's tested by the library)
- Next.js framework features (routing, rendering)

### Pattern

```typescript
// __tests__/server/queries/users.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { createUser, getUserById } from '@/server/queries/users';
import { testDb } from '@/lib/db/test-helper';

describe('users queries', () => {
  beforeEach(async () => {
    await testDb.delete(users);
  });

  it('creates and retrieves a user', async () => {
    const result = await createUser({ id: 'test_1', email: 'a@b.com', name: 'Test' });
    expect(result.ok).toBe(true);

    const user = await getUserById('test_1');
    expect(user?.email).toBe('a@b.com');
  });
});
```

---

## Git Conventions

- **Branch naming**: `feat/add-users`, `fix/login-redirect`, `chore/update-deps`
- **Commit messages**: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`)
- **PR size**: Aim for <300 lines changed. If bigger, split the PR.
- **Never commit directly to `main`**. Always use a branch + PR.

---

## Quick Reference: Adding a New Resource

When adding a new resource (e.g., "projects"), follow this checklist:

1. **Schema**: Add table to `src/lib/db/schema.ts`
2. **Migrate**: Run `pnpm db:generate` → review → `pnpm db:migrate`
3. **Types**: Add Zod schemas to `src/lib/validations/projects.ts`
4. **Queries**: Create `src/server/queries/projects.ts` (CRUD functions)
5. **API routes**: Create `src/app/api/projects/route.ts` and `src/app/api/projects/[id]/route.ts`
6. **Server Actions**: Create `src/server/actions/projects.ts` (optional, for form mutations)
7. **Components**: Create `src/components/features/projects/` (table, form, detail)
8. **Pages**: Create `src/app/(dashboard)/projects/page.tsx` and sub-pages
9. **Navigation**: Add to sidebar/menu in dashboard layout

---

*This file is the single source of truth for project conventions. When in doubt, read this first. When something is unclear, update this file to make it clear for next time.*
