# CLAUDE.md — Next.js 15 + SQLite SaaS Project Template

## Stack & Versions

- **Runtime**: Node.js 20+
- **Framework**: Next.js 15 (App Router, React 19)
- **Database**: SQLite via `better-sqlite3` (sync, no ORM magic)
- **Auth**: NextAuth.js v5 or custom JWT (no Auth0, no Clerk — keep it self-contained)
- **Styling**: Tailwind CSS v4 (utility-first, no CSS-in-JS)
- **Deployment**: Vercel or Node adapter

**Why this stack**: Minimal dependencies, zero cold starts, SQLite is production-ready for <100k DAU, no external DB services needed.

---

## Project Structure

```
├── app/                    # Next.js App Router pages
│   ├── (auth)/             # Auth routes: /login, /register, /logout
│   ├── (dashboard)/       # Protected routes requiring authentication
│   │   ├── page.tsx        # Dashboard home
│   │   ├── settings/       # User settings
│   │   └── [id]/           # Resource detail pages
│   ├── api/                # Route handlers (avoid if possible — prefer Server Actions)
│   │   └── webhooks/       # Third-party webhooks only
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Landing/marketing page
├── components/
│   ├── ui/                 # Headless base components (buttons, inputs, modals)
│   │   └── button.tsx      # ONE button component, variants via className
│   ├── forms/              # Form components bound to Zod schemas
│   └── features/            # Feature-specific components (co-located with feature)
├── lib/
│   ├── db.ts                # SQLite connection singleton (better-sqlite3)
│   ├── schema.sql           # All DDL — committed, never auto-generated
│   └── migrations/          # Numbered SQL files: 001_init.sql, 002_add_field.sql
├── actions/                # Next.js Server Actions (prefer over API routes)
│   ├── auth.ts
│   ├── users.ts
│   └── [resource].ts
├── middleware.ts           # Auth guard only — no business logic
└── package.json
```

**Why**: Flat is better than nested. If a component isn't reused, keep it inside the feature folder. No `utils/` folder — put utilities where they belong.

---

## Database Conventions

### Migrations (MANDATORY)

**Never modify schema.sql directly after v1.** All changes go through migrations.

```
migrations/
├── 001_init.sql
├── 002_add_users_avatar.sql
└── 003_create_subscriptions.sql
```

Run migrations on startup:
```ts
// lib/db.ts
import Database from 'better-sqlite3'
import { readFileSync } from 'fs'
import { join } from 'path'

const db = new Database(process.env.DATABASE_PATH || './data/app.db')
db.pragma('journal_mode = WAL')
db.pragma('foreign_keys = ON')

// Run pending migrations
const migrations = db.prepare(`
  CREATE TABLE IF NOT EXISTS migrations (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    applied_at TEXT DEFAULT CURRENT_TIMESTAMP
  )
`)

const applied = new Set(db.prepare('SELECT name FROM migrations').all().map((r: any) => r.name))
const files = readdirSync(join(process.cwd(), 'lib/migrations')).sort()

for (const file of files) {
  if (!applied.has(file)) {
    db.exec(readFileSync(join(process.cwd(), 'lib/migrations', file), 'utf-8'))
    db.prepare('INSERT INTO migrations (name) VALUES (?)').run(file)
    console.log('Applied migration:', file)
  }
}
```

### Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Tables | snake_case, plural | `users`, `subscriptions` |
| Columns | snake_case | `created_at`, `stripe_customer_id` |
| Indexes | `idx_<table>_<column>` | `idx_users_email` |
| Foreign keys | `<table>_id` | `user_id`, `plan_id` |

**Why**: SQLite doesn't enforce FKs by default — always name your FK columns explicitly.

### SQL Rules

1. **Always use parameterized queries** — never string concatenation:
   ```ts
   // WRONG
   db.prepare(`SELECT * FROM users WHERE email = '${email}'`)
   
   // RIGHT
   db.prepare('SELECT * FROM users WHERE email = ?').get(email)
   ```

2. **SELECT always includes columns explicitly** — no `SELECT *` in application code.

3. **Every table has**: `id` (INTEGER PRIMARY KEY), `created_at`, `updated_at`.

4. **Soft deletes preferred** over hard deletes for user data. Hard deletes only for user-initiated GDPR requests.

---

## Component Patterns

### Rules

1. **Server Components by default.** Add `'use client'` only when you need interactivity.
2. **One component per file.** No barrelled exports of everything.
3. **No prop drilling.** Use React Context or URL state for shared state.
4. **Form components are client components.** They validate with Zod on the client AND re-validate with Server Actions on the server.

### Component File Structure

```tsx
// components/features/billing/plan-card.tsx
'use client'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/classname'
import type { Plan } from './types'

interface Props {
  plan: Plan
  currentPlanId: string | null
  onSelect: (planId: string) => void
}

export function PlanCard({ plan, currentPlanId, onSelect }: Props) {
  const isCurrent = plan.id === currentPlanId
  
  return (
    <div className={cn('border rounded-lg p-4', isCurrent && 'ring-2 ring-primary')}>
      <h3>{plan.name}</h3>
      <Button onClick={() => onSelect(plan.id)} disabled={isCurrent}>
        {isCurrent ? 'Current Plan' : 'Select'}
      </Button>
    </div>
  )
}
```

---

## What We Don't Do (and Why)

### Anti-patterns to Avoid

| Anti-pattern | Why | Use Instead |
|-------------|-----|-------------|
| `console.log` in production | Leaks data, no log levels | `console.error` or a proper logger |
| `try/catch` swallowing errors | Silent failures are worse than crashes | Let errors propagate, handle at boundary |
| `useEffect` for data fetching | Hydration mismatch risk, no SSR | Server Components or Server Actions |
| `getServerSideProps` | Deprecated in App Router | Server Components directly |
| API Routes for CRUD | Extra network hop, no co-location | Server Actions |
| Client-side auth checks | Bypassable | Middleware + Server Action checks |
| Environment variables starting with `NEXT_PUBLIC_` for secrets | Exposed to browser | Server-only via Server Actions |

---

## Dev Commands

```bash
npm run dev      # Start dev server (http://localhost:3000)
npm run build    # Production build
npm run db:migrate  # Run migrations (wrapper around better-sqlite3 CLI)
npm run db:seed  # Seed development data
npm run lint     # ESLint + TypeScript
npm run typecheck # tsc --noEmit
```

---

## Testing Strategy

- **Unit**: Zod schemas, utility functions → `vitest`
- **Integration**: Server Actions, DB queries → `vitest` with in-memory SQLite
- **E2E**: Critical flows (auth, payments) → Playwright

No test for the sake of test coverage. Test behavior, not implementation.

---

## Environment Variables

```bash
# Required
DATABASE_PATH=./data/app.db

# Optional
NEXTAUTH_SECRET=   # Generate with: openssl rand -base64 32
NEXTAUTH_URL=http://localhost:3000
```

**Never commit `.env` files. Use `.env.example` with all variable names (no values).**
