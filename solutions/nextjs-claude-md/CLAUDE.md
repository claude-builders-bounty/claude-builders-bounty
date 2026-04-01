# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> Opinionated conventions for Claude Code. Every rule exists because ignoring it
> causes real bugs or tech-debt in Next.js 15 App Router + SQLite projects.

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── (auth)/             # Route group: login, register, forgot-password
│   ├── (dashboard)/        # Route group: authenticated pages
│   ├── api/                # Route Handlers (API endpoints)
│   │   └── v1/             # Versioned API — always version from day one
│   ├── layout.tsx          # Root layout (providers, fonts, metadata)
│   └── not-found.tsx       # Custom 404
├── components/
│   ├── ui/                 # Primitives (Button, Input, Card) — no business logic
│   └── features/           # Feature components (UserTable, InvoiceForm)
├── lib/
│   ├── db/
│   │   ├── index.ts        # Database connection (singleton)
│   │   ├── schema.ts       # Table definitions + types
│   │   └── migrations/     # Numbered SQL files: 001_init.sql, 002_users.sql
│   ├── auth.ts             # Auth utilities (session, middleware)
│   └── utils.ts            # Pure helper functions (no side effects)
├── hooks/                  # Custom React hooks
├── types/                  # Shared TypeScript types/interfaces
└── middleware.ts           # Next.js middleware (auth checks, redirects)
```

## Naming Conventions

| What | Convention | Example | Why |
|------|-----------|---------|-----|
| Files | `kebab-case` | `user-settings.tsx` | Next.js convention, URL-friendly |
| Components | `PascalCase` | `UserSettings` | React convention |
| DB tables | `snake_case`, plural | `user_sessions` | SQL convention |
| DB columns | `snake_case` | `created_at` | SQL convention |
| API routes | `kebab-case` | `/api/v1/user-sessions` | REST convention |
| Environment vars | `SCREAMING_SNAKE` | `DATABASE_URL` | Universal convention |
| TypeScript types | `PascalCase` | `UserSession` | TS convention |
| Hooks | `camelCase` with `use` prefix | `useUserSession` | React convention |

**Anti-pattern:** Never mix conventions. `userSessions` table or `user_sessions.tsx` file = instant reject.

## Database (SQLite)

### Connection

```typescript
// lib/db/index.ts — SINGLETON. Import this everywhere.
import Database from 'better-sqlite3';
import path from 'path';

const DB_PATH = process.env.DATABASE_URL || path.join(process.cwd(), 'data', 'app.db');

let db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!db) {
    db = new Database(DB_PATH);
    db.pragma('journal_mode = WAL');      // Required for concurrent reads
    db.pragma('busy_timeout = 5000');     // Wait 5s instead of instant SQLITE_BUSY
    db.pragma('foreign_keys = ON');       // Enforce FK constraints
    db.pragma('synchronous = NORMAL');    // Safe with WAL, faster than FULL
  }
  return db;
}
```

**Rules:**
- Always use WAL mode. Without it, readers block writers.
- Always set `busy_timeout`. Default 0 causes random SQLITE_BUSY errors under load.
- Always enable foreign keys. SQLite disables them by default (!).
- Never create a new `Database()` instance per request. Use the singleton.

### Migrations

```
lib/db/migrations/
├── 001_init.sql
├── 002_add_users.sql
├── 003_add_sessions.sql
```

**Rules:**
- Files are numbered sequentially: `001_`, `002_`, etc. Never rename or reorder.
- Each file is idempotent: use `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`.
- Run migrations on app startup (`getDb()` should apply pending migrations).
- Never delete a migration file. To undo, create a new migration.
- Every table has `id` (TEXT, UUID), `created_at` (TEXT, ISO 8601), `updated_at` (TEXT, ISO 8601).

```sql
-- 001_init.sql
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  email TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
```

### Queries

- Use parameterized queries. **Never** interpolate values into SQL strings.
- Use `db.prepare()` and cache prepared statements for hot paths.
- Wrap multi-statement operations in `db.transaction()`.
- Return plain objects from DB layer, not Database.Statement results.

```typescript
// ✅ Good
const user = getDb().prepare('SELECT * FROM users WHERE id = ?').get(userId) as User | undefined;

// ❌ Bad — SQL injection
const user = getDb().prepare(`SELECT * FROM users WHERE id = '${userId}'`).get();
```

## API Routes (Route Handlers)

```typescript
// app/api/v1/users/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { getDb } from '@/lib/db';
import { requireAuth } from '@/lib/auth';

export async function GET(req: NextRequest) {
  const session = await requireAuth(req);
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const users = getDb().prepare('SELECT id, name, email FROM users').all();
  return NextResponse.json({ data: users });
}
```

**Rules:**
- Always return `{ data: ... }` for success, `{ error: string }` for errors.
- Always validate request body with zod. No `any` types.
- Always return proper HTTP status codes: 200, 201, 400, 401, 403, 404, 500.
- Always version your API (`/api/v1/`). You will need v2 sooner than you think.
- Never expose internal errors to clients. Log them, return generic messages.

## Components

**Rules:**
- `components/ui/` = stateless, no data fetching, no business logic. These are your design system.
- `components/features/` = may fetch data, contain business logic, compose UI primitives.
- Server Components by default. Add `'use client'` only when you need interactivity.
- Never put `'use client'` on a component that only renders HTML. It disables streaming.
- Props interfaces live in the same file, not in `types/`.

```typescript
// components/ui/button.tsx — UI primitive
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
}

export function Button({ variant = 'primary', size = 'md', ...props }: ButtonProps) {
  return <button className={cn(baseStyles, variants[variant], sizes[size])} {...props} />;
}
```

## Error Handling

- API routes: try/catch at the top level, return `{ error }` with status code.
- Server Components: use `error.tsx` boundaries per route segment.
- Client Components: use React Error Boundaries.
- Never swallow errors silently. At minimum, `console.error()`.
- Use a custom `AppError` class for expected errors (validation, not-found, unauthorized).

## Environment Variables

```env
# .env.local (git-ignored)
DATABASE_URL=./data/app.db
AUTH_SECRET=generate-with-openssl-rand-hex-32
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

**Rules:**
- `NEXT_PUBLIC_` prefix = exposed to browser. Use sparingly.
- Validate all env vars at startup. Fail fast if missing.
- Never commit `.env.local`. Commit `.env.example` with placeholder values.

## Dev Commands

```bash
npm run dev          # Start dev server (port 3000)
npm run build        # Production build
npm run start        # Start production server
npm run lint         # ESLint
npm run typecheck    # tsc --noEmit
npm run test         # Vitest
npm run db:migrate   # Run pending migrations
npm run db:seed      # Seed development data
npm run db:reset     # Drop + recreate + seed (dev only!)
```

## Anti-Patterns (Never Do These)

1. **Don't use `prisma` with SQLite in production.** Prisma's SQLite adapter doesn't support WAL mode properly and has known concurrency issues. Use `better-sqlite3` directly or Drizzle ORM.

2. **Don't store files in SQLite.** Store file paths or S3 URLs. BLOBs destroy WAL performance.

3. **Don't use `Date` objects in SQLite.** Store as ISO 8601 TEXT strings. SQLite has no native date type.

4. **Don't create indexes on every column.** Index only columns used in WHERE/JOIN/ORDER BY. Each index slows writes.

5. **Don't use `SELECT *` in production queries.** Select only the columns you need. Especially important when tables grow.

6. **Don't skip `key` props in lists.** Use stable IDs, never array indices.

7. **Don't use `useEffect` for data fetching.** Use Server Components or Route Handlers.

8. **Don't put secrets in `NEXT_PUBLIC_` vars.** They're bundled into client JavaScript.

## Patterns to Follow

1. **Optimistic UI updates** for mutations (delete, toggle, update).
2. **Server Actions** for form submissions instead of API routes when possible.
3. **Streaming** with `loading.tsx` and Suspense boundaries.
4. **Parallel data fetching** in layouts/pages (don't waterfall).
5. **Revalidation** with `revalidatePath()` or `revalidateTag()` after mutations.
