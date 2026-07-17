# CLAUDE.md — Next.js 15 + SQLite SaaS

This file helps Claude Code understand your project. Paste it at the root of any Next.js 15 App Router + SQLite SaaS.

---

## Stack & Versions

- **Next.js 15** (App Router, React 19, Server Components)
- **TypeScript 5.x** (strict mode)
- **SQLite** via `better-sqlite3` (local) or `Turso` (edge)
- **Drizzle ORM** for schema + migrations
- **Tailwind CSS 4.x** for styling
- **Biome** for linting + formatting (not ESLint)
- **Vitest** for unit tests, **Playwright** for E2E

---

## Folder Structure

```
├── app/                    # Next.js App Router pages
│   ├── (auth)/             # Auth route group (login, register)
│   ├── (dashboard)/        # Dashboard route group
│   ├── api/                # API routes (Route Handlers)
│   └── layout.tsx          # Root layout
├── components/             # Shared React components
│   ├── ui/                 # Primitives (Button, Input, Modal)
│   └── forms/              # Form components
├── lib/                    # Utilities and business logic
│   ├── db/                 # Database connection + schema
│   │   ├── schema.ts       # Drizzle schema definitions
│   │   ├── migrations/     # Auto-generated migrations
│   │   └── index.ts        # DB client export
│   ├── auth/               # Authentication logic
│   ├── email/              # Email sending utilities
│   └── utils/              # Generic helpers (date, format, etc.)
├── hooks/                  # Custom React hooks
├── types/                  # Shared TypeScript types
├── public/                 # Static assets
├── drizzle.config.ts       # Drizzle ORM configuration
├── next.config.ts          # Next.js configuration
├── tailwind.config.ts      # Tailwind configuration
├── tsconfig.json           # TypeScript configuration
├── biome.json              # Biome linter/formatter config
└── package.json
```

---

## SQL / Migration Conventions

### Schema Definition
```typescript
// lib/db/schema.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const users = sqliteTable('users', {
  id: text('id').primaryKey(),  // Always use text IDs (cuid2 or nanoid)
  email: text('email').notNull().unique(),
  name: text('name'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull(),
});
```

### Rules
- **Always use `text` for IDs** — never auto-increment integers
- **Use `cuid2` or `nanoid`** for generating IDs (import from `@paralleldrive/cuid2` or `nanoid`)
- **Timestamps as integers** — use `integer('created_at', { mode: 'timestamp' })`
- **Never use `datetime`** — SQLite doesn't have a datetime type
- **Foreign keys as `text`** — match the referenced table's ID type
- **Run migrations after schema changes**: `npx drizzle-kit generate`

### Migration Workflow
```bash
# After editing schema.ts
npx drizzle-kit generate    # Generate migration SQL
npx drizzle-kit migrate     # Apply to local DB
npx drizzle-kit studio      # Visual inspection (optional)
```

---

## Component Patterns

### Server Components (Default)
```typescript
// app/dashboard/page.tsx
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';

export default async function DashboardPage() {
  const allUsers = await db.select().from(users);
  return <UserList users={allUsers} />;
}
```

### Client Components (When Needed)
```typescript
// components/ui/button.tsx
'use client';

import { useState } from 'react';

export function Button({ children, onClick }: { children: React.ReactNode; onClick: () => void }) {
  const [loading, setLoading] = useState(false);
  
  return (
    <button 
      className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
      onClick={async () => {
        setLoading(true);
        await onClick();
        setLoading(false);
      }}
      disabled={loading}
    >
      {loading ? 'Loading...' : children}
    </button>
  );
}
```

### Rules
- **Default to Server Components** — only add `'use client'` when you need interactivity
- **Co-locate related components** — keep `Button` in `components/ui/button.tsx`
- **Use `@/` path alias** — never relative imports like `../../components`
- **Props as interfaces** — define `Props` type, not inline props

---

## Dev Commands

```bash
# Development
npm run dev              # Start dev server (http://localhost:3000)
npm run build            # Production build
npm run start            # Start production server

# Database
npx drizzle-kit generate # Generate migration from schema changes
npx drizzle-kit migrate  # Run pending migrations
npx drizzle-kit studio   # Open Drizzle Studio

# Testing
npm run test             # Run unit tests (Vitest)
npm run test:e2e         # Run E2E tests (Playwright)
npm run test:coverage    # Run with coverage

# Linting
npm run lint             # Run Biome linter
npm run format           # Run Biome formatter
npm run check            # Run both lint + format
```

---

## What We Don't Do (And Why)

### No ESLint
We use **Biome** instead. It's faster, has better TypeScript support, and handles both linting and formatting in one tool.

### No Prisma
We use **Drizzle ORM**. It's lighter, generates better TypeScript, and gives us full SQL control. Prisma's query engine adds overhead we don't need.

### No REST APIs (Usually)
We prefer **Server Actions** for mutations. Use Route Handlers (`app/api/`) only for webhooks or external integrations.

### No `any` Types
TypeScript strict mode is enabled. If you're tempted to use `any`, define a proper type or use `unknown` with type guards.

### No Global State
Use Server Components and server-side data fetching. Client state should be local (`useState`) or URL-based (`searchParams`).

---

## Common Pitfalls

1. **Forgetting `'use client'`** — Components with hooks, event handlers, or browser APIs need this directive
2. **Using `datetime` in SQLite** — Use `integer` with `mode: 'timestamp'` instead
3. **Not running migrations** — Always run `npx drizzle-kit generate` after schema changes
4. **Relative imports** — Use `@/lib/...` not `../../lib/...`
5. **Mutating props** — Never mutate props directly; create copies
6. **Missing loading states** — Always show loading indicators for async operations
7. **Ignoring TypeScript errors** — Fix them, don't suppress with `@ts-ignore`

---

## Where to Start

### For New Features
1. **Database first** — Define schema in `lib/db/schema.ts`
2. **Generate migration** — `npx drizzle-kit generate`
3. **Create server action** — In `lib/actions/` or inline in Server Component
4. **Build UI** — Components in `components/`, pages in `app/`

### For Bug Fixes
1. **Find the page** — Look in `app/` for the route
2. **Trace the data** — Check Server Component or API route
3. **Check schema** — Verify DB structure in `lib/db/schema.ts`
4. **Test locally** — Run `npm run dev` and reproduce

### For Database Issues
1. **Check schema** — `lib/db/schema.ts`
2. **Check migrations** — `lib/db/migrations/`
3. **Use Drizzle Studio** — `npx drizzle-kit studio` to inspect data
4. **Check connection** — Verify `lib/db/index.ts` configuration

---

## Testing Strategy

### Unit Tests (Vitest)
```typescript
// __tests__/utils.test.ts
import { describe, it, expect } from 'vitest';
import { formatDate } from '@/lib/utils/date';

describe('formatDate', () => {
  it('formats ISO string to readable date', () => {
    expect(formatDate('2024-01-15')).toBe('January 15, 2024');
  });
});
```

### E2E Tests (Playwright)
```typescript
// e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test('user can login', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name=email]', 'test@example.com');
  await page.fill('[name=password]', 'password123');
  await page.click('button[type=submit]');
  await expect(page).toHaveURL('/dashboard');
});
```

---

## Environment Variables

```env
# Database
DATABASE_URL=file:./local.db          # Local SQLite
# DATABASE_URL=file:./local.db?cache=shared  # With connection pooling

# Auth
NEXTAUTH_SECRET=your-secret-here
NEXTAUTH_URL=http://localhost:3000

# Email (optional)
RESEND_API_KEY=re_...
EMAIL_FROM=noreply@yourdomain.com
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Add new table | Edit `schema.ts` → `npx drizzle-kit generate` |
| Add new page | Create `app/[route]/page.tsx` |
| Add new API | Create `app/api/[route]/route.ts` |
| Add new component | Create `components/[name].tsx` |
| Run tests | `npm run test` |
| Lint code | `npm run lint` |
| Format code | `npm run format` |

---

*Last updated: 2026-07-17*
