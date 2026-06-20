# CLAUDE.md — Next.js 15 + SQLite SaaS

This file provides context for Claude Code when working in this project.

## Stack & Versions

- **Framework**: Next.js 15 (App Router)
- **Runtime**: Node.js 20+
- **Database**: SQLite via better-sqlite3 (or Turso for edge)
- **Auth**: NextAuth.js v5 (Auth.js)
- **Styling**: Tailwind CSS v4
- **Language**: TypeScript 5.x (strict mode)

## Project Structure

```
├── app/                  # App Router pages and layouts
│   ├── (auth)/           # Auth route group (login, register)
│   ├── (dashboard)/      # Dashboard route group
│   ├── api/              # API routes
│   └── layout.tsx        # Root layout
├── components/           # Shared React components
│   ├── ui/               # Base UI components (button, input, etc.)
│   └── features/         # Feature-specific components
├── lib/                  # Utilities and shared logic
│   ├── db.ts             # Database connection singleton
│   ├── auth.ts           # Auth configuration
│   └── utils.ts          # General utilities
├── drizzle/              # Database migrations (if using Drizzle ORM)
│   └── migrations/
├── public/               # Static assets
├── types/                # Shared TypeScript types
├── drizzle.config.ts     # Drizzle ORM config
├── next.config.ts        # Next.js config
└── package.json
```

## Database Conventions

### Connection

```typescript
// lib/db.ts
import Database from 'better-sqlite3';
import path from 'path';

const globalForDb = globalThis as unknown as { db: Database.Database };

export const db = globalForDb.db || new Database(path.join(process.cwd(), 'data.db'));

if (process.env.NODE_ENV !== 'production') globalForDb.db = db;
```

### Migrations

- Use Drizzle Kit for migrations: `npx drizzle-kit generate`
- Migration files go in `drizzle/migrations/`
- Never edit migration files after they're generated
- Always test migrations up AND down before committing
- Run `npx drizzle-kit migrate` before starting dev

### Query Patterns

- Use parameterized queries — never interpolate user input into SQL
- Keep complex queries in dedicated query files under `lib/queries/`
- Use transactions for multi-step operations:

```typescript
import { db } from '@/lib/db';

const insertUser = db.transaction((data) => {
  const user = db.prepare('INSERT INTO users (email) VALUES (?)').run(data.email);
  db.prepare('INSERT INTO accounts (user_id) VALUES (?)').run(user.lastInsertRowid);
  return user;
});
```

### Schema Conventions

- Table names: `snake_case` plural (e.g., `users`, `blog_posts`)
- Column names: `snake_case` (e.g., `created_at`, `user_id`)
- Always include `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- Always include `created_at` and `updated_at` columns
- Use `TEXT` for dates (ISO 8601 strings), `INTEGER` for booleans (0/1)
- Foreign keys: `{table}_id` with explicit `REFERENCES` in schema

## Component Patterns

### Server Components (default)

```typescript
// components/features/user-card.tsx
import { db } from '@/lib/db';

export function UserCard({ userId }: { userId: number }) {
  const user = db.prepare('SELECT * FROM users WHERE id = ?').get(userId);
  return <div>{user.name}</div>;
}
```

### Client Components (only when needed)

```typescript
'use client';

import { useState } from 'react';

export function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

### Naming

- Components: `PascalCase` files (e.g., `user-card.tsx`)
- Utilities: `camelCase` files (e.g., `format-date.ts`)
- Types: `PascalCase` in `types/` directory
- API routes: `route.ts` inside `app/api/[segment]/`

## What We Don't Do (and Why)

| Anti-pattern | Why |
|-------------|-----|
| `useEffect` for data fetching | Server Components handle this natively |
| `any` type | Defeats TypeScript's purpose; use `unknown` and narrow |
| `console.log` in production code | Use proper error handling or structured logging |
| barrel exports (`index.ts`) | Hurts tree-shaking and makes imports ambiguous |
| Client-side state for server data | Use Server Components or SWR/React Query |
| Raw SQL strings | Always parameterize to prevent injection |
| `export default` for components | Named exports improve refactoring and searchability |
| Magic numbers/strings | Extract to constants with descriptive names |

## Dev Commands

```bash
npm run dev          # Start dev server
npm run build        # Production build
npm run lint         # ESLint check
npm run typecheck    # TypeScript check
npm run db:generate  # Generate migrations
npm run db:migrate   # Run migrations
npm run db:studio    # Open Drizzle Studio
npm test             # Run test suite
```

## File Naming

- Pages: `page.tsx`
- Layouts: `layout.tsx`
- Loading states: `loading.tsx`
- Error boundaries: `error.tsx`
- Not found: `not-found.tsx`
- API handlers: `route.ts`
- Middleware: `middleware.ts` (root only)

## Environment Variables

- Never commit `.env` files
- Use `NEXT_PUBLIC_` prefix for client-exposed vars
- Validate env vars at startup in `lib/env.ts`
- Required vars: `DATABASE_URL`, `AUTH_SECRET`, `NEXTAUTH_URL`
