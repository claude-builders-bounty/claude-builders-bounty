# CLAUDE.md — Next.js 15 + SQLite SaaS

This is a Next.js 15 App Router project with SQLite (better-sqlite3) as the database.
Read this file completely before making any changes.

## Stack & Versions

- **Framework**: Next.js 15 (App Router only — no Pages Router)
- **Runtime**: Node.js 20+
- **Language**: TypeScript 5.x (strict mode)
- **Database**: SQLite via better-sqlite3
- **Styling**: Tailwind CSS 4
- **Auth**: next-auth v5 (Auth.js)
- **Package manager**: pnpm

## Dev Commands

```bash
pnpm dev          # Start dev server (port 3000)
pnpm build        # Production build
pnpm lint         # ESLint
pnpm typecheck    # tsc --noEmit
pnpm db:migrate   # Run pending migrations
pnpm db:seed      # Seed dev data
pnpm test         # Vitest
```

Always run `pnpm typecheck` before committing. If it fails, fix it — don't suppress with `@ts-ignore`.

## Folder Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/             # Auth-required route group
│   │   ├── dashboard/
│   │   └── settings/
│   ├── (public)/           # Public route group
│   │   ├── page.tsx        # Landing page
│   │   └── pricing/
│   ├── api/                # API routes
│   │   └── [resource]/
│   │       └── route.ts    # One file per resource
│   ├── layout.tsx          # Root layout
│   └── globals.css
├── components/
│   ├── ui/                 # Primitive UI components (Button, Input, Card)
│   └── [feature]/          # Feature-specific components
├── lib/
│   ├── db.ts               # Database connection (singleton)
│   ├── db/
│   │   ├── migrations/     # Numbered SQL files
│   │   ├── migrate.ts      # Migration runner
│   │   ├── seed.ts         # Dev seed data
│   │   └── queries/        # Named query functions
│   │       ├── users.ts
│   │       └── projects.ts
│   ├── auth.ts             # Auth config
│   └── utils.ts            # Shared utilities
├── types/
│   └── index.ts            # Shared TypeScript types
└── middleware.ts            # Auth middleware
```

### Rules

- **One route.ts per API resource.** Don't put multiple resources in one file.
- **Group routes by access level.** `(auth)/` requires login, `(public)/` doesn't. Use route groups, not middleware checks in every page.
- **Components are either `ui/` (reusable, no business logic) or `[feature]/` (specific to a feature).** Never mix.
- **All database queries live in `lib/db/queries/`.** Components and routes never write raw SQL.

## Database (SQLite + better-sqlite3)

### Connection (`lib/db.ts`)

```typescript
import Database from 'better-sqlite3';
import path from 'path';

const DB_PATH = process.env.DATABASE_URL || path.join(process.cwd(), 'data', 'app.db');

// Singleton — one connection per process
const db = new Database(DB_PATH);
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');
db.pragma('busy_timeout = 5000');

export default db;
```

**Critical rules:**
- Always enable WAL mode and foreign keys (as shown above)
- Always use parameterized queries: `db.prepare('SELECT * FROM users WHERE id = ?').get(id)` — never string concatenation
- Database file goes in `data/` directory (gitignored)
- Singleton connection — import from `lib/db.ts`, don't create new connections

### Migrations (`lib/db/migrations/`)

Name migrations with zero-padded numbers:
```
001_create_users.sql
002_create_projects.sql
003_add_user_email_index.sql
```

**Migration rules:**
- Migrations are forward-only. Never edit a migration that has been committed.
- Each migration is a single `.sql` file with plain SQL statements.
- Always include `IF NOT EXISTS` for CREATE TABLE.
- Always add indexes for columns used in WHERE/JOIN.
- Always include `created_at` and `updated_at` columns (INTEGER, Unix timestamps).
- Never use autoincrement — use `INTEGER PRIMARY KEY` (SQLite's rowid alias is faster).

```sql
-- 001_create_users.sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    created_at INTEGER NOT NULL DEFAULT (unixepoch()),
    updated_at INTEGER NOT NULL DEFAULT (unixepoch())
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
```

### Query Functions (`lib/db/queries/`)

```typescript
// lib/db/queries/users.ts
import db from '@/lib/db';

export function getUserById(id: number) {
    return db.prepare('SELECT * FROM users WHERE id = ?').get(id) as User | undefined;
}

export function createUser(email: string, name: string) {
    return db.prepare('INSERT INTO users (email, name) VALUES (?, ?)').run(email, name);
}
```

**Rules:**
- One file per table/resource
- Export named functions, not classes
- Return typed results (use `as Type` assertions at the query boundary)
- Use `prepare()` for all queries — never `exec()` with user input

## Component Patterns

### Server Components (default)

All components are Server Components unless they need interactivity. This is the default in App Router.

```tsx
// app/(auth)/dashboard/page.tsx — Server Component
import { getUserProjects } from '@/lib/db/queries/projects';

export default async function DashboardPage() {
    const projects = getUserProjects(userId);
    return <ProjectList projects={projects} />;
}
```

### Client Components (opt-in)

Add `'use client'` only when you need:
- `useState`, `useEffect`, `useRef`
- Event handlers (`onClick`, `onChange`)
- Browser APIs

```tsx
// components/ui/Button.tsx — still a Server Component (no state needed)
export function Button({ children, ...props }) {
    return <button className="..." {...props}>{children}</button>;
}

// components/dashboard/ProjectFilter.tsx — Client Component (needs state)
'use client';
export function ProjectFilter() {
    const [query, setQuery] = useState('');
    // ...
}
```

**Rule: Every `'use client'` must justify itself.** If you're adding it "just in case", don't.

### API Routes

```typescript
// app/api/projects/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { getProjects, createProject } from '@/lib/db/queries/projects';
import { auth } from '@/lib/auth';

export async function GET(req: NextRequest) {
    const session = await auth();
    if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const projects = getProjects(session.user.id);
    return NextResponse.json(projects);
}

export async function POST(req: NextRequest) {
    const session = await auth();
    if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const body = await req.json();
    // Validate body here
    const result = createProject(session.user.id, body.name);
    return NextResponse.json(result, { status: 201 });
}
```

**Rules:**
- Always check auth first
- Always validate request body
- Return appropriate HTTP status codes
- Use NextResponse.json() for all responses

## Naming Conventions

| What | Convention | Example |
|------|-----------|---------|
| Files/folders | kebab-case | `project-list.tsx` |
| Components | PascalCase | `ProjectList` |
| Functions | camelCase | `getUserById` |
| DB tables | snake_case, plural | `user_projects` |
| DB columns | snake_case | `created_at` |
| Types | PascalCase | `User`, `Project` |
| Env vars | SCREAMING_SNAKE | `DATABASE_URL` |
| CSS classes | Tailwind only | No custom CSS files |

## What We Don't Do (and Why)

| Don't | Why |
|-------|-----|
| Don't use Pages Router | App Router is the future. Don't mix routing paradigms. |
| Don't use ORMs (Prisma, Drizzle) | For SQLite, direct better-sqlite3 is faster, simpler, and has zero overhead. ORMs add complexity we don't need. |
| Don't use `any` type | Defeats the purpose of TypeScript. Use `unknown` and narrow. |
| Don't use `@ts-ignore` | Fix the type error instead. |
| Don't create custom CSS files | Tailwind handles everything. Custom CSS creates maintenance burden. |
| Don't use `useEffect` for data fetching | Use Server Components or React Server Actions. |
| Don't use `autoincrement` in SQLite | `INTEGER PRIMARY KEY` already auto-generates IDs and is faster. |
| Don't edit committed migrations | Create a new migration instead. Data loss risk. |
| Don't store secrets in code | Use `.env.local` (gitignored). |
| Don't use string concatenation in SQL | SQL injection risk. Always use parameterized queries. |
| Don't import from `@/app/` in `@/lib/` | lib is lower-level. It should not depend on app routes. |

## Error Handling

```typescript
// Consistent error response shape
type ApiError = {
    error: string;
    details?: string;
};

// In API routes:
try {
    // ... operation
} catch (e) {
    console.error('[API] Operation failed:', e);
    return NextResponse.json(
        { error: 'Internal server error' } satisfies ApiError,
        { status: 500 }
    );
}
```

**Rules:**
- Never expose internal error messages to clients
- Always log errors server-side with context
- Use `satisfies` for type-safe error responses

## Environment Variables

```bash
# .env.local (gitignored)
DATABASE_URL=data/app.db
NEXTAUTH_SECRET=your-secret-here
NEXTAUTH_URL=http://localhost:3000
```

**Rule:** Every env var must have a fallback or a clear error message if missing. Don't silently fail.
