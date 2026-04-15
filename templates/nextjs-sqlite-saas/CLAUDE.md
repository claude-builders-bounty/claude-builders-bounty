# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated conventions for production-ready SaaS projects.

---

## Stack & Versions

| Layer | Tech | Version | Reason |
|-------|------|---------|--------|
| Framework | Next.js | 15.x | App Router, Server Components, streaming |
| Runtime | Node.js | 20.x | LTS, native fetch, performance |
| Database | SQLite | 3.x | better-sqlite3 (sync) or Turso (libsql) |
| ORM | Drizzle | 0.30+ | Type-safe, migrations, zero-runtime |
| Auth | Lucia | 3.x | Session-based, lightweight, no bloat |
| Styling | Tailwind | 3.4+ | Utility-first, design system ready |
| UI | shadcn/ui | Latest | Accessible, customizable primitives |
| Validation | Zod | 3.22+ | Runtime + compile-time safety |
| Testing | Vitest | 1.x + Playwright | Unit + E2E coverage |

---

## Folder Structure

```
my-saas/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Route groups for auth pages
│   │   ├── login/
│   │   ├── signup/
│   │   └── layout.tsx     # Auth layout (no nav)
│   ├── (dashboard)/       # Route group for app
│   │   ├── dashboard/
│   │   ├── settings/
│   │   └── layout.tsx     # Dashboard layout (with nav)
│   ├── api/               # API routes
│   │   └── [...]/route.ts # One route per file
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Landing page
├── components/            # React components
│   ├── ui/               # shadcn/ui components
│   ├── forms/            # Form-specific components
│   └── features/         # Feature-specific components
├── lib/                   # Utilities & config
│   ├── db/               # Database layer
│   │   ├── index.ts      # Connection + client
│   │   ├── schema.ts     # Drizzle schema
│   │   └── migrations/   # Generated migrations
│   ├── auth/             # Auth utilities
│   ├── validation/       # Zod schemas
│   └── utils.ts          # General utilities
├── hooks/                 # Custom React hooks
├── types/                 # Global TypeScript types
├── tests/                 # Test files
│   ├── unit/
│   └── e2e/
├── scripts/               # Build & utility scripts
└── CLAUDE.md             # This file
```

---

## Naming Conventions

### Files
- **Components**: PascalCase (`UserCard.tsx`)
- **Utilities**: camelCase (`formatDate.ts`)
- **API Routes**: lowercase with dashes (`user-profile/route.ts`)
- **Database**: snake_case in schema, camelCase in TypeScript

### Database Tables
- Plural, snake_case: `users`, `subscriptions`, `audit_logs`
- Junction tables: `user_workspaces` (alphabetical order)
- Timestamps: `created_at`, `updated_at` (always include)

### Components
- One component per file
- Default export for page components
- Named exports for reusable components
- Props interface: `{ComponentName}Props`

---

## SQL & Migration Conventions

### Schema Design
```typescript
// lib/db/schema.ts
import { sqliteTable, text, integer, real } from 'drizzle-orm/sqlite-core';

export const users = sqliteTable('users', {
  id: text('id').primaryKey(), // CUID, not auto-increment
  email: text('email').notNull().unique(),
  name: text('name').notNull(),
  role: text('role', { enum: ['user', 'admin'] }).default('user'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull(),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull(),
});
```

### Migration Rules
1. **Never modify existing migrations** — create new ones
2. **Always test migrations** on a copy of production data
3. **Include rollback plan** for destructive changes
4. **Timestamp naming**: `0000_initial`, `0001_add_stripe_customer_id`

### Query Patterns
```typescript
// Good: Typed, explicit, handles errors
const user = await db.query.users.findFirst({
  where: eq(users.id, userId),
});

if (!user) {
  throw new Error('User not found');
}

// Bad: Untyped, implicit error handling
const user = await db.select().from(users).where(eq(users.id, userId));
```

---

## Component Patterns

### Server Components (Default)
```tsx
// app/dashboard/page.tsx
import { getUser } from '@/lib/auth';
import { db } from '@/lib/db';

export default async function DashboardPage() {
  const user = await getUser();
  
  if (!user) {
    redirect('/login');
  }
  
  const projects = await db.query.projects.findMany({
    where: eq(projects.userId, user.id),
  });
  
  return <ProjectList projects={projects} />;
}
```

### Client Components (When Needed)
```tsx
// components/forms/create-project-form.tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export function CreateProjectForm() {
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  
  // Interactivity requires 'use client'
  // But keep minimal — move logic to Server Actions
}
```

### Server Actions
```typescript
// app/dashboard/actions.ts
'use server';

import { revalidatePath } from 'next/cache';
import { z } from 'zod';

const createProjectSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional(),
});

export async function createProject(formData: FormData) {
  const user = await getUser();
  if (!user) throw new Error('Unauthorized');
  
  const data = createProjectSchema.parse({
    name: formData.get('name'),
    description: formData.get('description'),
  });
  
  const project = await db.insert(projects).values({
    ...data,
    userId: user.id,
    createdAt: new Date(),
  }).returning();
  
  revalidatePath('/dashboard');
  return project[0];
}
```

---

## What We Do (And Why)

### ✅ Do
- **Use Server Components by default** — Less JS, better performance
- **Validate at boundaries** — Zod for forms, DB constraints for data
- **Explicit error handling** — No silent failures
- **Optimistic UI** — Show feedback immediately, rollback on error
- **Database transactions** — For multi-step operations
- **Soft deletes** — `deleted_at` timestamp, never `DELETE`
- **Audit logging** — Who changed what, when

### ❌ Don't (And Why)

| Don't | Why | Do Instead |
|-------|-----|------------|
| Use `any` type | Loses type safety | Define interfaces, use `unknown` |
| Direct DB calls in components | Hard to test, tight coupling | Use Server Actions or API routes |
| `console.log` in production | No persistence, hard to search | Structured logging (Pino/Winston) |
| Client-side auth checks | Bypassable | Server-side validation always |
| Magic numbers/strings | Hard to maintain | Constants/enums |
| Nested ternaries | Unreadable | Early returns, helper functions |
| `!important` in CSS | Hard to override | Specificity, component variants |

---

## Dev Commands

```bash
# Setup
npm install
npm run db:generate   # Generate migrations
npm run db:migrate    # Run migrations
npm run db:seed       # Seed dev data

# Development
npm run dev           # Start dev server
npm run test          # Run unit tests
npm run test:e2e      # Run E2E tests
npm run lint          # ESLint + Prettier

# Production
npm run build         # Build for production
npm run start         # Start production server
```

---

## Environment Variables

```bash
# .env.local (never commit)
DATABASE_URL="file:./dev.db"
# OR for Turso:
# DATABASE_URL="libsql://..."
# DATABASE_AUTH_TOKEN="..."

NEXTAUTH_SECRET="generate-with-openssl-rand-base64-32"
NEXTAUTH_URL="http://localhost:3000"

# OAuth providers
GITHUB_CLIENT_ID="..."
GITHUB_CLIENT_SECRET="..."

# Stripe (if using)
STRIPE_SECRET_KEY="sk_test_..."
STRIPE_WEBHOOK_SECRET="whsec_..."
```

---

## Testing Strategy

### Unit Tests (Vitest)
```typescript
// tests/unit/utils.test.ts
import { describe, it, expect } from 'vitest';
import { formatDate } from '@/lib/utils';

describe('formatDate', () => {
  it('formats ISO date to readable string', () => {
    const result = formatDate('2026-04-15');
    expect(result).toBe('April 15, 2026');
  });
});
```

### E2E Tests (Playwright)
```typescript
// tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test('user can sign up', async ({ page }) => {
  await page.goto('/signup');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'password123');
  await page.click('button[type="submit"]');
  
  await expect(page).toHaveURL('/dashboard');
});
```

---

## Deployment Checklist

- [ ] Environment variables set
- [ ] Database migrations run
- [ ] Build passes (`npm run build`)
- [ ] Tests pass (`npm run test`)
- [ ] Lighthouse score > 90
- [ ] Security headers configured
- [ ] Error tracking (Sentry) enabled
- [ ] Analytics (Plausible/PostHog) configured

---

## Resources

- [Next.js Docs](https://nextjs.org/docs)
- [Drizzle ORM](https://orm.drizzle.team)
- [Lucia Auth](https://lucia-auth.com)
- [shadcn/ui](https://ui.shadcn.com)

---

*Generated for claude-builders-bounty #2*