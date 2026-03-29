# CLAUDE.md - Next.js 15 + SQLite SaaS Project

**Last Updated:** 2026-03-29  
**Stack:** Next.js 15 (App Router) + SQLite (better-sqlite3) + TypeScript + Tailwind CSS

---

## Project Overview

This is a production SaaS application built with:
- **Next.js 15** with App Router (not Pages Router)
- **SQLite** via `better-sqlite3` for local dev and production
- **TypeScript** (strict mode enabled)
- **Tailwind CSS** for styling
- **React Server Components** by default

---

## Folder Structure

```
/
├── app/                    # Next.js 15 App Router
│   ├── (auth)/            # Auth-gated routes (login, signup)
│   ├── (dashboard)/       # Dashboard routes (protected)
│   ├── api/               # API routes
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page
├── components/            # React components
│   ├── ui/               # shadcn/ui components
│   └── [feature]/        # Feature-specific components
├── lib/                   # Core utilities
│   ├── db.ts             # Database connection & helpers
│   ├── auth.ts           # Authentication logic
│   └── utils.ts          # Shared utilities
├── db/                    # Database files
│   ├── schema.sql        # Base schema (versioned)
│   ├── migrations/       # Migration files (numbered)
│   └── dev.db            # SQLite database file (gitignored)
├── types/                 # TypeScript type definitions
├── public/               # Static assets
└── scripts/              # DB seed scripts, etc.
```

### Key Principles:
- **App Router only** — no mixing with Pages Router
- **Route groups** (`(auth)`, `(dashboard)`) for layout organization
- **Server Components by default** — mark Client Components explicitly with `'use client'`
- **Database code lives in `/lib/db.ts`** — never inline SQL in components

---

## Database Conventions

### Schema Management
- **Base schema:** `db/schema.sql` (version-controlled)
- **Migrations:** Numbered files in `db/migrations/` (e.g., `001_add_users.sql`, `002_add_posts.sql`)
- **Migration format:**
  ```sql
  -- Migration: 001_add_users.sql
  -- Description: Create users table
  -- Date: 2026-03-29

  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  CREATE INDEX idx_users_email ON users(email);
  ```

### Migration Rules
1. **Never modify existing migrations** — create a new one to change the schema
2. **Always include IF NOT EXISTS** in CREATE statements
3. **Always add indexes** for foreign keys and frequently queried columns
4. **Test rollback** — every migration should be reversible (include `-- Rollback:` comments)
5. **Run migrations manually** via script: `npm run db:migrate`

### SQL Style
- Use `INTEGER PRIMARY KEY AUTOINCREMENT` for IDs (SQLite auto-optimization)
- Use `TEXT` for strings, `INTEGER` for numbers, `REAL` for decimals
- Use `DATETIME DEFAULT CURRENT_TIMESTAMP` for timestamps
- Foreign keys: `user_id INTEGER REFERENCES users(id) ON DELETE CASCADE`
- Snake_case for table/column names (e.g., `created_at`, not `createdAt`)

### Database Helper (`lib/db.ts`)
```typescript
import Database from 'better-sqlite3';

const db = new Database(process.env.DATABASE_PATH || 'db/dev.db');
db.pragma('journal_mode = WAL'); // Performance optimization

export function query<T>(sql: string, params: any[] = []): T[] {
  return db.prepare(sql).all(...params) as T[];
}

export function queryOne<T>(sql: string, params: any[] = []): T | undefined {
  return db.prepare(sql).get(...params) as T | undefined;
}

export function execute(sql: string, params: any[] = []): void {
  db.prepare(sql).run(...params);
}

export default db;
```

**Usage:**
```typescript
import { query, queryOne, execute } from '@/lib/db';

// Fetch multiple rows
const users = query<User>('SELECT * FROM users WHERE active = ?', [1]);

// Fetch single row
const user = queryOne<User>('SELECT * FROM users WHERE id = ?', [userId]);

// Insert/Update
execute('INSERT INTO users (email, name) VALUES (?, ?)', [email, name]);
```

---

## Component Patterns

### Server Components (Default)
- Use for data fetching, database queries, static content
- No `'use client'` directive needed
- **Example:**
  ```tsx
  // app/(dashboard)/users/page.tsx
  import { query } from '@/lib/db';

  export default async function UsersPage() {
    const users = query<User>('SELECT * FROM users');
    return <div>{users.map(u => <UserCard key={u.id} user={u} />)}</div>;
  }
  ```

### Client Components
- Use for interactivity (onClick, useState, useEffect, etc.)
- Mark with `'use client'` at the top
- **Example:**
  ```tsx
  'use client';
  import { useState } from 'react';

  export function UserForm() {
    const [email, setEmail] = useState('');
    // ... interactive form logic
  }
  ```

### Component Organization
- **UI components** (`/components/ui/`) — reusable, generic (buttons, inputs, cards)
- **Feature components** (`/components/[feature]/`) — domain-specific (e.g., `/components/users/UserCard.tsx`)
- **Collocate with features** — if a component is only used in one route, keep it in that route folder

### Naming Conventions
- **Components:** PascalCase (e.g., `UserCard.tsx`)
- **Utilities:** camelCase (e.g., `formatDate.ts`)
- **API routes:** lowercase with hyphens (e.g., `app/api/users/route.ts`)

---

## API Routes

### Structure
```
app/api/
├── users/
│   ├── route.ts           # GET /api/users, POST /api/users
│   └── [id]/
│       └── route.ts       # GET /api/users/:id, PUT /api/users/:id
└── auth/
    ├── login/route.ts
    └── signup/route.ts
```

### API Route Template
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { query, execute } from '@/lib/db';

export async function GET(request: NextRequest) {
  try {
    const users = query<User>('SELECT * FROM users');
    return NextResponse.json(users);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch users' }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    execute('INSERT INTO users (email, name) VALUES (?, ?)', [body.email, body.name]);
    return NextResponse.json({ success: true }, { status: 201 });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to create user' }, { status: 500 });
  }
}
```

### API Best Practices
- **Validate input** — use Zod or similar for request validation
- **Return consistent JSON** — `{ data: ..., error: ... }` structure
- **Handle errors** — always return proper HTTP status codes
- **Use middleware** for auth checks (e.g., `app/api/middleware.ts`)

---

## Development Commands

```bash
# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Database migrations
npm run db:migrate

# Database seed (for dev)
npm run db:seed

# Type checking
npm run type-check

# Linting
npm run lint
```

### package.json Scripts
```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit",
    "db:migrate": "node scripts/migrate.js",
    "db:seed": "node scripts/seed.js"
  }
}
```

---

## What We Don't Do (and Why)

### ❌ No Prisma/ORMs
- **Why:** SQLite + better-sqlite3 is fast and simple. ORMs add complexity and slow down development.
- **Instead:** Write raw SQL via helper functions in `lib/db.ts`

### ❌ No MongoDB or NoSQL
- **Why:** This project uses SQLite. Mixing databases creates maintenance hell.
- **Instead:** Use SQLite JSON columns if you need flexible schema

### ❌ No Pages Router
- **Why:** We're on Next.js 15 with App Router. Pages Router is legacy.
- **Instead:** Use `app/` directory exclusively

### ❌ No Inline SQL in Components
- **Why:** SQL logic belongs in API routes or server actions, not in component files.
- **Instead:** Create helper functions in `lib/db.ts` or use API routes

### ❌ No Client-Side Database Queries
- **Why:** Database queries must run server-side. SQLite doesn't work in the browser.
- **Instead:** Use Server Components or API routes for data fetching

### ❌ No CSS Modules or Styled Components
- **Why:** Tailwind CSS is the standard here. Mixing styling approaches causes inconsistency.
- **Instead:** Use Tailwind utility classes

### ❌ No Default Exports (Except Pages)
- **Why:** Named exports are easier to refactor and autocomplete.
- **Instead:** `export function MyComponent()` (except for Next.js page files which require default exports)

---

## Authentication Patterns

- Use **server-side session management** (e.g., `iron-session` or JWT in httpOnly cookies)
- Store user sessions in SQLite: `CREATE TABLE sessions (id TEXT PRIMARY KEY, user_id INTEGER, expires_at DATETIME)`
- **Never store passwords in plaintext** — use bcrypt or Argon2
- Protect API routes with middleware:
  ```typescript
  import { NextRequest, NextResponse } from 'next/server';
  import { getSession } from '@/lib/auth';

  export async function middleware(request: NextRequest) {
    const session = await getSession(request);
    if (!session) {
      return NextResponse.redirect(new URL('/login', request.url));
    }
    return NextResponse.next();
  }

  export const config = {
    matcher: '/dashboard/:path*',
  };
  ```

---

## Environment Variables

Required `.env.local`:
```env
DATABASE_PATH=./db/dev.db
SESSION_SECRET=your-secret-key-here
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

---

## Testing

- Use **Vitest** for unit tests
- Use **Playwright** for E2E tests
- Test database queries with in-memory SQLite: `new Database(':memory:')`

---

## Production Deployment

### Turso (Recommended for SQLite in production)
- Use **Turso** (libSQL) for serverless SQLite
- Replace `better-sqlite3` with `@libsql/client` in production
- Keep local dev with `better-sqlite3`

### Vercel / Netlify
- SQLite files don't persist on serverless platforms
- Use Turso or switch to PostgreSQL for production

---

## Additional Notes

- **TypeScript strict mode is enabled** — fix type errors before pushing
- **Commit migrations to Git** — they are part of the codebase
- **Use `npx shadcn-ui@latest add [component]`** for UI components
- **Keep dependencies minimal** — fewer dependencies = fewer breaking changes

---

**This CLAUDE.md should be enough for Claude Code to understand the entire project structure and conventions without asking clarifying questions. If Claude asks "should I use X or Y?", this document is incomplete.**
