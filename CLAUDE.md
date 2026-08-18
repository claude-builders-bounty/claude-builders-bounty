---
project: Next.js + SQLite SaaS
stack: Next.js 15 App Router, SQLite (better-sqlite3/Turso), TypeScript, Tailwind CSS
---

# Next.js + SQLite SaaS Project

You are an expert full-stack developer working on a production SaaS application built with Next.js 15 App Router and SQLite. Follow these conventions strictly.

## Stack & Versions

- **Next.js**: 15.x (App Router only - no Pages Router)
- **React**: 19.x
- **TypeScript**: 5.x (strict mode enabled)
- **SQLite**: better-sqlite3 (local) or Turso (remote)
- **ORM**: Drizzle ORM (type-safe, no Prisma)
- **Styling**: Tailwind CSS (no CSS-in-JS libraries)
- **Auth**: NextAuth.js v5 (Auth.js)
- **Validation**: Zod (no Yup or Joi)
- **Forms**: React Hook Form + Zod validation
- **Testing**: Vitest + Playwright
- **Package Manager**: pnpm (not npm or yarn)

## Folder Structure

```
app/
  (auth)/
    login/page.tsx
    register/page.tsx
  (dashboard)/
    layout.tsx
    page.tsx
    settings/page.tsx
  api/
    webhooks/stripe/route.ts
    trpc/[...trpc]/route.ts
components/
  ui/              # Reusable UI components (shadcn/ui style)
  features/        # Feature-specific components
lib/
  db/              # Database setup and migrations
    schema.ts      # Drizzle schema definitions
    migrations/     # SQL migration files
  auth/            # Auth configuration
  utils/           # Utility functions
hooks/             # React hooks
prisma/            # ❌ NEVER USE - we use Drizzle
```

**Naming Conventions:**
- **Files**: kebab-case (`user-profile.tsx`, not `UserProfile.tsx`)
- **Components**: PascalCase (`UserProfile`, not `user-profile`)
- **Functions**: camelCase (`getUserById`, not `get_user_by_id`)
- **Constants**: UPPER_SNAKE_CASE (`API_BASE_URL`, not `apiBaseUrl`)
- **Types/Interfaces**: PascalCase (`UserProfile`, not `userProfile`)

## Database & Migrations

### Schema Rules
- Use Drizzle ORM for all database operations
- Define schemas in `lib/db/schema.ts`
- Use explicit column types (never rely on inference)
- Add indexes on foreign keys and frequently queried columns
- Use `sql` tag for raw SQL only when necessary

### Migration Workflow
1. Create migration: `pnpm drizzle-kit generate`
2. Review generated SQL in `lib/db/migrations/`
3. Apply migration: `pnpm drizzle-kit migrate`
4. Never edit migration files after generation
5. Always include rollback in migration comments

### SQL Conventions
```sql
-- Table names: snake_case, plural
CREATE TABLE users (...);

-- Column names: snake_case
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

-- Foreign keys: explicit naming
CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES users(id)
```

### Anti-Patterns
- ❌ Using Prisma (we use Drizzle)
- ❌ Raw SQL strings in components (use Drizzle queries)
- ❌ `SELECT *` (specify columns explicitly)
- ❌ N+1 queries (use joins or separate queries with relations)
- ❌ Missing indexes on foreign keys

## Component Patterns

### Server Components (Default)
- Use Server Components by default in App Router
- Only use Client Components when:
  - Interactive features (onClick, useState, etc.)
  - Browser APIs (localStorage, window, etc.)
  - Third-party libraries requiring client-side execution

### Component Structure
```typescript
// components/features/user-profile.tsx
import { getUserById } from '@/lib/db/queries'

export async function UserProfile({ userId }: { userId: string }) {
  const user = await getUserById(userId)
  
  return (
    <div className="p-4">
      <h1>{user.name}</h1>
    </div>
  )
}
```

### Client Components
```typescript
'use client'

import { useState } from 'react'

export function UserForm() {
  const [name, setName] = useState('')
  
  return (
    <form>
      <input value={name} onChange={(e) => setName(e.target.value)} />
    </form>
  )
}
```

### Data Fetching
- Use Server Components for data fetching (no useEffect)
- Use React Server Components for initial data
- Use SWR or TanStack Query for client-side caching if needed
- Never fetch data in useEffect when Server Components can do it

### Anti-Patterns
- ❌ `'use client'` on components that don't need it
- ❌ Fetching data in useEffect when Server Components work
- ❌ Prop drilling (use React Context or Server Components)
- ❌ Inline styles (use Tailwind classes)
- ❌ CSS-in-JS libraries (use Tailwind)

## API Routes

### Route Handlers
```typescript
// app/api/users/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { getUsers } from '@/lib/db/queries'

export async function GET(request: NextRequest) {
  const users = await getUsers()
  return NextResponse.json(users)
}
```

### Validation
- Use Zod for request validation
- Validate at the route handler level
- Return 400 with validation errors

```typescript
import { z } from 'zod'

const createUserSchema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
})

export async function POST(request: NextRequest) {
  const body = await request.json()
  const result = createUserSchema.safeParse(body)
  
  if (!result.success) {
    return NextResponse.json({ errors: result.error.errors }, { status: 400 })
  }
  
  // Process valid data
}
```

### Anti-Patterns
- ❌ Using API routes for data that Server Components can fetch
- ❌ Missing validation on POST/PUT/PATCH
- ❌ Returning 500 for validation errors (use 400)
- ❌ Not handling CORS (use Next.js built-in CORS)

## Authentication

### NextAuth.js v5 Configuration
```typescript
// lib/auth/config.ts
import NextAuth from 'next-auth'
import Credentials from 'next-auth/providers/credentials'

export const { handlers, auth } = NextAuth({
  providers: [
    Credentials({
      credentials: {
        email: { type: 'email' },
        password: { type: 'password' },
      },
      authorize: async (credentials) => {
        // Validate credentials
      },
    }),
  ],
})
```

### Protected Routes
```typescript
// app/(dashboard)/layout.tsx
import { auth } from '@/lib/auth/config'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await auth()
  
  if (!session) {
    redirect('/login')
  }
  
  return <div>{children}</div>
}
```

### Anti-Patterns
- ❌ Storing passwords in plain text (use bcrypt)
- ❌ Using session storage for auth tokens (use httpOnly cookies)
- ❌ Missing CSRF protection (NextAuth handles this)
- ❌ Custom auth implementations (use NextAuth.js)

## Development Commands

```bash
# Development
pnpm dev

# Build
pnpm build

# Database migrations
pnpm drizzle-kit generate
pnpm drizzle-kit migrate
pnpm drizzle-kit studio

# Type checking
pnpm tsc --noEmit

# Linting
pnpm lint
pnpm lint:fix

# Testing
pnpm test
pnpm test:e2e
```

## What We Don't Do (And Why)

### ❌ Prisma ORM
**Why:** Drizzle is type-safe, faster, and has better TypeScript support. Prisma's generated client is heavy and has performance issues.

### ❌ Pages Router
**Why:** App Router is the future of Next.js. Pages Router is legacy and will be deprecated. App Router has better performance and developer experience.

### ❌ CSS-in-JS (styled-components, emotion)
**Why:** Tailwind CSS is faster, has better DX, and smaller bundle size. CSS-in-JS adds runtime overhead and complexity.

### ❌ Redux
**Why:** React Context + Server Components handle state better. Redux is overkill for most apps and adds unnecessary complexity.

### ❌ Custom hooks for data fetching
**Why:** Server Components fetch data directly. Client components use SWR/TanStack Query if needed. Custom hooks add abstraction without benefit.

### ❌ Micro-frontend architecture
**Why:** Adds unnecessary complexity for SaaS apps. Monorepo with proper boundaries is simpler and more maintainable.

### ❌ GraphQL
**Why:** Overkill for most SaaS apps. REST with proper API design is simpler and sufficient. GraphQL adds complexity without clear benefits.

### ❌ Webpack configuration
**Why:** Next.js handles this. Custom webpack config breaks frequently and adds maintenance burden.

### ❌ Storybook
**Why:** Adds build time and complexity. Visual testing is better done with Playwright E2E tests.

## Performance Rules

- Use `next/image` for all images (no `<img>` tags)
- Use `next/link` for internal links (no `<a>` tags)
- Implement proper caching headers for API routes
- Use React.memo only when profiling shows benefit
- Lazy load heavy components with `next/dynamic`
- Optimize database queries with proper indexes
- Use streaming for large data sets with Server Components

## Security Rules

- Never commit secrets (use environment variables)
- Validate all user input with Zod
- Use parameterized queries (Drizzle handles this)
- Implement rate limiting on API routes
- Use httpOnly cookies for auth tokens
- Sanitize user-generated content
- Implement CSP headers
- Keep dependencies updated with `pnpm audit`

## Testing Strategy

- Unit tests: Vitest for utility functions
- Integration tests: Vitest for API routes
- E2E tests: Playwright for critical user flows
- Test coverage: minimum 80% for business logic
- Always test authentication flows
- Test database migrations in CI

## Code Review Checklist

- [ ] TypeScript strict mode passes
- [ ] No `any` types (use proper types)
- [ ] No console.log in production code
- [ ] Proper error handling with try/catch
- [ ] Database queries are indexed
- [ ] No N+1 query problems
- [ ] Components are Server Components by default
- [ ] Client components are marked with 'use client'
- [ ] Environment variables are documented
- [ ] Tests pass for new features