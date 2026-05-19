# CLAUDE.md — Next.js 15 + SQLite SaaS Blueprint

**Stack**: Next.js 15 (App Router) + TypeScript + better-sqlite3 (local) / Turso (cloud) + Tailwind CSS  
**Philosophy**: Opinionated, minimal, production-ready. Questions answered before you ask.

---

## 📁 Project Structure (Non-Negotiable)

```
my-saas/
├── app/                    # App Router (NOT pages/)
│   ├── (auth)/            # Auth group (login, register)
│   ├── (dashboard)/       # Protected dashboard group
│   ├── api/               # API routes (webhooks, background jobs)
│   ├── globals.css        # Tailwind imports only
│   ├── layout.tsx         # Root layout (html, body, providers)
│   └── page.tsx           # Landing page
├── components/
│   ├── ui/                # Base UI (Button, Input, Card) — headless + Tailwind
│   ├── forms/             # Form components (LoginForm, SignupForm)
│   └── layout/            # Layout components (Navbar, Sidebar, Footer)
├── db/
│   ├── index.ts           # Database singleton export
│   ├── schema.sql         # Source of truth for schema
│   ├── migrations/        # Migration files (001_init.sql, 002_add_users.sql)
│   └── seed.ts            # Seed data for development
├── lib/
│   ├── auth.ts            # Auth logic (session, cookies, middleware)
│   ├── validation.ts      # Zod schemas for validation
│   └── utils.ts           # Pure utility functions (cn(), formatters)
├── actions/               # Server Actions (NOT API routes for mutations)
│   ├── auth-actions.ts    # login, register, logout
│   └── user-actions.ts    # updateUser, deleteUser
├── middleware.ts          # Auth guard (redirect if unauthenticated)
├── Drizzle Kit / Kysely   # Optional: ORM layer (Drizzle recommended)
└── package.json
```

**Why this structure**:  
- `(auth)` and `(dashboard)` are route groups (no URL segment, shared layout)  
- `actions/` separates server actions from components (testable, reusable)  
- `db/` isolates all database concerns (schema, migrations, queries)  
- `lib/` holds pure utilities (no React dependencies)

---

## 🗣️ Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Components | PascalCase | `UserTable`, `LoginForm` |
| Files | kebab-case | `user-table.tsx`, `login-form.tsx` |
| Server Actions | verb-noun | `createUser`, `updateProfile` |
| API Routes | noun-plural | `/api/users`, `/api/payments` |
| Database tables | snake_case | `user_sessions`, `password_reset_tokens` |
| TypeScript types | PascalCase | `User`, `Session`, `PaymentIntent` |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_PAGE_SIZE`, `API_BASE_URL` |

**Why**: Consistency reduces cognitive load. `snake_case` for DB (SQL standard), PascalCase for TS (TS standard).

---

## 🗄️ Database & Migrations

### Rule: Schema is Source of Truth
- `db/schema.sql` is the ONLY source of truth
- Migrations are incremental SQL files (NO auto-generated migrations)
- Each migration file = one business change (e.g., `003_add_subscription_tiers.sql`)

### Migration Naming
`<sequence>_description.sql` → `001_init.sql`, `002_add_users_table.sql`

### SQLite Specifics
- **Local**: `better-sqlite3` (synchronous, fast, file-based)  
- **Cloud**: Turso (libSQL, sync-compatible)  
- **NEVER use `sqlite3` package** (no async support, deprecated)

### Example Query Pattern
```typescript
// db/queries/users.ts
import { db } from '../index';

export const findUserByEmail = (email: string) => {
  return db.query('SELECT * FROM users WHERE email = ?').get(email);
};

export const createUser = (data: InsertUser) => {
  const result = db.query(`
    INSERT INTO users (email, password_hash, created_at)
    VALUES (?, ?, datetime('now'))
  `).run(data.email, data.passwordHash);
  return { ...data, id: result.lastInsertRowid };
};
```

**Why**: Raw SQL > ORM for SQLite. You see what's executed, no abstraction leaks.

---

## 🔐 Auth Pattern (Session-based)

### Flow
1. Login → create session in DB (`user_sessions` table)  
2. Set cookie (`session_id`)  
3. Middleware checks session → injects user into request  
4. Logout → delete session from DB, clear cookie

### Why Session-based NOT JWT
- Instant invalidation (JWT requires wait or blacklist)  
- No secret management  
- SQLite handles it fine (1 query per request)

```typescript
// lib/auth.ts
export async function createSession(userId: number) {
  const sessionId = crypto.randomUUID();
  db.query(`
    INSERT INTO user_sessions (id, user_id, expires_at)
    VALUES (?, ?, datetime('now', '+7 days'))
  `).run(sessionId, userId);
  
  cookies().set('session_id', sessionId, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    maxAge: 7 * 24 * 60 * 60, // 7 days
  });
}
```

---

## ⚡ Server Actions (NOT API Routes for Mutations)

### Use Server Actions For:
- User-triggered mutations (login, create, update, delete)  
- Form submissions  
- Anything that needs validation + DB write  

### Use API Routes For:
- Webhooks (Stripe, GitHub)  
- Cron jobs / background tasks  
- Third-party integrations  

### Why: Server actions are co-located with forms, no API design overhead, built-in progressive enhancement.

```typescript
// actions/auth-actions.ts
'use server';

import { redirect } from 'next/navigation';
import { loginSchema } from '@/lib/validation';
import { authenticateUser } from '@/lib/auth';
import { createSession } from '@/lib/session';

export async function loginAction(formData: FormData) {
  const validated = loginSchema.safeParse({
    email: formData.get('email'),
    password: formData.get('password'),
  });
  
  if (!validated.success) {
    return { error: validated.error.errors[0].message };
  }
  
  const user = await authenticateUser(validated.data);
  if (!user) {
    return { error: 'Invalid credentials' };
  }
  
  await createSession(user.id);
  redirect('/dashboard');
}
```

---

## 🎯 Component Patterns

### UI Components (Headless + Tailwind)
```typescript
// components/ui/button.tsx
import { cva } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva('inline-flex items-center justify-center rounded-md font-medium', {
  variants: {
    variant: {
      primary: 'bg-blue-600 text-white hover:bg-blue-700',
      secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200',
      destructive: 'bg-red-600 text-white hover:bg-red-700',
    },
    size: {
      sm: 'h-8 px-3 text-sm',
      md: 'h-10 px-4 text-base',
      lg: 'h-12 px-6 text-lg',
    },
  },
  defaultVariants: {
    variant: 'primary',
    size: 'md',
  },
});

export function Button({ variant, size, className, ...props }: ButtonProps) {
  return <button className={cn(buttonVariants({ variant, size, className }))} {...props} />;
}
```

**Why**: `cva` for variants, `cn` for conditional classes, no runtime theme object.

---

## 🚫 Anti-Patterns (NEVER DO THIS)

### 1. `useEffect` for data fetching
```typescript
// ❌ BAD
useEffect(() => {
  fetch('/api/users').then(setUsers);
}, []);
```

```typescript
// ✅ GOOD
const users = await db.query('SELECT * FROM users').all();
return <UserTable users={users} />;
```

**Why**: Server Components fetch on server, zero client bundle, no loading states needed.

---

### 2. API Routes for Form Submissions
```typescript
// ❌ BAD: /api/login (POST handler)
// ✅ GOOD: Server Action
```

**Why**: API routes add latency, require client-side state management, no progressive enhancement.

---

### 3. JWT for Session Management
```typescript
// ❌ BAD: jwt.sign(), jwt.verify()
// ✅ GOOD: DB session with random ID
```

**Why**: JWTs can't be revoked without blacklist, SQLite handles session lookups fine.

---

### 4. Prisma for SQLite
```typescript
// ❌ BAD: Prisma (overhead, slow cold starts)
// ✅ GOOD: better-sqlite3 (raw SQL)
```

**Why**: Prisma adds 100MB+ bundle, slow startup, SQLite doesn't need an ORM.

---

## 🛠️ Dev Commands (package.json scripts)

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint . --ext .ts,.tsx",
    "db:migrate": "node scripts/migrate.js",
    "db:seed": "tsx db/seed.ts",
    "db:reset": "rm -f db.sqlite && npm run db:migrate && npm run db:seed"
  }
}
```

---

## 📦 Dependencies (Exact Versions)

```json
{
  "dependencies": {
    "next": "15.0.0",
    "react": "19.0.0",
    "better-sqlite3": "^11.0.0",
    "zod": "^3.23.0",
    "tailwindcss": "^3.4.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0"
  },
  "devDependencies": {
    "@types/better-sqlite3": "^7.6.0",
    "@types/node": "^22.0.0",
    "typescript": "^5.5.0",
    "eslint": "^9.0.0"
  }
}
```

**Why these versions**: Next 15 for stable App Router, React 19 for actions support, `better-sqlite3` for synchronous queries.

---

## 🧪 Testing Strategy

### Unit Tests (Vitest)
```typescript
// tests/unit/validation.test.ts
import { describe, it, expect } from 'vitest';
import { loginSchema } from '@/lib/validation';

describe('loginSchema', () => {
  it('validates correct input', () => {
    const result = loginSchema.safeParse({ email: 'test@example.com', password: 'password123' });
    expect(result.success).toBe(true);
  });
});
```

### Integration Tests (Playwright)
```typescript
// tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test('login flow', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name=email]', 'test@example.com');
  await page.fill('[name=password]', 'password123');
  await page.click('button[type=submit]');
  await expect(page).toHaveURL('/dashboard');
});
```

**Why**: Vitest for fast unit tests, Playwright for full E2E (mimics real user).

---

## 🔒 Security Checklist

- [ ] All inputs validated with Zod (schemas are type + validation)
- [ ] Prepared statements for SQL (NEVER string interpolate)
- [ ] `httpOnly` cookies for sessions
- [ ] CSP headers in `next.config.js`
- [ ] Rate limiting on auth actions (`express-rate-limit` or custom)
- [ ] SQL injection tested in E2E (try `' OR 1=1 --`)

---

## 📝 File Templates

### New Component
```typescript
// components/<name>/<ComponentName>.tsx
'use client';

import { useState } from 'react';

interface ComponentNameProps {
  // Props here
}

export function ComponentName({}: ComponentNameProps) {
  const [state, setState] = useState(null);
  
  return (
    <div>
      {/* JSX here */}
    </div>
  );
}
```

### New Server Action
```typescript
// actions/<domain>-actions.ts
'use server';

import { z } from 'zod';
import { db } from '@/db';

const schema = z.object({
  // fields
});

export async function actionName(input: FormData) {
  const validated = schema.safeParse(Object.fromEntries(input));
  if (!validated.success) return { error: validated.error.errors[0].message };
  
  // DB operation
  // Return success/error
}
```

### New Migration
```sql
-- db/migrations/004_description.sql
-- Purpose: What this migration adds
-- Impact: Tables/columns affected

CREATE TABLE IF NOT EXISTS table_name (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  column_name TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 💡 Decision Framework

### "Should I create an API route or server action?"
- User-triggered mutation? → **Server Action**
- Background job / webhook? → **API Route**

### "Session or JWT?"
- App-managed auth (you control server)? → **Session**
- Distributed auth (multiple services)? → JWT (but still prefer session)

### "ORM or raw SQL?"
- SQLite? → **Raw SQL** (Drizzle only if you need codegen)
- Postgres? → Drizzle > Kysely > raw

### "Client or Server Component?"
- Needs `useEffect`, `useState`? → **Client**
- Fetches data? → **Server**
- Interactive (button, input)? → **Client** (with Server Action for mutation)

---

## 🎯 Quick Reference

```typescript
// cn() utility (lib/utils.ts)
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Usage
<div className={cn('base-class', isActive && 'active')} />
```

```bash
# Run development server with hot reload
npm run dev

# Create production build
npm run build

# Reset DB (delete + migrate + seed)
npm run db:reset
```

---

## ✅ Validation Checklist (Before Committing Code)

- [ ] Schema updated in `db/schema.sql`
- [ ] Migration created if schema changed
- [ ] Input validated with Zod before DB operation
- [ ] Error messages don't leak internals
- [ ] Server components used for data fetching
- [ ] Client components marked `'use client'`
- [ ] Tests pass (unit + E2E)

---

**Last updated**: 2026-05-17  
**Maintainer**: Claude Code Contributors
