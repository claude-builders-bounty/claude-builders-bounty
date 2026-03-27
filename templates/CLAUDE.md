# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> Opinionated project context for AI assistants (Claude Code, Cursor, etc.)
> Version: 1.0.0 | Updated: 2026-03-27

---

## 📦 Stack & Versions

| Component | Version | Notes |
|-----------|---------|-------|
| Node.js | ≥20.x | Use LTS |
| Next.js | 15.x | App Router only |
| React | 19.x | Server Components preferred |
| SQLite | better-sqlite3 or Turso | Local = better-sqlite3, Prod = Turso |
| TypeScript | 5.x | Strict mode enabled |
| Tailwind CSS | 4.x | Utility-first |
| Drizzle ORM | Latest | Type-safe SQL |

### Package Manager
- **Use**: `pnpm` (preferred) or `npm`
- **Never**: `yarn` (conflicts with lockfiles)

---

## 📁 Folder Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Auth route group
│   │   ├── login/
│   │   ├── register/
│   │   └── layout.tsx
│   ├── (dashboard)/       # Protected routes
│   │   ├── dashboard/
│   │   ├── settings/
│   │   └── layout.tsx
│   ├── api/               # API routes
│   │   ├── auth/
│   │   ├── users/
│   │   └── webhooks/
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Landing page
│
├── components/
│   ├── ui/                # Base UI components (shadcn-style)
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   └── dialog.tsx
│   ├── forms/             # Form components
│   ├── layouts/           # Layout components
│   └── features/          # Feature-specific components
│
├── lib/
│   ├── db/                # Database layer
│   │   ├── schema.ts      # Drizzle schema
│   │   ├── migrations/    # SQL migrations
│   │   └── index.ts       # DB client
│   ├── auth/              # Auth utilities
│   ├── api/               # API helpers
│   └── utils.ts           # Shared utilities
│
├── hooks/                 # Custom React hooks
├── types/                 # TypeScript types
│   ├── api.ts
│   └── models.ts
│
└── styles/
    └── globals.css

tests/
├── unit/                  # Vitest unit tests
├── e2e/                   # Playwright E2E tests
└── setup.ts

drizzle.config.ts
next.config.ts
tsconfig.json
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Components | PascalCase | `UserCard.tsx` |
| Hooks | camelCase + `use` prefix | `useCurrentUser.ts` |
| Utils | camelCase | `formatDate.ts` |
| API routes | kebab-case | `/api/user-profiles/` |
| DB tables | snake_case | `user_profiles` |
| DB columns | snake_case | `created_at` |
| Types/Interfaces | PascalCase | `UserProfile`, `ApiResponse` |
| Constants | SCREAMING_SNAKE | `MAX_RETRIES` |
| Env vars | NEXT_PUBLIC_ prefix | `NEXT_PUBLIC_API_URL` |

---

## 🗄️ Database Conventions

### Schema Definition (Drizzle)

```typescript
// lib/db/schema.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core'

export const users = sqliteTable('users', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  email: text('email').notNull().unique(),
  name: text('name').notNull(),
  createdAt: integer('created_at', { mode: 'timestamp' }).$defaultFn(() => new Date()),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).$defaultFn(() => new Date()),
})

export const userProfiles = sqliteTable('user_profiles', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  userId: integer('user_id').references(() => users.id, { onDelete: 'cascade' }),
  bio: text('bio'),
  avatar: text('avatar'),
  createdAt: integer('created_at', { mode: 'timestamp' }).$defaultFn(() => new Date()),
})
```

### Migration Rules

1. **Always use migrations** — Never modify schema without migration
2. **One change per migration** — Atomic, reversible
3. **Name format**: `NNNN_description.sql` (e.g., `0001_add_users_table.sql`)
4. **Always include rollback** — Down migration required

```sql
-- Migration: 0001_add_users_table
-- Up
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  created_at INTEGER DEFAULT (strftime('%s', 'now')),
  updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- Down
DROP TABLE users;
```

### Query Patterns

```typescript
// ✅ Good: Use Drizzle ORM
import { db } from '@/lib/db'
import { users } from '@/lib/db/schema'
import { eq } from 'drizzle-orm'

const user = await db.select().from(users).where(eq(users.email, email))

// ❌ Bad: Raw SQL (unless absolutely necessary)
const user = await db.execute(sql`SELECT * FROM users WHERE email = ${email}`)
```

### Timestamps

- SQLite stores timestamps as Unix epoch (integer seconds)
- Always use `{ mode: 'timestamp' }` in Drizzle for JS Date objects
- Use `$defaultFn(() => new Date())` for auto-population

---

## ⚛️ Component Patterns

### Server Components (Default)

```typescript
// ✅ Good: Server Component (default)
// app/(dashboard)/dashboard/page.tsx
import { db } from '@/lib/db'
import { users } from '@/lib/db/schema'

export default async function DashboardPage() {
  const allUsers = await db.select().from(users)
  
  return (
    <div>
      <h1>Dashboard</h1>
      <UserList users={allUsers} />
    </div>
  )
}
```

### Client Components (When Needed)

```typescript
// ✅ Good: Client Component for interactivity
// components/features/UserList.tsx
'use client'

import { useState } from 'react'

export function UserList({ users }: { users: User[] }) {
  const [filter, setFilter] = useState('')
  const filtered = users.filter(u => u.name.includes(filter))
  
  return (
    <div>
      <input 
        value={filter} 
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Filter users..."
      />
      <ul>
        {filtered.map(user => (
          <li key={user.id}>{user.name}</li>
        ))}
      </ul>
    </div>
  )
}
```

### When to Use Client Components

| Use Client | Use Server |
|------------|------------|
| `useState`, `useEffect` | Data fetching |
| Event handlers | Direct DB access |
| Browser APIs | Secret keys |
| Third-party UI libs | Initial render |

### Component Organization

```typescript
// ✅ Good: Feature-based organization
// components/features/user/UserCard.tsx
// components/features/user/UserList.tsx
// components/features/user/UserForm.tsx

// ❌ Bad: Flat structure
// components/UserCard.tsx
// components/UserList.tsx
// components/Everything.tsx
```

---

## 🚫 What We Don't Do (And Why)

### No Redux/Zustand/Jotai
**Why**: React Server Components + URL state is sufficient for most SaaS apps.
**Alternative**: Use URL search params for filters, Server Actions for mutations.

### No Client-Side Data Fetching (Unless Necessary)
**Why**: Server Components can fetch directly, eliminating loading states and waterfalls.
**Alternative**: Fetch in Server Component, pass as props.

### No `useEffect` for Data Fetching
**Why**: Causes waterfalls, loading flickers, and hydration issues.
**Alternative**: Server Components, or SWR/React Query if client-side is required.

### No `any` Types
**Why**: Defeats the purpose of TypeScript.
**Alternative**: Use `unknown` and type guards, or define proper types.

### No `.env` in Client Bundles
**Why**: Exposes secrets to browser.
**Alternative**: Use `NEXT_PUBLIC_` prefix only for truly public values.

### No ORM Magic Strings
**Why**: Breaks TypeScript safety.
**Alternative**: Use Drizzle's type-safe query builder.

### No Custom Auth (Unless You're Building Auth)
**Why**: Security is hard; use battle-tested solutions.
**Alternative**: Clerk, Auth.js, Supabase Auth, or Lucia.

---

## 🛠️ Dev Commands

```bash
# Development
pnpm dev                 # Start dev server (port 3000)
pnpm build              # Production build
pnpm start              # Start production server
pnpm lint               # Run ESLint
pnpm typecheck          # TypeScript check

# Database
pnpm db:generate        # Generate Drizzle migrations
pnpm db:migrate         # Run migrations
pnpm db:push            # Push schema (dev only!)
pnpm db:studio          # Open Drizzle Studio

# Testing
pnpm test               # Run unit tests (Vitest)
pnpm test:e2e           # Run E2E tests (Playwright)
pnpm test:coverage      # Coverage report

# Misc
pnpm format             # Format with Prettier
pnpm clean              # Remove .next, node_modules
```

---

## 📐 API Route Patterns

### Standard Response Format

```typescript
// lib/api/response.ts
import { NextResponse } from 'next/server'

export function success<T>(data: T, status = 200) {
  return NextResponse.json({ success: true, data }, { status })
}

export function error(message: string, status = 400, code?: string) {
  return NextResponse.json(
    { success: false, error: { message, code } },
    { status }
  )
}
```

### Route Handler Example

```typescript
// app/api/users/route.ts
import { success, error } from '@/lib/api/response'
import { db } from '@/lib/db'
import { users } from '@/lib/db/schema'
import { z } from 'zod'

const createUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1),
})

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { email, name } = createUserSchema.parse(body)
    
    const [user] = await db.insert(users).values({ email, name }).returning()
    
    return success(user, 201)
  } catch (e) {
    if (e instanceof z.ZodError) {
      return error('Invalid input', 400, 'VALIDATION_ERROR')
    }
    return error('Internal server error', 500)
  }
}
```

---

## 🔐 Auth Pattern

### Server-Side Session Check

```typescript
// lib/auth/session.ts
import { cookies } from 'next/headers'
import { db } from '@/lib/db'
import { sessions, users } from '@/lib/db/schema'
import { eq } from 'drizzle-orm'

export async function getCurrentUser() {
  const cookieStore = await cookies()
  const sessionToken = cookieStore.get('session_token')?.value
  
  if (!sessionToken) return null
  
  const [session] = await db
    .select()
    .from(sessions)
    .where(eq(sessions.token, sessionToken))
    .innerJoin(users, eq(sessions.userId, users.id))
  
  if (!session || session.sessions.expiresAt < new Date()) {
    return null
  }
  
  return session.users
}
```

### Protected Route Group

```typescript
// app/(dashboard)/layout.tsx
import { redirect } from 'next/navigation'
import { getCurrentUser } from '@/lib/auth/session'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const user = await getCurrentUser()
  
  if (!user) {
    redirect('/login')
  }
  
  return (
    <div className="flex">
      <Sidebar user={user} />
      <main>{children}</main>
    </div>
  )
}
```

---

## 🧪 Testing Patterns

### Unit Tests (Vitest)

```typescript
// tests/unit/lib/utils.test.ts
import { describe, it, expect } from 'vitest'
import { formatDate } from '@/lib/utils'

describe('formatDate', () => {
  it('formats ISO date correctly', () => {
    const date = '2026-03-27T12:00:00Z'
    expect(formatDate(date)).toBe('March 27, 2026')
  })
})
```

### E2E Tests (Playwright)

```typescript
// tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test'

test('user can login', async ({ page }) => {
  await page.goto('/login')
  await page.fill('input[name="email"]', 'test@example.com')
  await page.fill('input[name="password"]', 'password123')
  await page.click('button[type="submit"]')
  
  await expect(page).toHaveURL('/dashboard')
})
```

---

## 📋 Pre-Commit Checklist

Before every commit, ensure:

- [ ] `pnpm typecheck` passes
- [ ] `pnpm lint` shows no errors
- [ ] `pnpm test` passes
- [ ] No `console.log` in production code
- [ ] No hardcoded values (use env vars)
- [ ] No `.env` committed (use `.env.example`)
- [ ] Migration files included if schema changed

---

## 🎯 AI Assistant Guidelines

When working with Claude or other AI assistants on this codebase:

1. **Always check existing patterns** before suggesting new ones
2. **Prefer Server Components** unless interactivity requires client
3. **Use Drizzle ORM** for all database operations
4. **Follow the folder structure** strictly
5. **Keep components small** (<200 lines)
6. **Write tests** for utility functions and API routes
7. **Update this file** if conventions change

---

## 📚 References

- [Next.js 15 Docs](https://nextjs.org/docs)
- [Drizzle ORM](https://orm.drizzle.team/docs/overview)
- [SQLite Functions](https://www.sqlite.org/lang_corefunc.html)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Zod Validation](https://zod.dev/)

---

*This file is designed to be dropped into any Next.js 15 + SQLite SaaS project without modification. Claude Code should understand the context immediately without asking clarifying questions.*