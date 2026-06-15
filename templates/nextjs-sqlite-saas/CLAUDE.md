# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions

- **Framework**: Next.js 15 (App Router, React 19)
- **Database**: SQLite via `better-sqlite3` (synchronous, no ORM)
- **Auth**: `next-auth` v5 (beta) — credentials + OAuth providers
- **Styling**: Tailwind CSS v4
- **Payments**: Stripe (webhooks handled in `app/api/webhooks/stripe/route.ts`)
- **Runtime**: Node.js 20+, deployed on Railway or Fly.io (not Vercel — SQLite needs persistent disk)

## Folder Structure

```
app/
  (auth)/          # login, signup, reset — no sidebar layout
  (dashboard)/     # protected routes — sidebar layout
    layout.tsx     # checks session, redirects to /login if missing
    page.tsx       # /dashboard root
  api/
    webhooks/
      stripe/      # POST only, raw body, verify Stripe-Signature header
    auth/          # next-auth handlers
  layout.tsx       # root layout — fonts, global providers
  page.tsx         # marketing homepage

lib/
  db.ts            # single better-sqlite3 instance, exported as `db`
  auth.ts          # next-auth config — import here, not from next-auth directly
  stripe.ts        # Stripe client singleton

migrations/        # numbered SQL files: 0001_init.sql, 0002_add_teams.sql
scripts/
  migrate.ts       # run with: npx tsx scripts/migrate.ts

components/
  ui/              # shadcn/ui primitives — never edit these directly
  app/             # app-specific components
```

## Database Rules

**Always use `lib/db.ts`** — never instantiate `better-sqlite3` anywhere else:

```ts
// lib/db.ts
import Database from 'better-sqlite3'
import path from 'path'

const DB_PATH = process.env.DB_PATH || path.join(process.cwd(), 'data', 'app.db')
export const db = new Database(DB_PATH)
db.pragma('journal_mode = WAL')
db.pragma('foreign_keys = ON')
```

**Migrations** live in `migrations/` as numbered SQL files. Run `npx tsx scripts/migrate.ts` — never use `db.exec()` with inline schema in application code.

**No ORM.** Use prepared statements directly:

```ts
// Good
const user = db.prepare('SELECT * FROM users WHERE id = ?').get(userId)
const users = db.prepare('SELECT * FROM users WHERE plan = ?').all(plan)

// Never
db.exec(`SELECT * FROM users WHERE id = ${userId}`)  // SQL injection
```

**Transactions** for multi-step writes:

```ts
const transferCredits = db.transaction((fromId: number, toId: number, amount: number) => {
  db.prepare('UPDATE users SET credits = credits - ? WHERE id = ?').run(amount, fromId)
  db.prepare('UPDATE users SET credits = credits + ? WHERE id = ?').run(amount, toId)
})
transferCredits(1, 2, 100)
```

## SQL Conventions

- Table names: `snake_case`, plural (`users`, `stripe_events`, `team_members`)
- Column names: `snake_case`
- Primary keys: `id INTEGER PRIMARY KEY AUTOINCREMENT`
- Timestamps: `created_at INTEGER NOT NULL DEFAULT (unixepoch())` — store as Unix seconds, not ISO strings
- Soft deletes: `deleted_at INTEGER` — filter with `WHERE deleted_at IS NULL`
- Foreign keys: always define `REFERENCES table(id) ON DELETE CASCADE` or `ON DELETE SET NULL`
- Indexes: add for every column used in WHERE or JOIN — name as `idx_table_column`

## Next.js Patterns

**Server Components by default.** Only add `'use client'` when you need:
- `useState` / `useEffect`
- Browser APIs
- Event handlers that aren't form submissions

**Data fetching**: fetch in Server Components directly — no API routes for internal data:

```tsx
// app/(dashboard)/page.tsx
import { db } from '@/lib/db'
import { auth } from '@/lib/auth'

export default async function DashboardPage() {
  const session = await auth()
  const usage = db.prepare('SELECT * FROM usage WHERE user_id = ?').get(session!.user.id)
  return <UsageCard usage={usage} />
}
```

**Mutations**: use Server Actions, not API routes:

```ts
'use server'
import { db } from '@/lib/db'
import { auth } from '@/lib/auth'
import { revalidatePath } from 'next/cache'

export async function updateDisplayName(name: string) {
  const session = await auth()
  if (!session) throw new Error('Unauthorized')
  db.prepare('UPDATE users SET display_name = ? WHERE id = ?').run(name, session.user.id)
  revalidatePath('/dashboard/settings')
}
```

**Route protection**: handle in `middleware.ts`, not in each page:

```ts
// middleware.ts
export { auth as middleware } from '@/lib/auth'
export const config = { matcher: ['/dashboard/:path*', '/api/(?!webhooks).*'] }
```

## Development Commands

```bash
npm run dev          # start dev server (port 3000)
npm run build        # production build
npm run lint         # eslint
npm run typecheck    # tsc --noEmit
npx tsx scripts/migrate.ts   # run pending migrations
```

## Environment Variables

```bash
# .env.local (never commit)
DATABASE_URL=./data/app.db        # or absolute path on prod
NEXTAUTH_SECRET=<random-32-chars>
NEXTAUTH_URL=http://localhost:3000
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

Claude: always read `.env.example` before asking about env vars. Never create a `.env` file — only `.env.local` for development.

## What We Don't Do (And Why)

- **No Prisma / Drizzle** — adds abstraction over SQLite that doesn't pay off; prepared statements are faster and clearer
- **No tRPC** — Server Actions replace the need for a typed API layer for internal calls
- **No `useEffect` for data fetching** — use Server Components; `useEffect` fetching causes waterfall and no caching
- **No API routes for dashboard data** — they add a round-trip; Server Components fetch directly
- **No `any` types** — if you don't know the type, derive it: `typeof db.prepare('...').get()`
- **No inline styles** — Tailwind only; no `style={{}}` except for dynamic values that can't be expressed as classes
- **No `console.log` in production code** — use a structured logger (`pino`) or remove before commit
- **No `db.exec()` with user input** — always use prepared statements with `?` placeholders
- **No Vercel deployment** — SQLite needs a persistent disk; use Railway, Fly.io, or a VPS
- **No storing timestamps as ISO strings** — use `unixepoch()` (INTEGER); convert to Date in the UI layer only

## Stripe Webhook Rules

- Always verify `Stripe-Signature` header before processing
- Use `stripe.webhooks.constructEvent(rawBody, sig, process.env.STRIPE_WEBHOOK_SECRET!)`
- Raw body is required — do NOT parse JSON first; use `req.text()` not `req.json()`
- Store processed event IDs in `stripe_events` table to prevent double-processing
- Return `200` immediately for unknown event types — never return 4xx for unhandled events

## Component Conventions

- `components/ui/` — shadcn/ui only, never modified
- `components/app/` — business components, named by feature: `SubscriptionCard.tsx`, `UsageChart.tsx`
- Props interfaces inline in the file, named `<ComponentName>Props`
- No default exports for components — named exports only
- One component per file
