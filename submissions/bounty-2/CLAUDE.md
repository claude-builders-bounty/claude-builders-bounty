# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

This file configures Claude's behavior for this codebase. Every rule here exists for a specific reason; the reason is stated so you can make better judgments in edge cases.

---

## Project Overview

This is a SaaS application built with:
- **Next.js 15** (App Router, React Server Components by default)
- **SQLite via better-sqlite3** (synchronous, embedded, single-file database)
- **TypeScript** (strict mode)
- **Tailwind CSS**

---

## Project Structure

```
.
├── app/                        # Next.js App Router — pages, layouts, API routes
│   ├── (auth)/                 # Route group: auth pages (no shared layout with app)
│   ├── (dashboard)/            # Route group: authenticated app pages
│   ├── api/                    # Route handlers (API endpoints)
│   └── layout.tsx              # Root layout
├── components/                 # Shared React components
│   ├── ui/                     # Primitive UI components (buttons, inputs, modals)
│   └── [feature]/              # Feature-specific components
├── lib/                        # Non-React logic: DB, auth, utilities
│   ├── db/                     # Database layer
│   │   ├── client.ts           # better-sqlite3 singleton
│   │   ├── migrations.ts       # Migration runner
│   │   └── queries/            # Typed query functions, one file per domain
│   ├── auth/                   # Auth helpers (session, tokens)
│   └── utils/                  # Pure utility functions
├── migrations/                 # Numbered SQL migration files
│   ├── 0001_create_users.sql
│   └── 0002_create_sessions.sql
├── types/                      # Global TypeScript types and interfaces
├── hooks/                      # Client-side custom hooks (use sparingly)
├── public/                     # Static assets
├── .env.local                  # Local secrets (never commit)
├── .env.example                # Committed template showing required env vars
└── next.config.ts
```

**Why this structure:** The `lib/db/queries/` separation means route handlers never contain SQL — they call typed functions that can be tested in isolation. Route groups `(auth)` and `(dashboard)` allow different root layouts without polluting the URL.

---

## Naming Conventions

| Thing | Convention | Example |
|---|---|---|
| Files (components) | PascalCase | `UserAvatar.tsx` |
| Files (everything else) | kebab-case | `create-session.ts` |
| React components | PascalCase | `function UserAvatar()` |
| Functions, variables | camelCase | `getUserById`, `isExpired` |
| DB columns | snake_case | `created_at`, `user_id` |
| Types/Interfaces | PascalCase | `type Session`, `interface UserRow` |
| Constants | SCREAMING_SNAKE | `MAX_SESSION_DURATION` |
| CSS classes | kebab-case (Tailwind) | `bg-slate-900` |
| Route handlers | `route.ts` | `app/api/users/route.ts` |
| Server Actions | `actions.ts` | `app/(dashboard)/settings/actions.ts` |

**Why snake_case for DB columns:** SQLite is case-insensitive for column names; snake_case is the SQL community standard and avoids quoting issues. Map to camelCase at the query boundary in `lib/db/queries/`.

---

## React & Next.js Patterns

### Server Components are the default

Every component is a Server Component unless it explicitly needs to be a Client Component. Do not add `"use client"` preemptively.

**Use Client Components ONLY when the component needs:**
- `useState` or `useReducer`
- `useEffect` (see restriction below)
- Browser APIs (`window`, `document`, `localStorage`)
- Event handlers that cannot be Server Actions (`onChange`, `onKeyDown`, etc.)

```tsx
// CORRECT — server component fetches data directly
// app/(dashboard)/users/page.tsx
import { getUsers } from '@/lib/db/queries/users'

export default async function UsersPage() {
  const users = await getUsers()
  return <UserList users={users} />
}

// CORRECT — client component wrapper only where interaction is needed
// components/ui/SearchInput.tsx
'use client'
import { useState } from 'react'

export function SearchInput({ onSearch }: { onSearch: (q: string) => void }) {
  const [value, setValue] = useState('')
  // ...
}
```

### Never use useEffect for data fetching

`useEffect` for data fetching causes loading waterfalls, is hard to cache, and is unnecessary with Server Components.

```tsx
// WRONG
'use client'
export function UserProfile({ userId }: { userId: string }) {
  const [user, setUser] = useState(null)
  useEffect(() => {
    fetch(`/api/users/${userId}`).then(r => r.json()).then(setUser)
  }, [userId])
}

// CORRECT
// app/(dashboard)/profile/page.tsx
import { getUserById } from '@/lib/db/queries/users'

export default async function ProfilePage({ params }: { params: { id: string } }) {
  const user = await getUserById(params.id)
  return <UserProfile user={user} />
}
```

The only acceptable `useEffect` uses: syncing with non-React systems (analytics, third-party DOM libraries), cleanup on unmount, responding to user interactions that require timing.

### Server Actions for mutations

Use Server Actions (not API routes) for form submissions and mutations triggered from the UI. Define them in `actions.ts` co-located with the page.

```tsx
// app/(dashboard)/settings/actions.ts
'use server'
import { updateUser } from '@/lib/db/queries/users'
import { revalidatePath } from 'next/cache'

export async function updateProfileAction(formData: FormData) {
  const name = formData.get('name') as string
  await updateUser({ name })
  revalidatePath('/settings')
}
```

Use API routes (`app/api/`) only for: webhooks, external service callbacks, or endpoints consumed by non-Next.js clients.

### Data fetching in layouts vs pages

- Fetch shared data (user session, org) in layouts
- Fetch page-specific data in the page component
- Never fetch the same data in both — pass it as props or use React `cache()`

```tsx
// app/(dashboard)/layout.tsx
import { getSession } from '@/lib/auth/session'

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const session = await getSession()
  if (!session) redirect('/login')
  return <div>{children}</div>
}
```

---

## Database Layer

### The DB singleton

`lib/db/client.ts` exports a single `better-sqlite3` instance. Never import `better-sqlite3` directly anywhere else.

```ts
// lib/db/client.ts
import Database from 'better-sqlite3'
import path from 'path'

const DB_PATH = process.env.DATABASE_PATH ?? path.join(process.cwd(), 'data', 'app.db')

const db = new Database(DB_PATH)
db.pragma('journal_mode = WAL')
db.pragma('foreign_keys = ON')
db.pragma('busy_timeout = 5000')

export default db
```

**Why WAL mode:** WAL (Write-Ahead Logging) allows concurrent reads during writes, which matters for SSR where multiple requests hit the DB simultaneously.

**Why foreign_keys = ON:** SQLite disables FK constraints by default. Enabling it catches referential integrity bugs at the DB level, not in application code.

### Query functions

All SQL lives in `lib/db/queries/`. One file per domain (users, sessions, billing, etc.). Export typed functions.

```ts
// lib/db/queries/users.ts
import db from '@/lib/db/client'

export interface UserRow {
  id: string
  email: string
  name: string
  created_at: number
}

export function getUserById(id: string): UserRow | undefined {
  return db.prepare('SELECT * FROM users WHERE id = ?').get(id) as UserRow | undefined
}

export function getUserByEmail(email: string): UserRow | undefined {
  return db.prepare('SELECT * FROM users WHERE email = ?').get(email) as UserRow | undefined
}

export function createUser(data: { id: string; email: string; name: string }): UserRow {
  db.prepare('INSERT INTO users (id, email, name) VALUES (?, ?, ?)').run(
    data.id, data.email, data.name
  )
  return getUserById(data.id)!
}
```

**Why no raw SQL in route handlers or components:** SQL in handlers makes it impossible to unit-test queries, creates scattered ownership, and leads to copy-paste bugs.

### Transactions for multi-step writes

Any operation that writes to more than one table MUST use a transaction. `better-sqlite3` transactions are synchronous and composable.

```ts
// lib/db/queries/auth.ts
import db from '@/lib/db/client'

export const createUserWithSession = db.transaction((
  user: { id: string; email: string; name: string },
  session: { id: string; user_id: string; expires_at: number }
) => {
  db.prepare('INSERT INTO users (id, email, name) VALUES (?, ?, ?)').run(
    user.id, user.email, user.name
  )
  db.prepare('INSERT INTO sessions (id, user_id, expires_at) VALUES (?, ?, ?)').run(
    session.id, session.user_id, session.expires_at
  )
})
```

**Why:** Without a transaction, a crash between two writes leaves the DB in a corrupt state (e.g., a user with no session, or a session pointing to a non-existent user).

### Prepared statements

Always use `db.prepare()`. Never use string interpolation to build SQL queries.

```ts
// WRONG — SQL injection vulnerability
db.exec(`SELECT * FROM users WHERE email = '${email}'`)

// CORRECT
db.prepare('SELECT * FROM users WHERE email = ?').get(email)
```

### Migrations

Migrations are numbered SQL files in `/migrations/`. They run in order and are tracked in a `_migrations` table.

```
migrations/
  0001_create_users.sql
  0002_create_sessions.sql
  0003_add_stripe_customer_id_to_users.sql
```

Run migrations:
```bash
npm run migrate
```

**Rules:**
- Never modify an already-applied migration. Add a new one.
- Migration filenames: `{4-digit-number}_{snake_case_description}.sql`
- Each migration file should be idempotent where possible (`CREATE TABLE IF NOT EXISTS`)
- Migrations run at app startup in development, and as a deploy step in production

Migration runner (`lib/db/migrations.ts`):

```ts
import db from '@/lib/db/client'
import fs from 'fs'
import path from 'path'

export function runMigrations() {
  db.exec(`
    CREATE TABLE IF NOT EXISTS _migrations (
      filename TEXT PRIMARY KEY,
      applied_at INTEGER NOT NULL DEFAULT (unixepoch())
    )
  `)

  const applied = new Set(
    (db.prepare('SELECT filename FROM _migrations').all() as { filename: string }[])
      .map(r => r.filename)
  )

  const migrationsDir = path.join(process.cwd(), 'migrations')
  const files = fs.readdirSync(migrationsDir)
    .filter(f => f.endsWith('.sql'))
    .sort()

  for (const file of files) {
    if (applied.has(file)) continue
    const sql = fs.readFileSync(path.join(migrationsDir, file), 'utf8')
    db.exec(sql)
    db.prepare('INSERT INTO _migrations (filename) VALUES (?)').run(file)
    console.log(`[migrate] applied: ${file}`)
  }
}
```

---

## Error Handling

### Never swallow errors

```ts
// WRONG
try {
  await doSomething()
} catch {
  // silently fail
}

// WRONG — returns undefined when an error occurred, caller can't distinguish
try {
  return await doSomething()
} catch {
  return null
}

// CORRECT
try {
  return await doSomething()
} catch (err) {
  console.error('[doSomething] failed:', err)
  throw err
}
```

**Why:** Swallowed errors make bugs invisible. Log before re-throwing so the error is observable even if the caller also swallows it.

### Error types

Define application errors in `types/errors.ts`. Use them to distinguish user-facing errors from unexpected bugs.

```ts
// types/errors.ts
export class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number = 400
  ) {
    super(message)
    this.name = 'AppError'
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string) {
    super(`${resource} not found`, 'NOT_FOUND', 404)
  }
}

export class UnauthorizedError extends AppError {
  constructor() {
    super('Unauthorized', 'UNAUTHORIZED', 401)
  }
}
```

### Route handler error handling

```ts
// app/api/users/[id]/route.ts
import { NextResponse } from 'next/server'
import { AppError } from '@/types/errors'
import { getUserById } from '@/lib/db/queries/users'

export async function GET(
  _req: Request,
  { params }: { params: { id: string } }
) {
  try {
    const user = getUserById(params.id)
    if (!user) throw new NotFoundError('User')
    return NextResponse.json(user)
  } catch (err) {
    if (err instanceof AppError) {
      return NextResponse.json({ error: err.message, code: err.code }, { status: err.statusCode })
    }
    console.error('[GET /api/users/:id]', err)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
```

---

## Environment Variables

### Rules

- `.env.local` — secrets and local overrides. **Never commit this file.**
- `.env.example` — committed template with placeholder values. Keep it in sync with `.env.local`.
- `.env` — non-secret defaults that apply in all environments (e.g., `NODE_ENV`).
- Never hardcode secrets, API keys, or URLs that differ between environments.

### Required variables

Document all required env vars in `.env.example`:

```bash
# .env.example
DATABASE_PATH=./data/app.db

# Auth
AUTH_SECRET=replace-with-32-char-random-string

# Stripe (get from dashboard.stripe.com)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...

# App
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### Accessing env vars

Validate required env vars at startup, not at call time:

```ts
// lib/env.ts
function requireEnv(name: string): string {
  const value = process.env[name]
  if (!value) throw new Error(`Missing required environment variable: ${name}`)
  return value
}

export const env = {
  authSecret: requireEnv('AUTH_SECRET'),
  databasePath: process.env.DATABASE_PATH ?? './data/app.db',
  stripeSecretKey: requireEnv('STRIPE_SECRET_KEY'),
  appUrl: requireEnv('NEXT_PUBLIC_APP_URL'),
}
```

---

## Development Commands

```bash
npm run dev          # Start dev server (localhost:3000)
npm run build        # Production build
npm run start        # Start production server
npm run migrate      # Run pending DB migrations
npm run typecheck    # tsc --noEmit (run before commits)
npm run lint         # ESLint
npm test             # Run all tests (vitest)
npm run test:watch   # Watch mode
```

**Before opening a PR:**
1. `npm run typecheck` — must pass with 0 errors
2. `npm run lint` — must pass
3. `npm test` — must pass

---

## Testing

### Co-locate tests with source files

```
lib/db/queries/users.ts
lib/db/queries/users.test.ts     ← test lives here, not in __tests__/

lib/auth/session.ts
lib/auth/session.test.ts
```

**Why:** Co-location makes it obvious when a file has no tests, prevents tests from going stale when files are moved, and keeps imports short.

### Test structure

Use Vitest. Tests for DB query functions use a real in-memory SQLite database — never mock `better-sqlite3`.

```ts
// lib/db/queries/users.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import Database from 'better-sqlite3'
import { runMigrations } from '@/lib/db/migrations'

// Override the DB client for tests
vi.mock('@/lib/db/client', () => ({
  default: new Database(':memory:')
}))

describe('getUserById', () => {
  beforeEach(() => {
    runMigrations()
  })

  it('returns undefined for unknown id', () => {
    expect(getUserById('does-not-exist')).toBeUndefined()
  })

  it('returns the user after creation', () => {
    createUser({ id: 'u1', email: 'a@example.com', name: 'Alice' })
    expect(getUserById('u1')).toMatchObject({ email: 'a@example.com' })
  })
})
```

**Why real DB in tests:** SQLite mocks hide bugs that only appear with real SQL (e.g., constraint violations, wrong column names, transaction rollback behavior).

### What to test

- All query functions in `lib/db/queries/`
- Auth helpers in `lib/auth/`
- Utility functions in `lib/utils/`
- Server Actions (test the function directly, not via the UI)

Do not write tests for:
- React component rendering (use manual QA or Playwright for E2E)
- Next.js routing behavior (framework-tested)
- Trivial pass-through functions with no logic

---

## Anti-Patterns

These patterns are forbidden in this codebase:

### SQL in route handlers or components
```ts
// NEVER DO THIS in app/api/ or components/
import db from '@/lib/db/client'
const user = db.prepare('SELECT * FROM users WHERE id = ?').get(id)
```
Always go through `lib/db/queries/`.

### Client components fetching data with useEffect
```tsx
// NEVER DO THIS
'use client'
useEffect(() => { fetch('/api/data').then(...) }, [])
```
Use Server Components or SWR/React Query only when real-time updates are required.

### Mutating DB state directly from a component
Components should call Server Actions or API routes, never import DB query functions directly.

### String-interpolated SQL
```ts
// NEVER DO THIS — SQL injection
db.exec(`DELETE FROM users WHERE id = '${id}'`)
```

### Committing .env.local
Add `.env.local` to `.gitignore` and keep it there.

### Editing applied migrations
Once a migration is in production, it is immutable. Add a new migration instead.

### Catching errors without logging
```ts
// NEVER DO THIS
} catch { }
} catch (err) { return null }
```

### useEffect for derived state
```tsx
// NEVER DO THIS — use useMemo or compute inline
const [fullName, setFullName] = useState('')
useEffect(() => { setFullName(`${first} ${last}`) }, [first, last])
```

---

## TypeScript

- Strict mode is enabled. No `any` without a comment explaining why.
- Prefer `interface` for object shapes, `type` for unions and computed types.
- DB row types (suffixed `Row`) represent the raw DB shape. Application types strip `_at` timestamps and convert IDs. Map at the query boundary.

```ts
interface UserRow { id: string; email: string; created_at: number }
interface User { id: string; email: string; createdAt: Date }

function rowToUser(row: UserRow): User {
  return { id: row.id, email: row.email, createdAt: new Date(row.created_at * 1000) }
}
```

- Use `satisfies` to get both type checking and inference:
```ts
const config = {
  maxRetries: 3,
  timeout: 5000,
} satisfies Partial<RequestConfig>
```

---

## Security

- Validate all user input at the API boundary before it reaches the DB layer. Use `zod` for schema validation.
- Sanitize HTML before rendering user-generated content (use `DOMPurify` on the client or `sanitize-html` on the server).
- Session tokens must be cryptographically random (use `crypto.randomBytes(32).toString('hex')`).
- Set `httpOnly` and `sameSite=lax` on session cookies.
- Rate-limit auth endpoints. Use a middleware-based approach rather than per-route logic.

---

## Git & PRs

- Branch names: `feat/short-description`, `fix/short-description`, `chore/short-description`
- Commit messages follow Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`
- One logical change per commit. Do not bundle unrelated changes.
- PRs require `npm run typecheck` and `npm test` to pass in CI before merge.
