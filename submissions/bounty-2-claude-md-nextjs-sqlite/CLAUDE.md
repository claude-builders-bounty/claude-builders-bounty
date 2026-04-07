# CLAUDE.md

> Opinionated conventions for Next.js 15 + SQLite SaaS projects
> Version: 1.0.0 | Last updated: 2026-03-29

---

## Stack Overview

| Category | Technology | Version | Reason |
|----------|------------|---------|--------|
| Framework | Next.js | 15.x | App Router, Server Components, optimal DX |
| Language | TypeScript | 5.x | Type safety without runtime overhead |
| Database | SQLite | 3.x | better-sqlite3 for sync, zero config, file-based |
| ORM/Query | Drizzle ORM | 0.30+ | Type-safe SQL, lightweight, migrations built-in |
| Styling | Tailwind CSS | 3.x | Utility-first, no CSS-in-JS runtime |
| UI Components | shadcn/ui | latest | Accessible, customizable, no bloat |
| Auth | Lucia Auth | 3.x | Lightweight, session-based, type-safe |
| Validation | Zod | 3.x | Runtime validation, inferred types |

**Why this stack?**
- SQLite: Single file, zero setup, perfect for SaaS MVP to scale
- Drizzle: Write SQL with type safety, not an abstraction layer
- App Router: Server-first, less client JS, better performance

---

## Project Structure

```
my-saas/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Route groups for auth pages
│   │   ├── login/
│   │   ├── register/
│   │   └── layout.tsx     # Auth layout (no nav)
│   ├── (dashboard)/       # Route group for app
│   │   ├── dashboard/
│   │   ├── settings/
│   │   └── layout.tsx     # Dashboard layout (with nav)
│   ├── api/               # API routes (minimal, prefer Server Actions)
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Landing page
├── components/
│   ├── ui/                # shadcn/ui components (auto-generated)
│   ├── forms/             # Form components with validation
│   ├── layout/            # Layout components (Header, Sidebar, etc.)
│   └── features/          # Feature-specific components
├── lib/
│   ├── db/                # Database layer
│   │   ├── schema.ts      # Drizzle schema definitions
│   │   ├── migrations/    # Generated migrations
│   │   └── index.ts       # DB connection & queries
│   ├── auth/              # Auth utilities
│   ├── utils.ts           # General utilities
│   └── validations/       # Zod schemas
├── hooks/                 # Custom React hooks
├── types/                 # Global TypeScript types
├── public/                # Static assets
├── scripts/               # Build/deployment scripts
├── tests/                 # Test files
├── drizzle.config.ts      # Drizzle configuration
├── next.config.js
├── tailwind.config.ts
└── CLAUDE.md              # This file
```

---

## Naming Conventions

### Files

| Type | Pattern | Example |
|------|---------|---------|
| Components | PascalCase | `UserCard.tsx`, `LoginForm.tsx` |
| Utilities | camelCase | `formatDate.ts`, `cn.ts` |
| Server Actions | camelCase + Action suffix | `createUserAction.ts` |
| API Routes | kebab-case | `route.ts` (inside folder) |
| Database | snake_case in SQL | `user_sessions`, `created_at` |
| Constants | UPPER_SNAKE_CASE | `MAX_UPLOAD_SIZE` |

### Database Tables

- **Singular nouns**: `user`, `organization`, `subscription`
- **Join tables**: `user_organization` (alphabetical order)
- **Timestamps**: Always `created_at`, `updated_at`
- **Soft delete**: `deleted_at` (nullable) instead of hard delete
- **Foreign keys**: `user_id` references `user(id)`

### Components

```tsx
// ✅ Good: Descriptive, single responsibility
function UserProfileCard({ user }: { user: User }) {
  return <div>...</div>
}

// ❌ Bad: Vague, does too much
function Card({ data }) {
  return <div>...</div>
}
```

---

## Database Conventions

### Schema Definition (Drizzle)

```typescript
// lib/db/schema.ts
import { sqliteTable, text, integer, real } from 'drizzle-orm/sqlite-core'
import { sql } from 'drizzle-orm'

// Always export types
export const user = sqliteTable('user', {
  id: text('id').primaryKey(), // ULID or nanoid, never auto-increment
  email: text('email').notNull().unique(),
  name: text('name').notNull(),
  role: text('role', { enum: ['admin', 'user'] }).notNull().default('user'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().default(sql`(unixepoch())`),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull().default(sql`(unixepoch())`),
})

// Export types for type safety
export type User = typeof user.$inferSelect
export type NewUser = typeof user.$inferInsert
```

### Migration Rules

1. **Never modify existing migrations** — create new ones
2. **One migration per logical change** — not per table
3. **Always test migrations** on a copy of production data
4. **Naming**: `0000_init.sql`, `0001_add_user_role.sql`

```bash
# Generate migration
npx drizzle-kit generate

# Apply migration
npx drizzle-kit migrate

# Check pending migrations
npx drizzle-kit check
```

### Query Patterns

```typescript
// lib/db/index.ts
import { drizzle } from 'drizzle-orm/better-sqlite3'
import Database from 'better-sqlite3'
import * as schema from './schema'

const sqlite = new Database('sqlite.db')
export const db = drizzle(sqlite, { schema })

// Queries live here
export async function getUserByEmail(email: string) {
  return db.query.user.findFirst({
    where: (user, { eq }) => eq(user.email, email)
  })
}

export async function createUser(data: NewUser) {
  return db.insert(schema.user).values(data).returning()
}
```

---

## Component Patterns

### Server Components (Default)

```tsx
// app/dashboard/page.tsx
import { getUser } from '@/lib/auth'
import { getProjects } from '@/lib/db/queries'

// ✅ Server Component: Fetch data directly
export default async function DashboardPage() {
  const user = await getUser()
  const projects = await getProjects(user.id)
  
  return (
    <div>
      <h1>Welcome, {user.name}</h1>
      <ProjectList projects={projects} />
    </div>
  )
}
```

### Client Components (When Needed)

```tsx
// components/forms/CreateProjectForm.tsx
'use client'

import { useState } from 'react'
import { createProjectAction } from '@/lib/actions'

// ✅ Client Component: Interactivity required
export function CreateProjectForm() {
  const [isLoading, setIsLoading] = useState(false)
  
  async function handleSubmit(formData: FormData) {
    setIsLoading(true)
    await createProjectAction(formData)
    setIsLoading(false)
  }
  
  return <form action={handleSubmit}>...</form>
}
```

### Server Actions

```typescript
// lib/actions.ts
'use server'

import { revalidatePath } from 'next/cache'
import { createProject } from '@/lib/db/queries'
import { projectSchema } from '@/lib/validations'

export async function createProjectAction(formData: FormData) {
  // Validate
  const data = projectSchema.parse({
    name: formData.get('name'),
    description: formData.get('description')
  })
  
  // Mutate
  const project = await createProject(data)
  
  // Revalidate
  revalidatePath('/dashboard')
  
  return project
}
```

---

## Form Handling

### Validation Schema

```typescript
// lib/validations.ts
import { z } from 'zod'

export const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters')
})

export type LoginInput = z.infer<typeof loginSchema>
```

### Form Component

```tsx
// components/forms/LoginForm.tsx
'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { loginSchema, type LoginInput } from '@/lib/validations'

export function LoginForm() {
  const form = useForm<LoginInput>({
    resolver: zodResolver(loginSchema)
  })
  
  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      <input {...form.register('email')} />
      {form.formState.errors.email && (
        <span>{form.formState.errors.email.message}</span>
      )}
    </form>
  )
}
```

---

## Anti-Patterns (Don't Do This)

| Anti-Pattern | Why Not | Do Instead |
|--------------|---------|------------|
| `useEffect` for data fetching | Race conditions, no SSR | Server Components + Server Actions |
| `axios` or `fetch` in components | Unnecessary client JS | Server Actions for mutations |
| `any` type | Loses type safety | Proper types or `unknown` with validation |
| Hardcoded strings | No i18n, error-prone | Constants or i18n keys |
| Direct SQL in components | Security, maintainability | Centralized queries in `lib/db/queries.ts` |
| `console.log` in production | Noisy, security risk | Proper logging service |
| Large client bundles | Slow TTI | Server Components by default |
| CSS-in-JS (styled-components) | Runtime overhead, no RSC | Tailwind + CSS Modules |

---

## Dev Commands

```bash
# Development
npm run dev              # Start dev server on localhost:3000

# Database
npm run db:generate      # Generate Drizzle migrations
npm run db:migrate       # Run pending migrations
npm run db:studio        # Open Drizzle Studio (GUI)

# Build & Deploy
npm run build            # Production build
npm run start            # Start production server

# Code Quality
npm run lint             # ESLint
npm run typecheck        # TypeScript check
npm run test             # Run tests
```

---

## Environment Variables

```bash
# .env.local (never commit this)
DATABASE_URL="file:./sqlite.db"
NEXTAUTH_SECRET="your-secret-here"
NEXTAUTH_URL="http://localhost:3000"
```

---

## Testing Strategy

- **Unit tests**: Utilities, validation schemas
- **Integration tests**: Database queries, Server Actions
- **E2E tests**: Critical user flows (Playwright)

```typescript
// tests/db/user.test.ts
import { describe, it, expect } from 'vitest'
import { createUser, getUserByEmail } from '@/lib/db/queries'

describe('User queries', () => {
  it('should create and retrieve a user', async () => {
    const user = await createUser({
      email: 'test@example.com',
      name: 'Test User'
    })
    
    const found = await getUserByEmail('test@example.com')
    expect(found?.id).toBe(user.id)
  })
})
```

---

## Deployment Checklist

- [ ] Environment variables set
- [ ] Database migrations run
- [ ] Build passes (`npm run build`)
- [ ] Type check passes (`npm run typecheck`)
- [ ] No `console.log` statements
- [ ] Error tracking configured (Sentry)
- [ ] Analytics configured (optional)

---

## Quick Start

```bash
# 1. Create project
npx create-next-app@latest my-saas --typescript --tailwind --app

# 2. Install dependencies
npm install drizzle-orm better-sqlite3 zod @hookform/resolvers
npm install -D drizzle-kit @types/better-sqlite3

# 3. Copy this CLAUDE.md to your project

# 4. Start building
npm run dev
```

---

**Questions?** Check the examples in `/examples/` or ask Claude about specific patterns.
