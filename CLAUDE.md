# Project Overview

SaaS application built with Next.js 15 (App Router), SQLite via better-sqlite3, and TypeScript strict mode. The DB runs locally as a file — no external database servers, no Docker required to develop.

## Stack & Versions

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15 (App Router) | RSC, Server Actions, streaming |
| Database | SQLite via better-sqlite3 | Zero infra, file-based, fast enough for most SaaS workloads |
| ORM | None — raw SQL via a `db/` layer | ORMs hide SQLite's strengths; raw SQL is transparent and debuggable |
| Styling | Tailwind CSS v4 | Utility-first, no runtime, tree-shakeable |
| Auth | next-auth v5 (Auth.js) | App Router native, works with Server Actions |
| Migrations | Custom `migrations/` folder with sequential SQL files | Simple, auditable, no framework lock-in |
| Testing | Vitest + Playwright | Fast unit tests + full browser E2E |
| Package Manager | pnpm | Disk efficient, strict dependency resolution |

## Folder Structure

```
├── app/                    # Next.js App Router pages and API routes
│   ├── (auth)/             # Route group — auth pages (login, register)
│   ├── (dashboard)/        # Route group — authenticated pages
│   │   ├── @sidebar/       # Parallel route — sidebar slot
│   │   └── dashboard/      # Dashboard pages
│   ├── api/                # API route handlers (webhooks, external callbacks)
│   ├── layout.tsx          # Root layout
│   └── globals.css         # Tailwind imports + CSS variables
├── components/             # Shared React components
│   ├── ui/                 # Primitive UI components (Button, Input, Modal)
│   ├── forms/              # Form components connected to Server Actions
│   └── layouts/            # Shell components (Sidebar, Header, PageContainer)
├── lib/                    # Pure utility functions, no React
│   ├── db/                 # Database access layer
│   │   ├── client.ts       # better-sqlite3 singleton
│   │   ├── queries/        # Raw SQL query functions, one file per domain
│   │   └── migrate.ts      # Migration runner
│   ├── auth.ts             # Auth.js config
│   ├── email.ts            # Email helpers
│   └── utils.ts            # General utilities
├── migrations/             # Timestamped SQL migration files
│   ├── 20250101000000_create_users.sql
│   ├── 20250102000000_create_teams.sql
│   └── 20250103000000_add_stripe_customer_id.sql
├── public/                 # Static assets
├── tests/                  # Test files
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── config/                 # App configuration
    ├── site.ts             # Public site config (name, URL, support email)
    └── features.ts         # Feature flags
```

**Why this layout:** Groups by concern (db, auth, email) not by type. Putting `db/` under `lib/` signals these are internal implementation details, not public API. Migrations live at the root level because they're the source of truth for schema — they should be easy to find.

## Dev Commands

```bash
pnpm dev              # Start dev server on localhost:3000
pnpm build            # Production build (runs lint + migrate check)
pnpm start            # Start production server
pnpm test             # Run Vitest unit/integration tests
pnpm test:e2e         # Run Playwright E2E tests
pnpm lint             # ESLint + TypeScript check
pnpm format           # Prettier formatting
pnpm db:migrate       # Apply pending migrations
pnpm db:seed          # Seed development database
pnpm db:reset         # Drop and re-create DB (dev only)
```

## Naming Conventions

### Files

| Pattern | Example | Rule |
|---------|---------|------|
| `kebab-case` for routes | `app/(dashboard)/settings/billing/page.tsx` | App Router convention |
| `PascalCase` for components | `components/ui/PrimaryButton.tsx` | JSX component names must be capitalized |
| `camelCase` for utilities | `lib/db/queries/getUserByEmail.ts` | These are functions, not components |
| `snake_case` for SQL | `SELECT id, created_at FROM users` | SQL convention — Postgres/SQLite idiomatic |
| `YYYYMMDDHHmmss_` for migrations | `20250101000000_create_users.sql` | Sortable, conflict-free timestamps |

### Variables

| Context | Convention | Example |
|---------|-----------|---------|
| JavaScript/TypeScript | `camelCase` | `const userEmail = ...` |
| Database columns | `snake_case` | `created_at`, `stripe_customer_id` |
| Environment variables | `UPPER_SNAKE_CASE` | `DATABASE_URL`, `STRIPE_SECRET_KEY` |
| React state | `camelCase` — no prefix | `const [user, setUser] = ...` |
| Server Action | `camelCase` verb | `export async function createTeam(...)` |

### Routes (App Router Conventions)

- `app/page.tsx` — homepage
- `app/login/page.tsx` — login page
- `app/dashboard/page.tsx` — dashboard
- `app/api/stripe/webhook/route.ts` — webhook handler
- Layouts co-located in route groups: `app/(dashboard)/layout.tsx`

**Why kebab-case for routes:** Next.js treats folder names as URL segments. kebab-case is URL-safe, lowercase avoids casing ambiguity across platforms, and hyphens improve readability over underscores in URLs.

## SQL / Migration Conventions

### Migration Rules

1. **Every migration gets its own file** in `migrations/` with a Unix timestamp prefix.
2. **Never delete or edit a migration after it's been applied.** Always create a new migration.
3. **All schema changes use transactions** — wrap everything in `BEGIN` / `COMMIT`.
4. **Migrations are idempotent** — use `IF NOT EXISTS` / `IF EXISTS` or check before creating.
5. **One conceptual change per migration.** Don't bundle unrelated schema changes.
6. **Down migrations are optional** — up-only is acceptable. If you include a down migration, it must reverse the up migration exactly.

### Migration Template

```sql
-- migrations/20250101000000_create_users.sql
BEGIN;

CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    email         TEXT NOT NULL UNIQUE,
    name          TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_users_email ON users(email);

COMMIT;
```

### SQL Style

```sql
-- Good: explicit column list, consistent indentation, keyword casing
SELECT
    u.id,
    u.email,
    u.name,
    t.slug AS team_slug
FROM users u
INNER JOIN team_members tm ON tm.user_id = u.id
INNER JOIN teams t ON t.id = tm.team_id
WHERE u.email = ?;
```

- SQL keywords in UPPERCASE
- Table aliases (short, meaningful)
- `?` placeholders (better-sqlite3 convention) — never interpolate values into SQL
- One clause per line in complex queries
- Explicit column lists — never `SELECT *` in application code

### Database Access Patterns

```typescript
// lib/db/queries/users.ts
import db from '@/lib/db/client'

export function getUserByEmail(email: string) {
  return db.prepare('SELECT * FROM users WHERE email = ?').get(email) as User | undefined
}

export function createUser(email: string, name: string) {
  return db.prepare('INSERT INTO users (email, name) VALUES (?, ?) RETURNING *').get(email, name) as User
}

export function updateUser(id: string, data: Partial<Pick<User, 'name' | 'email'>>) {
  const sets = Object.keys(data).map(k => `${k} = ?`).join(', ')
  const values = Object.values(data)
  return db.prepare(`UPDATE users SET ${sets}, updated_at = datetime('now') WHERE id = ? RETURNING *`).get(...values, id) as User
}
```

**Why no ORM:** better-sqlite3's prepared statements are already a clean query builder. Adding Prisma/Drizzle layers an opaque codegen step on top. For SQLite-scale projects, the ORM abstraction adds more friction than it removes — schema drift between migrations and the ORM schema file, extra build step, and another set of errors to debug. Raw SQL is the source of truth.

## Component Patterns

### Server Components by Default

Every component starts as a Server Component. Only add `'use client'` when you NEED:

- `useState` / `useReducer` — interactive UI state
- `useEffect` — browser API access
- `useContext` — theme, auth context
- `onClick` / `onSubmit` — event handlers
- Browser-only APIs — `window`, `localStorage`, `IntersectionObserver`

```typescript
// ✅ Server Component (default)
// app/dashboard/page.tsx
import { getCurrentUser } from '@/lib/auth'
import { getUserTeams } from '@/lib/db/queries/teams'
import { TeamList } from '@/components/TeamList'

export default async function DashboardPage() {
  const user = await getCurrentUser()
  const teams = await getUserTeams(user.id)
  return <TeamList teams={teams} />
}
```

```typescript
// ✅ Client Component (only when needed)
// components/TeamList.tsx
'use client'
import { useState } from 'react'
import type { Team } from '@/types'

export function TeamList({ teams: initial }: { teams: Team[] }) {
  const [teams] = useState(initial)
  return <ul>{teams.map(t => <li key={t.id}>{t.name}</li>)}</ul>
}
```

### Loading States

Every page that awaits data must have a co-located `loading.tsx`:

```
app/dashboard/
├── page.tsx          # Async server component
├── loading.tsx       # Suspense fallback UI
└── error.tsx         # Error boundary
```

**Why co-located:** App Router routes are independently loadable. A loading state in a parent layout shouldn't block child routes. Co-located `loading.tsx` gives each segment its own Suspense boundary.

### Error Boundaries

Every route segment gets an `error.tsx`. The error boundary catches:

- Server Component render errors
- Server Action errors
- Client Component errors

```typescript
// app/dashboard/error.tsx
'use client'
export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div>
      <h2>Something went wrong</h2>
      <p>{error.message}</p>
      <button onClick={reset}>Try again</button>
    </div>
  )
}
```

### What NOT to do

- **No `getServerSideProps` or `getStaticProps`** — App Router native data fetching replaces both
- **No `_app.tsx` or `_document.tsx`** — replaced by `app/layout.tsx` and `app/template.tsx`
- **No `pages/` directory** — use `app/` exclusively. Mixing routers causes confusion

## Data Access Patterns

### Mutations: Server Actions

All data mutations go through Server Actions:

```typescript
// lib/actions/teams.ts
'use server'
import { revalidatePath } from 'next/cache'
import { createTeam as createTeamQuery } from '@/lib/db/queries/teams'
import { getCurrentUser } from '@/lib/auth'

export async function createTeam(formData: FormData) {
  const user = await getCurrentUser()
  const name = formData.get('name') as string

  const team = createTeamQuery(name, user.id)
  revalidatePath('/dashboard')
  return { team }
}
```

```typescript
// components/forms/CreateTeamForm.tsx
'use client'
import { createTeam } from '@/lib/actions/teams'

export function CreateTeamForm() {
  return (
    <form action={createTeam}>
      <input name="name" required />
      <button type="submit">Create Team</button>
    </form>
  )
}
```

### Queries: Server Components

Data fetching happens in Server Components, not in `useEffect`:

```typescript
// ✅
export default async function TeamPage({ params }: { params: { id: string } }) {
  const team = await getTeamById(params.id)
  return <TeamDetail team={team} />
}

// ❌ Never do this in client components unless you need real-time updates
// const [team, setTeam] = useState(null)
// useEffect(() => { fetch(`/api/teams/${id}`).then(setTeam) }, [id])
```

### Transactions for Multi-Step Operations

When an operation touches multiple tables, wrap it in a transaction:

```typescript
// lib/db/queries/teams.ts
import db from '@/lib/db/client'

export function createTeam(name: string, userId: string) {
  const createTeam = db.prepare('INSERT INTO teams (name) VALUES (?) RETURNING id')
  const addMember = db.prepare('INSERT INTO team_members (team_id, user_id, role) VALUES (?, ?, ?)')

  return db.transaction(() => {
    const { id } = createTeam.get(name) as { id: string }
    addMember.run(id, userId, 'owner')
    return id
  })()
}
```

**Why transactions:** Without them, a crash between the two inserts leaves orphan rows. SQLite transactions are cheap (no network round-trips like Postgres) so there's no perf reason to skip them.

## What We Don't Do (and why)

| Anti-pattern | Why we don't do it |
|---|---|
| **ORM (Prisma, Drizzle, TypeORM)** | SQLite direct access via better-sqlite3 is simpler and faster at this scale. Prisma's codegen step adds build complexity. Drizzle's query builder adds an abstraction layer between you and the SQL you're writing anyway. Raw SQL is transparent, debuggable, and the source of truth. |
| **CSS-in-JS (styled-components, Emotion)** | Tailwind CSS gives consistent design tokens, zero runtime cost, and tree-shaking. CSS-in-JS adds runtime overhead and a serialization step that hurts RSC performance. |
| **getServerSideProps / getStaticProps** | Replaced by native async Server Components in App Router. No more juggling props between `getServerSideProps` and the component — just `async function Page()`. |
| **Client-side state management (Zustand, Redux, Jotai)** | React Server Actions + URL search params + React context handle 95% of SaaS state needs. Global state libraries were a workaround for the absence of Server Actions and RSC. |
| **API routes for internal data (calling your own API from Server Components)** | Server Components can import DB queries directly. Wrapping internal queries in HTTP calls adds latency, error surface area, and unnecessary serialization. API routes are for external consumers (webhooks, third-party integrations). |
| **Cascading deletes in application code** | Define `ON DELETE CASCADE` in the migration schema. Application-level cascading is error-prone and duplicated across code paths. |
| **Migrations in CI applying automatically** | Migrations are manual via `pnpm db:migrate` before deployment. Automatic migration in CI risks partial deploys and race conditions. |
| **Feature flags as environment variables** | Feature flags live in `config/features.ts` as exported constants. Environment variables are for secrets, not toggles. Changing a flag means a deploy — that's intentional, not a bug. |
| **Console.log debugging** | Use `console.error` or a structured logger. `console.log` output is silent in production Next.js and invisible in server component logs. |
