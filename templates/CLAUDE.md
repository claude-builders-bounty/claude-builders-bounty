# CLAUDE.md - Next.js 15 + SQLite SaaS Project Guide

> Production-ready context file for Claude Code. Every rule has a reason.

---

## 📦 Stack & Versions

| Layer | Tech | Version | Why |
|-------|------|---------|-----|
| Framework | Next.js | 15.x | App Router, React Server Components |
| Runtime | Node.js | 20.x | LTS, native SQLite bindings |
| Database | SQLite | better-sqlite3 or Turso | Local dev, edge deployment |
| Auth | NextAuth.js | 5.x | Session-based, OAuth-ready |
| Styling | Tailwind CSS | 4.x | Utility-first, rapid iteration |
| Validation | Zod | 3.x | Runtime type safety |

**Do NOT use:** Prisma, Sequelize, or any ORM. Raw SQL + prepared statements is faster and more transparent.

---

## 📁 Folder Structure

```
app/
├── (auth)/           # Auth route group (login, register, callback)
│   ├── login/
│   ├── register/
│   └── callback/
├── (dashboard)/      # Protected routes group
│   ├── dashboard/
│   ├── settings/
│   └── api/
│       └── routes/   # API routes (tRPC or REST)
├── api/              # Public API endpoints
│   ├── health/
│   └── webhook/
├── layout.tsx        # Root layout (providers, fonts)
├── page.tsx          # Landing page
└── globals.css       # Tailwind imports

components/
├── ui/               # Base components (Button, Input, Card)
├── forms/            # Form components with Zod validation
├── dashboard/        # Dashboard-specific components
└── providers/        # Context providers (Theme, Session)

lib/
├── db/               # Database layer
│   ├── index.ts      # SQLite connection
│   ├── migrations/   # Migration files
│   ├── queries/      # Typed query functions
│   └── schema.sql    # Initial schema
├── auth/             # Auth utilities
│   ├── config.ts     # NextAuth configuration
│   ├── session.ts    # Session helpers
├── utils/            # Utility functions
└── constants/        # App constants

types/
├── index.ts          # Shared types
├── api.ts            # API request/response types
└── db.ts             # Database row types

public/
├── fonts/            # Local fonts (optional)
└── images/           # Static assets
```

**Naming convention:** All files use lowercase with hyphens (`user-profile.tsx`). Components exported use PascalCase (`UserProfile`).

---

## 🗄️ SQL / Migration Conventions

### Schema Rules

1. **Always use prepared statements** - Never interpolate SQL strings
2. **Integer primary keys** - `id INTEGER PRIMARY KEY AUTOINCREMENT`
3. **Timestamps as ISO strings** - `created_at TEXT DEFAULT (datetime('now'))`
4. **Foreign keys enabled** - `PRAGMA foreign_keys = ON`
5. **No ORMs** - Raw SQL gives full control and visibility

### Migration Pattern

```sql
-- migrations/001_users.sql
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

-- migrations/002_sessions.sql
CREATE TABLE IF NOT EXISTS sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  token TEXT UNIQUE NOT NULL,
  expires_at TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### Query Pattern

```typescript
// lib/db/queries/users.ts
import { db } from '../index';
import type { User } from '../../types/db';

export function getUserById(id: number): User | null {
  const stmt = db.prepare('SELECT * FROM users WHERE id = ?');
  return stmt.get(id) as User | null;
}

export function createUser(email: string, name?: string): User {
  const stmt = db.prepare(
    'INSERT INTO users (email, name) VALUES (?, ?) RETURNING *'
  );
  return stmt.get(email, name ?? null) as User;
}
```

**Migration order:** Sequential numbered files (`001_*.sql`, `002_*.sql`). Run on app startup.

---

## 🎨 Component Patterns

### Server Components (Default)

```typescript
// app/(dashboard)/dashboard/page.tsx
import { getUser } from '@/lib/auth/session';
import { Dashboard } from '@/components/dashboard';

export default async function DashboardPage() {
  const user = await getUser(); // Server-side auth check
  return <Dashboard user={user} />;
}
```

### Client Components (Interactive)

```typescript
// components/ui/button.tsx
'use client';

import { cn } from '@/lib/utils';
import { ButtonHTMLAttributes, forwardRef } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'rounded-lg px-4 py-2 font-medium transition-colors',
          variant === 'primary' && 'bg-blue-600 text-white hover:bg-blue-700',
          variant === 'secondary' && 'bg-gray-200 text-gray-900 hover:bg-gray-300',
          variant === 'ghost' && 'hover:bg-gray-100',
          className
        )}
        {...props}
      />
    );
  }
);
```

### Form Pattern (Zod + React Hook Form)

```typescript
// components/forms/register-form.tsx
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

const registerSchema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Password must be 8+ characters'),
  name: z.string().optional(),
});

type RegisterForm = z.infer<typeof registerSchema>;

export function RegisterForm() {
  const { register, handleSubmit, formState: { errors } } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterForm) => {
    // API call here
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Input {...register('email')} error={errors.email?.message} />
      <Input type="password" {...register('password')} error={errors.password?.message} />
      <Button type="submit">Register</Button>
    </form>
  );
}
```

---

## 🔧 Dev Commands

```bash
# Development
pnpm dev              # Start dev server (localhost:3000)
pnpm build            # Production build
pnpm start            # Start production server

# Database
pnpm db:migrate       # Run migrations
pnpm db:seed          # Seed test data
pnpm db:reset         # Reset database (dev only!)

# Testing
pnpm test             # Run unit tests
pnpm test:e2e         # Run E2E tests (Playwright)

# Code Quality
pnpm lint             # ESLint check
pnpm format           # Prettier format
pnpm typecheck        # TypeScript check
```

---

## 🚫 What We Don't Do (And Why)

| Avoid | Reason |
|-------|--------|
| **No Prisma/ORM** | Adds abstraction layer, slower queries, harder debugging |
| **No Redux** | Server Components + React Query handle state better |
| **No CSS-in-JS** | Tailwind + CSS variables are faster, no runtime cost |
| **No useEffect for data** | Use Server Components or React Query instead |
| **No inline styles** | Tailwind classes enforce consistency |
| **No next/router** | Use `next/navigation` (App Router API) |
| **No getServerSideProps** | App Router uses async Server Components |
| **No .env.local for secrets** | Use environment variables on host platform |
| **No client-side DB calls** | All DB operations through API routes or Server Components |

---

## 📐 Patterns to Follow

1. **Server-first** - Default to Server Components, add `'use client'` only when needed
2. **One query per route** - Fetch data in page component, pass to children
3. **Error boundaries** - Wrap route groups in error.tsx
4. **Loading states** - Add loading.tsx for async routes
5. **Parallel routes** - Use `@folder` syntax for independent loading
6. **Typed API** - Zod schemas for all API inputs/outputs

---

## 🛡️ Security Checklist

- [ ] Foreign keys enabled in SQLite
- [ ] Prepared statements for all queries
- [ ] CSRF protection on forms
- [ ] Rate limiting on auth endpoints
- [ ] Input validation with Zod
- [ ] Session token rotation
- [ ] HTTPS only (production)

---

## 📝 Quick Reference

```typescript
// Server-side auth check
import { getUser } from '@/lib/auth/session';
const user = await getUser();

// Database query
import { db } from '@/lib/db';
const stmt = db.prepare('SELECT * FROM users WHERE id = ?');
const user = stmt.get(id);

// Zod validation
const schema = z.object({ email: z.string().email() });
const parsed = schema.parse(data);

// Route handler
export async function POST(request: Request) {
  const body = await request.json();
  // ...
}
```

---

*This file is designed to give Claude Code full context without questions. Follow the rules exactly.*