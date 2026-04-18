# CLAUDE.md - Next.js 15 + SQLite SaaS Project

> **Purpose**: Production-ready configuration for AI-assisted development of SaaS applications using Next.js 15 App Router and SQLite.

## Stack & Versions

```json
{
  "next": "15.x",
  "react": "19.x",
  "typescript": "5.x",
  "better-sqlite3": "11.x",
  "drizzle-orm": "0.36.x",
  "tailwindcss": "4.x",
  "lucide-react": "latest",
  "next-auth": "5.0.0-beta.x"
}
```

## Folder Structure

```
project/
├── app/                      # Next.js 15 App Router
│   ├── (auth)/              # Auth routes (login, signup)
│   ├── (dashboard)/         # Protected dashboard routes
│   ├── api/                 # API routes
│   ├── layout.tsx           # Root layout
│   └── page.tsx             # Home page
├── db/
│   ├── schema.ts            # Database schema (Drizzle)
│   ├── index.ts             # Database connection
│   └── migrate.ts           # Migration scripts
├── components/
│   ├── ui/                  # Reusable UI components
│   ├── forms/               # Form components
│   └── dashboard/           # Dashboard-specific components
├── lib/
│   ├── auth.ts              # Auth configuration
│   ├── utils.ts             # Utility functions
│   └── validations.ts       # Zod schemas
├── hooks/                   # Custom React hooks
├── types/                   # TypeScript type definitions
├── drizzle.ts               # Drizzle config
├── tailwind.config.ts       # Tailwind config
└── next.config.ts           # Next.js config
```

## Database Conventions (SQLite + Drizzle)

### Schema Design Rules
```typescript
// ✅ DO: Use snake_case for database columns
export const users = sqliteTable('users', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  email: text('email').notNull().unique(),
  password_hash: text('password_hash').notNull(),
  created_at: integer('created_at', { mode: 'timestamp' }).$defaultFn(() => new Date()),
  updated_at: integer('updated_at', { mode: 'timestamp' }).$onUpdate(() => new Date()),
});

// ❌ DON'T: Use camelCase for database columns
export const users = sqliteTable('users', {
  userId: text('userId').primaryKey(), // BAD
  createdAt: integer('createdAt'),     // BAD
});
```

### Migration Rules Checklist
- [ ] Every schema change requires a migration
- [ ] Migrations are additive-only (no destructive operations in production)
- [ ] Always test migrations on a copy of production data
- [ ] Include rollback instructions for each migration
- [ ] Use `drizzle-kit generate` to create migrations

### Query Patterns
```typescript
// ✅ DO: Use parameterized queries
const user = await db.select().from(users).where(eq(users.id, userId)).get();

// ✅ DO: Use transactions for multi-step operations
await db.transaction(async (tx) => {
  await tx.insert(users).values({ email: 'test@example.com' });
  await tx.insert(profiles).values({ user_id: '123' });
});

// ❌ DON'T: Use string interpolation (SQL injection risk)
const user = await db.execute(sql.raw(`SELECT * FROM users WHERE id = ${userId}`));
```

## Component Patterns

### Server Components (Default)
```typescript
// ✅ DO: Use Server Components by default
async function UserProfile({ userId }: { userId: string }) {
  const user = await db.query.users.findFirst({ where: eq(users.id, userId) });
  return <div>{user?.email}</div>;
}
```

### Client Components (When Needed)
```typescript
// ✅ DO: Mark as client component when using hooks
'use client';

import { useState } from 'react';

export function InteractiveForm() {
  const [value, setValue] = useState('');
  return <input value={value} onChange={(e) => setValue(e.target.value)} />;
}
```

### Component Naming
- Use PascalCase for component names: `UserProfile.tsx`
- Use lowercase with dashes for folders: `user-profile/`
- One component per file (with rare exceptions)

## Development Commands

```bash
# Development
npm run dev          # Start dev server
npm run build        # Production build
npm run start        # Start production server
npm run lint         # ESLint check

# Database
npm run db:generate  # Generate Drizzle migration
npm run db:migrate   # Run migrations
npm run db:studio    # Open Drizzle Studio
npm run db:push      # Push schema to DB (dev only)

# Testing
npm run test         # Run tests
npm run test:watch   # Watch mode
```

## Anti-Patterns (What We Don't Do)

### ❌ Don't Use `useEffect` for Data Fetching
```typescript
// BAD: Unnecessary client-side fetching
export function UserProfile({ userId }: { userId: string }) {
  const [user, setUser] = useState(null);
  useEffect(() => {
    fetch(`/api/users/${userId}`).then(setUser);
  }, []);
  return <div>{user?.email}</div>;
}

// GOOD: Server-side fetching
export async function UserProfile({ userId }: { userId: string }) {
  const user = await db.query.users.findFirst({ where: eq(users.id, userId) });
  return <div>{user?.email}</div>;
}
```

### ❌ Don't Use Global State for Server Data
- Use React Query/TanStack Query if client caching is needed
- Prefer URL state over global state
- Don't use Redux/Zustand for server data

### ❌ Don't Ignore TypeScript Errors
- `@ts-ignore` is forbidden
- `as any` should be avoided
- Fix the root cause instead

### ❌ Don't Use `any` Type
```typescript
// BAD
function process(data: any) { return data; }

// GOOD
function process(data: unknown) {
  if (typeof data === 'string') { /* ... */ }
}

// BETTER
interface Data { id: string; name: string }
function process(data: Data) { return data; }
```

## Security Rules

1. **Always validate input with Zod**
```typescript
import { z } from 'zod';

const userSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});
```

2. **Never trust client-side data**
- Validate on server
- Sanitize HTML output
- Use CSP headers

3. **Environment variables**
- Prefix with `NEXT_PUBLIC_` only if needed in browser
- Store secrets in `.env.local` (gitignored)
- Use `.env.example` as template

## Testing Guidelines

### Unit Tests
```typescript
import { describe, it, expect } from 'vitest';

describe('UserService', () => {
  it('should create user with valid email', async () => {
    const user = await createUser('test@example.com');
    expect(user.email).toBe('test@example.com');
  });
});
```

### Integration Tests
- Use test database (separate from dev/prod)
- Clean up after each test
- Test critical user flows

## Deployment Checklist

- [ ] Environment variables documented in `.env.example`
- [ ] Database migrations tested on staging
- [ ] All tests passing
- [ ] Lighthouse score > 90
- [ ] No TypeScript errors
- [ ] No console warnings
- [ ] Sentry/error tracking configured

## Why These Rules?

| Rule | Reason |
|------|--------|
| Server Components by default | Better performance, SEO, smaller bundle |
| Snake case in DB | SQLite convention, avoids quoting issues |
| Drizzle ORM | Type-safe, lightweight, SQLite-optimized |
| No global state | Reduces complexity, server state is source of truth |
| Zod validation | Catches errors early, auto-generates types |

---

**Last Updated**: 2026-04-18  
**Maintained By**: Bounty Hunter Agent  
**License**: MIT
