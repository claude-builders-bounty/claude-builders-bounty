# CLAUDE.md - Next.js 15 + SQLite SaaS Template

> Opinionated production-ready template. Every rule has a reason.

---

## Stack & Versions

| Layer | Tech | Version | Why |
|-------|------|---------|-----|
| Frontend | Next.js App Router | 15.x | React Server Components, streaming, better DX |
| Database | better-sqlite3 | 11.x | Sync API, fast, zero-config local dev |
| ORM | None (raw SQL) | - | SQLite is simple enough, Kysely optional |
| Auth | NextAuth.js | 5.x | Industry standard, flexible |
| Styling | Tailwind CSS | 4.x | Utility-first, no CSS-in-JS overhead |
| Testing | Vitest | 3.x | Fast, ESM-native, Jest-compatible API |

---

## Folder Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/             # Auth route group (no layout)
│   │   ├── login/
│   │   └── signup/
│   ├── (dashboard)/        # Protected route group
│   │   ├── layout.tsx      # Auth check wrapper
│   │   ├── dashboard/
│   │   └── settings/
│   ├── api/                # API routes (REST, not tRPC)
│   │   ├── users/
│   │   └── sessions/
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Landing page
├── components/
│   ├── ui/                 # Primitive components (Button, Input)
│   ├── forms/              # Form components
│   └── layouts/            # Layout components
├── lib/
│   ├── db.ts               # SQLite connection
│   ├── auth.ts             # NextAuth config
│   ├── utils.ts            # Helper functions
├── migrations/             # SQL migration files
├── types/                  # TypeScript types
└── middleware.ts           # Next.js middleware (auth)
```

---

## SQL / Migration Conventions

### Database Connection

```typescript
// lib/db.ts
import Database from 'better-sqlite3';

const db = new Database('data/app.db');
db.pragma('journal_mode = WAL'); // Better performance

export default db;
```

### Migration Files

```
migrations/
├── 001_init.sql
├── 002_users.sql
├── 003_sessions.sql
```

**Naming:** `NNNN_description.sql` (4-digit prefix)

**Migration Content:**

```sql
-- migrations/001_init.sql
-- Create users table
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  created_at INTEGER DEFAULT (strftime('%s', 'now')),
  updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- Index for common queries
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
```

**Timestamps:** Always use INTEGER (Unix epoch). No DATETIME.

### Query Patterns

```typescript
// Good: Prepared statements
const getUser = db.prepare('SELECT * FROM users WHERE id = ?');
const user = getUser.get(userId);

// Good: Transaction for multiple writes
const insertUser = db.prepare('INSERT INTO users (email, name) VALUES (?, ?)');
const insertSession = db.prepare('INSERT INTO sessions (user_id) VALUES (?)');

db.transaction(() => {
  const { lastInsertRowid } = insertUser.run(email, name);
  insertSession.run(lastInsertRowid);
})();
```

---

## Component Patterns

### Server Components (Default)

```tsx
// app/(dashboard)/dashboard/page.tsx
import db from '@/lib/db';

export default async function DashboardPage() {
  const users = db.prepare('SELECT * FROM users').all();
  
  return (
    <div>
      <h1>Dashboard</h1>
      <UserList users={users} />
    </div>
  );
}
```

**Rule:** Default to Server Components. Only use 'use client' when needed for:
- Event handlers (onClick, onSubmit)
- Browser APIs (localStorage, window)
- Hooks (useState, useEffect)

### Client Components

```tsx
// components/ui/Button.tsx
'use client';

export function Button({ children, onClick }) {
  return <button onClick={onClick}>{children}</button>;
}
```

### Form Pattern

```tsx
// components/forms/UserForm.tsx
'use client';

import { useState } from 'react';

export function UserForm({ onSuccess }) {
  const [email, setEmail] = useState('');
  
  async function handleSubmit(e) {
    e.preventDefault();
    await fetch('/api/users', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
    onSuccess();
  }
  
  return (
    <form onSubmit={handleSubmit}>
      <input value={email} onChange={(e) => setEmail(e.target.value)} />
      <Button type="submit">Create</Button>
    </form>
  );
}
```

---

## API Routes (REST)

```typescript
// app/api/users/route.ts
import db from '@/lib/db';
import { NextResponse } from 'next/server';

export async function GET() {
  const users = db.prepare('SELECT * FROM users').all();
  return NextResponse.json(users);
}

export async function POST(request: Request) {
  const { email, name } = await request.json();
  
  const stmt = db.prepare('INSERT INTO users (email, name) VALUES (?, ?)');
  const { lastInsertRowid } = stmt.run(email, name);
  
  return NextResponse.json({ id: lastInsertRowid }, { status: 201 });
}
```

**Rule:** Use REST, not tRPC. Keep it simple.

---

## Dev Commands

```bash
# Development
npm run dev              # Start dev server

# Database
npm run db:migrate       # Run migrations
npm run db:seed          # Seed test data
npm run db:reset         # Reset database

# Testing
npm run test             # Run tests
npm run test:watch       # Watch mode

# Build
npm run build            # Production build
npm run start            # Start production server
```

---

## What We DON'T Do (and Why)

| Don't | Why |
|-------|-----|
| Use Prisma | Overkill for SQLite, adds query overhead |
| Use tRPC | REST is simpler, no client library needed |
| Use Zod in routes | TypeScript already validates types |
| Use DATETIME columns | INTEGER timestamps are faster, portable |
| Use client components by default | Server Components are faster, less JS |
| Create API routes for everything | Use Server Components for data fetching |
| Use CSS-in-JS | Tailwind is enough, no runtime overhead |

---

## Anti-Patterns to Avoid

### ❌ Fetching data in client components

```tsx
// Bad
'use client';
useEffect(() => {
  fetch('/api/users').then(...);
}, []);
```

**Fix:** Use Server Components.

### ❌ No prepared statements

```typescript
// Bad
db.exec(`SELECT * FROM users WHERE id = ${userId}`);
```

**Fix:** Use prepared statements.

```typescript
// Good
db.prepare('SELECT * FROM users WHERE id = ?').get(userId);
```

### ❌ Mixing route groups incorrectly

```tsx
// Bad: Auth pages in dashboard group
app/(dashboard)/login/page.tsx
```

**Fix:** Use separate route groups.

---

## Testing Pattern

```typescript
// tests/user.test.ts
import { describe, it, expect } from 'vitest';
import db from '@/lib/db';

describe('User operations', () => {
  it('creates a user', () => {
    const stmt = db.prepare('INSERT INTO users (email, name) VALUES (?, ?)');
    const result = stmt.run('test@example.com', 'Test');
    expect(result.lastInsertRowid).toBeGreaterThan(0);
  });
});
```

---

## Quick Start

```bash
npx create-next-app@latest --typescript --tailwind --app
npm install better-sqlite3 nextauth
mkdir -p src/lib src/migrations src/components/ui src/components/forms
cp CLAUDE.md src/CLAUDE.md
```

---

*This template is opinionated. If you disagree with a rule, change it — but document why.*