# CLAUDE.md — Next.js 15 + SQLite SaaS

This file tells Claude how to work in this codebase. Read it fully before writing any code.

## Stack

- **Framework**: Next.js 15 (App Router, React Server Components)
- **Database**: SQLite via `better-sqlite3` (local) or `@libsql/client` (Turso in prod)
- **Auth**: `next-auth` v5 (Auth.js)
- **Styling**: Tailwind CSS v4
- **Validation**: Zod
- **ORM**: None — raw SQL with typed query helpers

## Project Structure

```
src/
  app/                    # App Router pages and layouts
    (auth)/               # Route group — unauthenticated pages
    (dashboard)/          # Route group — protected pages
    api/                  # API route handlers
  components/
    ui/                   # Primitive UI components (Button, Input, Modal)
    features/             # Domain-specific components (UserCard, BillingPanel)
  lib/
    db.ts                 # SQLite client singleton
    queries/              # One file per domain: users.ts, subscriptions.ts
    validations/          # Zod schemas
    auth.ts               # Auth.js config
  hooks/                  # Client-side React hooks
  types/                  # Shared TypeScript types
migrations/               # SQL migration files — never edit, only add
public/
```

## Database Rules

1. **Never edit migration files** — only add new ones.
2. Migration filenames: `YYYYMMDD_HHMMSS_description.sql` (e.g. `20260528_143000_add_stripe_customer_id.sql`)
3. All migrations run via `npm run migrate` (reads `migrations/` in order)
4. Schema changes require a migration. Never use `ALTER TABLE` interactively.
5. Use `INTEGER PRIMARY KEY` for IDs — SQLite auto-increments.
6. Booleans: store as `INTEGER` (0/1). Dates: store as `TEXT` ISO-8601 or `INTEGER` Unix timestamp.
7. Always use parameterized queries — never string-interpolate user input into SQL.

```typescript
// ✅ correct
const user = db.prepare('SELECT * FROM users WHERE email = ?').get(email)

// ❌ never
const user = db.prepare(`SELECT * FROM users WHERE email = '${email}'`).get()
```

## Naming Conventions

| Thing | Convention | Example |
|---|---|---|
| Files | kebab-case | `user-profile.tsx` |
| Components | PascalCase | `UserProfile` |
| Server actions | camelCase + `Action` suffix | `updateUserAction` |
| DB query fns | verb + noun | `getUserById`, `createSubscription` |
| API routes | REST nouns | `/api/users`, `/api/subscriptions/[id]` |
| Env vars | SCREAMING_SNAKE | `DATABASE_URL` |

## Patterns to Follow

### Server Components by default
Fetch data in Server Components. Use `'use client'` only when you need interactivity or browser APIs.

```typescript
// ✅ server component — fetch directly
export default async function DashboardPage() {
  const user = await getUserById(session.user.id)
  return <UserCard user={user} />
}
```

### Server Actions for mutations
```typescript
'use server'
import { z } from 'zod'
import { revalidatePath } from 'next/cache'

const schema = z.object({ name: z.string().min(1).max(100) })

export async function updateProfileAction(formData: FormData) {
  const { name } = schema.parse(Object.fromEntries(formData))
  updateUser(session.user.id, { name })
  revalidatePath('/dashboard/profile')
}
```

### Error handling
- Server actions return `{ error: string }` on failure — never throw to the client
- Use `notFound()` from `next/navigation` for missing resources
- Log errors server-side; never expose stack traces to the client

### Auth guard
```typescript
import { auth } from '@/lib/auth'
import { redirect } from 'next/navigation'

export default async function ProtectedPage() {
  const session = await auth()
  if (!session) redirect('/login')
  // ...
}
```

## Anti-patterns to Avoid

- ❌ `useEffect` for data fetching — use Server Components or `useSWR`
- ❌ Storing secrets in `.env.local` without adding to `.env.example`
- ❌ `any` types — use `unknown` and narrow with Zod
- ❌ Inline SQL in components — all queries go in `src/lib/queries/`
- ❌ Direct DB calls in API routes — always go through query helpers
- ❌ Client-side redirect after mutation — use `redirect()` in server action
- ❌ Editing `package-lock.json` manually

## Dev Commands

```bash
npm run dev          # Start dev server (http://localhost:3000)
npm run build        # Production build
npm run migrate      # Run pending SQL migrations
npm run db:seed      # Seed dev database
npm run lint         # ESLint
npm run typecheck    # tsc --noEmit
npm test             # Vitest
```

## Environment Variables

```bash
# Required
DATABASE_URL=file:./dev.db          # local SQLite path or Turso URL
AUTH_SECRET=<32-char random string>  # openssl rand -base64 32
NEXTAUTH_URL=http://localhost:3000

# Optional
TURSO_AUTH_TOKEN=                    # Turso production token
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
```

Never commit `.env.local`. Always update `.env.example` when adding a new variable.

## Before You Write Code

1. Check `src/lib/queries/` — the query you need might already exist
2. Check `src/components/ui/` — the UI primitive might already exist
3. Run `npm run typecheck` and `npm run lint` before considering a task done
4. Server actions always validate input with Zod before touching the DB
