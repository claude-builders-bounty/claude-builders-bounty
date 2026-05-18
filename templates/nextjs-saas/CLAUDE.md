# Next.js 15 + SQLite SaaS — CLAUDE.md

> **Opinionated project context for Claude Code. Every rule has a reason.**
> Drop this file at the repo root and Claude Code immediately understands your codebase.

---

## Stack & Versions

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15 (App Router) | RSC, streaming, server components — no Pages Router |
| Language | TypeScript (strict) | `strict: true` in tsconfig. Catch bugs at compile time |
| Database | SQLite via `better-sqlite3` | Synchronous API = no async/await hell. WAL mode for concurrent reads. Zero dependencies beyond the native binding |
| Auth | Auth.js v5 | Edge-compatible, works with any OAuth provider |
| Styling | Tailwind CSS 4 | Utility-first, no runtime CSS-in-JS overhead |
| Package Manager | pnpm | Strict dependency resolution, disk-efficient |

**What we DON'T use (and why):**
- **Prisma / Drizzle ORM** — Adds abstraction that hides SQL. For SQLite, raw SQL with prepared statements is simpler and faster. You can see exactly what query runs.
- **tRPC** — Adds ceremony for what is essentially a function call. Server Actions + Route Handlers cover the same ground with less code.
- **Zustand / Jotai** — Server Components + URL state (searchParams) eliminates most client state needs. For the rare client-only state, React Context is sufficient.

---

## Folder Structure

```
src/
├── app/                          # App Router (file-system routing)
│   ├── (auth)/                   # Route group: public auth pages
│   │   ├── login/page.tsx        #   /login
│   │   └── register/page.tsx     #   /register
│   ├── (dashboard)/              # Route group: authenticated pages
│   │   ├── layout.tsx            #   Shared sidebar + nav
│   │   ├── page.tsx              #   /dashboard
│   │   └── settings/page.tsx     #   /dashboard/settings
│   ├── api/                      # Route Handlers (REST endpoints)
│   │   └── webhooks/route.ts     #   External webhook receiver
│   ├── layout.tsx                # Root layout (fonts, metadata, providers)
│   └── page.tsx                  # Landing page (/)
├── components/
│   ├── ui/                       # Primitive components (Button, Input, Card, Modal)
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   └── index.ts             # Barrel export
│   └── [feature]/                # Feature-specific components (one folder per feature)
│       └── billing/
│           ├── plan-card.tsx
│           └── checkout-form.tsx
├── lib/
│   ├── db.ts                     # Database singleton (THE only db connection)
│   ├── db/
│   │   ├── schema.sql            # Canonical schema — single source of truth
│   │   ├── migrate.ts            # Migration runner
│   │   └── migrations/           # Numbered SQL migrations
│   │       ├── 001-create-users.sql
│   │       └── 002-add-teams.sql
│   ├── auth.ts                   # Auth.js configuration
│   ├── auth/
│   │   ├── session.ts            # getSession() helper for server components
│   │   └── middleware.ts         # Route protection logic
│   └── utils.ts                  # Pure utility functions (no side effects)
└── types/
    └── index.ts                  # Shared TypeScript types
```

**Why this structure:**
- `(auth)` and `(dashboard)` are route groups — they share layouts without affecting the URL
- `components/ui/` is flat. No deep nesting. If you have more than 15 primitives, split by category
- `lib/db/` groups everything database-related. A new developer knows exactly where to look
- No `hooks/` folder. Custom hooks live next to the components that use them

---

## Naming Conventions

| What | Convention | Example | Why |
|------|-----------|---------|-----|
| Files (components) | `kebab-case.tsx` | `plan-card.tsx` | Next.js file-system routing uses kebab-case. Consistency across the project |
| Files (utilities) | `kebab-case.ts` | `format-currency.ts` | Same as above |
| React components | `PascalCase` | `PlanCard` | Default export, matches filename convention |
| Functions | `camelCase` | `getUserById()` | Standard TypeScript |
| Database tables | `snake_case` | `user_teams` | SQL convention. Don't mix with camelCase |
| Database columns | `snake_case` | `created_at` | SQL convention. Always include `id`, `created_at`, `updated_at` |
| Migrations | `NNN-description.sql` | `003-add-invites.sql` | Sortable by prefix, readable by description |
| Route params | `[entityId]` | `[teamId]` | Descriptive param names, not just `[id]` |

---

## Commands

```bash
pnpm dev              # Start dev server on port 3000
pnpm build            # Production build
pnpm start            # Start production server
pnpm lint             # ESLint (strict config)
pnpm typecheck        # tsc --noEmit (type checking without emitting)
pnpm db:migrate       # Run pending migrations
pnpm db:seed          # Seed dev database with test data
pnpm db:reset         # Drop and recreate dev database (NEVER in production)
pnpm test             # Vitest (unit + integration)
pnpm test:e2e         # Playwright (end-to-end)
```

**When to run what:**
- Before every commit: `pnpm typecheck && pnpm lint`
- After adding a migration: `pnpm db:migrate`
- Before opening a PR: `pnpm test`

---

## Database Rules

### Schema is Law
`lib/db/schema.sql` is the **single source of truth**. When you need to understand the data model, read this file — not the migrations. Every table, column, index, and foreign key lives here with comments.

```sql
-- lib/db/schema.sql
CREATE TABLE IF NOT EXISTS users (
  id         TEXT PRIMARY KEY,           -- UUID v4
  email      TEXT NOT NULL UNIQUE,
  name       TEXT NOT NULL,
  avatar_url TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS teams (
  id         TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  owner_id   TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_teams_owner ON teams(owner_id);
```

### Migration Rules
- **Forward-only.** Never edit an existing migration file. Create a new one.
- **Naming:** `NNN-verb-noun.sql` (e.g., `004-add-billing-table.sql`)
- **Idempotent.** Use `IF NOT EXISTS` / `IF EXISTS` so re-running is safe
- **Tested.** Every migration must work on a fresh database AND on an existing one
- **No data in migrations.** Migrations change structure. Seed files add data.

### Query Patterns
Write raw SQL with prepared statements. One file per entity.

```typescript
// lib/db/queries/users.ts
import { db } from '@/lib/db';

interface User {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
  created_at: string;
}

export function getUserById(id: string): User | undefined {
  return db.prepare('SELECT * FROM users WHERE id = ?').get(id) as User | undefined;
}

export function getUserByEmail(email: string): User | undefined {
  return db.prepare('SELECT * FROM users WHERE email = ?').get(email) as User | undefined;
}

export function createUser(email: string, name: string): User {
  const id = crypto.randomUUID();
  db.prepare(
    'INSERT INTO users (id, email, name) VALUES (?, ?, ?)'
  ).run(id, email, name);
  return getUserById(id)!;
}

export function listUsersByTeam(teamId: string): User[] {
  return db.prepare(`
    SELECT u.* FROM users u
    JOIN team_members tm ON u.id = tm.user_id
    WHERE tm.team_id = ?
    ORDER BY u.name
  `).all(teamId) as User[];
}
```

**Query rules:**
- Always use prepared statements (`db.prepare().get/all/run`). Never string-interpolate user input.
- Return typed results. Use interfaces defined at the top of the file.
- One export per operation. Name describes exactly what it does.

### Database Connection
Exactly ONE database instance. Created once, shared everywhere.

```typescript
// lib/db.ts
import Database from 'better-sqlite3';
import path from 'path';

const DB_PATH = path.join(process.cwd(), 'data', 'app.db');

const db = new Database(DB_PATH);

// Performance
db.pragma('journal_mode = WAL');       // Write-Ahead Logging: concurrent reads
db.pragma('foreign_keys = ON');        // Enforce FK constraints
db.pragma('busy_timeout = 5000');      // Wait 5s before throwing SQLITE_BUSY

export { db };
```

---

## Component Patterns

### Server Components by Default
Start with a Server Component. Only add `'use client'` when you need interactivity.

```tsx
// app/(dashboard)/page.tsx — Server Component (no 'use client')
import { getSession } from '@/lib/auth/session';
import { listTeams } from '@/lib/db/queries/teams';
import { DashboardClient } from '@/components/dashboard/dashboard-client';

export default async function DashboardPage() {
  const session = await getSession();
  const teams = listTeams(session.user.id);  // Direct DB call — no API layer

  return <DashboardClient teams={teams} user={session.user} />;
}
```

**Why:** Server Components run on the server, can directly access the database, and ship zero JavaScript to the client. They're faster and simpler.

### Client Components for Interactivity
Only the leaf node that needs interactivity is a Client Component. Pass data as props from the parent Server Component.

```tsx
// components/dashboard/dashboard-client.tsx — Client Component
'use client';

import { useState } from 'react';
import { createTeam } from '@/app/actions/teams';

export function DashboardClient({ teams, user }: Props) {
  const [isCreating, setIsCreating] = useState(false);

  return (
    <div>
      <button onClick={() => setIsCreating(true)}>New Team</button>
      {/* Only this button needs client JS. The team list is server-rendered. */}
    </div>
  );
}
```

### Server Actions for Mutations
Use Server Actions (not API routes) for form submissions and data mutations. They're type-safe, automatically handle CSRF, and work without JavaScript.

```tsx
// app/actions/teams.ts
'use server';

import { revalidatePath } from 'next/cache';
import { getSession } from '@/lib/auth/session';
import { createTeam } from '@/lib/db/queries/teams';

export async function createTeamAction(formData: FormData) {
  const session = await getSession();
  if (!session) throw new Error('Unauthorized');

  const name = formData.get('name') as string;
  await createTeam({ name, ownerId: session.user.id });

  revalidatePath('/dashboard');  // Refresh the page data
}
```

### Data Fetching
Fetch data in Server Components. No `useEffect` + `fetch`. No React Query. No SWR.

```tsx
// ✅ DO: Direct DB access in Server Component
export default async function TeamPage({ params }: { params: { teamId: string } }) {
  const team = getTeamById(params.teamId);
  const members = listTeamMembers(params.teamId);
  return <TeamDetail team={team} members={members} />;
}

// ❌ DON'T: useEffect + fetch
// useEffect(() => { fetch('/api/team').then(...) }, [])
```

---

## Auth Patterns

### Protecting Routes
Use `middleware.ts` for broad route protection. Use `getSession()` for data-level auth.

```typescript
// middleware.ts
export { auth as middleware } from '@/lib/auth';

export const config = {
  matcher: ['/dashboard/:path*', '/api/:path*'],  // Protect these routes
};
```

### Getting the Session
```typescript
// In Server Components:
import { getSession } from '@/lib/auth/session';
const session = await getSession();
if (!session) redirect('/login');

// NEVER use client-side session checks for data access.
// The server component is the security boundary.
```

---

## Anti-Patterns (What We Don't Do)

| Anti-Pattern | Why It's Wrong | Do This Instead |
|-------------|----------------|-----------------|
| `useEffect` for data fetching | Causes client-server waterfalls. No SSR. | Fetch in Server Component |
| API routes for internal mutations | Adds unnecessary network hop for server-to-server calls | Server Actions or direct DB calls |
| Client-side auth guards | Auth check can be bypassed. Client is not a security boundary | Middleware + Server Component session check |
| `any` type | Defeats TypeScript. Hides bugs | Define interfaces. Use `unknown` if truly dynamic |
| `.env` in source control | Leaks secrets. Every dev who clones sees them | `.env.example` only. Real values in `.env.local` (gitignored) |
| ORM for SQLite | Adds 100KB+ of abstraction for a local database | Raw SQL with prepared statements |
| `SELECT *` in production queries | Wastes memory, breaks when schema changes | Explicit column list |
| Deep component nesting (>4 levels) | Hard to trace props. Slow renders | Flatten. Compose at the page level |
| Barrel exports from `components/` root | Causes circular imports | Barrel exports only within feature folders |

---

## Testing

```bash
pnpm test              # Vitest: unit + integration
pnpm test -- --ui      # Vitest UI (visual test runner)
pnpm test:e2e          # Playwright: browser tests
```

**Testing rules:**
- Database queries get integration tests with a real SQLite :memory: database
- UI components get unit tests with `@testing-library/react`
- Critical user flows (signup → create team → invite) get Playwright e2e tests
- Test filenames: `*.test.ts` for unit, `*.spec.ts` for e2e

---

## Environment Variables

```
# .env.example — safe to commit
DATABASE_PATH=data/app.db
AUTH_SECRET=           # Generate: openssl rand -base64 32
AUTH_GOOGLE_ID=        # OAuth client ID
AUTH_GOOGLE_SECRET=    # OAuth client secret
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

**Never commit `.env.local`. Never log environment variables.**

---

## Quick Start Checklist

When starting a new feature, Claude Code should follow this order:

1. **Read** `lib/db/schema.sql` — understand the data model
2. **Check** if a migration is needed → create one if yes
3. **Write** the query in `lib/db/queries/[entity].ts`
4. **Create** the Server Component page in `app/`
5. **Add** Client Components only where interactivity is needed
6. **Run** `pnpm typecheck && pnpm lint` before considering work done
