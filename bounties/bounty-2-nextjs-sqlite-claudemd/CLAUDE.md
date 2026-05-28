# CLAUDE.md — Next.js 15 + SQLite SaaS Starter

> Drop this file into the root of any greenfield **Next.js 15 App Router + SQLite (better-sqlite3 or Turso)** project. Claude Code will pick up the conventions automatically.

---

## Stack & Versions

| Layer | Choice | Version | Why |
|---|---|---|---|
| Framework | Next.js (App Router) | 15.x | Server Components by default, streaming, partial prerendering |
| Runtime | Node.js | ≥ 20 LTS | Required by Next.js 15 |
| Language | TypeScript | 5.x strict | Zero `any`; enable `noUncheckedIndexedAccess` |
| Database | SQLite via better-sqlite3 | 11.x | Single-file, zero-config, fast for single-server SaaS |
| DB Driver (optional) | @libsql/client | latest | For Turso (libSQL) edge deployments |
| Auth | NextAuth.js v5 | beta | App Router native; supports OAuth + credentials |
| Styling | Tailwind CSS | 4.x | Utility-first; no runtime CSS-in-JS |
| Validation | Zod | 3.x | Shared schemas for client + server + API routes |
| ORM | None (raw SQL) | — | better-sqlite3 is fast enough; avoids abstraction leaks |
| Package Manager | pnpm | 9.x | Strict node_modules, faster installs |
| Testing | Vitest + Testing Library | latest | Native ESM, fast, Vite-based |
| Linting | ESLint + Prettier | latest | Enforced on `pre-commit` via `lint-staged` |

---

## Dev Commands

```bash
pnpm install              # Install dependencies
pnpm dev                  # Start dev server (http://localhost:3000)
pnpm build                # Production build (type-checks + compiles)
pnpm start                # Run production build
pnpm lint                 # ESLint
pnpm format               # Prettier (write)
pnpm test                 # Vitest (single run)
pnpm test:watch           # Vitest (watch mode)
pnpm db:migrate           # Run pending migrations
pnpm db:seed              # Seed development data
pnpm db:studio            # Open Drizzle Studio (if using Drizzle — optional)
```

---

## Folder Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/             # Auth route group (login, register)
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/        # Protected route group
│   │   ├── layout.tsx      # Dashboard shell (sidebar + nav)
│   │   ├── page.tsx        # /dashboard
│   │   └── settings/
│   │       └── page.tsx
│   ├── api/                # API route handlers
│   │   └── health/route.ts
│   ├── layout.tsx          # Root layout (providers, fonts, metadata)
│   ├── page.tsx            # Landing page
│   └── globals.css
├── components/
│   ├── ui/                 # Primitive UI components (Button, Input, Dialog…)
│   └── features/           # Feature-composed components
├── lib/
│   ├── db/
│   │   ├── client.ts       # Database connection singleton
│   │   ├── schema.ts       # Table definitions & types (optional Drizzle)
│   │   └── migrations/     # Numbered SQL migration files
│   │       ├── 001_create_users.sql
│   │       └── 002_create_projects.sql
│   ├── auth.ts             # NextAuth configuration
│   ├── validations/        # Zod schemas
│   │   └── user.ts
│   ├── utils.ts            # Pure helper functions (cn, formatDate, etc.)
│   └── constants.ts        # App-wide constants
├── hooks/                  # Custom React hooks
├── types/                  # Shared TypeScript types & interfaces
│   └── index.ts
└── actions/                # Server Actions (use server)
    └── user.ts
```

### Rules

1. **Every route** gets its own folder with a `page.tsx`. Never put multiple pages in one file.
2. **Route groups** `(parentheses)` are for layout sharing, not URL segments.
3. **Colocate tests**: `component.test.tsx` lives next to `component.tsx`.
4. **Never** import from `@/components/ui` inside `lib/`. UI depends on lib, not the reverse.
5. **Server Actions** go in `src/actions/`. They are the primary way to mutate data from the client.

---

## SQL / Migration Conventions

### File Naming

```
migrations/
  001_create_users.sql
  002_create_projects.sql
  003_add_email_to_users.sql
```

- Zero-padded, 3-digit prefix.
- Descriptive snake_case name.
- One logical change per migration.

### Schema Rules

```sql
-- Always use these columns on every table:
CREATE TABLE users (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  uuid       TEXT UNIQUE NOT NULL DEFAULT (lower(hex(randomblob(16)))),
  email      TEXT UNIQUE NOT NULL,
  name       TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  deleted_at TEXT  -- soft delete; NULL = active
);

-- Index foreign keys and frequently queried columns:
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_deleted_at ON users(deleted_at);
```

- **Primary key**: Always `id INTEGER PRIMARY KEY AUTOINCREMENT`.
- **UUID**: Store as `TEXT` for external-facing IDs. Never expose `id` to the API.
- **Timestamps**: `TEXT` in ISO 8601 format (`datetime('now')`). No INTEGER timestamps.
- **Soft delete**: `deleted_at TEXT`. Queries must filter `WHERE deleted_at IS NULL` unless explicitly fetching trashed records.
- **Booleans**: SQLite stores as `INTEGER` (0/1). Map to `boolean` in TypeScript.
- **No ORMs** (by default). Write raw SQL in `src/lib/db/client.ts` helper functions. If you add Drizzle, keep it in `schema.ts` and generate migrations from it.
- **Never** use `ALTER TABLE … DROP COLUMN`. Create a new table + migration instead.

### Querying

```typescript
// lib/db/client.ts
import Database from 'better-sqlite3';
import path from 'path';

const DB_PATH = path.join(process.cwd(), 'data', 'app.db');

// Singleton pattern — one connection for the entire server
let _db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!_db) {
    _db = new Database(DB_PATH);
    _db.pragma('journal_mode = WAL');      // Better concurrent read performance
    _db.pragma('foreign_keys = ON');       // Enforce FK constraints
    _db.pragma('busy_timeout = 5000');     // Wait up to 5s for locks
  }
  return _db;
}
```

```typescript
// Usage in server code:
import { getDb } from '@/lib/db/client';

export function getUserByUuid(uuid: string) {
  const db = getDb();
  return db.prepare('SELECT * FROM users WHERE uuid = ? AND deleted_at IS NULL').get(uuid);
}
```

- **Always** use parameterized queries (`?` placeholders). Never interpolate strings.
- **Prepared statements**: Use `.prepare()` for queries run more than once.
- **Transactions**: Wrap multi-step mutations in `db.transaction(() => { … })`.
- **WAL mode**: Always enable. Required for concurrent reads during writes.

---

## Component Patterns

### Server vs Client Components

```tsx
// Default: Server Component (no "use client")
// app/(dashboard)/page.tsx
import { getProjects } from '@/lib/db/client';
import { ProjectList } from '@/components/features/project-list';

export default async function DashboardPage() {
  const projects = await getProjects();  // Direct DB access in Server Component
  return <ProjectList initialProjects={projects} />;
}
```

```tsx
// Client Component (only when needed: interactivity, hooks, browser APIs)
// components/features/project-list.tsx
'use client';

import { useState } from 'react';

export function ProjectList({ initialProjects }) {
  const [filter, setFilter] = useState('');
  // ... client-side filtering
}
```

### Rules

1. **Server Components by default.** Only add `'use client'` when you need:
   - `useState`, `useEffect`, event handlers
   - Browser APIs (`window`, `localStorage`)
   - Custom hooks with client-side logic
2. **Props**: Define with inline TypeScript types or Zod schemas. No separate `.types.ts` files for component props.
3. **UI primitives** (`components/ui/`) accept `className` via `cva` (class-variance-authority) and spread `...props`. They never make API calls.
4. **Feature components** compose UI primitives. They may call Server Actions.
5. **Never** use `fetch()` to call your own API routes from Server Components. Import the function directly.

### Server Actions

```tsx
// actions/user.ts
'use server';

import { z } from 'zod';
import { getDb } from '@/lib/db/client';
import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';

const UpdateNameSchema = z.object({
  uuid: z.string(),
  name: z.string().min(1).max(100),
});

export async function updateName(formData: FormData) {
  const { uuid, name } = UpdateNameSchema.parse({
    uuid: formData.get('uuid'),
    name: formData.get('name'),
  });

  const db = getDb();
  db.prepare('UPDATE users SET name = ?, updated_at = datetime(\'now\') WHERE uuid = ?')
    .run(name, uuid);

  revalidatePath('/settings');
  redirect('/settings');
}
```

- **Always** validate with Zod at the action boundary. Never trust form data.
- **Always** call `revalidatePath()` after mutations to update cached data.
- Return `redirect()` for navigation after success; throw errors for failures.

---

## API Routes (when needed)

```typescript
// app/api/health/route.ts
import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({ status: 'ok', timestamp: new Date().toISOString() });
}
```

- Use API routes only for: webhooks, third-party callbacks, or non-HTML responses.
- For internal data mutations, prefer Server Actions over API routes.
- Always return proper HTTP status codes (201 for creation, 422 for validation errors, etc.).

---

## Auth Pattern

```typescript
// lib/auth.ts
import NextAuth from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import { getDb } from '@/lib/db/client';

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Credentials({
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        const db = getDb();
        const user = db.prepare(
          'SELECT * FROM users WHERE email = ? AND deleted_at IS NULL'
        ).get(credentials.email);
        // ... verify password hash
        return user;
      },
    }),
  ],
  session: { strategy: 'jwt' },
});
```

- Use `auth()` in Server Components to check session.
- Use `useSession()` in Client Components.
- Protect routes via middleware: `middleware.ts` at project root.

---

## What We Don't Do (and Why)

| We don't | Why |
|---|---|
| Use Prisma or TypeORM | Heavy abstraction over SQLite adds latency & complexity. Raw SQL + typed results is simpler and faster. |
| Use `getServerSideProps` or Pages Router | App Router is the standard. Mixing routers causes confusion. |
| Store files in the database | Use cloud storage (S3, R2) or local `public/` for assets. SQLite is for structured data only. |
| Use `any` type | TypeScript strict mode. Use `unknown` + type narrowing instead. |
| Build a monorepo for a single app | Premature optimization. Split when you have 2+ deployable units. |
| Use CSS-in-JS (styled-components, emotion) | Runtime overhead. Tailwind handles styling at build time. |
| Make every component a Client Component | Server Components reduce JS bundle. Default to server; opt-in to client. |
| Use environment variables without validation | Validate with Zod at startup: `const env = EnvSchema.parse(process.env)`. |
| Write integration tests for SQLite | SQLite is the test database. Use Vitest + in-memory (`:memory:`) for speed. |
| Use `INTEGER` for timestamps | `TEXT` ISO 8601 is human-readable, sortable, and timezone-aware. |
| Deploy to Vercel with better-sqlite3 | Native modules don't work on Vercel. Use Turso/libSQL for edge, or deploy on a VPS/Fly.io. |

---

## Common Patterns

### Error Handling

```typescript
// Server Actions: use result types
type ActionResult<T> = 
  | { ok: true; data: T }
  | { ok: false; error: string };

export async function createProject(name: string): Promise<ActionResult<{ uuid: string }>> {
  try {
    const db = getDb();
    const uuid = crypto.randomUUID();
    db.prepare('INSERT INTO projects (uuid, name) VALUES (?, ?)').run(uuid, name);
    return { ok: true, data: { uuid } };
  } catch (e) {
    return { ok: false, error: 'Failed to create project' };
  }
}
```

### Environment Variables

```typescript
// lib/env.ts
import { z } from 'zod';

const EnvSchema = z.object({
  DATABASE_PATH: z.string().default('./data/app.db'),
  NEXTAUTH_SECRET: z.string().min(32),
  NEXTAUTH_URL: z.string().url(),
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
});

export const env = EnvSchema.parse(process.env);
```

- Validate at import time. App crashes immediately on missing vars — no silent failures.

### Testing

```typescript
// lib/db/test-helpers.ts
import Database from 'better-sqlite3';

export function createTestDb() {
  const db = new Database(':memory:');
  db.pragma('journal_mode = WAL');
  db.pragma('foreign_keys = ON');
  // Run migrations
  const migration = readFileSync('src/lib/db/migrations/001_create_users.sql', 'utf-8');
  db.exec(migration);
  return db;
}
```

- Use in-memory SQLite for tests. No mocking.
- Seed with factories, not fixtures.
- Test server actions through direct function calls, not HTTP.

---

## Quick Checklist for New Features

1. [ ] Migration file created in `src/lib/db/migrations/`
2. [ ] Zod validation schema in `src/lib/validations/`
3. [ ] DB helper functions (typed queries) in `src/lib/db/client.ts`
4. [ ] Server Action in `src/actions/` (mutation + revalidation)
5. [ ] Server Component for data fetch, Client Component for interactivity
6. [ ] Route in `src/app/(dashboard)/feature/page.tsx`
7. [ ] Test file colocated: `feature.test.tsx`

---

*This file is designed for Next.js 15 App Router + SQLite (better-sqlite3 or Turso). Adjust versions and package names if your stack differs. Every convention here exists because it prevents a specific class of bugs or performance problems in production SaaS apps.*
