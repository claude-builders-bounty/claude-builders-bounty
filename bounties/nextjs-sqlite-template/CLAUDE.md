# Project: Next.js + SQLite SaaS

## Stack

- **Framework**: Next.js 15 (App Router)
- **Database**: SQLite via better-sqlite3 (or Turso for edge)
- **ORM**: Drizzle ORM
- **Auth**: NextAuth.js v5 with database sessions
- **Styling**: Tailwind CSS + shadcn/ui
- **Runtime**: Node.js 20+

## Folder Structure

```
├── app/
│   ├── (auth)/           # Auth routes (login, register, forgot-password)
│   ├── (dashboard)/      # Protected routes requiring auth
│   ├── api/              # API routes
│   │   └── [...]/route.ts
│   ├── layout.tsx        # Root layout with providers
│   └── page.tsx          # Landing page
├── components/
│   ├── ui/               # shadcn/ui primitives (do not modify)
│   └── [feature]/        # Feature-specific components
├── lib/
│   ├── db/
│   │   ├── index.ts      # Database connection
│   │   ├── schema.ts     # Drizzle schema definitions
│   │   └── migrations/   # SQL migration files
│   ├── auth.ts           # NextAuth configuration
│   └── utils.ts          # Shared utilities
├── actions/              # Server Actions
└── types/                # TypeScript type definitions
```

## Naming Conventions

| Item | Convention | Example |
|------|------------|---------|
| Files/folders | kebab-case | `user-settings.tsx` |
| React components | PascalCase | `UserSettings` |
| Functions/variables | camelCase | `getUserById` |
| Database tables | snake_case | `user_sessions` |
| Environment variables | SCREAMING_SNAKE | `DATABASE_URL` |
| Server Actions | verbNoun | `createUser`, `deletePost` |

## Database Rules

### Schema Definition

Define all tables in `lib/db/schema.ts` using Drizzle:

```typescript
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const users = sqliteTable('users', {
  id: text('id').primaryKey(),
  email: text('email').notNull().unique(),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull(),
});
```

### Migrations

1. Generate: `npx drizzle-kit generate`
2. Apply: `npx drizzle-kit push` (dev) or `npx drizzle-kit migrate` (prod)
3. Never modify generated migration files
4. Each migration should be atomic and reversible when possible

### Query Patterns

```typescript
// Use Drizzle query builder
const user = await db.query.users.findFirst({
  where: eq(users.id, userId),
  with: { posts: true }
});

// Transactions for multi-table operations
await db.transaction(async (tx) => {
  await tx.insert(users).values(userData);
  await tx.insert(profiles).values(profileData);
});
```

### Constraints

- Always add `createdAt` and `updatedAt` timestamps
- Use UUIDs (via `crypto.randomUUID()`) for primary keys
- Add indexes for columns used in WHERE clauses
- Foreign keys must reference existing tables

## Component Patterns

### Server Components (Default)

```typescript
// app/dashboard/page.tsx
import { db } from '@/lib/db';

export default async function DashboardPage() {
  const data = await db.query.posts.findMany();
  return <Dashboard data={data} />;
}
```

### Client Components (When Needed)

```typescript
'use client';

import { useState } from 'react';

export function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

Only add `'use client'` when you need:
- useState, useEffect, or other hooks
- Event handlers (onClick, onChange, etc.)
- Browser APIs

### Server Actions

```typescript
// actions/posts.ts
'use server';

import { db } from '@/lib/db';
import { revalidatePath } from 'next/cache';

export async function createPost(formData: FormData) {
  const title = formData.get('title') as string;
  
  await db.insert(posts).values({
    id: crypto.randomUUID(),
    title,
    createdAt: new Date(),
  });
  
  revalidatePath('/posts');
}
```

## API Routes

```typescript
// app/api/users/route.ts
import { NextResponse } from 'next/server';
import { db } from '@/lib/db';

export async function GET() {
  const users = await db.query.users.findMany();
  return NextResponse.json(users);
}

export async function POST(request: Request) {
  const body = await request.json();
  // Validate with zod before inserting
  await db.insert(users).values(body);
  return NextResponse.json({ success: true }, { status: 201 });
}
```

## Authentication

```typescript
// lib/auth.ts
import NextAuth from 'next-auth';
import { DrizzleAdapter } from '@auth/drizzle-adapter';
import { db } from '@/lib/db';

export const { handlers, auth, signIn, signOut } = NextAuth({
  adapter: DrizzleAdapter(db),
  providers: [/* ... */],
});
```

Protected routes:
```typescript
import { auth } from '@/lib/auth';
import { redirect } from 'next/navigation';

export default async function ProtectedPage() {
  const session = await auth();
  if (!session) redirect('/login');
  // ...
}
```

## Dev Commands

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start dev server (port 3000) |
| `npm run build` | Production build |
| `npm run db:generate` | Generate migrations |
| `npm run db:push` | Apply migrations (dev) |
| `npm run db:studio` | Open Drizzle Studio |

## What We Don't Do

| Anti-Pattern | Why | Do This Instead |
|--------------|-----|-----------------|
| Raw SQL strings | SQL injection risk, no type safety | Drizzle query builder |
| `any` type | Defeats TypeScript's purpose | Define proper types |
| Client-side data fetching for initial load | Slower, worse SEO | Server Components |
| Storing secrets in code | Security vulnerability | Environment variables |
| Giant components (>200 lines) | Hard to maintain | Extract smaller components |
| Direct database access in components | Couples UI to data layer | Use Server Actions or API routes |
| Modifying `components/ui/` | Breaks shadcn updates | Create wrappers in `components/` |
| Multiple database connections | Connection exhaustion | Single shared instance in `lib/db` |
| Inline styles | Inconsistent, hard to maintain | Tailwind classes |
| `useEffect` for data fetching | Race conditions, complexity | Server Components or SWR/React Query |

## Error Handling

```typescript
// Wrap database operations
try {
  await db.insert(users).values(data);
} catch (error) {
  if (error.code === 'SQLITE_CONSTRAINT_UNIQUE') {
    return { error: 'Email already exists' };
  }
  throw error;
}
```

## Environment Variables

Required in `.env.local`:
```
DATABASE_URL=./data/app.db
AUTH_SECRET=<generate with: openssl rand -base64 32>
```

Access only via `process.env` in server code. Never expose to client.
