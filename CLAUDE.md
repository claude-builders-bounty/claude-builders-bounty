# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

## Stack

- **Next.js 15** (App Router only — no Pages Router)
- **React 19**
- **TypeScript 5.8+**
- **SQLite** via `better-sqlite3` (sync, server-only)
- **Node.js 20+ LTS**

## Project Structure

```
src/
├── app/                    # App Router — file-based routing
│   ├── (auth)/            # Auth route group (login, register, etc.)
│   │   ├── login/page.tsx
│   │   └── layout.tsx
│   ├── (dashboard)/       # Protected routes
│   │   ├── layout.tsx
│   │   └── [slug]/page.tsx
│   ├── api/               # Route Handlers (server-only)
│   │   └── users/route.ts
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home
├── components/
│   ├── ui/                # Headless UI primitives (no CSS framework)
│   │   ├── Button.tsx
│   │   └── Modal.tsx
│   ├── forms/             # React Hook Form + Zod schemas
│   └── features/          # Domain-specific (e.g., Billing, UserProfile)
├── lib/
│   ├── db.ts              # better-sqlite3 singleton (SERVER ONLY)
│   ├── queries/           # SQL query functions by table
│   │   ├── users.ts
│   │   └── sessions.ts
│   └── utils.ts           # Shared utilities (date, string, etc.)
├── migrations/            # Named SQL migrations, up/down pairs
│   └── YYYYMMDD_HHMMSS_*.sql
├── types/                 # TypeScript interfaces (not classes)
│   └── database.ts        # Raw DB row types
└── middleware.ts          # Auth guard, rate limiting
```

**Why this structure**: Route groups `(name)` share layouts without affecting URLs. `lib/queries/` keeps SQL in one place — easy to test, optimize, and find. `components/ui/` has zero business logic — just props → DOM.

---

## Naming Conventions

| Context | Format | Example |
|---|---|---|
| Files / directories | `kebab-case` | `user-profile.tsx`, `api/routes/` |
| React components | `PascalCase` | `UserProfile`, `DataTable` |
| Functions / vars | `camelCase` | `getUserById`, `formatDate` |
| DB tables | `snake_case` | `user_profiles`, `api_keys` |
| DB columns | `snake_case` | `created_at`, `is_active` |
| TypeScript types | `PascalCase` | `UserProfile`, `DbUser` |
| Environment vars | `SCREAMING_SNAKE_CASE` | `DATABASE_URL`, `JWT_SECRET` |

**Why kebab-case files**: macOS默认大小写不敏感，PascalCase 会踩坑。

---

## Component Rules

### Rule 1: Default to Server Components

```typescript
// ✅ CORRECT — Server Component (default in App Router)
export default async function UserProfile({ userId }: { userId: string }) {
  const user = await getUserById(userId);   // direct DB access, no API call
  return <div>{user.name}</div>;
}
```

```typescript
// ❌ WRONG — Don't reach for useState/useEffect first
export default function UserProfile({ userId }: { userId: string }) {
  const [user, setUser] = useState(null);
  useEffect(() => { fetch(`/api/users/${userId}`)... }, [userId]);
  // ...
}
```

**Why**: Server Components ship zero JS to the browser, run on server, and can query the DB directly.

### Rule 2: Client Components = explicit 'use client'

Add `'use client'` **only** when you need:
- Browser APIs (`window`, `localStorage`, `document`)
- React hooks (`useState`, `useEffect`, event handlers)
- Interactive UI (modals, dropdowns, real-time forms)

```typescript
'use client';

import { useState } from 'react';

export function LoginForm() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  // ...
}
```

### Rule 3: Server → Client boundary via composition

```typescript
// ✅ CORRECT — Server fetches, Client receives serializable props
export default async function DashboardPage() {
  const data = await getDashboardData();   // runs on server, hits DB
  return <DashboardClient initialData={data} />;  // Client component receives plain object
}
```

**Why**: Keeps data fetching on server. Client component only handles interactivity.

---

## Database Rules

### Rule 1: better-sqlite3 is sync — use it only in Server Components and Route Handlers

```typescript
// lib/db.ts — singleton, created once per process
import Database from 'better-sqlite3';
import path from 'path';

let db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!db) {
    const dbPath = process.env.DATABASE_PATH ?? path.join(process.cwd(), 'data.db');
    db = new Database(dbPath);
    db.pragma('journal_mode = WAL');   // concurrent reads
    db.pragma('foreign_keys = ON');    // enforce FK constraints
  }
  return db;
}
```

**Never** import `getDb` in Client Components — it will throw at runtime.

### Rule 2: All schema changes via migrations

```bash
# Migration file naming: YYYYMMDD_HHMMSS_description.sql
migrations/
└── 20260328_120000_create_users.sql
```

```sql
-- migrations/20260328_120000_create_users.sql

-- === UP ===
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
);

-- === DOWN ===
DROP TABLE users;
```

**Why**: Migrations are version control for your schema. They enable rollback, CI validation, and consistent team environments.

### Rule 3: Query functions organized by table

```
lib/queries/
├── users.ts     ← all user-related SQL
└── sessions.ts  ← auth session SQL
```

```typescript
// lib/queries/users.ts
import { getDb } from '@/lib/db';

export const usersQueries = {
  findById: getDb().prepare('SELECT * FROM users WHERE id = ?'),
  findByEmail: getDb().prepare('SELECT * FROM users WHERE email = ?'),
  create: getDb().prepare(
    'INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)'
  ),
};

// Usage in Server Component or Route Handler
const user = usersQueries.findByEmail.get('alice@example.com');
```

### Rule 4: Prepared statements only — no string interpolation

```typescript
// ✅ CORRECT — prepared statement, safe
const user = db.prepare('SELECT * FROM users WHERE id = ?').get(userId);

// ❌ WRONG — SQL injection vulnerability
const user = db.exec(`SELECT * FROM users WHERE id = '${userId}'`);
```

---

## Anti-Patterns (Forbidden)

### ❌ useState in Server Components
Server Components run on the server. React hooks only work in Client Components.

### ❌ Direct DOM manipulation
`document.getElementById(...)` breaks React's virtual DOM. Use refs and state instead.

### ❌ SQL string interpolation
Always use `?` placeholders in prepared statements. Never `${variable}` in SQL strings.

### ❌ Client-side secrets
`process.env.SECRET_KEY` in client-side code is visible to anyone. Keep secrets in Server Components, Route Handlers, or middleware only.

### ❌ Mixing Server and Client Components in one file
```typescript
// ❌ WRONG — don't export both
export default async function ServerComponent() { /* ... */ }
export function ClientComponent() { 'use client'; /* ... */ }
```

---

## Dev Commands

```bash
npm run dev          # Dev server (localhost:3000)
npm run build        # Production build
npm start            # Production server

# Database
npm run migrate       # Apply pending migrations
npm run migrate:rollback  # Rollback last migration

# Code quality
npm run lint         # ESLint
npm run type-check   # TypeScript (no emit)
```

---

## Environment Variables

Create `.env.local` (gitignored — never commit secrets):

```bash
DATABASE_PATH=./data/production.db
SESSION_SECRET=<generate with: openssl rand -base64 32>
```

---

## When to Ask

Before implementing, ask if:
- Auth strategy is defined (session vs JWT vs OAuth)
- Database schema is designed or needs schema review
- Third-party API keys are required
- Performance constraints exist (concurrent users, data volume)
