# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Stack & Versions

We use **exact versions** to avoid "works on my machine" bugs. Pin everything.

```
Node.js: 20.x LTS (check .nvmrc)
Next.js: 15.x (App Router, NOT Pages Router)
React: 19.x (comes with Next.js 15)
SQLite: 3.x (via better-sqlite3 or @libsql/client for Turso)
TypeScript: 5.x (strict mode, no opts out)
```

**Runtime drivers:**
- Local dev: `better-sqlite3` — synchronous, faster, no connection overhead
- Production (edge/serverless): `@libsql/client` with `libsql:`, `ws:` or `https:` URL
- **Never mix drivers.** Pick one at initialization time and stick with it.

---

## Dev Commands

```bash
npm run dev        # Start dev server (localhost:3000)
npm run build      # Production build
npm run start      # Start production server
npm run db:migrate # Run pending migrations
npm run db:seed    # Seed dev DB with sample data
npm run db:studio  # Open SQLite studio (sqlitebrower.org or CLI)
npm run lint       # ESLint
npm run typecheck  # tsc --noEmit
npm run test       # Vitest
```

**Install dev deps we always want:**
```bash
npm install -D better-sqlite3 @types/better-sqlite3 vitest
```

---

## Folder Structure

```
my-saas/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx          # Root layout (fonts, providers)
│   ├── page.tsx            # Landing page
│   ├── (auth)/             # Auth route group (no layout shared with app)
│   │   ├── login/page.tsx
│   │   └── signup/page.tsx
│   ├── (dashboard)/        # Protected app routes
│   │   ├── layout.tsx      # Sidebar/nav layout + auth guard
│   │   ├── page.tsx        # Dashboard home
│   │   └── settings/page.tsx
│   └── api/                # Route Handlers (only for external integrations)
│       └── webhooks/       # NEVER put business logic in Route Handlers
├── components/
│   ├── ui/                 # Generic, unstyled primitives (Button, Input, etc.)
│   │   └── button.tsx
│   ├── forms/              # Form components bound to schemas
│   │   └── signup-form.tsx
│   └── data/               # Components that read/write DB (use data/ lib)
│       └── user-list.tsx
├── lib/
│   ├── db/
│   │   ├── index.ts        # DB client singleton (better-sqlite3 or libsql)
│   │   ├── schema.ts       # SQL schema as executable migrations
│   │   └── migrations/     # Numbered SQL files: 001_init.sql, 002_...
│   ├── data/               # Data access layer — ONLY place that queries DB
│   │   ├── user.ts         # User queries
│   │   └── index.ts        # Re-exports for convenience
│   └── auth/
│       └── session.ts      # Session management (lucia, iron-session, etc.)
├── public/                 # Static assets
├── .env.local              # Secrets (never commit)
├── .env.example            # Template for .env.local
├── next.config.ts
├── tsconfig.json           # strict: true, no suppressions
└── package.json
```

**Why this structure:**
- `lib/data/` is the only door to the DB. If you query `db` anywhere else, it's a bug.
- `components/data/` wraps `lib/data/` for React use — never imports `better-sqlite3` directly.
- Route groups `(auth)` and `(dashboard)` are purely organizational — they don't create URL segments.

---

## SQL / Migration Conventions

### Every table gets an `id` and `created_at` by default

```sql
CREATE TABLE users (
  id         TEXT    PRIMARY KEY DEFAULT (generate_uuidv4()),
  email      TEXT    NOT NULL UNIQUE,
  password_hash TEXT,
  created_at INTEGER NOT NULL DEFAULT (unixepoch()),
  updated_at INTEGER NOT NULL DEFAULT (unixepoch())
);
```

- `id` is `TEXT` using `generate_uuidv4()` (built into SQLite) — no integer auto-increment for user-facing tables. UUIDs are merge-safe and work across distributed DBs.
- `created_at` / `updated_at` are `INTEGER` Unix timestamps — not `DATETIME`. Unix timestamps sort correctly, take less space, and are timezone-agnostic.

### Migrations are sequential and immutable

```
lib/db/migrations/
├── 001_init.sql
├── 002_add_users_premium.sql
└── 003_fix_sessions.sql   <-- If a migration is wrong, write a NEW migration to fix it. Never edit old files.
```

**Rules:**
1. Migrations run **once and only once** — track executed migrations in a `schema_migrations` table.
2. Migrations are **additive by default** — add columns with defaults, not NOT NULL without defaults.
3. **Never drop a column in a migration** — deprecate it, wait a release cycle, then remove.
4. **Never rename a column** — add a new column, backfill, switch reads, then drop old.
5. Before merging, test migrations against a DB that has been running for 6+ months of simulated data (use a fixture).

### SQLite-specific rules

- **Avoid `ALTER TABLE` as much as possible** — SQLite has limited ALTER support. Design tables right the first time.
- **Use `INTEGER` for booleans** — SQLite has no BOOLEAN type. `0` = false, `1` = true.
- **Index foreign keys** — `CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);`
- **Use `LIMIT` on deletes** — `DELETE FROM events WHERE created_at < ? LIMIT 100;` — never delete unbounded rows in production.
- ** WAL mode in production:** `PRAGMA journal_mode = WAL;` — better concurrency, required for Turso.

---

## Component Patterns

### Server Components first

Default to **Server Components**. Only add `'use client'` when you need:
- Browser APIs (localStorage, IntersectionObserver)
- useState / useReducer / useEffect
- Event listeners (onClick, onChange)

```tsx
// ✅ Good: Server Component fetching data
import { getUser } from '@/lib/data';

export default async function UserProfile({ id }: { id: string }) {
  const user = await getUser(id);
  return <div>{user.email}</div>;
}
```

```tsx
// ✅ Good: Client Component for interactive form
'use client';
import { useState } from 'react';
import { createUser } from '@/lib/data';

export function SignupForm() {
  const [email, setEmail] = useState('');
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await createUser({ email });
  }
  return <form onSubmit={handleSubmit}>...</form>;
}
```

```tsx
// ❌ Bad: DB query in a Client Component (breaks server-side rendering)
'use client';
import { db } from '@/lib/db'; // NEVER import db in client components

export function BadComponent() {
  db.query('SELECT * FROM users'); // ❌
}
```

### Data access via `lib/data/`, not direct DB imports

```ts
// lib/data/user.ts
import { db } from '@/lib/db';

export function getUser(id: string) {
  return db.prepare('SELECT * FROM users WHERE id = ?').get(id);
}

export function createUser(data: { email: string; password_hash: string }) {
  const stmt = db.prepare(
    'INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)'
  );
  return stmt.run(generateUuid(), data.email, data.password_hash);
}
```

**Why:** Centralizing DB access means you can add caching, rate limiting, or switch the DB driver without touching components.

### Props are typed, not `any`

```tsx
// ❌ Bad
function Card({ data }: any) { ... }

// ✅ Good
interface CardProps {
  user: { id: string; email: string };
  onUpdate: (id: string) => Promise<void>;
}
function Card({ user, onUpdate }: CardProps) { ... }
```

---

## What We Don't Do (and Why)

### ❌ No `await` in Server Components without ErrorBoundary
Next.js 15 streaming can partially render a page. If a DB call fails, the whole component tree fails. Always wrap async Server Components in `<Suspense>`:

```tsx
// ✅ Good
import { Suspense } from 'react';
export default function Dashboard() {
  return (
    <Suspense fallback={<DashboardSkeleton />}>
      <DashboardInner /> {/* async, might fail */}
    </Suspense>
  );
}
```

```tsx
// ❌ Bad — unhandled rejection, white screen on DB error
export default async function Dashboard() {
  const data = await getDashboardData(); // ❌ No Suspense
  return <div>{data}</div>;
}
```

### ❌ No raw SQL in Route Handlers or API routes
Route Handlers are thin adapters. Keep business logic in `lib/data/`:

```tsx
// app/api/users/route.ts — only handles HTTP
import { NextResponse } from 'next/server';
import { getUser } from '@/lib/data';

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const id = searchParams.get('id');
  if (!id) return NextResponse.json({ error: 'Missing id' }, { status: 400 });
  const user = getUser(id);
  if (!user) return NextResponse.json({ error: 'Not found' }, { status: 404 });
  return NextResponse.json(user);
}
```

### ❌ No `console.log` in production
Use structured logging with levels:

```ts
// lib/logger.ts
type LogLevel = 'debug' | 'info' | 'warn' | 'error';
const level: LogLevel = process.env.LOG_LEVEL ?? 'info';
```

Replace `console.log` with this. In production, `console.log` floods stdout and has no level filtering.

### ❌ No password storage in plain text
Always hash passwords:

```ts
// ✅ Good — use argon2 or bcrypt
import { argon2id } from 'argon2';
const hash = await argon2id(password);
// Verify: argon2.verify(hash, password)

// ❌ Bad — plain text
const user = { password }; // ❌
```

### ❌ No secrets in the DB as plain text
Use `APP_KEY` / `AUTH_SECRET` env vars for session tokens, not stored in SQLite.

### ❌ No N+1 queries
```ts
// ❌ Bad — N+1
const users = db.prepare('SELECT * FROM users').all();
users.forEach(u => {
  const posts = db.prepare('SELECT * FROM posts WHERE user_id = ?').all(u.id); // N queries
});

// ✅ Good — single JOIN
const data = db.prepare(`
  SELECT u.*, COUNT(p.id) as post_count
  FROM users u
  LEFT JOIN posts p ON p.user_id = u.id
  GROUP BY u.id
`).all();
```

### ❌ No ORM as the primary DB layer
We use raw SQL. ORMs hide query complexity, generate inefficient SQL, and add runtime overhead. Raw SQL is:
- Faster (no ORM overhead)
- Debuggable (you see exactly what runs)
- Portable (SQLite syntax works with Turso, Postgres, etc.)

Exception: Drizzle ORM is acceptable if you write raw SQL for complex queries and only use Drizzle for schema management.

### ❌ No seeding production DBs
`npm run db:seed` only runs in development. Production data is sacred. All production DB access goes through authenticated, audited API calls.

---

## Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Tables | `snake_case, plural` | `users`, `post_comments` |
| Columns | `snake_case` | `created_at`, `user_id` |
| Functions | `camelCase, verb-noun` | `getUser`, `createPost` |
| React Components | `PascalCase, descriptive` | `UserProfile`, `SignupForm` |
| Files (components) | `PascalCase.tsx` | `user-profile.tsx` |
| Files (lib/data) | `lowercase.ts` | `user.ts`, `post.ts` |
| Migrations | `NNN_name.sql` | `001_init.sql` |
| Env vars | `SCREAMING_SNAKE_CASE` | `DATABASE_URL`, `APP_SECRET` |
| CSS classes | `kebab-case` (if using Tailwind, that's automatic) |

---

## Environment Variables

Create `.env.local` (never committed) and `.env.example` (committed):

```bash
# .env.example
DATABASE_URL=file:./data/dev.db       # local SQLite
# DATABASE_URL=libsql://your-db.turso.io?authToken=...
# DATABASE_URL=ws://localhost:8080    # Turso local dev

LOG_LEVEL=info
APP_SECRET=                     # Generate: openssl rand -base64 32
AUTH_SECRET=                    # For session management
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

**Never put default values for secrets in `.env.example`** — force the developer to make a conscious choice.