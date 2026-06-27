# CLAUDE.md — Next.js 15 + SQLite SaaS

> Production-grade SaaS conventions. Read before every change.

## Stack & Versions

| Layer | Choice | Version | Why |
|-------|--------|---------|-----|
| Framework | Next.js App Router | 15.x | RSC + streaming SSR, ideal for SaaS |
| Language | TypeScript | 5.x strict | Type safety, fewer runtime errors |
| Database | better-sqlite3 | 11.x | Sync API, zero latency, embedded |
| ORM | Drizzle ORM | 0.3x | Type-safe SQL, native SQLite support |
| Styling | Tailwind CSS | 4.x | Atomic, zero runtime overhead |
| Package Manager | pnpm | 9.x | Fast, disk-efficient, strict isolation |
| Runtime | Node.js | 20 LTS | Stable, long-term support |

**We do NOT use:** Prisma (weak SQLite support), MongoDB (poor fit for SaaS), CSS-in-JS (runtime overhead), Redux (over-engineering).

## Folder Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/             # Auth route group
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/        # Post-login main UI
│   │   ├── layout.tsx      # Sidebar + top bar
│   │   ├── page.tsx        # Dashboard home
│   │   └── settings/
│   ├── api/                # API routes
│   │   └── v1/             # Versioned API
│   ├── layout.tsx          # Root layout
│   └── globals.css
├── components/
│   ├── ui/                 # Base UI components (no business logic)
│   ├── forms/              # Form components
│   └── layouts/            # Layout components
├── db/
│   ├── schema.ts           # Drizzle table definitions
│   ├── migrations/         # Auto-generated migration files
│   └── index.ts            # Database connection instance
├── lib/
│   ├── auth.ts             # Authentication logic
│   ├── email.ts            # Email sending
│   └── utils.ts            # Pure utility functions
├── hooks/                  # Custom React hooks
├── types/                  # Global type definitions
└── constants.ts            # Constants
```

**Rules:**
- Route files in `app/` must not exceed 200 lines; extract to `components/` if they do
- `components/ui/` must not import from `db/` or any business module
- Each file in `lib/` has a single responsibility — no "miscellaneous utils" catch-all

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| File names | kebab-case | `user-profile.tsx` |
| Component names | PascalCase | `UserProfile` |
| Function names | camelCase | `getUserById` |
| Constants | UPPER_SNAKE | `MAX_FILE_SIZE` |
| DB tables | snake_case | `user_accounts` |
| DB columns | snake_case | `created_at` |
| CSS classes | Tailwind atomic | `flex items-center` |
| Route paths | kebab-case | `/dashboard/user-settings` |

**TypeScript naming:**
- No `I` prefix on interfaces: `User` not `IUser`
- Use `type` by default; use `interface` only when inheritance is needed
- Use `as const` objects instead of `enum`

## Database / SQLite Rules

### Schema Definition

```typescript
// src/db/schema.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core'
import { nanoid } from 'nanoid'

export const users = sqliteTable('users', {
  id: text('id').primaryKey().$defaultFn(() => nanoid()),
  email: text('email').notNull().unique(),
  name: text('name').notNull(),
  createdAt: integer('created_at', { mode: 'timestamp_ms' }).notNull(),
  updatedAt: integer('updated_at', { mode: 'timestamp_ms' }).notNull(),
})
```

**Rules:**
- Primary keys use `text` + `nanoid()`, never auto-increment (SaaS needs unpredictable IDs)
- Timestamps use `integer` with `timestamp_ms` mode (Unix milliseconds)
- All tables must have `createdAt` and `updatedAt`
- Foreign keys use `.references(() => table.id)`, no hand-written SQL
- Booleans use `integer` (0/1) — SQLite has no native boolean

### Migrations

```bash
# Generate migration
pnpm drizzle-kit generate

# Run migration
pnpm drizzle-kit migrate

# View diff
pnpm drizzle-kit diff
```

**Rules:**
- Migration files are auto-generated, never hand-edited
- Migration files must be committed to git
- Production only runs `migrate`, never `generate`
- Destructive changes (drop column, change type) require two-step migration: add new column → migrate data → drop old column

### Query Patterns

```typescript
// ✅ Correct: type-safe Drizzle query
const user = await db.select().from(users).where(eq(users.id, userId)).get()

// ❌ Wrong: hand-written SQL string
const user = await db.get(`SELECT * FROM users WHERE id = ?`, [userId])

// ✅ Complex queries use sql template
const result = await db.select({
  count: sql<number>`count(*)`,
}).from(users).where(sql`${users.createdAt} > ${oneWeekAgo}`)
```

## Component Patterns

### Server Component (default)

```typescript
// app/(dashboard)/page.tsx
import { db } from '@/db'
import { users } from '@/db/schema'

export default async function DashboardPage() {
  const userList = await db.select().from(users).all()
  return <UserList users={userList} />
}
```

**Rules:**
- Default to Server Components; add `'use client'` only when interactivity is needed
- Data fetching happens in Server Components, passed to Client Components via props
- No `useState` or `useEffect` in Server Components

### Client Component

```typescript
'use client'

import { useState } from 'react'

interface UserListProps {
  users: { id: string; name: string }[]
}

export function UserList({ users }: UserListProps) {
  const [filter, setFilter] = useState('')
  // ...
}
```

**Rules:**
- `'use client'` must be at the top of the file
- Props types defined in the same file, not in a separate types file
- Extract logic to a custom hook when component exceeds 150 lines

### Forms

```typescript
// Use Server Actions
'use server'

import { db } from '@/db'
import { users } from '@/db/schema'
import { nanoid } from 'nanoid'

export async function createUser(formData: FormData) {
  const name = formData.get('name') as string
  const email = formData.get('email') as string

  if (!name || !email) {
    return { error: 'Name and email are required' }
  }

  await db.insert(users).values({
    id: nanoid(),
    name,
    email,
    createdAt: new Date(),
    updatedAt: new Date(),
  })

  return { success: true }
}
```

**Rules:**
- Forms use Server Actions, not API Routes
- Validation happens in Server Actions — never trust the client
- Return `{ error: string } | { success: true }` — no try/catch wrapping business logic

## Dev Commands

```bash
# Development
pnpm dev                    # Start dev server (http://localhost:3000)
pnpm build                  # Production build
pnpm start                  # Start production server

# Database
pnpm db:generate            # Generate migration (alias for drizzle-kit generate)
pnpm db:migrate             # Run migration (alias for drizzle-kit migrate)
pnpm db:studio              # Open Drizzle Studio (data viewer)
pnpm db:seed                # Seed test data

# Code Quality
pnpm lint                   # ESLint check
pnpm typecheck              # TypeScript type check
pnpm test                   # Run tests
pnpm test:watch             # Watch mode tests
```

> Note: `pnpm db:*` scripts are aliases for the corresponding `pnpm drizzle-kit` commands defined in `package.json`.

## Anti-Patterns (Forbidden)

| ❌ Don't | ✅ Do instead | Why |
|----------|--------------|-----|
| `useEffect` for data fetching | Server Component direct query | Avoids waterfall requests, improves FCP |
| `any` type | `unknown` + type guards | `any` bypasses type checking, causes runtime crashes |
| Giant `utils.ts` | Split `lib/` files by responsibility | Maintainability, tree-shaking |
| CSS modules + Tailwind mixed | Pure Tailwind | Avoids style conflicts, unified maintenance |
| Client state management libs | React Context + `useState` | SaaS scale doesn't need Redux/Zustand |
| Hand-written SQL strings | Drizzle query builder | Type safety, SQL injection prevention |
| Hardcoded env vars | `process.env` + `.env.local` | Security, environment isolation |
| Auto-increment IDs | `nanoid()` string IDs | Unpredictable, URL-friendly, distributed-safe |
| `console.log` debugging | Structured logging (pino) | Production observability |
| Calling DB in Client Components | Server Action / API Route | Separation of concerns |

## What We Don't Do (and Why)

- **No GraphQL** — REST + Server Actions are sufficient; GraphQL adds complexity without payoff
- **No microservices** — Monolith is better for early SaaS; simpler deployment, easier debugging
- **No SSR caching** — SQLite is local, queries are fast enough, no HTTP cache layer needed
- **No OAuth libraries** — Self-implement email+password auth; social login not needed early
- **No Docker for dev** — SQLite needs no containerization, runs locally
- **No tests before CI** — Write business code first, add tests once stable
- **No i18n** — Unless multilingual is explicitly required, don't introduce translation layer

## Git Conventions

```
feat: new feature
fix: bug fix
refactor: restructure (no behavior change)
style: styling adjustments
docs: documentation
chore: build/tooling
```

**Rules:**
- One concern per commit
- Never commit `node_modules/`, `.next/`, `*.db` files
- PR title format: `feat: short description`

## Environment Variables

```bash
# .env.local (not committed to git)
DATABASE_URL=file:./data/app.db
AUTH_SECRET=random-32-char-string
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

**Rules:**
- Client-accessible vars must have `NEXT_PUBLIC_` prefix
- Secrets are server-only, no `NEXT_PUBLIC_` prefix
- `.env.local` is in `.gitignore`
