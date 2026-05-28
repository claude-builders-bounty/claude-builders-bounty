# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions

- **Framework**: Next.js 15 (App Router, React 19)
- **Database**: SQLite via `better-sqlite3` (local dev) or `@libsql/client` (Turso in prod)
- **ORM**: None — raw SQL with typed query helpers
- **Auth**: `better-auth` with SQLite adapter
- **Styling**: Tailwind CSS v4 with `shadcn/ui` components
- **Validation**: `zod` for schema validation at all boundaries
- **Testing**: Vitest + Playwright for E2E
- **Runtime**: Node.js 22 LTS

## Folder Structure

```
src/
  app/                   # Next.js App Router pages
    (auth)/              # Auth route group (login, register, reset)
    (dashboard)/         # Authenticated route group
    api/                 # API routes (route.ts only, no page.tsx)
  components/
    ui/                  # shadcn/ui primitives (never edit these)
    shared/              # Reusable app components
    features/            # Feature-scoped components (co-located with pages)
  lib/
    db/
      client.ts          # Single DB connection export
      schema.sql         # Source of truth — all CREATE TABLE statements
      migrations/        # Sequential numbered migration files (0001_init.sql)
    auth.ts              # better-auth config
    validations/         # Zod schemas (one file per domain)
  hooks/                 # React hooks (client-side only)
  types/                 # Shared TypeScript types (no runtime code)

db.sqlite                # Local dev DB (gitignored)
```

## Dev Commands

```bash
npm run dev          # Start dev server (port 3000)
npm run db:migrate   # Apply pending migrations
npm run db:seed      # Seed dev data
npm run db:reset     # Drop + recreate + seed (dev only)
npm test             # Vitest unit tests
npm run test:e2e     # Playwright E2E tests
npm run build        # Production build
npm run typecheck    # tsc --noEmit (run before every commit)
```

## SQL / Migration Rules

**Schema is the source of truth.** `schema.sql` always reflects current state.

**Migration conventions:**
- File name: `0001_init.sql`, `0002_add_users.sql` — sequential, never gaps
- Never edit an existing migration — create a new one instead
- Each migration must be idempotent: use `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`
- Foreign keys are always enabled: `PRAGMA foreign_keys = ON` runs on every connection

**Query patterns — always use these:**
```ts
// Good: parameterized, typed
const user = db.prepare('SELECT * FROM users WHERE id = ?').get(id) as User | null

// Bad: string concatenation
const user = db.prepare(`SELECT * FROM users WHERE id = ${id}`).get() // SQL injection risk
```

**Never use raw `db.exec()` with user input.** Only for migrations and seeds.

## Component Patterns

**Server Components by default.** Only add `'use client'` when you need:
- `useState`, `useEffect`, or other hooks
- Browser APIs (`window`, `document`)
- Event handlers that fire on user interaction

**Data fetching lives in Server Components:**
```tsx
// Good — fetch in RSC, pass data down
export default async function UsersPage() {
  const users = await getUsers() // direct DB call, no API round-trip
  return <UserList users={users} />
}

// Bad — fetching in useEffect
export default function UsersPage() {
  const [users, setUsers] = useState([])
  useEffect(() => { fetch('/api/users').then(...) }, []) // unnecessary API hop
}
```

**Server Actions for mutations:**
```ts
'use server'
export async function createUser(formData: FormData) {
  const parsed = userSchema.safeParse(Object.fromEntries(formData))
  if (!parsed.success) return { error: parsed.error.flatten() }
  // insert into DB
  return { success: true }
}
```

**Component file rules:**
- One component per file, filename matches component name
- Props interface defined at the top of the file, named `<ComponentName>Props`
- No default exports from `lib/` — named exports only

## Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Components | PascalCase | `UserCard.tsx` |
| Hooks | camelCase with `use` prefix | `useCurrentUser.ts` |
| Server actions | camelCase verbs | `createUser`, `deletePost` |
| DB tables | snake_case plural | `users`, `subscription_plans` |
| DB columns | snake_case | `created_at`, `stripe_customer_id` |
| Zod schemas | camelCase with `Schema` suffix | `userSchema`, `createPostSchema` |
| API routes | kebab-case segments | `/api/subscription-plans` |

## Patterns to Follow

**Validate at every boundary:**
```ts
// API route: validate request body
const result = createUserSchema.safeParse(await request.json())
if (!result.success) return NextResponse.json({ error: result.error.flatten() }, { status: 400 })
```

**Error handling — explicit, never silent:**
```ts
// Good
try {
  const user = db.prepare('SELECT * FROM users WHERE id = ?').get(id)
  if (!user) return null
  return user as User
} catch (err) {
  console.error('[db] getUser failed:', err)
  throw new Error('Failed to fetch user')
}

// Bad
const user = db.prepare('SELECT * FROM users WHERE id = ?').get(id) // unhandled exception crashes server
```

**Auth check at the top of every Server Component and Server Action:**
```ts
const session = await auth.api.getSession({ headers: await headers() })
if (!session) redirect('/login')
```

## What We Don't Do (and Why)

| ❌ Don't | ✅ Do instead | Why |
|---------|-------------|-----|
| `pages/` directory | `app/` directory | We're on App Router — mixing breaks layouts |
| Prisma or Drizzle ORM | Raw SQL + typed helpers | SQLite + ORMs add complexity without benefit at this scale |
| `useEffect` for data fetching | Server Components | Eliminates loading states, waterfalls, and client bundles |
| `any` type | Explicit types or `unknown` | `any` defeats the purpose of TypeScript |
| Mutating state directly | `setState(prev => ({...prev, key: val}))` | Prevents subtle React bugs |
| `console.log` in production code | Structured logging or remove | Leaks internals, pollutes logs |
| Inline SQL in components | `lib/db/queries/*.ts` | Keeps data access testable and auditable |
| Multiple DB connections | Single `lib/db/client.ts` | SQLite is file-locked — one connection per process |
| `DELETE FROM table` without WHERE | Always specify a WHERE clause | One typo wipes the entire table |
| Storing secrets in code | `.env.local` + validate at startup | Secrets in code = leak in git history forever |

## Environment Variables

Required at startup — validated in `lib/env.ts`:
```ts
// lib/env.ts
import { z } from 'zod'
const envSchema = z.object({
  DATABASE_URL: z.string().min(1),        // 'file:./db.sqlite' or Turso URL
  BETTER_AUTH_SECRET: z.string().min(32),
  BETTER_AUTH_URL: z.string().url(),
})
export const env = envSchema.parse(process.env)
```

Never access `process.env` directly outside `lib/env.ts`.

## SQLite-Specific Rules

- **WAL mode** enabled on every connection: `PRAGMA journal_mode = WAL`
- **One write connection, one read connection** in production (Turso handles this automatically)
- Timestamps stored as `INTEGER` (Unix epoch ms), not ISO strings — faster comparisons
- Boolean stored as `INTEGER` (0/1) — SQLite has no native boolean type
- UUIDs generated in application layer (`crypto.randomUUID()`), not in SQL
