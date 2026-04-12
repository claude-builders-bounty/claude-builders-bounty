# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Stack & Versions

- **Node.js**: 20.x LTS (use `nvm use` if .nvmrc present)
- **Next.js**: 15.x with App Router (NOT pages router)
- **SQLite**: better-sqlite3 (synchronous, not async) or Turso (libsql)
- **Package Manager**: npm (not yarn/pnpm unless project specifies)
- **TypeScript**: 5.x strict mode

```bash
node --version  # Must be 20+
npm --version   # Must be 10+
```

---

## Project Structure

```
/
├── app/                    # Next.js App Router pages
│   ├── (auth)/            # Auth route group (login, register)
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/        # Protected dashboard routes
│   │   ├── layout.tsx     # Dashboard layout with sidebar
│   │   └── [slug]/page.tsx
│   ├── api/               # API Route Handlers only
│   │   └── webhooks/
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Landing page / marketing
├── components/
│   ├── ui/                # Primitive UI components (Button, Input, Card)
│   │   └── button.tsx     # One component per file
│   ├── forms/             # Form components with react-hook-form
│   │   └── login-form.tsx
│   └── shared/            # Shared layout components (Header, Footer, Sidebar)
├── lib/
│   ├── db/
│   │   ├── index.ts       # DB connection singleton
│   │   ├── schema.ts      # Table definitions
│   │   └── migrations/    # SQL migration files
│   ├── auth.ts            # Session/auth utilities
│   └── utils.ts           # Shared utilities (cn(), formatDate(), etc.)
├── public/                # Static assets
├── scripts/
│   └── migrate.ts         # Migration runner script
└── .env.local            # Environment variables (never commit)
```

### Rules

- **`app/` = pages, `components/` = UI, `lib/` = logic**. Never mix these.
- **Route groups** `(auth)` and `(dashboard)` are for organization only — they don't affect URLs.
- **Colocate** components with their feature. A dashboard component stays in `components/dashboard/`, not a generic `components/` folder.

---

## SQL / Migration Conventions

### Migration File Naming

```
scripts/migrations/
├── 0001_initial_schema.sql
├── 0002_add_users_table.sql
├── 0003_add_soft_delete.sql
└── 0004_add_indexes.sql
```

### Migration Format

```sql
-- Migration: 0001_initial_schema.sql
-- Description: Create users and sessions tables
-- Created: 2024-01-15

BEGIN;

CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at INTEGER NOT NULL DEFAULT (unixepoch()),
  updated_at INTEGER NOT NULL DEFAULT (unixepoch()),
  deleted_at INTEGER -- soft delete
);

CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at INTEGER NOT NULL,
  created_at INTEGER NOT NULL DEFAULT (unixepoch())
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);

COMMIT;
```

### Key Rules

- **Always use `IF NOT EXISTS`** for tables and indexes — allows safe re-runs.
- **Wrap multi-statement migrations in `BEGIN...COMMIT`** — atomic execution.
- **Unix timestamps** (integers) for all dates — SQLite has no native datetime type.
- **UUIDs** via `lower(hex(randomblob(16)))` — better than auto-increment for distributed systems.
- **Soft deletes** with `deleted_at INTEGER` — never hard-delete user data.
- **One migration per logical change** — don't batch unrelated changes.

### Running Migrations

```bash
# Run pending migrations
npm run migrate

# Check status
npm run migrate:status
```

### Query Patterns

```typescript
// ✅ CORRECT — parameterized, explicit column list
const user = db.prepare(`
  SELECT id, email, created_at 
  FROM users 
  WHERE email = ? AND deleted_at IS NULL
`).get(email);

// ❌ WRONG — string interpolation, SELECT *
const user = db.prepare(`SELECT * FROM users WHERE email = '${email}'`);
```

---

## Component Patterns

### File Naming

- **Pages**: `page.tsx`
- **Layouts**: `layout.tsx`
- **Components**: `PascalCase.tsx`
- **Utilities**: `camelCase.ts`

### Server vs Client Components

```typescript
// ✅ Default: Server Component (no "use client", no hooks, no browser APIs)
export default async function DashboardPage({ params }: { params: { slug: string } }) {
  const data = await fetchData(params.slug);
  return <Dashboard data={data} />;
}

// ✅ Explicit: Client Component ("use client" only when needed)
'use client';
import { useState } from 'react';
export function LoginForm() {
  const [email, setEmail] = useState('');
  return <input value={email} onChange={e => setEmail(e.target.value)} />;
}
```

### Rules

- **Server first**: Start as a server component. Add `'use client'` only when you need hooks, browser APIs, or event handlers.
- **Propdrilling is fine** for server components passing data to other server components.
- **State management**: Use React hooks only. No Redux/Zustand/Jotai unless the project explicitly requires it.

### UI Component Structure

```typescript
// components/ui/button.tsx
import { cn } from '@/lib/utils';
import type { ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'destructive' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
}

export function Button({ 
  className, 
  variant = 'primary', 
  size = 'md',
  ...props 
}: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center rounded-md font-medium',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
        'disabled:pointer-events-none disabled:opacity-50',
        {
          'bg-primary text-primary-foreground hover:bg-primary/90': variant === 'primary',
          'bg-secondary text-secondary-foreground hover:bg-secondary/80': variant === 'secondary',
          'bg-destructive text-destructive-foreground hover:bg-destructive/90': variant === 'destructive',
          'hover:bg-accent hover:text-accent-foreground': variant === 'ghost',
        },
        { 'h-8 px-3 text-sm': size === 'sm', 'h-10 px-4': size === 'md', 'h-12 px-6 text-lg': size === 'lg' },
        className
      )}
      {...props}
    />
  );
}
```

---

## Dev Commands

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Run database migrations
npm run migrate

# Run type checking
npm run typecheck

# Run linter
npm run lint

# Build for production
npm run build

# Run production server
npm start
```

---

## Patterns to Follow

1. **Use `lib/utils.ts` for shared utilities** — `cn()` for class merging, date formatters, etc.
2. **Prepare statements for repeated queries** — `db.prepare()` is pre-compiled in better-sqlite3.
3. **Use route groups** `(auth)/` and `(dashboard)/` to organize routes without affecting URLs.
4. **Soft delete everything** — set `deleted_at` instead of removing rows.
5. **Environment variables** — access via `process.env` in server code, never expose to client.
6. **Async is for API routes** — pages and components are synchronous by default in Next.js App Router.

---

## Anti-Patterns to Avoid

1. **Don't use `SELECT *`** — always list the columns you need.
2. **Don't hardcode IDs** — use `crypto.randomUUID()` or SQLite's `randomblob(16)`.
3. **Don't mix App Router with Pages Router** — pick one and stick with it.
4. **Don't use `new Date()` for timestamps** — use `Date.now()` or `Math.floor(Date.now() / 1000)` for Unix seconds.
5. **Don't commit `.env.local`** — it contains secrets. Use `.env.example` for template.
6. **Don't put business logic in components** — keep it in `lib/` and call from server components.
7. **Don't use `any`** — use `unknown` and narrow it, or define proper types.

---

## What We Don't Do (And Why)

| Anti-pattern | Why we avoid it |
|--------------|-----------------|
| `SELECT *` | Transfers unnecessary data, breaks when columns are added/removed |
| Auto-increment IDs | Conflicts in distributed/multi-instance deployments |
| Hard deletes | Data loss, breaks foreign key cascades, removes audit trail |
| Client-side DB connections | Exposes credentials to browser, security risk |
| Mixing API styles | Inconsistent DX, harder to maintain |
| `.env` in git | Secrets get leaked to repository history |

---

## Testing Confirmation

After pasting this CLAUDE.md into a greenfield Next.js + SQLite project:

1. `npm run dev` should start without errors
2. `npm run migrate` should create the initial schema
3. Creating a user via the signup form should persist to SQLite
4. Logging in should create a session and redirect to dashboard
5. Deleting a user should set `deleted_at`, not remove the row
