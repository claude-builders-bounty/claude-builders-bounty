# CLAUDE.md — Next.js 15 + SQLite SaaS Project Template

> Opinionated project context for Claude Code. Not generic — every rule has a reason.

## Stack & Versions

| Component | Version | Why |
|-----------|---------|-----|
| Next.js | 15 (App Router) | File-based routing, Server Components, built-in API routes |
| React | 19 | Concurrent features, use() hook, improved Suspense |
| SQLite | via better-sqlite3 | Zero-config, single-file, ACID transactions, no migration needed for simple schemas |
| Turso | (libSQL fork) | SQLite-over-HTTP for edge deployment, local dev is plain SQLite |
| TypeScript | 5.x | Strict mode enabled, no `any` without explicit opt-in |
| Tailwind CSS | 4.x | Utility-first, co-located with components |
| next-auth | 5.x | Session management, OAuth providers |

**Why SQLite over Postgres for SaaS MVP:**
- No external service to provision or rotate credentials
- `better-sqlite3` has synchronous API that fits Next.js Server Components
- Turso gives you global edge replication when you need to scale
- Most SaaS apps never exceed SQLite's ~140TB limit

## Project Structure

```
/
├── app/                      # Next.js 15 App Router
│   ├── (auth)/              # Auth route group (login, register, etc.)
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/         # Protected dashboard route group
│   │   ├── layout.tsx       # Dashboard layout with sidebar
│   │   ├── page.tsx         # Dashboard home
│   │   └── settings/
│   ├── api/                  # API routes (route handlers)
│   │   ├── auth/
│   │   └── v1/
│   │       └── [resource]/  # RESTful resource endpoints
│   └── layout.tsx           # Root layout
├── components/
│   ├── ui/                  # Primitive UI components (Button, Input, Card)
│   ├── forms/               # Form components with react-hook-form
│   └── layout/              # Layout components (Header, Sidebar, Footer)
├── lib/
│   ├── db/                  # Database layer
│   │   ├── index.ts         # DB connection singleton
│   │   ├── schema.ts        # Schema definitions
│   │   └── migrations/      # SQL migration files
│   ├── auth/                # Auth utilities
│   │   ├── session.ts       # Session management
│   │   └── middleware.ts     # Auth middleware
│   └── utils/               # Utility functions
├── styles/
│   └── globals.css          # Global styles + Tailwind
├── drizzle.config.ts        # Drizzle ORM config (optional)
├── .env.local               # Local env vars (never commit)
└── package.json
```

**Why this structure:**
- Route groups `(auth)` and `(dashboard)` organize routes without affecting URLs
- `lib/db` separates database concerns from business logic
- `components/ui` holds primitives; `components/forms` holds composed forms
- API routes under `api/v1/` allow future versioning

## Naming Conventions

### Files

| Pattern | Example | Why |
|---------|---------|-----|
| React components | `DashboardLayout.tsx` (PascalCase) | Standard React convention |
| Page files | `page.tsx`, `layout.tsx` | Next.js file conventions |
| Route handlers | `route.ts` | Next.js convention |
| Utilities | `formatCurrency.ts` (camelCase) | Non-component modules |
| Database schema | `schema.ts` (noun, singular) | Drizzle convention |
| Migration files | `00001_add_users.sql` (semver prefix) | Sequential, descriptive |

### Variables & Functions

```typescript
// Good: descriptive, follows camelCase for vars/functions
const userAuthenticationToken = 'Bearer ...'
async function fetchUserByEmail(email: string): Promise<User>

// Bad: abbreviated, Hungarian notation
const token = 'Bearer ...'
function getUser(email: string) {}

// React components: props interfaces named ComponentNameProps
interface UserCardProps {
  user: User
  onSelect?: (user: User) => void
}

// Database: use `id`, `createdAt`, `updatedAt` consistently
interface User {
  id: string          // UUID, generated in app layer
  email: string
  createdAt: Date
  updatedAt: Date
}
```

## Database Migrations

### Rules

1. **Migrations are SQL files, never ORM-only**
   - Drizzle generates migrations, but SQL is source of truth
   - Store in `lib/db/migrations/00001_*.sql`
   - Review generated SQL before running

2. **Always add createdAt/updatedAt to tables**
   ```sql
   CREATE TABLE users (
     id TEXT PRIMARY KEY,
     email TEXT NOT NULL UNIQUE,
     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
     updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
   );
   ```

3. **Use TEXT for IDs, not AUTOINCREMENT**
   - UUIDs prevent enumeration attacks
   - Generate in application layer: `crypto.randomUUID()`

4. **Migrations are additive-only in development**
   - Don't drop columns in migration (add new column, migrate data, drop old)
   - Old code might run during deployment window

### Migration Workflow

```bash
# 1. Create migration (Drizzle auto-generates from schema diff)
pnpm db:generate

# 2. Review generated SQL in lib/db/migrations/
# 3. Run migration against local DB
pnpm db:push  # for development

# 4. In production, migrations run automatically on deploy
```

### Why not Drizzle's auto-migrate?

Drizzle's `push` command pushes schema directly. For production:
- Use migration files with `drizzle-kit generate`
- Run migrations via CI/CD pipeline
- Keep schema.ts as the "intended" state, migrations as historical record

## Component Patterns

### Server vs Client Components

```typescript
// app/dashboard/page.tsx — Server Component (default)
// Data fetching happens here, no 'use client'
export default async function DashboardPage() {
  const users = await db.query.users.findMany()
  return <UserList users={users} />
}

// components/UserList.tsx — Client Component
// Interactive, uses useState, useEffect, event handlers
'use client'
export function UserList({ users }: UserListProps) {
  const [filter, setFilter] = useState('')
  return (/* ... */)
}
```

**Rule:** Keep components Server Components unless they need interactivity. This reduces JS bundle size.

### Form Handling

```typescript
// components/forms/UserForm.tsx
'use client'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { userSchema } from '@/lib/validations/user'

export function UserForm({ onSubmit }: UserFormProps) {
  const form = useForm<UserFormData>({
    resolver: zodResolver(userSchema),
    defaultValues: { email: '' }
  })

  return (
    <Form {...form}>
      <FormField
        control={form.control}
        name="email"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Email</FormLabel>
            <FormControl>
              <Input {...field} type="email" />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </Form>
  )
}
```

### API Route Handlers

```typescript
// app/api/v1/users/route.ts
import { NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { userSchema } from '@/lib/validations/user'

export async function GET(request: Request) {
  const users = await db.select().from(usersTable)
  return NextResponse.json(users)
}

export async function POST(request: Request) {
  const body = await request.json()
  const parsed = userSchema.safeParse(body)

  if (!parsed.success) {
    return NextResponse.json(
      { error: 'Validation failed', details: parsed.error.flatten() },
      { status: 400 }
    )
  }

  const [user] = await db.insert(usersTable).values(parsed.data).returning()
  return NextResponse.json(user, { status: 201 })
}
```

## What We Don't Do (And Why)

### No Direct Database Queries in Client Components

```typescript
// Bad: Client component importing db directly
'use client'
import { db } from '@/lib/db' // NO!
const users = await db.select().from(users) // NO!

// Good: Server component fetches, passes to client
// app/users/page.tsx (Server)
const users = await db.select().from(users)
return <UserList users={users} />
```

**Why:** Database credentials should never reach the browser. Client Components can only call API routes.

### No Mixed API Styles

```typescript
// Bad: Mixing REST and RPC in same route
export async function GET(request: Request) { /* ... */ }
export async function POST(request: Request) { /* ... */ }
// Also export some RPC-style function? NO!

// Good: RESTful resources only
// app/api/v1/users/route.ts — GET list, POST create
// app/api/v1/users/[id]/route.ts — GET one, PUT update, DELETE
```

### No `console.log` in API Routes

```typescript
// Bad: console.log leaks to stdout, pollutes logs
export async function POST(request: Request) {
  console.log('User creation attempted') // NO!
  // ...
}

// Good: Structured logging via logger utility
import { logger } from '@/lib/utils/logger'
export async function POST(request: Request) {
  logger.info('user.create.attempted')
  // ...
}
```

### No `any` Without `// eslint-disable-next-line @typescript-eslint/no-explicit-any`

```typescript
// Bad: silently opting out of type safety
function parseJSON(str: any) { // NO!

// Good: explicit opt-in with comment
function parseJSON(str: unknown) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const data = str as any // Still explicit about the cast
}
```

## Dev Commands

```bash
# Development
pnpm dev              # Start Next.js dev server (http://localhost:3000)
pnpm build            # Production build
pnpm start            # Start production server

# Database
pnpm db:generate      # Generate migrations from schema
pnpm db:push           # Push schema to local DB (dev only)
pnpm db:studio         # Open Drizzle Studio (visual DB explorer)

# Code Quality
pnpm lint             # ESLint
pnpm typecheck         # TypeScript type checking
pnpm test              # Run tests

# Deployment
pnpm db:migrate        # Run pending migrations (production)
```

## Environment Variables

```bash
# .env.local (never commit this file)
DATABASE_URL=file:./local.db          # SQLite file path for dev
# DATABASE_URL=libsql://your-db.turso.io  # Turso for production
NEXTAUTH_SECRET=your-secret-here      # Generate with: openssl rand -base64 32
NEXTAUTH_URL=http://localhost:3000    # Canonical URL
```

**Rule:** All secrets go in `.env.local`. `.env.example` contains non-sensitive defaults only.

## Testing Strategy

```typescript
// tests/example.test.ts
import { describe, it, expect } from 'vitest'
import { userSchema } from '@/lib/validations/user'

describe('userSchema', () => {
  it('accepts valid email', () => {
    const result = userSchema.safeParse({ email: 'test@example.com' })
    expect(result.success).toBe(true)
  })

  it('rejects invalid email', () => {
    const result = userSchema.safeParse({ email: 'not-an-email' })
    expect(result.success).toBe(false)
  })
})
```

**Run tests with:** `pnpm test`

## Deployment Checklist

- [ ] All environment variables set in production
- [ ] `DATABASE_URL` points to production database (Turso or hosted SQLite)
- [ ] `NEXTAUTH_SECRET` regenerated for production
- [ ] `NEXTAUTH_URL` set to canonical production URL
- [ ] Run `pnpm db:migrate` to apply any pending migrations
- [ ] Enable automatic migration on Vercel/other platform (if supported)

## Anti-Patterns to Avoid

1. **Don't use `useEffect` for data fetching in Client Components**
   - Use React Server Components or call API routes instead
   - `useEffect` for data fetching causes waterfall requests

2. **Don't put business logic in route handlers**
   - Route handlers = HTTP layer
   - Business logic = service layer in `lib/services/`

3. **Don't ignore TypeScript errors before shipping**
   - `pnpm typecheck` must pass before merge
   - Fix type errors, don't suppress with `as any`

4. **Don't commit `.env.local`**
   - Add `.env.local` to `.gitignore`
   - Env vars are for configuration, not secret storage in code

---

**Last updated:** 2026-05-20 | **Next.js version:** 15.x | **SQLite:** better-sqlite3