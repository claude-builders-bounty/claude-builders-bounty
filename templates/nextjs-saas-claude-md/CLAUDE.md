# CLAUDE.md - Next.js 15 + SQLite SaaS Template

> Opinionated context file for Claude Code on Next.js 15 App Router + SQLite projects.
> Paste this into the root of your SaaS project. Claude will understand your stack, conventions, and patterns.

---

## Stack & Versions

| Layer | Technology | Version | Why |
|-------|------------|---------|-----|
| Framework | Next.js | 15.x | App Router, Server Components, streaming |
| Runtime | Node.js | 20.x LTS | Stable, native better-sqlite3 support |
| Database | SQLite | 3.45+ | Zero-config, perfect for MVP/SaaS <10K users |
| ORM | better-sqlite3 | 11.x | Sync API, fastest SQLite binding |
| Auth | NextAuth.js | 5.x | App Router native, multi-provider |
| Styling | Tailwind CSS | 4.x | Utility-first, no runtime overhead |
| Forms | React Hook Form | 7.x | Performant, minimal re-renders |
| Validation | Zod | 3.x | Type-safe schemas, shared client/server |

**Do NOT use**: Prisma (async overhead), PlanetScale (migration complexity), MongoDB (no relational model for SaaS).

---

## Folder Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/             # Auth route group (no layout wrapper)
│   │   ├── login/
│   │   ├── signup/
│   │   └── layout.tsx      # Minimal auth layout
│   ├── (dashboard)/        # Protected route group
│   │   ├── dashboard/
│   │   ├── settings/
│   │   └── layout.tsx      # Dashboard shell + auth check
│   ├── api/                # Route handlers (REST)
│   │   ├── users/
│   │   ├── subscriptions/
│   │   └── webhooks/
│   ├── layout.tsx          # Root layout (fonts, providers)
│   └── page.tsx            # Landing page
├── components/
│   ├── ui/                 # Base UI (Button, Input, Card)
│   ├── forms/              # Form components (wrapped in RHF)
│   ├── dashboard/          # Dashboard-specific widgets
│   └── providers/          # Context providers (Theme, Session)
├── lib/
│   ├── db/                 # Database layer
│   │   ├── schema.ts       # Table definitions
│   │   ├── migrations.ts   # Migration runner
│   │   ├── index.ts        # DB connection (singleton)
│   │   └── queries/        # Typed query functions
│   ├── auth/               # NextAuth configuration
│   ├── validations/        # Zod schemas (shared)
│   ├── utils/              # Helper functions
│   └── constants/          # Config values
├── hooks/                  # Custom React hooks
├── types/                  # TypeScript types (global)
└── styles/                 # Global CSS
```

**Naming convention**:
- Files: lowercase with dashes (`user-profile.tsx`)
- Components: PascalCase export (`export function UserProfile`)
- Folders: lowercase (`components/ui/`)

---

## SQL / Migration Conventions

### Database Connection Pattern

```typescript
// lib/db/index.ts
import Database from 'better-sqlite3';
import path from 'path';

const dbPath = path.join(process.cwd(), 'data', 'app.db');
export const db = new Database(dbPath);

// Enable WAL mode for better concurrent reads
db.pragma('journal_mode = WAL');

// Singleton - imported everywhere, same connection
```

### Schema Definition Pattern

```typescript
// lib/db/schema.ts
import { db } from './index';

export function initSchema() {
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT UNIQUE NOT NULL,
      name TEXT,
      created_at INTEGER DEFAULT (strftime('%s', 'now')),
      updated_at INTEGER DEFAULT (strftime('%s', 'now'))
    );

    CREATE TABLE IF NOT EXISTS subscriptions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL REFERENCES users(id),
      tier TEXT NOT NULL DEFAULT 'free',
      status TEXT NOT NULL DEFAULT 'active',
      stripe_id TEXT,
      created_at INTEGER DEFAULT (strftime('%s', 'now'))
    );

    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS idx_subs_user ON subscriptions(user_id);
  `);
}
```

### Migration Rules

1. **No migration files** - Use `initSchema()` that runs on every startup
2. **Safe changes only** - `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`
3. **Breaking changes require manual migration** - Write a migration script in `lib/db/migrations.ts`
4. **Timestamps are integers** - Unix epoch, no datetime parsing overhead
5. **Foreign keys are explicit** - `REFERENCES table(id)`, no magic

### Query Pattern

```typescript
// lib/db/queries/users.ts
import { db } from '../index';
import type { User } from '@/types';

export function getUserByEmail(email: string): User | undefined {
  return db.prepare('SELECT * FROM users WHERE email = ?').get(email);
}

export function createUser(email: string, name: string): number {
  const stmt = db.prepare('INSERT INTO users (email, name) VALUES (?, ?)');
  const result = stmt.run(email, name);
  return result.lastInsertRowid;
}

// Transaction pattern
export function createUserWithSubscription(email: string, name: string) {
  const insertUser = db.prepare('INSERT INTO users (email, name) VALUES (?, ?)');
  const insertSub = db.prepare('INSERT INTO subscriptions (user_id, tier) VALUES (?, ?)');

  const transaction = db.transaction((email, name) => {
    const userId = insertUser.run(email, name).lastInsertRowid;
    insertSub.run(userId, 'free');
    return userId;
  });

  return transaction(email, name);
}
```

---

## Component Patterns

### Server Component (Default)

```typescript
// app/(dashboard)/dashboard/page.tsx
import { getUser } from '@/lib/db/queries/users';
import { DashboardShell } from '@/components/dashboard/shell';

export default async function DashboardPage() {
  // Direct DB access - no fetch needed
  const user = await getUser(session.user.id);
  
  return <DashboardShell user={user} />;
}
```

### Client Component (Interactive)

```typescript
// components/dashboard/user-form.tsx
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { updateUserSchema } from '@/lib/validations/user';

export function UserForm({ user }: { user: User }) {
  const form = useForm({
    resolver: zodResolver(updateUserSchema),
    defaultValues: user,
  });

  const onSubmit = async (data) => {
    await fetch('/api/users', { method: 'PATCH', body: JSON.stringify(data) });
  };

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      {/* fields */}
    </form>
  );
}
```

### API Route Handler

```typescript
// app/api/users/route.ts
import { db } from '@/lib/db';
import { updateUserSchema } from '@/lib/validations/user';
import { NextResponse } from 'next/server';

export async function PATCH(request: Request) {
  const body = await request.json();
  const parsed = updateUserSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error }, { status: 400 });
  }

  const stmt = db.prepare('UPDATE users SET name = ?, updated_at = ? WHERE id = ?');
  stmt.run(parsed.data.name, Math.floor(Date.now() / 1000), parsed.data.id);

  return NextResponse.json({ success: true });
}
```

---

## Patterns to Follow

1. **Server Components for data** - No `useEffect` fetching, direct DB queries
2. **Client Components for interactivity** - Forms, animations, real-time updates
3. **Zod shared schemas** - One source of truth for validation
4. **WAL mode** - Enable for better read concurrency
5. **Transaction blocks** - Wrap multi-step writes in `db.transaction()`
6. **Route groups** - Use `(group)` for layout variations
7. **Prepared statements** - Reuse prepared statements for performance
8. **Integer timestamps** - Avoid datetime parsing, use Unix epoch

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Correct Approach |
|--------------|--------------|------------------|
| `useEffect` for fetching | Waterfall requests, no SSR | Server Component direct DB |
| Prisma ORM | Async overhead, complex schema | better-sqlite3 sync API |
| `datetime` columns | String parsing, timezone issues | Integer Unix timestamps |
| No transactions | Race conditions, partial writes | `db.transaction()` wrapper |
| Client-side validation only | Security risk, type drift | Zod shared schemas |
| Global CSS modules | Naming conflicts | Tailwind utilities |
| Inline styles | No caching, hard to maintain | Tailwind classes |
| `pages/` directory | Legacy, no streaming | `app/` App Router |

---

## What We Don't Do (And Why)

1. **No GraphQL** - REST is simpler for SQLite, no query complexity management
2. **No Redux/Zustand** - Server Components + URL state is enough for most SaaS
3. **No Server Actions for mutations** - API routes give better error handling
4. **No ORMs** - better-sqlite3 is faster, we need raw SQL for complex queries
5. **No sharding** - SQLite handles 10K concurrent users, scale later
6. **No microservices** - Monolith first, split when team size demands it
7. **No docker-compose for dev** - SQLite is file-based, no container needed

---

## Dev Commands

```bash
# Development
npm run dev              # Start Next.js dev server (port 3000)

# Database
npm run db:init          # Run schema initialization
npm run db:migrate       # Run pending migrations
npm run db:seed          # Seed test data

# Build
npm run build            # Build for production
npm run start            # Production server

# Testing
npm run test             # Run Vitest unit tests
npm run test:e2e         # Run Playwright E2E tests
```

---

## Environment Variables

```env
# Required
DATABASE_URL=./data/app.db
NEXTAUTH_SECRET=your-secret-here
NEXTAUTH_URL=http://localhost:3000

# Optional (Stripe)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

# Optional (Email)
SMTP_HOST=
SMTP_USER=
SMTP_PASS=
```

---

## Quick Start Checklist

When starting a new project with this template:

1. Create `src/app/` structure
2. Copy `lib/db/` folder
3. Add `better-sqlite3` to dependencies
4. Create `data/app.db` file location
5. Add `initSchema()` to `layout.tsx` or startup script
6. Install Zod, React Hook Form, Tailwind
7. Add auth provider layout
8. Start building server components

---

_This CLAUDE.md is tested on greenfield Next.js 15 + SQLite projects. Claude Code will understand the full stack context without asking clarifying questions._