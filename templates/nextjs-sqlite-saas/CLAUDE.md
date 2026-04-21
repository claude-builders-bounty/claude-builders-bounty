# CLAUDE.md — Next.js 15 + SQLite SaaS

> This file tells Claude Code how this project works.
> Every rule is opinionated and has a reason. If something feels wrong, read the "why" before changing it.

---

## Stack & Versions

| Layer | Choice | Version | Why |
|-------|--------|---------|-----|
| Framework | Next.js (App Router) | 15.x | Server Components by default = less client JS, better SEO, simpler data fetching |
| Runtime | Node.js | 20 LTS+ | Stability over bleeding edge; matches Vercel/Railway defaults |
| Database | better-sqlite3 | 11.x | Synchronous, zero-network-hop, single-file DB. Perfect for single-server SaaS until you need geo-replication |
| Database (alt) | Turso (libsql) | latest | Drop-in replacement when you need edge reads or multi-region. Same SQL, same migration flow |
| ORM | None — raw SQL | — | ORMs hide query cost. In SQLite, every query is local and fast; raw SQL keeps it visible and debuggable |
| Migrations | Custom script (`db/migrate.ts`) | — | One file per migration, sequential numbering, no magic. Details below |
| Styling | Tailwind CSS | 4.x | Utility-first, zero runtime CSS, tree-shakes unused styles |
| UI Components | shadcn/ui | latest | Copy-paste components, no version lock-in, full control over markup |
| Auth | Better Auth | 1.x | TypeScript-native, self-hosted, no vendor lock-in. Supports email/password + OAuth out of the box |
| Validation | Zod | 3.x | Runtime + TypeScript type inference from one schema. Use everywhere: API input, form data, env vars |
| Package manager | pnpm | 9.x | Strict dependency resolution, faster installs, saves disk space |
| Linting | ESLint + Prettier | latest | Non-negotiable. `pnpm lint` must pass before any commit |
| Testing | Vitest | 2.x | Fast, ESM-native, compatible with Next.js. No Jest config wrestling |

---

## Dev Commands

```bash
# Install dependencies
pnpm install

# Run dev server (port 3000)
pnpm dev

# Run migrations
pnpm db:migrate

# Create a new migration
pnpm db:new <migration-name>
# → Creates db/migrations/NNNN_<migration-name>.sql

# Lint + format
pnpm lint
pnpm format

# Type check (no emit)
pnpm typecheck

# Run tests
pnpm test

# Build for production
pnpm build

# Start production server
pnpm start
```

### package.json scripts (expected)

```json
{
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build",
    "start": "next start",
    "lint": "next lint && prettier --check .",
    "format": "prettier --write .",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest",
    "db:migrate": "tsx db/migrate.ts",
    "db:new": "tsx db/new-migration.ts"
  }
}
```

---

## Folder Structure

```
.
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Auth route group (login, signup, forgot-password)
│   │   ├── login/page.tsx
│   │   ├── signup/page.tsx
│   │   └── layout.tsx            # Minimal layout, no sidebar
│   ├── (dashboard)/              # Authenticated route group
│   │   ├── layout.tsx            # Sidebar + header layout
│   │   ├── page.tsx              # Dashboard home
│   │   ├── settings/page.tsx
│   │   └── [feature]/page.tsx    # Feature pages
│   ├── api/                      # API routes (keep thin!)
│   │   └── [resource]/route.ts
│   ├── layout.tsx                # Root layout (html, body, providers)
│   └── globals.css               # Tailwind imports only
├── components/                   # Shared UI components
│   ├── ui/                       # shadcn/ui primitives (Button, Input, Dialog…)
│   └── [feature]/                # Feature-specific components
├── lib/                          # Core utilities and business logic
│   ├── db.ts                     # Database connection singleton
│   ├── auth.ts                   # Better Auth config
│   ├── validators/               # Zod schemas (one file per domain)
│   └── [domain].ts               # Domain logic (users.ts, billing.ts, etc.)
├── db/
│   ├── migrations/               # SQL migration files (0001_create_users.sql, …)
│   ├── migrate.ts                # Migration runner script
│   ├── new-migration.ts          # Migration generator script
│   └── schema.sql                # Full schema snapshot (regenerated after each migration)
├── types/                        # Shared TypeScript types
│   └── index.ts                  # Re-exports all types
├── public/                       # Static assets
├── tests/                        # Test files (mirrors app/ structure)
├── .env.local                    # Local env vars (never committed)
├── .env.example                  # Template for env vars
└── CLAUDE.md                     # This file
```

### Why this structure?

- **`app/` route groups** `(auth)` and `(dashboard)` share different layouts without nesting URLs. Auth pages have no sidebar; dashboard pages do.
- **`components/ui/`** is reserved for shadcn/ui primitives. Never put business logic here.
- **`lib/`** is the brain. All business logic lives here, not in API routes or components.
- **`db/`** is separate from `lib/` because migration scripts run outside the app context.
- **`types/`** avoids circular imports. Components and lib both import from here.

---

## Naming Conventions

### Files & Directories

| What | Convention | Example | Why |
|------|-----------|---------|-----|
| React components | PascalCase | `UserCard.tsx` | Matches the component name, standard React convention |
| Pages & layouts | lowercase `page.tsx` / `layout.tsx` | `app/(dashboard)/page.tsx` | Next.js convention, non-negotiable |
| Utilities / lib | camelCase | `lib/formatDate.ts` | Distinguishes non-component files from components |
| DB migrations | `NNNN_snake_case.sql` | `0001_create_users.sql` | Sequential ordering, grep-friendly |
| API routes | `route.ts` in resource folder | `app/api/users/route.ts` | Next.js convention |
| Test files | `*.test.ts(x)` | `tests/lib/users.test.ts` | Vitest default pattern |
| Env vars | `SCREAMING_SNAKE_CASE` | `DATABASE_URL` | Universal convention |

### Code

| What | Convention | Example |
|------|-----------|---------|
| Variables & functions | camelCase | `getUserById`, `isActive` |
| Types & interfaces | PascalCase | `User`, `CreateUserInput` |
| Constants | SCREAMING_SNAKE | `MAX_RETRIES`, `DEFAULT_PAGE_SIZE` |
| Database tables | snake_case, plural | `users`, `user_sessions`, `billing_plans` |
| Database columns | snake_case | `created_at`, `is_active`, `stripe_customer_id` |
| Zod schemas | camelCase + `Schema` suffix | `createUserSchema`, `updateSettingsSchema` |
| Boolean vars | `is`/`has`/`can` prefix | `isActive`, `hasSubscription`, `canEdit` |

---

## Database & SQL Conventions

### Connection (lib/db.ts)

```typescript
import Database from "better-sqlite3";
import path from "node:path";

const DB_PATH = process.env.DATABASE_URL || path.join(process.cwd(), "db", "app.db");

// Singleton — one connection per process
const db = new Database(DB_PATH);

// WAL mode: allows concurrent reads while writing. Essential for web servers.
db.pragma("journal_mode = WAL");

// Foreign keys are OFF by default in SQLite. Always turn them on.
db.pragma("foreign_keys = ON");

// Busy timeout: wait 5s instead of throwing SQLITE_BUSY immediately.
db.pragma("busy_timeout = 5000");

export default db;
```

**Why WAL mode?** Default journal mode locks the entire DB on writes. WAL allows readers and one writer to work concurrently. For a web server handling multiple requests, this is non-negotiable.

**Why busy_timeout?** Without it, concurrent write attempts throw immediately. 5 seconds gives the first writer time to finish.

### Migration Rules

1. **One migration = one `.sql` file** in `db/migrations/`
2. **Sequential numbering**: `0001_`, `0002_`, `0003_` — no timestamps, no UUIDs
3. **Forward-only**: No down migrations. If you need to undo, write a new migration that reverses the change.
   - *Why?* Down migrations are never tested and always broken in production. A forward-only approach is simpler and safer.
4. **Every migration is idempotent where possible**: Use `IF NOT EXISTS` for tables, `CREATE INDEX IF NOT EXISTS`, etc.
5. **Never modify a migration that has been committed**. Write a new one instead.
6. **Migration runner tracks applied migrations** in a `_migrations` table:

```sql
-- This table is auto-created by the migration runner
CREATE TABLE IF NOT EXISTS _migrations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### SQL Style

```sql
-- ✅ Good: explicit, readable, predictable
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  email TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
```

**ID strategy**: Random hex string (32 chars). Not auto-increment integers (predictable, enumerable), not UUIDs (too long for URLs). `lower(hex(randomblob(16)))` is fast, unique enough for a single-server DB, and URL-friendly.

**Timestamps as TEXT**: SQLite has no native datetime type. `TEXT` with ISO 8601 format (`datetime('now')`) is sortable, human-readable, and avoids timezone bugs.

**Booleans as INTEGER**: SQLite has no boolean type. Use `INTEGER` with `0`/`1`. Name columns with `is_` prefix for clarity.

### Query Patterns

```typescript
// ✅ Always use prepared statements — never interpolate user input
const getUser = db.prepare("SELECT * FROM users WHERE id = ?");
const user = getUser.get(userId);

// ✅ Use transactions for multi-step writes
const createUserWithProfile = db.transaction((userData, profileData) => {
  const insertUser = db.prepare("INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)");
  const insertProfile = db.prepare("INSERT INTO profiles (user_id, bio) VALUES (?, ?)");

  const result = insertUser.run(userData.email, userData.name, userData.passwordHash);
  insertProfile.run(result.lastInsertRowid, profileData.bio);
});

// ✅ Pagination: offset-based is fine for SQLite (no network round-trip penalty)
const listUsers = db.prepare(
  "SELECT * FROM users WHERE is_active = 1 ORDER BY created_at DESC LIMIT ? OFFSET ?"
);
const users = listUsers.all(pageSize, (page - 1) * pageSize);
```

---

## Component Patterns

### Server Components (Default)

Every component is a Server Component unless it needs interactivity. This is the #1 rule.

```tsx
// app/(dashboard)/users/page.tsx
// ✅ Server Component — fetches data directly, no "use client", no useEffect
import { getUsers } from "@/lib/users";
import { UserList } from "@/components/users/UserList";

export default async function UsersPage() {
  const users = await getUsers();
  return (
    <main className="container mx-auto py-8">
      <h1 className="text-2xl font-bold mb-6">Users</h1>
      <UserList users={users} />
    </main>
  );
}
```

### Client Components (Only When Needed)

Add `"use client"` only when the component needs:
- Event handlers (`onClick`, `onChange`, `onSubmit`)
- Hooks (`useState`, `useEffect`, `useRef`)
- Browser APIs (`window`, `localStorage`, `IntersectionObserver`)

```tsx
// components/users/UserSearch.tsx
"use client";
// ✅ Client Component — needs useState for search input
import { useState } from "react";
import { Input } from "@/components/ui/input";

export function UserSearch({ onSearch }: { onSearch: (query: string) => void }) {
  const [query, setQuery] = useState("");
  // ...
}
```

**Rule**: Push `"use client"` as far down the tree as possible. A page should never be a Client Component. Extract the interactive part into a child component.

### Server Actions

Use Server Actions for form submissions and mutations. They replace API routes for most write operations.

```tsx
// app/(dashboard)/settings/actions.ts
"use server";

import { z } from "zod";
import { revalidatePath } from "next/cache";
import { updateUserSettings } from "@/lib/users";
import { updateSettingsSchema } from "@/lib/validators/users";

export async function updateSettings(formData: FormData) {
  const raw = Object.fromEntries(formData);
  const parsed = updateSettingsSchema.safeParse(raw);

  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors };
  }

  await updateUserSettings(parsed.data);
  revalidatePath("/settings");
  return { success: true };
}
```

**Rules for Server Actions:**
1. Always validate input with Zod — never trust `formData` directly
2. Put actions in a separate `actions.ts` file, not inline in the component
3. Return `{ error }` or `{ success }` — don't throw (the client can't catch Server Action throws gracefully)
4. Call `revalidatePath` or `revalidateTag` after mutations to refresh cached data

### API Routes (When You Actually Need Them)

Use API routes only for:
- Webhooks (Stripe, OAuth callbacks)
- External API consumers (mobile apps, third-party integrations)
- File uploads

```typescript
// app/api/users/route.ts
import { NextRequest, NextResponse } from "next/server";
import { getUsers, createUser } from "@/lib/users";
import { createUserSchema } from "@/lib/validators/users";

export async function GET() {
  const users = getUsers();
  return NextResponse.json(users);
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const parsed = createUserSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 });
  }

  const user = createUser(parsed.data);
  return NextResponse.json(user, { status: 201 });
}
```

**Rule**: API route handlers must be thin. Validate → call lib function → return response. No business logic in route files.

### Error Handling

```tsx
// app/(dashboard)/error.tsx
"use client";
// ✅ Error boundaries must be Client Components
export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px]">
      <h2 className="text-xl font-semibold mb-4">Something went wrong</h2>
      <button onClick={reset} className="btn btn-primary">
        Try again
      </button>
    </div>
  );
}
```

Every route group should have its own `error.tsx`. Don't let errors bubble to the root.

### Loading States

```tsx
// app/(dashboard)/users/loading.tsx
// ✅ Automatic loading UI via file convention
import { Skeleton } from "@/components/ui/skeleton";

export default function UsersLoading() {
  return (
    <div className="container mx-auto py-8">
      <Skeleton className="h-8 w-48 mb-6" />
      <div className="space-y-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    </div>
  );
}
```

---

## Environment Variables

```bash
# .env.example

# Database
DATABASE_URL=./db/app.db          # Local SQLite path
# TURSO_URL=libsql://...          # Uncomment for Turso
# TURSO_AUTH_TOKEN=...            # Uncomment for Turso

# Auth (Better Auth)
BETTER_AUTH_SECRET=               # Random 32+ char string. Generate: openssl rand -hex 32
BETTER_AUTH_URL=http://localhost:3000

# App
NEXT_PUBLIC_APP_NAME=MyApp
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

**Rules**:
- `NEXT_PUBLIC_` prefix = exposed to the browser. Never put secrets here.
- Validate all env vars at startup with Zod:

```typescript
// lib/env.ts
import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().default("./db/app.db"),
  BETTER_AUTH_SECRET: z.string().min(32),
  BETTER_AUTH_URL: z.string().url(),
  NEXT_PUBLIC_APP_NAME: z.string().default("MyApp"),
  NEXT_PUBLIC_APP_URL: z.string().url(),
});

export const env = envSchema.parse(process.env);
```

---

## What We Don't Do (and Why)

| ❌ Don't | Why |
|----------|-----|
| Use an ORM (Prisma, Drizzle) | SQLite queries are local and fast. An ORM adds abstraction without solving a real problem. Raw SQL is more debuggable, and `better-sqlite3` is synchronous — no async/await noise. |
| Use `useEffect` for data fetching | Server Components fetch data directly. `useEffect` fetching causes loading waterfalls, layout shifts, and race conditions. |
| Put business logic in API routes | API routes are transport adapters. Logic belongs in `lib/`. This makes it testable and reusable across Server Actions and API routes. |
| Use `default export` for components (except pages) | Named exports enable better tree-shaking and IDE auto-imports. Pages use `default export` because Next.js requires it. |
| Create barrel files (`index.ts` re-exports) | They break tree-shaking, create circular dependency risks, and make "Go to Definition" useless. Import from the specific file. |
| Use relative imports across boundaries | Always use `@/` path aliases. `import { db } from "@/lib/db"` is clear; `import { db } from "../../../lib/db"` is not. |
| Store dates as Unix timestamps | ISO 8601 strings are human-readable, sortable, and debuggable. Unix timestamps require conversion at every read. |
| Use auto-increment integer IDs | Predictable, enumerable (users can guess `/users/1`, `/users/2`). Random hex IDs are URL-safe and don't leak information. |
| Add `"use client"` to pages | Pages should be Server Components. Extract interactive parts into child Client Components. A `"use client"` page loses all Server Component benefits. |
| Skip Zod validation on server inputs | TypeScript types disappear at runtime. Without Zod, a malformed request crashes your server instead of returning a clean 400. |
| Use `any` or `as` type assertions | If you need `any`, the types are wrong. Fix the types. `as` hides real bugs. |
| Write down migrations | They're never tested, always broken in production, and create false confidence. Forward-only migrations are simpler. |
| Use `next/font` with more than 2 fonts | Each font adds weight. One sans + one mono is enough. More fonts = slower loads and inconsistent design. |
| Catch errors silently (`catch (e) {}`) | Silent catches hide bugs. Log the error, or don't catch it. |

---

## Testing Conventions

```typescript
// tests/lib/users.test.ts
import { describe, it, expect, beforeEach } from "vitest";
import db from "@/lib/db";
import { createUser, getUserByEmail } from "@/lib/users";

// Use a separate test database
beforeEach(() => {
  db.exec("DELETE FROM users");
});

describe("createUser", () => {
  it("creates a user and returns it", () => {
    const user = createUser({
      email: "test@example.com",
      name: "Test User",
      passwordHash: "hashed",
    });

    expect(user.email).toBe("test@example.com");
    expect(user.id).toHaveLength(32);
  });

  it("rejects duplicate emails", () => {
    createUser({ email: "dup@example.com", name: "A", passwordHash: "h" });
    expect(() =>
      createUser({ email: "dup@example.com", name: "B", passwordHash: "h" })
    ).toThrow();
  });
});
```

**Rules**:
- Test `lib/` functions directly — they contain all the logic
- Don't test UI components unless they have complex conditional rendering
- Use a real SQLite database for tests (in-memory or temp file), not mocks
- Each test file sets up and tears down its own data

---

## Git Conventions

```bash
# Commit message format
<type>: <short description>

# Types
feat:     New feature
fix:      Bug fix
refactor: Code change that doesn't fix a bug or add a feature
docs:     Documentation only
test:     Adding or updating tests
chore:    Build process, dependencies, tooling
db:       Database migrations or schema changes

# Examples
feat: add user settings page
fix: prevent duplicate email registration
db: add billing_plans table
refactor: extract auth middleware to lib/
```

**Rules**:
- One commit = one logical change
- Migrations get their own commit with `db:` prefix
- Never force-push to `main`

---

## Performance Notes

- **SQLite is fast** — a simple query takes ~0.01ms locally. Don't over-optimize.
- **Use `db.prepare()`** — Prepared statements are compiled once and reused. Always prepare outside the request handler.
- **Batch writes in transactions** — 100 individual INSERTs: slow. 100 INSERTs in one transaction: fast.
- **Add indexes for WHERE/ORDER BY columns** — But not for every column. Indexes slow down writes.
- **Use `loading.tsx`** for perceived performance — The page feels fast even if the query takes 200ms.

---

## Deployment Notes

- **Single server**: SQLite lives on disk. You need a persistent filesystem (Railway, Fly.io with volumes, VPS).
- **NOT serverless**: Vercel's serverless functions have ephemeral filesystems. SQLite files are wiped between invocations. Use Turso if deploying to Vercel.
- **Backups**: Set up daily `sqlite3 app.db ".backup backup.db"` via cron. SQLite supports hot backups with `.backup`.
- **WAL files**: `app.db-wal` and `app.db-shm` are part of the database. Include them in backups, don't delete them.

---

*This CLAUDE.md is opinionated by design. Every rule exists because the alternative caused real problems in production. When in doubt, follow the rule first, then propose changes with evidence.*
