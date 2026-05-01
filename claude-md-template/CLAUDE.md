# CLAUDE.md — Project Instructions for Claude Code

## Project Overview

> **[Project Name]** — A Next.js 15 SaaS application with SQLite (via better-sqlite3) for persistent local data storage.

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15 (App Router) | Server Components, streaming, and built-in API routes |
| Language | TypeScript 5 (strict mode) | Catch bugs at compile time, not in production |
| Database | SQLite via `better-sqlite3` | Zero-config, embedded, fast — perfect for single-server SaaS |
| ORM | None — raw SQL via `better-sqlite3` | ORMs add complexity for a single-table SQLite DB. SQL is clearer. |
| Styling | Tailwind CSS 4 | Co-located styles, no naming debates, fast prototyping |
| Linting | ESLint + Prettier | Enforced on pre-commit via husky |
| Testing | Vitest + React Testing Library | Fast, ESM-native, great Next.js support |
| Validation | Zod | Runtime type checking at API boundaries |
| Auth | NextAuth.js (optional) | Battle-tested, integrates with App Router |

## Project Structure

```
├── app/                         # Next.js App Router
│   ├── layout.tsx               # Root layout (providers, fonts, metadata)
│   ├── page.tsx                 # Landing / home page
│   ├── globals.css              # Tailwind imports + design tokens
│   ├── api/                     # API routes (server-only)
│   │   └── [resource]/
│   │       └── route.ts         # REST endpoints (GET, POST, PATCH, DELETE)
│   └── (dashboard)/             # Authenticated route group
│       ├── layout.tsx           # Dashboard shell (sidebar, nav)
│       ├── loading.tsx          # Suspense fallback
│       ├── error.tsx            # Error boundary
│       └── [feature]/
│           └── page.tsx         # Feature pages
├── components/
│   ├── ui/                      # Primitives: Button, Input, Card, Modal
│   │   └── index.ts             # Barrel export
│   └── features/                # Feature-specific components
│       └── [feature-name]/
│           └── ComponentName.tsx
├── lib/
│   ├── db.ts                    # Database singleton (WAL mode, FK on)
│   ├── schema.ts                # Table definitions + migration runner
│   ├── queries/                 # Reusable query functions
│   │   └── users.ts
│   ├── utils.ts                 # Generic helpers (cn, formatDate, etc.)
│   └── types.ts                 # Shared TypeScript types
├── db/
│   ├── migrations/              # Numbered SQL files: 001_create_users.sql
│   └── data.sqlite              # Database file (gitignored)
├── public/
├── .env.local                   # Secrets (gitignored)
├── .husky/                      # Git hooks
├── CLAUDE.md                    # This file
└── package.json
```

## Commands

```bash
# Development
npm run dev              # Start dev server → http://localhost:3000
npm run build            # Production build (run before deploy)
npm run start            # Production server

# Database
npm run db:migrate       # Run pending migrations from db/migrations/
npm run db:seed          # Seed with test data (dev only)
npm run db:reset         # Drop all tables, re-migrate, re-seed

# Code Quality
npm run lint             # ESLint check (fails on warnings)
npm run lint:fix         # ESLint auto-fix
npm run format           # Prettier format all files
npm run typecheck        # tsc --noEmit (type-check without emitting)

# Testing
npm run test             # Run all tests once
npm run test:watch       # Watch mode (dev workflow)
npm run test:coverage    # Coverage report
```

## Naming Conventions

| What | Convention | Example |
|------|-----------|---------|
| React components | PascalCase | `UserProfile.tsx` |
| Utility functions | camelCase | `formatDate.ts` |
| API route files | `route.ts` | `app/api/users/route.ts` |
| SQL migrations | `NNN_description.sql` | `001_create_users.sql` |
| Test files | `*.test.ts(x)` | `db.test.ts` (co-located) |
| CSS modules | `*.module.css` | (prefer Tailwind) |
| Environment vars | UPPER_SNAKE_CASE | `DATABASE_PATH` |
| DB tables | snake_case, plural | `user_sessions` |
| DB columns | snake_case | `created_at`, `user_id` |
| Git branches | `feat/`, `fix/`, `chore/` | `feat/user-auth` |

## Database Migration Rules

### Creating a Migration

1. Create a new file in `db/migrations/` with the next number:
   ```
   003_add_user_avatar.sql
   ```
2. Write the SQL — include both UP and DOWN in comments:
   ```sql
   -- UP
   ALTER TABLE users ADD COLUMN avatar_url TEXT;

   -- DOWN (for manual rollback)
   -- ALTER TABLE users DROP COLUMN avatar_url;
   ```
3. Run `npm run db:migrate`

### Migration Rules

- **Never edit an existing migration** — create a new one to fix mistakes
- **Always include `IF NOT EXISTS` / `IF EXISTS`** — migrations must be idempotent
- **Add indexes in the same migration as the column** — don't forget performance
- **Test migrations on a copy of production data** before deploying

### Schema Pattern (`lib/schema.ts`)

```typescript
import db from './db';
import { readdirSync, readFileSync } from 'fs';
import { join } from 'path';

export function runMigrations() {
  db.pragma('journal_mode = WAL');
  db.pragma('foreign_keys = ON');

  db.exec(`
    CREATE TABLE IF NOT EXISTS migrations (
      id INTEGER PRIMARY KEY,
      name TEXT NOT NULL,
      applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  const migrationDir = join(process.cwd(), 'db', 'migrations');
  const files = readdirSync(migrationDir).filter(f => f.endsWith('.sql')).sort();

  const applied = db.prepare('SELECT name FROM migrations').all().map(r => r.name);

  for (const file of files) {
    if (applied.includes(file)) continue;
    const sql = readFileSync(join(migrationDir, file), 'utf-8');
    db.exec(sql);
    db.prepare('INSERT INTO migrations (name) VALUES (?)').run(file);
    console.log(`✅ Applied migration: ${file}`);
  }
}
```

## Component Patterns

### Server Component (default)

```typescript
// app/(dashboard)/page.tsx
import db from '@/lib/db';
import { UserList } from '@/components/features/users/UserList';

export default async function DashboardPage() {
  // Direct DB access — no API call needed
  const users = db.prepare('SELECT * FROM users ORDER BY created_at DESC').all();
  return <UserList users={users} />;
}
```

### Client Component (interactive)

```typescript
// components/features/users/UserCard.tsx
'use client';

import { useState } from 'react';

interface UserCardProps {
  user: { id: number; name: string; email: string };
}

export function UserCard({ user }: UserCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  // ... interactive logic
}
```

### Server Action (mutations)

```typescript
// app/actions/users.ts
'use server';

import { revalidatePath } from 'next/cache';
import db from '@/lib/db';
import { z } from 'zod';

const CreateUserSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
});

export async function createUser(formData: FormData) {
  const result = CreateUserSchema.safeParse({
    name: formData.get('name'),
    email: formData.get('email'),
  });

  if (!result.success) {
    return { error: result.error.flatten().fieldErrors };
  }

  db.prepare('INSERT INTO users (name, email) VALUES (?, ?)').run(
    result.data.name,
    result.data.email
  );

  revalidatePath('/users');
  return { success: true };
}
```

### API Route Handler

```typescript
// app/api/users/route.ts
import { NextRequest, NextResponse } from 'next/server';
import db from '@/lib/db';
import { z } from 'zod';

export async function GET(request: NextRequest) {
  const page = Number(request.nextUrl.searchParams.get('page') ?? '1');
  const limit = 20;
  const offset = (page - 1) * limit;

  const users = db.prepare('SELECT * FROM users LIMIT ? OFFSET ?').all(limit, offset);
  const total = db.prepare('SELECT COUNT(*) as count FROM users').get().count;

  return NextResponse.json({ users, total, page, limit });
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const result = CreateUserSchema.safeParse(body);

  if (!result.success) {
    return NextResponse.json({ errors: result.error.issues }, { status: 400 });
  }

  const info = db.prepare('INSERT INTO users (name, email) VALUES (?, ?)').run(
    result.data.name,
    result.data.email
  );

  return NextResponse.json({ id: info.lastInsertRowid }, { status: 201 });
}
```

## Patterns to Follow

### Data Fetching

- **Server Components** — fetch directly with `db.prepare()`, no `fetch()` needed
- **Client Components** — receive data as props from server parents
- **API Routes** — for external consumers or client-side fetching

### Error Handling

- API routes: return structured JSON `{ error: string, details?: unknown }`
- Server actions: return `{ error: ... }` or `{ success: true }`
- Use appropriate HTTP status codes (400 validation, 404 not found, 500 server error)
- Log server errors with context, never expose internals to client

### State Management

- **Server state** — live in the database, fetched fresh per request
- **URL state** — filters, pagination, search queries in the URL
- **Client state** — `useState` for UI-only state (modals, form inputs)
- **No global state library** — you don't need Redux/Zustand for a SQLite SaaS

### Caching

- `revalidatePath('/users')` after mutations — don't serve stale data
- `revalidateTag('users')` for granular cache invalidation
- Use `unstable_cache()` for expensive read queries that don't change often

## Anti-Patterns (What We Don't Do and Why)

### ❌ No ORM (Prisma, Drizzle, etc.)

**Why not:** SQLite is simple. An ORM adds a 200MB `node_modules` dependency, generates verbose SQL, and makes debugging harder. Raw SQL with `better-sqlite3` is synchronous, fast, and the SQL you write is the SQL that runs.

### ❌ No `'use client'` on pages

**Why not:** Client components disable Server Components. Keep `'use client'` on leaf components (buttons, forms). Pages should be server-rendered by default.

### ❌ No `fetch()` to your own API routes from Server Components

**Why not:** Server Components can import `db` directly. Calling your own API via `fetch()` adds a network hop for no reason.

### ❌ No `any` type

**Why not:** `any` defeats TypeScript. Use `unknown` and narrow, or define the actual type. Every `any` is a future bug.

### ❌ No barrel exports for everything

**Why not:** Barrel files (`index.ts` that re-exports everything) cause circular dependencies and slow builds. Use them only for `components/ui/` where you have many small primitives.

### ❌ No `@apply` in Tailwind

**Why not:** `@apply` in CSS defeats Tailwind's purpose. If you need a reusable style, make a component, not a CSS class. Exception: `globals.css` for base resets.

### ❌ No inline SQL strings in route handlers

**Why not:** Put reusable queries in `lib/queries/`. Route handlers should call query functions, not contain SQL. This makes testing and reuse possible.

### ❌ No concurrent writes to SQLite

**Why not:** SQLite supports one writer at a time. Use WAL mode (set in `schema.ts`) for concurrent reads, but serialize writes through your application logic.

### ❌ No storing DB in `public/`

**Why not:** Files in `public/` are served as static assets. Your database would be downloadable by anyone.

### ❌ No `export default` for components

**Why not:** Named exports are searchable, refactorable, and prevent accidental renaming. Use `export function ComponentName()`.

## Environment Variables

```bash
# .env.local
DATABASE_PATH=./db/data.sqlite    # SQLite file path
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

## Gotchas & Notes

- **SQLite is single-writer** — don't try concurrent writes; WAL mode helps with reads
- **`better-sqlite3` is sync** — this is a feature, not a bug; it's fast and simple
- **Server Components can't use hooks** — no `useState`, `useEffect` in server files
- **API routes run on the server** — you can access `db` directly, no fetch needed
- **`revalidatePath`/`revalidateTag`** — use for cache invalidation after mutations
- **Migrations run at app startup** — in `lib/schema.ts`, called from root layout

## Git Workflow

- **Branch naming:** `feat/`, `fix/`, `chore/`, `docs/`
- **Commit format:** Conventional Commits (`feat:`, `fix:`, `chore:`)
- **PR description:** Include what changed and why, not just what
- **Squash merge** to main — keep history clean

## Resources

- [Next.js Docs](https://nextjs.org/docs)
- [better-sqlite3 API](https://github.com/WiseLibs/better-sqlite3/blob/master/docs/api.md)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Vitest Docs](https://vitest.dev/)
- [Zod Docs](https://zod.dev/)
