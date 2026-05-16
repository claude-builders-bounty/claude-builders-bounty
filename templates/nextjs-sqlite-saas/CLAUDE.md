# CLAUDE.md — Next.js 15 + SQLite SaaS

> **Opinionated template** for building multi-tenant SaaS applications with
> Next.js 15 App Router, SQLite (better-sqlite3), and zero-friction deployments.
>
> Every rule below includes a 🤔 *Reasoning Callout* explaining *why* the
> convention exists — so you can decide when to break it.

---

## 1. Stack & Versions

| Layer              | Choice                          | 🤔 Why?                                                              |
|--------------------|---------------------------------|----------------------------------------------------------------------|
| Framework          | **Next.js 15.x** (App Router)   | App Router is the canonical Next.js paradigm; Pages Router is legacy. |
| React              | **19.x**                        | Required by Next.js 15. Includes improved hydration & concurrency.    |
| Database           | **better-sqlite3** (synchronous)| Sync API avoids callback complexity; 10x faster than async wrappers.  |
| Alternative DB     | **@libsql/client** (Turso)      | Edge-compatible drop-in — swap connection string for Turso deploy.     |
| Node               | **20.x LTS**                    | Current LTS; includes built-in fetch, test runner, and .env support.   |
| Package Manager    | **npm**                         | Universal in CI; avoids pnpm/yarn/bun lockfile incompatibilities.      |

> 🤔 **Why better-sqlite3 over drizzle-orm or Prisma?** — SQLite is the
> simplest production database. A single `better-sqlite3` connection gives
> you sub-millisecond reads and zero infrastructure. ORMs add cognitive
> overhead that outweighs their benefit at SaaS scale < 100 concurrent users.
> You can always migrate to Prisma later — just swap the query layer.

---

## 2. Project Structure (ASCII Diagram)

```
nextjs-sqlite-saas/
│
├── src/                              # All application source
│   ├── app/                          # Next.js App Router (file-based routing)
│   │   ├── (auth)/                   #   Route group: unauthenticated pages
│   │   │   ├── login/
│   │   │   │   └── page.tsx          #     GET → render login form
│   │   │   └── register/
│   │   │       └── page.tsx          #     GET → render registration form
│   │   ├── (dashboard)/              #   Route group: authenticated pages
│   │   │   ├── layout.tsx            #     Shared sidebar + header
│   │   │   ├── page.tsx              #     GET → dashboard home
│   │   │   ├── settings/
│   │   │   │   └── page.tsx          #     GET → user settings form
│   │   │   └── teams/
│   │   │       ├── page.tsx          #     GET → list teams
│   │   │       └── [teamId]/
│   │   │           └── page.tsx      #     GET → team detail
│   │   ├── api/                      #   Route Handler API layer
│   │   │   ├── auth/
│   │   │   │   ├── [...nextauth]/
│   │   │   │   │   └── route.ts      #     NextAuth.js handler
│   │   │   │   └── register/
│   │   │   │       └── route.ts      #     POST → create user
│   │   │   ├── teams/
│   │   │   │   ├── route.ts          #     GET / POST / PATCH / DELETE
│   │   │   │   └── [teamId]/
│   │   │   │       └── route.ts      #     GET / PATCH / DELETE single team
│   │   │   └── webhooks/
│   │   │       └── stripe/
│   │   │           └── route.ts      #     POST → Stripe webhook handler
│   │   ├── layout.tsx                #   Root layout (html, body, providers)
│   │   ├── globals.css               #   Global styles + CSS custom properties
│   │   └── not-found.tsx             #   404 page
│   │
│   ├── components/                   # React components
│   │   ├── ui/                       #   Shadcn/ui primitives only
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   ├── dialog.tsx
│   │   │   └── ...
│   │   ├── features/                 #   Feature-specific components
│   │   │   ├── auth/
│   │   │   │   ├── LoginForm.tsx     #       "use client" — form state + submit
│   │   │   │   └── AuthGuard.tsx     #       Redirect wrapper for protected pages
│   │   │   ├── teams/
│   │   │   │   ├── TeamList.tsx      #       Server component — renders team rows
│   │   │   │   └── CreateTeamDialog.tsx  #   Client component — modal form
│   │   │   └── billing/
│   │   │       ├── PricingCards.tsx  #       Server component — static pricing
│   │   │       └── SubscriptionBadge.tsx   # Client — real-time status
│   │   └── shared/                   #   Shared utility components
│   │       ├── EmptyState.tsx
│   │       ├── LoadingSpinner.tsx
│   │       └── ErrorBoundary.tsx
│   │
│   ├── lib/                          # Shared business logic (NO React imports)
│   │   ├── db.ts                     #   SQLite connection singleton
│   │   ├── migrations/               #   Raw SQL migration files
│   │   │   ├── 001_users.sql
│   │   │   ├── 002_teams.sql
│   │   │   └── 003_subscriptions.sql
│   │   ├── migrate.ts                #   Migration runner (reads + applies)
│   │   ├── auth.ts                   #   Auth utilities (getSession, hashPassword)
│   │   ├── teams.ts                  #   Team repository (query functions)
│   │   └── validators/               #   Zod schemas for input validation
│   │       ├── auth.ts               #     loginSchema, registerSchema
│   │       └── team.ts               #     createTeamSchema, updateTeamSchema
│   │
│   ├── types/                        # TypeScript type definitions
│   │   ├── db.ts                     #   Row types (User, Team, Subscription)
│   │   ├── api.ts                    #   API response envelope types
│   │   └── next-auth.d.ts            #   NextAuth type augmentation
│   │
│   └── middleware.ts                 # Next.js middleware — auth redirect + tenant
│
├── public/                           # Static assets (images, fonts, robots.txt)
│   └── images/
│       └── logo.svg
│
├── scripts/                          # Dev / ops scripts
│   ├── migrate.ts                    #   CLI: apply pending migrations
│   ├── seed.ts                       #   CLI: seed database with test data
│   └── backup.sh                     #   Cron: SQLite backup to S3
│
├── tests/                            # Test files (mirrors src/ structure)
│   ├── unit/
│   │   ├── lib/
│   │   │   ├── auth.test.ts
│   │   │   └── validators.test.ts
│   │   └── components/
│   │       └── AuthGuard.test.tsx
│   ├── integration/
│   │   ├── api/
│   │   │   ├── auth.register.test.ts
│   │   │   └── teams.test.ts
│   │   └── db/
│   │       └── migrations.test.ts
│   └── e2e/
│       ├── auth.spec.ts
│       └── teams.spec.ts
│
├── .env.local                        # Local secrets (gitignored)
├── .env.example                      # Documented env template (committed)
├── data/                             # SQLite database files (gitignored)
│   └── app.db                        #   Production database
├── vitest.config.ts                  # Vitest configuration
├── playwright.config.ts              # Playwright configuration
├── tsconfig.json
├── next.config.ts
├── tailwind.config.ts
├── package.json
└── CLAUDE.md                         # ← You are here
```

> 🤔 **Why this structure?** — By colocating `lib/`, `types/`, and `components/`
> under `src/`, you keep all application code in one tree — no hunting across
> the monorepo. The `(auth)` / `(dashboard)` route groups communicate intent
> without middleware hacks. `data/` for SQLite files keeps the DB path obvious
> and mountable in Docker.

---

## 3. Naming Conventions

| Category            | Convention          | Example                          | 🤔 Why?                                                       |
|---------------------|---------------------|----------------------------------|---------------------------------------------------------------|
| Variables           | `camelCase`         | `userId`, `isLoading`            | JavaScript convention; consistent with language stdlib.       |
| Functions           | `camelCase`         | `getUser()`, `createTeam()`      | Functions are verbs; camelVerb matches JS idioms.             |
| Constants           | `SCREAMING_SNAKE`   | `MAX_RETRY_COUNT`                | Distinguishes compile-time values from runtime variables.      |
| Types / Interfaces  | `PascalCase`        | `UserProfile`, `ApiResponse`     | JS convention for constructors and type names.                 |
| React Components    | `PascalCase.tsx`    | `UserProfile.tsx`                | JSX requires PascalCase; matches React.Component naming.      |
| Page files          | `kebab-case`        | `settings/page.tsx`              | Next.js expects directory-based routing; kebab reads naturally.|
| Utilities           | `camelCase.ts`      | `formatCurrency.ts`              | Pure functions; no JSX — consistent with function naming.      |
| SQL Tables          | `snake_case` plural | `users`, `team_members`          | SQL convention; plural avoids `SELECT * FROM user` ambiguity.  |
| SQL Columns         | `snake_case`        | `created_at`, `is_active`        | SQL convention; case-insensitive in queries.                   |
| Primary Keys        | `id`                | `id INTEGER PRIMARY KEY`         | Universal convention; avoids guessing (userId vs id).          |
| Foreign Keys        | `{table}_id`        | `user_id`, `team_id`             | Immediately clear which table it references.                   |
| CSS Classes         | `kebab-case`        | `user-profile`, `btn-primary`    | Tailwind + CSS Modules both use kebab naturally.               |
| Migration Files     | `NNN_description`   | `001_create_users.sql`           | Zero-padded numbers sort correctly in `ls` and git.            |
| Env Variables       | `SCREAMING_SNAKE`   | `DATABASE_URL`, `SESSION_SECRET` | Convention inherited from 12-factor app / dotenv.              |

### File Naming Decision Tree

```
┌────────────────────────────┐
│ Does this file export      │
│ a React component?         │
├─────── YES ──── NO ────────┤
│ PascalCase.tsx  camelCase.ts│
│ (JSX allowed)  (no JSX)    │
└────────────────────────────┘
```

---

## 4. Database & Migrations

### 4.1 Connection Singleton

```typescript
// src/lib/db.ts
import Database from 'better-sqlite3';
import path from 'path';

let db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!db) {
    db = new Database(path.join(process.cwd(), 'data', 'app.db'));
    db.pragma('journal_mode = WAL');    // 👈 50x faster concurrent reads
    db.pragma('foreign_keys = ON');     // 👈 Enforce referential integrity
  }
  return db;
}
```

> 🤔 **Why singleton?** — `better-sqlite3` connections are cheap but not free.
> A singleton prevents accidental connection leaks in serverless hot-reloads
> and ensures WAL mode is set exactly once. The `process.cwd()` path means
> the DB lives at the project root, not buried in `.next`.

### 4.2 Migration Files

```sql
-- src/lib/migrations/001_create_users.sql
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT    NOT NULL UNIQUE,
    name        TEXT    NOT NULL,
    password_hash TEXT   NOT NULL,
    created_at  INTEGER NOT NULL DEFAULT (unixepoch()),
    updated_at  INTEGER NOT NULL DEFAULT (unixepoch())
);

-- Always add index on foreign keys and queried columns
CREATE INDEX idx_users_email ON users(email);
```

> 🤔 **Why `unixepoch()` over `DATETIME('now')`?** — Unix timestamps are
> timezone-agnostic integers. No DST headaches. No string parsing. Store as
> INTEGER, format in the presentation layer. `Date.now() / 1000` in JS matches
> perfectly.

### 4.3 Migration Runner

```typescript
// src/lib/migrate.ts
import fs from 'fs';
import path from 'path';
import { getDb } from './db';

const MIGRATIONS_TABLE = '_migrations';

export function runMigrations(): void {
  const db = getDb();

  // Ensure tracking table exists
  db.exec(`
    CREATE TABLE IF NOT EXISTS ${MIGRATIONS_TABLE} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL UNIQUE,
      applied_at INTEGER NOT NULL DEFAULT (unixepoch())
    )
  `);

  const applied = new Set(
    db.prepare(`SELECT name FROM ${MIGRATIONS_TABLE}`)
      .all()
      .map((r: any) => r.name)
  );

  const migrationsDir = path.join(__dirname, 'migrations');
  const files = fs.readdirSync(migrationsDir).sort();

  for (const file of files) {
    if (!file.endsWith('.sql') || applied.has(file)) continue;

    const sql = fs.readFileSync(path.join(migrationsDir, file), 'utf-8');

    db.transaction(() => {
      db.exec(sql);
      db.prepare(`INSERT INTO ${MIGRATIONS_TABLE} (name) VALUES (?)`).run(file);
    })();

    console.log(`✅ Applied: ${file}`);
  }
}
```

> 🤔 **Why a custom migration runner?** — For SQLite in a SaaS context,
> you need exactly two things: (1) a tracking table, (2) ordered execution
> in a transaction. ORM migration tools add complexity (rollbacks,
> snapshot generation, schema dumps) that you won't use with SQLite.
> This is 30 lines and works forever.

### 4.4 Migration Rules (What We Don't Do)

```sql
-- ❌ NO: ALTER TABLE — SQLite's ALTER is anemic (can't drop columns)
-- Instead: CREATE new table, INSERT old data, DROP old table
ALTER TABLE users ADD COLUMN age INTEGER;

-- ✅ DO: Full table replacement
CREATE TABLE users_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    age INTEGER DEFAULT 0,
    created_at INTEGER NOT NULL DEFAULT (unixepoch())
);
INSERT INTO users_new (id, email, created_at) SELECT id, email, created_at FROM users;
DROP TABLE users;
ALTER TABLE users_new RENAME TO users;

-- ❌ NO: DROP TABLE without checking existence
DROP TABLE users;

-- ✅ DO: idempotent creation
CREATE TABLE IF NOT EXISTS users ( ... );

-- ❌ NO: SELECT * — unpredictable column ordering, extra data transfer
SELECT * FROM users WHERE id = ?;

-- ✅ DO: explicit columns
SELECT id, email, name, created_at FROM users WHERE id = ?;

-- ❌ NO: String interpolation in SQL — SQL injection vulnerability
db.exec(`SELECT * FROM users WHERE email = '${email}'`);

-- ✅ DO: Parameterized queries
db.prepare('SELECT * FROM users WHERE email = ?').get(email);

-- ❌ NO: DATETIME('now') — string-typed, timezone-dependent
INSERT INTO users (created_at) VALUES (DATETIME('now'));

-- ✅ DO: Unix timestamps — integer, timezone-agnostic, fast to sort
INSERT INTO users (created_at) VALUES (unixepoch());
```

> 🤔 **Why these strict rules?** — SQLite has no `ALTER COLUMN`, no `DROP
> COLUMN`, no concurrent writers. These limitations make certain patterns
> dangerous. The "create new table + migrate data" pattern is the only
> safe way to evolve a schema. Parameterized queries are non-negotiable.

---

## 5. Query Patterns

### 5.1 Repository Pattern (Always)

```typescript
// src/lib/teams.ts — Team Repository
import { getDb } from './db';
import type { Team, CreateTeamInput } from '@/types/db';

export function getTeamsByUserId(userId: number): Team[] {
  return getDb()
    .prepare(`
      SELECT t.id, t.name, t.slug, t.created_at
      FROM teams t
      JOIN team_members tm ON tm.team_id = t.id
      WHERE tm.user_id = ?
      ORDER BY t.created_at DESC
    `)
    .all(userId) as Team[];
}

export function getTeamById(teamId: number): Team | undefined {
  return getDb()
    .prepare('SELECT * FROM teams WHERE id = ?')
    .get(teamId) as Team | undefined;
}

export function createTeam(input: CreateTeamInput): Team {
  const db = getDb();
  const stmt = db.prepare(`
    INSERT INTO teams (name, slug, owner_id)
    VALUES (?, ?, ?)
  `);

  const result = db.transaction(() => {
    const info = stmt.run(input.name, input.slug, input.ownerId);
    // Also add owner as team member
    db.prepare('INSERT INTO team_members (team_id, user_id, role) VALUES (?, ?, ?)')
      .run(info.lastInsertRowid, input.ownerId, 'owner');
    return info.lastInsertRowid;
  })();

  return getTeamById(Number(result))!;
}
```

> 🤔 **Why repository pattern?** — Direct SQLite calls in route handlers
> couples your API layer to the database. A repository (one file per entity)
> gives you a single place to add caching, logging, or query optimization.
> It also makes unit testing trivial — mock the repository, not the DB.

### 5.2 Transactions for Multi-Step Operations

```typescript
// ✅ DO: Atomic transaction
export function transferTeamOwnership(teamId: number, newOwnerId: number): void {
  const db = getDb();
  db.transaction(() => {
    const team = db.prepare('SELECT owner_id FROM teams WHERE id = ?').get(teamId) as any;
    if (!team) throw new NotFoundError('Team not found');
    if (team.owner_id === newOwnerId) return; // no-op

    db.prepare('UPDATE teams SET owner_id = ? WHERE id = ?').run(newOwnerId, teamId);
    db.prepare('UPDATE team_members SET role = ? WHERE team_id = ? AND user_id = ?')
      .run('owner', teamId, newOwnerId);
    db.prepare('UPDATE team_members SET role = ? WHERE team_id = ? AND user_id = ?')
      .run('admin', teamId, team.owner_id);
  })();
  // 👆 If any step fails, ALL changes roll back
}
```

> 🤔 **Why manual transactions?** — SQLite is single-writer. Without explicit
> transactions, every `run()` call opens and commits its own implicit
> transaction. Wrapping multi-table writes in a single transaction is ~100x
> faster and guarantees atomicity.

---

## 6. Server Actions

### 6.1 Server Action Pattern

```typescript
// src/lib/actions/teams.ts
'use server';

import { revalidatePath } from 'next/cache';
import { getDb } from '@/lib/db';
import { createTeamSchema } from '@/lib/validators/team';
import { getSession } from '@/lib/auth';

export async function createTeamAction(formData: FormData) {
  const session = await getSession();
  if (!session) {
    return { error: 'Unauthorized' };
  }

  // Parse and validate input
  const raw = {
    name: formData.get('name'),
    slug: formData.get('slug'),
  };

  const parsed = createTeamSchema.safeParse(raw);
  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors };
  }

  try {
    const db = getDb();
    const existing = db.prepare('SELECT id FROM teams WHERE slug = ?')
      .get(parsed.data.slug) as any;

    if (existing) {
      return { error: { slug: ['Team slug already exists'] } };
    }

    const info = db.prepare(`
      INSERT INTO teams (name, slug, owner_id)
      VALUES (?, ?, ?)
    `).run(parsed.data.name, parsed.data.slug, session.userId);

    // Add creator as team member
    db.prepare(`
      INSERT INTO team_members (team_id, user_id, role)
      VALUES (?, ?, 'owner')
    `).run(info.lastInsertRowid, session.userId);

    revalidatePath('/dashboard/teams');
    return { success: true, teamId: Number(info.lastInsertRowid) };
  } catch (error) {
    console.error('Failed to create team:', error);
    return { error: { _form: ['Failed to create team. Please try again.'] } };
  }
}
```

```typescript
// Usage in a Client Component
'use client';

import { createTeamAction } from '@/lib/actions/teams';
import { useFormState } from 'react-dom';

export function CreateTeamForm() {
  const [state, formAction] = useFormState(createTeamAction, null);

  return (
    <form action={formAction}>
      <input name="name" placeholder="Team name" required />
      <input name="slug" placeholder="team-slug" required />
      {state?.error?.slug && (
        <p className="text-red-500">{state.error.slug.join(', ')}</p>
      )}
      <button type="submit">Create Team</button>
    </form>
  );
}
```

> 🤔 **Why Server Actions over API routes?** — Server Actions eliminate the
> client-server waterfall for form submissions. They run in the same request
> context as the page, so there's no JSON serialization overhead. Next.js 15
> also supports `useActionState` for pending states without external libs.
>
> Use API routes ONLY for: external webhooks, non-React clients, or when you
> need fine-grained cache headers.

### 6.2 Server Action Rules

```typescript
// ✅ DO: Validate on the server (never trust the client)
const parsed = schema.safeParse(formData);

// ✅ DO: Check authorization inside the action
const session = await getSession();
if (!session?.isAdmin) throw new Error('Forbidden');

// ✅ DO: Return structured errors, not throw
if (parsed.error) return { error: parsed.error.flatten() };

// ❌ DON'T: Trust formData types
const id = formData.get('id'); // Could be string | File | null
const userId = Number(id);     // Explicit cast

// ❌ DON'T: Revalidate every path — only the affected ones
revalidatePath('/dashboard/teams'); // ✅ specific
revalidatePath('/dashboard');       // ❌ too broad — cache everything
```

---

## 7. Components

### 7.1 Server vs Client Component Decision

```typescript
// ✅ DO: Server Component (default — no 'use client')
// src/components/features/teams/TeamList.tsx
import { getTeamsByUserId } from '@/lib/teams';
import { getSession } from '@/lib/auth';
import { TeamCard } from './TeamCard';       // Can import client components

export async function TeamList() {
  const session = await getSession();
  const teams = getTeamsByUserId(session!.userId);

  if (teams.length === 0) {
    return <EmptyState
      title="No teams yet"
      action={{ label: 'Create Team', href: '/dashboard/teams/new' }}
    />;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {teams.map(team => (
        <TeamCard key={team.id} team={team} />
      ))}
    </div>
  );
}
```

```typescript
// ✅ DO: Client Component (only when needed)
// src/components/features/teams/CreateTeamDialog.tsx
'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogTrigger } from '@/components/ui/dialog';
import { CreateTeamForm } from './CreateTeamForm';

export function CreateTeamDialog() {
  const [open, setOpen] = useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <button>Create Team</button>
      </DialogTrigger>
      <DialogContent>
        <h2>Create a new team</h2>
        <CreateTeamForm onSuccess={() => setOpen(false)} />
      </DialogContent>
    </Dialog>
  );
}
```

> 🤔 **Why Server Components by default?** — Server Components render to
> static HTML with zero client JS. They can directly `await` database calls
> and session checks without exposing secrets. Aim for 80%+ Server Components;
> only add `'use client'` for interactivity (forms, dialogs, real-time updates).

### 7.2 State Management Hierarchy

```
┌─────────────────────────────────────────┐
│ 1. URL State (searchParams, path params) │ ← Shareable, bookmarkable
├─────────────────────────────────────────┤
│ 2. Server Component (direct DB query)   │ ← Zero JS, fastest
├─────────────────────────────────────────┤
│ 3. useState + useActionState (form)     │ ← Component-local only
├─────────────────────────────────────────┤
│ 4. Zustand store (auth, theme, cart)    │ ← Global client state
├─────────────────────────────────────────┤
│ 5. React Query (real-time data polling) │ ← External API data
└─────────────────────────────────────────┘
```

> 🤔 **Why Zustand over Context?** — Context triggers re-renders on every
> consumer when any value changes. Zustand uses subscriptions — only the
> components that read the changed slice re-render. For auth tokens and theme,
> this matters at scale.

```typescript
// src/lib/stores/auth.ts
import { create } from 'zustand';

interface AuthState {
  user: { id: number; email: string; name: string } | null;
  isLoading: boolean;
  setUser: (user: AuthState['user']) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  setUser: (user) => set({ user, isLoading: false }),
  logout: () => set({ user: null }),
}));
```

### 7.3 Component Composition Rules

```typescript
// ✅ DO: Composition over configuration
<Card>
  <CardHeader>
    <CardTitle>{team.name}</CardTitle>
    <CardDescription>{team.memberCount} members</CardDescription>
  </CardHeader>
  <CardContent>
    <TeamActions teamId={team.id} />
  </CardContent>
</Card>

// ❌ DON'T: Props explosion for layout
<Card
  title={team.name}
  description={`${team.memberCount} members`}
  actions={<TeamActions teamId={team.id} />}
  variant="compact"
  showAvatar={false}
  loading={false}
  ...
/>
```

> 🤔 **Why composition?** — Props explosion creates implicit coupling between
> parent and child. Composition via `children` (or named slots like
> `<CardHeader>`) lets each piece manage its own concerns. Adding a new
> section doesn't require changing the parent component's signature.

---

## 8. Authentication

### 8.1 Session Helper

```typescript
// src/lib/auth.ts
import { getDb } from './db';
import bcrypt from 'bcryptjs';
import { cookies } from 'next/headers';
import { SignJWT, jwtVerify } from 'jose';

const SESSION_COOKIE = 'session';
const secret = new TextEncoder().encode(process.env.SESSION_SECRET);

export interface Session {
  userId: number;
  email: string;
  teamIds: number[];
}

export async function getSession(): Promise<Session | null> {
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get(SESSION_COOKIE)?.value;
    if (!token) return null;

    const { payload } = await jwtVerify(token, secret);
    return payload as unknown as Session;
  } catch {
    return null;
  }
}

export async function createSession(userId: number, email: string): Promise<string> {
  const db = getDb();
  const teamIds = db.prepare('SELECT team_id FROM team_members WHERE user_id = ?')
    .all(userId)
    .map((r: any) => r.team_id);

  return new SignJWT({ userId, email, teamIds })
    .setProtectedHeader({ alg: 'HS256' })
    .setExpirationTime('7d')
    .sign(secret);
}
```

### 8.2 Auth Middleware

```typescript
// src/middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { jwtVerify } from 'jose';

const AUTH_ROUTES = ['/login', '/register'];
const DASHBOARD_ROUTES = ['/dashboard'];
const secret = new TextEncoder().encode(process.env.SESSION_SECRET);

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get('session')?.value;

  // Protected route — redirect to login
  if (DASHBOARD_ROUTES.some(r => pathname.startsWith(r))) {
    if (!token) {
      const loginUrl = new URL('/login', request.url);
      loginUrl.searchParams.set('redirect', pathname);
      return NextResponse.redirect(loginUrl);
    }

    try {
      await jwtVerify(token, secret);
    } catch {
      const loginUrl = new URL('/login', request.url);
      return NextResponse.redirect(loginUrl);
    }
  }

  // Auth route — redirect to dashboard if already logged in
  if (AUTH_ROUTES.includes(pathname) && token) {
    try {
      await jwtVerify(token, secret);
      return NextResponse.redirect(new URL('/dashboard', request.url));
    } catch {
      // Token expired — let them through to login
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|images).*)'],
};
```

> 🤔 **Why JWT over database sessions?** — JWT tokens eliminate the DB lookup
> on every request. The session data (userId, teamIds) is embedded in the
> cookie. For SQLite under load, this saves a query per page. Just keep the
> payload small (< 4KB for cookie limits) and include only stable data.

### 8.3 Auth Rules

```typescript
// ✅ DO: Hash passwords with bcrypt (cost factor 12)
const hash = await bcrypt.hash(password, 12);

// ✅ DO: Compare in constant time
const match = await bcrypt.compare(password, hash);

// ❌ DON'T: Roll your own crypto
const hash = sha256(password + 'secret-salt'); // ❌ — vulnerable to timing + preimage

// ✅ DO: Check auth in every Server Action
const session = await getSession();
if (!session) return { error: 'Unauthorized' };

// ✅ DO: Check ownership before mutations
const team = getTeamById(teamId);
if (team.owner_id !== session.userId) return { error: 'Forbidden' };
```

---

## 9. Environment Variables

### 9.1 Template File

```bash
# .env.example — Document ALL variables here
# Copy to .env.local and fill in values

# === App ===
NEXT_PUBLIC_APP_URL=http://localhost:3000

# === Auth ===
SESSION_SECRET=generate-with: openssl rand -base64 32

# === Database ===
# SQLite: path is relative to project root
DATABASE_PATH=data/app.db

# === Auth Provider (if using NextAuth.js) ===
# AUTH_GITHUB_ID=
# AUTH_GITHUB_SECRET=
# AUTH_SECRET=

# === Stripe ===
# STRIPE_SECRET_KEY=
# NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=
# STRIPE_WEBHOOK_SECRET=
```

### 9.2 Validation at Startup

```typescript
// src/lib/env.ts
import { z } from 'zod';

const envSchema = z.object({
  SESSION_SECRET: z.string().min(32, 'SESSION_SECRET must be at least 32 chars'),
  DATABASE_PATH: z.string().default('data/app.db'),
  NEXT_PUBLIC_APP_URL: z.string().url(),
  NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: z.string().optional(),
});

export const env = envSchema.parse(process.env);
```

> 🤔 **Why validate process.env?** — Missing env variables cause cryptic
> runtime errors. Zod validation at module import gives you an immediate,
> descriptive error on `next dev` start. The typed `env` object also gives
> full IDE autocomplete.

### 9.3 Env Rules

```
✅ DO: Prefix client-exposed vars with NEXT_PUBLIC_
✅ DO: Keep .env.example in git (documentation)
✅ DO: Validate all required vars at startup
✅ DO: Use sane defaults for optional vars

❌ DON'T: Commit .env.local or .env.production
❌ DON'T: Hardcode secrets in source code
❌ DON'T: Pass secrets through Server Action return values
❌ DON'T: Log env variables (even in error messages)
```

---

## 10. Error Handling

### 10.1 Custom Error Classes

```typescript
// src/lib/errors.ts
export class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500,
    public details?: unknown,
  ) {
    super(message);
    this.name = 'AppError';
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string) {
    super(`${resource} not found`, 'NOT_FOUND', 404);
  }
}

export class UnauthorizedError extends AppError {
  constructor(message = 'Unauthorized') {
    super(message, 'UNAUTHORIZED', 401);
  }
}

export class ValidationError extends AppError {
  constructor(errors: Record<string, string[]>) {
    super('Validation failed', 'VALIDATION_ERROR', 400, errors);
  }
}
```

### 10.2 Error Boundary for Client Components

```typescript
// src/components/shared/ErrorBoundary.tsx
'use client';

import { Component, type ReactNode } from 'react';

interface Props { children: ReactNode; fallback?: ReactNode; }
interface State { hasError: boolean; error?: Error; }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('Error boundary caught:', error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="p-8 text-center">
          <h2 className="text-xl font-bold">Something went wrong</h2>
          <p className="text-muted-foreground mt-2">
            {this.state.error?.message || 'An unexpected error occurred'}
          </p>
          <button
            className="mt-4 px-4 py-2 bg-primary text-white rounded"
            onClick={() => this.setState({ hasError: false })}
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
```

### 10.3 Server Action Error Handling

```typescript
// ✅ DO: Catch and return structured errors
export async function deleteTeamAction(teamId: number) {
  try {
    const session = await getSession();
    if (!session) return { error: 'Unauthorized' };

    const team = getTeamById(teamId);
    if (!team) return { error: 'Team not found' };
    if (team.owner_id !== session.userId) return { error: 'Forbidden' };

    const db = getDb();
    db.transaction(() => {
      db.prepare('DELETE FROM team_members WHERE team_id = ?').run(teamId);
      db.prepare('DELETE FROM teams WHERE id = ?').run(teamId);
    })();

    revalidatePath('/dashboard/teams');
    return { success: true };
  } catch (error) {
    console.error('deleteTeamAction failed:', error);
    return { error: 'An unexpected error occurred. Please try again.' };
  }
}

// ❌ DON'T: Let errors bubble to the client
export async function unsafeAction() {
  const db = getDb();
  const result = db.prepare('...').run();
  // If this throws, the client sees a 500 HTML page — bad UX
}
```

> 🤔 **Why return errors instead of throwing?** — Server Actions serialized
> exceptions into HTTP 500 responses, breaking the form interaction. By
> returning `{ error: '...' }` or `{ success: true }`, the client component
> can display errors inline — same UX as a traditional API, but with zero
> network overhead.

---

## 11. Testing

### 11.1 Unit Test Pattern

```typescript
// tests/unit/lib/validators.test.ts
import { describe, it, expect } from 'vitest';
import { createTeamSchema } from '@/lib/validators/team';

describe('createTeamSchema', () => {
  it('accepts valid input', () => {
    const result = createTeamSchema.safeParse({
      name: 'My Team',
      slug: 'my-team',
    });
    expect(result.success).toBe(true);
  });

  it('rejects empty name', () => {
    const result = createTeamSchema.safeParse({
      name: '',
      slug: 'my-team',
    });
    expect(result.success).toBe(false);
  });

  it('rejects slug with spaces', () => {
    const result = createTeamSchema.safeParse({
      name: 'My Team',
      slug: 'my team',
    });
    expect(result.success).toBe(false);
  });

  it('rejects slug shorter than 3 characters', () => {
    const result = createTeamSchema.safeParse({
      name: 'My Team',
      slug: 'ab',
    });
    expect(result.success).toBe(false);
  });
});
```

### 11.2 Integration Test Pattern (Database)

```typescript
// tests/integration/db/teams.test.ts
import { describe, it, expect, beforeEach, afterAll } from 'vitest';
import Database from 'better-sqlite3';
import { createTeam, getTeamsByUserId } from '@/lib/teams';
import { runMigrations } from '@/lib/migrate';

// Use in-memory database for tests
let db: Database.Database;

beforeEach(() => {
  db = new Database(':memory:');
  // Override the singleton
  vi.mock('@/lib/db', () => ({
    getDb: () => db,
  }));
  runMigrations();
});

afterAll(() => {
  db?.close();
});

describe('createTeam', () => {
  it('creates a team and adds owner as member', () => {
    const team = createTeam({
      name: 'Test Team',
      slug: 'test-team',
      ownerId: 1,
    });

    expect(team.name).toBe('Test Team');
    expect(team.slug).toBe('test-team');

    const members = db.prepare('SELECT * FROM team_members WHERE team_id = ?')
      .all(team.id);
    expect(members).toHaveLength(1);
    expect(members[0]).toMatchObject({
      user_id: 1,
      role: 'owner',
    });
  });
});
```

### 11.3 E2E Test Pattern (Playwright)

```typescript
// tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('redirects unauthenticated users to login', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });

  test('shows validation errors on registration form', async ({ page }) => {
    await page.goto('/register');
    await page.click('button[type="submit"]');
    await expect(page.locator('.text-red-500')).toHaveCount(2);
  });

  test('allows registration and redirects to dashboard', async ({ page }) => {
    await page.goto('/register');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.fill('input[name="name"]', 'Test User');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/);
  });
});
```

> 🤔 **Why all three layers?** — Unit tests catch logic errors in 5ms.
> Integration tests catch SQL/DB errors in 50ms. E2E tests catch rendering
> and auth flow errors in 5s. Each layer catches different bug types;
> skipping any layer means you'll ship bugs that the other layers can't see.

---

## 12. Anti-Patterns (With Before/After Examples)

### 🚫 12.1 N+1 Queries in Server Components

```typescript
// ❌ BAD: N+1 — fetches team, then one query per member
async function TeamWithMembers({ teamId }: { teamId: number }) {
  const team = getTeamById(teamId);
  const members = team.memberIds.map(id => getUserById(id));
  // ...
}

// ✅ GOOD: Single JOIN query
async function TeamWithMembers({ teamId }: { teamId: number }) {
  const rows = getDb().prepare(`
    SELECT t.*, u.id as user_id, u.name as user_name, u.email
    FROM teams t
    JOIN team_members tm ON tm.team_id = t.id
    JOIN users u ON u.id = tm.user_id
    WHERE t.id = ?
  `).all(teamId);
  // ...
}
```

### 🚫 12.2 Prop Drilling

```typescript
// ❌ BAD: Props passed through 4 levels
<Page>
  <DashboardLayout userId={userId} teamId={teamId} isAdmin={isAdmin}>
    <Sidebar userId={userId} teamId={teamId}>
      <TeamSelector userId={userId} teamId={teamId} />
    </Sidebar>
  </DashboardLayout>
</Page>

// ✅ GOOD: Components request their own data
function TeamSelector() {
  const session = await getSession();
  const teams = getTeamsByUserId(session!.userId);
  return <select>{teams.map(t => <option key={t.id}>{t.name}</option>)}</select>;
}
```

### 🚫 12.3 Large Client Bundles

```typescript
// ❌ BAD: Importing a heavy library in a client component
'use client';
import { Chart } from 'chart.js';  // ~200KB — loaded for every user

// ✅ GOOD: Dynamic import for heavy components
const Chart = dynamic(() => import('chart.js'), { ssr: false });
```

### 🚫 12.4 Not Handling Empty/Loading/Error States

```typescript
// ❌ BAD: Assumes data always exists
function TeamPage({ params }: { params: { teamId: string } }) {
  const team = getTeamById(Number(params.teamId));
  return <h1>{team.name}</h1>; // 💥 TypeError if team is undefined
}

// ✅ GOOD: Handle all states
function TeamPage({ params }: { params: { teamId: string } }) {
  const team = getTeamById(Number(params.teamId));

  if (!team) return <NotFound />;
  // Or use <ErrorBoundary> and let it render for errors

  return <h1>{team.name}</h1>;
}
```

### 🚫 12.5 Over-fetching in Server Components

```typescript
// ❌ BAD: Fetching the whole user when only one field is needed
const user = getUserById(id);  // SELECT id, email, name, password_hash, created_at, updated_at, ...
return <span>{user.name}</span>;

// ✅ GOOD: Precise queries
const user = getDb().prepare('SELECT name FROM users WHERE id = ?').get(id);
return <span>{(user as any).name}</span>;

// Even better — create a query function for this exact use case
export function getUserName(id: number): string | undefined {
  const row = getDb().prepare('SELECT name FROM users WHERE id = ?').get(id) as any;
  return row?.name;
}
```

### 🚫 12.6 Mutating Without Revalidation

```typescript
// ❌ BAD: Mutation succeeds but page shows stale data
await db.prepare('UPDATE teams SET name = ? WHERE id = ?').run(newName, teamId);
// User still sees old name until manual refresh

// ✅ GOOD: Revalidate the affected path
await db.prepare('UPDATE teams SET name = ? WHERE id = ?').run(newName, teamId);
revalidatePath('/dashboard/teams'); // Page instantly reflects new data
```

---

## 13. Deployment Architecture

```
┌───────────────────┐
│   Cloudflare DNS  │
│   (CNAME → fly.io)│
└────────┬──────────┘
         │
┌────────▼──────────┐
│  Fly.io / Railway │         ← Single-region, single-VM
│  (Dockerfile)     │
│                   │
│  ┌─────────────┐  │
│  │ Next.js 15  │  │         ← SSR + API + Server Actions
│  │ App Router  │  │
│  └──────┬──────┘  │
│         │         │
│  ┌──────▼──────┐  │
│  │ SQLite WAL  │  │         ← Local file, NO external DB needed
│  │ app.db      │  │
│  └──────┬──────┘  │
│         │         │
│  ┌──────▼──────┐  │
│  │ Volume      │  │         ← Persistent volume (SQLite)
│  │ /data       │  │
│  └─────────────┘  │
└───────────────────┘
         │
┌────────▼──────────┐
│  Litestream       │         ← Continuous SQLite backup to S3
│  (backup to S3)   │
└───────────────────┘
```

> 🤔 **Why Fly.io single-VM?** — SQLite's superpower is zero-network I/O.
> Putting it behind a network filesystem (EBS, EFS) negates that advantage.
> Fly.io gives you a VM with a local persistent volume — SQLite at RAM speed.
> Litestream streams WAL pages to S3 for disaster recovery. No Postgres, no
> Redis, no complexity.

### Deployment Commands

```bash
# Deploy to Fly.io (requires flyctl)
fly launch --name my-saas --region iad
fly deploy

# Deploy to Railway (connects to GitHub repo)
# 1. Push to GitHub
# 2. Railway auto-detects Next.js
# 3. Add env vars in Railway dashboard
```

---

## 14. Automated Deployments (CI/CD)

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm run test:unit
      - run: npm run test:integration
      - run: npm run build

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl deploy --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

---

## 15. Before Committing Checklist

> Run through this checklist before every commit to maintain consistency.

### Primitives
- [ ] No `console.log` or `debugger` statements
- [ ] No `any` types (use `unknown` + casting if necessary)
- [ ] No hardcoded strings that should be env variables
- [ ] No `// @ts-ignore` or `// @ts-expect-error` without a comment explaining why

### Database
- [ ] New migration file added with `CREATE TABLE IF NOT EXISTS` pattern
- [ ] Index added for every foreign key and frequently queried column
- [ ] No `SELECT *` — only specified columns
- [ ] No string interpolation in SQL — all queries use `?` placeholders
- [ ] Multi-step operations wrapped in `db.transaction()`
- [ ] `ALTER TABLE` not used — full table replacement pattern instead

### Components
- [ ] Server Component by default — only add `'use client'` if interactivity is needed
- [ ] No prop drilling beyond 2 levels (extract or use composition)
- [ ] All data-fetching components handle empty state
- [ ] Dynamic imports for heavy libraries (>50KB)
- [ ] Client Components wrapped in `<ErrorBoundary>`

### Server Actions
- [ ] Input validated with Zod `safeParse` before processing
- [ ] Authorization checked (`getSession()`)
- [ ] `revalidatePath()` or `revalidateTag()` called after mutations
- [ ] Structured error object returned (not thrown)
- [ ] Form state accounts for pending/submission/error/success

### Auth
- [ ] `SESSION_SECRET` is 32+ random bytes
- [ ] Passwords hashed with bcrypt (cost 12+)
- [ ] Middleware protects all dashboard routes
- [ ] JWT tokens have expiration (max 7 days)

### Testing
- [ ] At least unit tests for new validators/utilities
- [ ] Integration tests for new query functions
- [ ] E2E tests for new user flows (critical paths)
- [ ] Tests pass locally (`npm run test`)

### Git
- [ ] Branch follows naming: `feat/description`, `fix/description`, `chore/description`
- [ ] Commit message follows Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`)
- [ ] No secrets or env files in the commit
- [ ] Migration files are included in the commit

### Performance
- [ ] No N+1 queries (check loops with DB calls)
- [ ] No unnecessary `revalidatePath('/')` — be specific about affected routes
- [ ] No `useEffect` with empty deps for data fetching (use Server Components)
- [ ] Static pages use `force-static` or `revalidate` instead of `dynamic`

---

## 16. Quick Reference

### Dev Commands

```bash
npm run dev              # Start dev server (includes auto-migration)
npm run build            # Production build with type checking
npm run start            # Start production server
npm run test             # Run all tests
npm run test:unit        # Unit tests only (Vitest)
npm run test:int         # Integration tests only
npm run test:e2e         # E2E tests (Playwright)
npm run db:migrate       # Apply pending migrations
npm run db:seed          # Seed database
npm run db:reset         # Drop + recreate + seed
npm run lint             # ESLint + Prettier check
npm run type-check       # tsc --noEmit
```

### API Route Structure

```
/api/{resource}             # GET (list), POST (create)
/api/{resource}/{id}       # GET (one), PATCH (update), DELETE (remove)
/api/{resource}/{id}/nested # Nested resources
```

### API Response Envelope

```typescript
// Success (single)
{ "data": { "id": 1, "name": "My Team", ... } }

// Success (collection)
{ "data": [ ... ], "total": 42, "page": 1, "pageSize": 20 }

// Error
{ "error": { "code": "NOT_FOUND", "message": "Team not found" } }

// Validation Error
{ "error": { "code": "VALIDATION_ERROR", "message": "Validation failed",
             "details": { "slug": ["Team slug already exists"] } } }
```

### Key Dependencies

```json
{
  "dependencies": {
    "next": "^15",
    "react": "^19",
    "better-sqlite3": "^11",
    "bcryptjs": "^2",
    "jose": "^5",
    "zod": "^3",
    "zustand": "^5"
  },
  "devDependencies": {
    "vitest": "^3",
    "@playwright/test": "^2",
    "typescript": "^5"
  }
}
```

---

## 17. Conventional Commits Reference

```
feat:     New feature for the user, not a new feature for build script
fix:      Bug fix for the user, not a fix to a build script
docs:     Changes to the documentation
style:    Formatting, missing semicolons, etc; no production code change
refactor: Refactoring production code, eg. renaming a variable
test:     Adding missing tests, refactoring tests; no production code change
chore:    Updating grunt tasks etc; no production code change
perf:     Performance improvements
ci:       CI related changes
build:    Changes that affect the build system or external dependencies
```

---

*This CLAUDE.md template is maintained at `templates/nextjs-sqlite-saas/CLAUDE.md`.
Generated with ❤️ for claude-builders-bounty.*

