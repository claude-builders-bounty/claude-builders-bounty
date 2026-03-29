# CLAUDE.md — Next.js 15 + SQLite SaaS Project

This file contains the project-specific rules and context for Claude Code.
Read this before making any changes. Every rule here exists because someone got burned.

---

## Project Overview

**Stack:** Next.js 15 (App Router) · TypeScript strict · SQLite (better-sqlite3) · Tailwind CSS · shadcn/ui

**This is a SaaS application.** It has paying users. Code changes can affect production.

---

## Directory Structure

```
src/
  app/                    # Next.js App Router pages and layouts
    (auth)/               # Auth group — login, register, forgot-password
    (dashboard)/          # Protected routes — sidebar layout
    api/                  # Route handlers (NOT server actions)
  components/
    ui/                   # shadcn/ui primitives — DO NOT modify
    features/             # Domain-specific components (billing/, onboarding/, etc.)
    shared/               # Shared across features (Logo, Avatar, etc.)
  lib/
    db/                   # Database layer ONLY — queries go here, NOT in components
      schema.ts           # Table definitions (single source of truth)
      migrations/         # SQL files: 001_initial.sql, 002_add_teams.sql, etc.
    auth/                 # Auth utilities (session, permissions)
    stripe/               # Stripe client and webhook handlers
  types/                  # Global TypeScript interfaces
db.sqlite                 # Local dev database — never commit
db.sqlite-wal             # WAL file — never commit
```

**Rule:** No business logic in `app/`. Pages fetch data, they don't compute it.
**Rule:** No direct `db` calls in components. All queries go through `src/lib/db/`.

---

## Dev Commands

```bash
npm run dev           # Start dev server (port 3000)
npm run build         # Production build (run before PR)
npm run typecheck     # TypeScript strict check — must pass
npm run lint          # ESLint — must pass
npm run db:migrate    # Apply pending SQL migrations
npm run db:seed       # Seed dev database
npm run db:reset      # Drop + recreate + seed (dev only)
npm run stripe:listen # Forward Stripe webhooks to localhost
```

**Before opening a PR:** `npm run build && npm run typecheck && npm run lint` must all pass.

---

## Database Rules

### Schema Changes

1. **Never use `db.exec()` to modify schema directly.** Create a migration file.
2. Migration files are in `src/lib/db/migrations/` named `NNN_description.sql` (e.g., `004_add_api_keys.sql`)
3. Run `npm run db:migrate` to apply — it's idempotent (uses `IF NOT EXISTS`)
4. **Never modify an existing migration file.** If you made a mistake, create a new migration.
5. Update `src/lib/db/schema.ts` to reflect the new schema after migrating.

**Why:** Migration files are the source of truth for production schema. Modifying them breaks deployments.

### Query Patterns

```typescript
// CORRECT — parameterized, goes through lib/db
import { db } from '@/lib/db'
const user = db.prepare('SELECT * FROM users WHERE id = ?').get(userId)

// WRONG — never construct queries with string interpolation
const user = db.prepare(`SELECT * FROM users WHERE id = ${userId}`).get() // SQL INJECTION

// CORRECT — batch inserts
const insertMany = db.transaction((rows) => {
  const stmt = db.prepare('INSERT INTO items (name, user_id) VALUES (?, ?)')
  for (const row of rows) stmt.run(row.name, row.userId)
})
insertMany(items)
```

**Rule:** Never use string interpolation in SQL queries. Always use `?` placeholders.

### SQLite-Specific Rules

- **WAL mode is enabled** (`PRAGMA journal_mode=WAL`). Don't change this.
- **Foreign keys are enforced** (`PRAGMA foreign_keys=ON`). Don't skip this.
- Use `INTEGER` for booleans (0/1), not `BOOLEAN` — SQLite doesn't have a boolean type.
- Timestamps are stored as `TEXT` in ISO 8601 (`DATETIME DEFAULT (datetime('now'))`)
- Row IDs are `INTEGER PRIMARY KEY` — they auto-increment, don't set them manually.

---

## Authentication

- Auth is cookie-based. Session is stored server-side in SQLite `sessions` table.
- `getSession()` in `src/lib/auth/session.ts` — use this in every server component and route handler that needs the current user.
- **Never expose user passwords.** The `users` table `password` column is a bcrypt hash — never SELECT it in responses.
- Protected routes are in `(dashboard)/` — the layout already calls `getSession()` and redirects to `/login` if unauthenticated.

```typescript
// In a Server Component or Route Handler:
import { getSession } from '@/lib/auth/session'
const session = await getSession()
if (!session) redirect('/login') // This should already be handled by layout
const { userId, email } = session
```

**Rule:** Never put auth checks in Client Components. Use Server Components or middleware.

---

## API Route Handlers

All API routes live in `src/app/api/`. They are Route Handlers, not pages.

```typescript
// src/app/api/items/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { getSession } from '@/lib/auth/session'

export async function GET(request: NextRequest) {
  const session = await getSession()
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }
  // ... business logic
  return NextResponse.json({ data })
}
```

**Rules:**
- Always check session in route handlers — layouts don't protect API routes.
- Return `{ error: string }` for errors, `{ data: T }` for success.
- Never throw unhandled errors in route handlers — catch and return 500.

---

## Stripe Integration

- Stripe client: `src/lib/stripe/client.ts`
- Webhook handler: `src/app/api/webhooks/stripe/route.ts`
- **Always verify webhook signatures.** Never skip `stripe.webhooks.constructEvent()`.
- Subscriptions are stored in `subscriptions` table — sync from Stripe webhooks, not from API calls.
- Use `stripe.customers.retrieve()` to get customer, not a raw DB query — Stripe is source of truth for billing.

**When adding a Stripe event handler:**
1. Add the event type to the switch in `webhook/route.ts`
2. Write a handler function in `src/lib/stripe/handlers.ts`
3. Test with `npm run stripe:listen` + `stripe trigger <event>`

---

## Component Patterns

### Server vs Client Components

- **Default to Server Components.** Only add `'use client'` when you need:
  - `useState` or `useEffect`
  - Browser events (`onClick`, `onChange`)
  - Browser APIs (`localStorage`, `window`)

```typescript
// CORRECT — Server Component (no directive needed)
async function UserProfile({ userId }: { userId: string }) {
  const user = db.prepare('SELECT name, email FROM users WHERE id = ?').get(userId)
  return <div>{user.name}</div>
}

// CORRECT — Client Component (only when necessary)
'use client'
function ToggleButton() {
  const [open, setOpen] = useState(false)
  return <button onClick={() => setOpen(!open)}>Toggle</button>
}
```

### Data Fetching

- Fetch data in Server Components or Route Handlers. Not in Client Components via `useEffect`.
- Use `React.cache()` for server-side data that's fetched multiple times per request.
- No `fetch('/api/...')` calls from Server Components — call the function directly.

---

## TypeScript Rules

- **`strict: true` is non-negotiable.** No `@ts-ignore`, no `any` without a comment explaining why.
- Use `z.infer<typeof Schema>` from Zod for form/API payload types.
- All DB rows have types in `src/types/db.ts` — add new ones when you add tables.
- Prefer `type` over `interface` for object shapes (consistency with existing code).

---

## What We Don't Do (Anti-Patterns)

| Don't | Why | Do This Instead |
|-------|-----|-----------------|
| `db.exec(dynamicSQL)` | SQL injection risk | Use `db.prepare().run()` with `?` params |
| `useEffect` to fetch data | Race conditions, waterfalls | Server Components or SWR |
| Storing secrets in code | Security | `.env.local`, never commit |
| `any` type | Defeats TypeScript | Proper types or `unknown` + guard |
| Modifying `src/components/ui/` | Breaks shadcn updates | Create in `features/` or `shared/` |
| Direct `process.env` in components | Leaks server secrets | `src/lib/config.ts` with explicit exports |
| `console.log` in production code | Log noise | Use the logger in `src/lib/logger.ts` |
| Synchronous SQLite in route handlers | Blocks event loop | better-sqlite3 is sync by design — keep queries fast |
| Client-side auth checks | Security bypass | Middleware + Server Components only |

---

## Environment Variables

Required in `.env.local`:

```env
# Database
DATABASE_URL=./db.sqlite

# Auth
AUTH_SECRET=<32-char random string>
NEXTAUTH_URL=http://localhost:3000

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...

# App
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

**Rule:** Variables prefixed with `NEXT_PUBLIC_` are exposed to the browser. Never put secrets there.

---

## Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Components | PascalCase | `UserProfile.tsx` |
| Hooks | camelCase, `use` prefix | `useSubscription.ts` |
| DB queries | camelCase functions | `getUserById()` |
| API routes | kebab-case directories | `api/billing-portal/route.ts` |
| Migration files | `NNN_snake_case.sql` | `005_add_team_members.sql` |
| Types | PascalCase | `type UserRow = {...}` |
| Env vars | UPPER_SNAKE_CASE | `STRIPE_SECRET_KEY` |

---

## Git / PR Rules

- Branch names: `feat/feature-name`, `fix/bug-description`, `chore/task-name`
- PRs must pass: `npm run build` + `npm run typecheck` + `npm run lint`
- No direct commits to `main` — always PR
- Keep PRs focused: one feature or fix per PR

---

## Common Tasks

**Add a new database table:**
```bash
# 1. Create migration
echo "CREATE TABLE IF NOT EXISTS widgets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);" > src/lib/db/migrations/005_add_widgets.sql

# 2. Apply migration
npm run db:migrate

# 3. Update schema.ts
# Add the WidgetRow type to src/types/db.ts
```

**Add a new protected page:**
```
# Create src/app/(dashboard)/widgets/page.tsx
# It's auto-protected by the (dashboard) layout
```

**Add a new API endpoint:**
```
# Create src/app/api/widgets/route.ts
# Add GET/POST handlers with session check
```
