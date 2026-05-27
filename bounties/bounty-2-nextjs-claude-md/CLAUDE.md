# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> **Stack**: Next.js 15 (App Router) · SQLite via better-sqlite3 · TypeScript · Tailwind CSS 4 · Auth.js v5

This file tells Claude Code everything it needs to know to work effectively on this project. Every rule here exists because we learned the hard way.

---

## Stack & Versions

| Layer | Choice | Version | Why |
|---|---|---|---|
| Framework | Next.js (App Router) | 15.x | Server Components, streaming, partial prerendering |
| Language | TypeScript | 5.x (strict) | Catch errors at build time, not runtime |
| Database | better-sqlite3 | 11.x | Synchronous, zero-config, fast for single-server |
| ORM | Drizzle ORM | 0.x | Type-safe, SQL-first, generates migrations |
| Styling | Tailwind CSS | 4.x | Utility-first, no dead CSS |
| Auth | Auth.js (NextAuth v5) | 5.x-beta | Server-first, supports multiple providers |
| Validation | Zod | 3.x | Runtime + compile-time schemas |
| Testing | Vitest + Testing Library | latest | Fast, ESM-native |

**Do not add** Prisma, TypeORM, or any async DB driver. We chose synchronous SQLite for a reason: no connection pool, no async mental model, fewer bugs.

---

## Folder Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Auth route group (login, register)
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/       # Protected routes
│   │   ├── layout.tsx     # Dashboard shell (sidebar, user menu)
│   │   ├── settings/
│   │   └── [feature]/
│   ├── api/               # Route Handlers (REST, not tRPC)
│   │   └── [resource]/
│   ├── layout.tsx         # Root layout (fonts, providers)
│   └── page.tsx           # Landing page
├── components/
│   ├── ui/                # Primitive components (Button, Input, Dialog…)
│   ├── forms/             # Form components tied to Zod schemas
│   └── [feature]/         # Feature-scoped composite components
├── lib/
│   ├── db/
│   │   ├── index.ts       # Database singleton (see pattern below)
│   │   ├── schema.ts      # Drizzle table definitions
│   │   └── migrations/    # Generated SQL migration files
│   ├── auth.ts            # Auth.js config
│   ├── validations/       # Zod schemas (one per resource)
│   └── utils.ts           # Pure utility functions
├── hooks/                 # Custom React hooks
└── types/                 # Shared TypeScript types (prefer Zod infer)
```

### Rules

- **Route groups** `(auth)`, `(dashboard)` keep layouts separate without affecting URL.
- **Never** put business logic in `app/` components. Use Server Actions or API routes.
- **Never** import `lib/db` in client components. All DB access is server-only.

---

## Database Conventions

### Schema Definition

Define tables in `src/lib/db/schema.ts` using Drizzle:

```typescript
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const users = sqliteTable('users', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  email: text('email').notNull().unique(),
  name: text('name').notNull(),
  createdAt: integer('created_at', { mode: 'timestamp' })
    .notNull().$defaultFn(() => new Date()),
});
```

### Database Singleton

```typescript
// src/lib/db/index.ts
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import * as schema from './schema';

const sqlite = new Database('data/app.db');
// WAL mode for better concurrent read performance
sqlite.pragma('journal_mode = WAL');
sqlite.pragma('foreign_keys = ON');

export const db = drizzle(sqlite, { schema });
```

### Migration Rules

1. **Always** use Drizzle Kit to generate migrations: `drizzle-kit generate`
2. **Never** edit migration SQL files by hand after generation.
3. **Never** use `db.run()` for DDL. Use the migration system.
4. Schema changes = generate migration → commit both schema.ts AND the SQL file.
5. **Column naming**: `snake_case` in DB, `camelCase` in TypeScript. Drizzle handles the mapping.

### Query Patterns

```typescript
// ✅ Good — typed, composable
import { eq, and } from 'drizzle-orm';
const user = await db.select().from(users).where(eq(users.email, email));

// ❌ Bad — raw SQL, no type safety
db.run('SELECT * FROM users WHERE email = ?', [email]);
```

---

## Component Patterns

### Server Components (Default)

Every component is a Server Component unless it needs interactivity.

```typescript
// app/(dashboard)/page.tsx
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';

export default async function DashboardPage() {
  const allUsers = await db.select().from(users);
  return <UserList users={allUsers} />;
}
```

### Client Components (When Needed)

```typescript
'use client';
import { useState } from 'react';
import { Button } from '@/components/ui/button';

export function Counter() {
  const [count, setCount] = useState(0);
  return <Button onClick={() => setCount(c => c + 1)}>{count}</Button>;
}
```

### When to use `'use client'`

Only when the component:
- Uses `useState`, `useEffect`, `useReducer`, or browser APIs
- Handles form submission with `onSubmit`
- Uses Auth.js `signIn()` / `signOut()` (client-side redirects)

Everything else stays a Server Component.

### Server Actions

```typescript
// app/(dashboard)/settings/actions.ts
'use server';
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';
import { eq } from 'drizzle-orm';
import { revalidatePath } from 'next/cache';
import { updateNameSchema } from '@/lib/validations/user';

export async function updateName(formData: FormData) {
  const raw = { name: formData.get('name') as string };
  const parsed = updateNameSchema.parse(raw); // Zod validates

  await db.update(users)
    .set({ name: parsed.name })
    .where(eq(users.id, userId));

  revalidatePath('/settings');
}
```

---

## API Routes (When Server Actions Don't Fit)

Use Route Handlers for webhooks, file uploads, or third-party integrations.

```typescript
// app/api/stripe/webhook/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const body = await request.text();
  // Verify Stripe signature, process event
  return NextResponse.json({ received: true });
}
```

**Rules:**
- Always return typed responses using `NextResponse.json()`.
- Validate all inputs with Zod schemas from `lib/validations/`.
- Webhooks: `POST` only, verify signatures, return `200` fast.

---

## What We Don't Do (And Why)

| ❌ Don't | Why |
|---|---|
| Use Prisma | Drizzle is lighter, generates readable SQL, no engine binary |
| Use tRPC | REST Route Handlers + Server Actions are enough for a SaaS this size |
| Use `getServerSideProps` | That's Pages Router. We use App Router (`async` components) |
| Store files in SQLite | Use cloud storage (S3/R2) for uploads. SQLite is for structured data |
| Use `any` type | TypeScript strict mode is enabled for a reason |
| Inline styles | Use Tailwind utilities. If you need complex styles, use `@apply` in CSS |
| Create global state (Redux, Zustand) | Server Components + URL state + `useState` cover 95% of cases |
| Use environment variables without validation | Validate with Zod at startup in `lib/env.ts` |

---

## Development Commands

```bash
# Install
pnpm install

# Development server (with hot reload)
pnpm dev

# Type-check (run before every commit)
pnpm tsc --noEmit

# Lint
pnpm lint

# Run database migrations
pnpm db:migrate        # drizzle-kit migrate

# Generate new migration after schema change
pnpm db:generate       # drizzle-kit generate

# Open Drizzle Studio (visual DB browser)
pnpm db:studio         # drizzle-kit studio

# Run tests
pnpm test              # vitest run
pnpm test:watch        # vitest --watch

# Build for production
pnpm build
```

---

## Git Conventions

- **Branch naming**: `feat/[feature-name]`, `fix/[bug-name]`, `chore/[task-name]`
- **Commit messages**: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`)
- **Always** run `tsc --noEmit` and `pnpm lint` before pushing.
- **One concern per PR** — don't mix features and refactors.

---

## Anti-Patterns to Avoid

1. **Don't fetch data in layouts** — fetch in the page/component that needs it. Layouts are shared and refetching is wasteful.
2. **Don't use `useEffect` for data fetching** — use Server Components.
3. **Don't create a `/components/index.ts` barrel file** — import directly from the component file. Barrels break tree-shaking.
4. **Don't hardcode API URLs** — use `process.env.NEXT_PUBLIC_APP_URL` or relative paths.
5. **Don't put secrets in client components** — anything with `NEXT_PUBLIC_` is visible in the browser.
6. **Don't use `moment.js`** — use native `Intl.DateTimeFormat` or `date-fns`.
7. **Don't create abstractions too early** — duplicate code twice before extracting.

---

## Testing Patterns

```typescript
// Vitest example
import { describe, it, expect } from 'vitest';
import { createUser } from './actions';

describe('createUser', () => {
  it('creates a user with valid input', async () => {
    const user = await createUser({ email: 'test@example.com', name: 'Test' });
    expect(user.email).toBe('test@example.com');
  });

  it('rejects invalid email', async () => {
    await expect(createUser({ email: 'bad', name: 'Test' }))
      .rejects.toThrow();
  });
});
```

**Rules:**
- Test business logic, not framework behavior.
- Use `vitest` for unit/integration tests.
- Co-locate test files: `actions.ts` → `actions.test.ts`.
- One test file per module. No shared test utilities that couple tests together.

---

## Environment Setup

Required `.env.local`:

```env
# App
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Auth (Auth.js)
AUTH_SECRET=<generate with `npx auth secret`>
AUTH_URL=http://localhost:3000

# OAuth (optional)
AUTH_GITHUB_ID=
AUTH_GITHUB_SECRET=
AUTH_GOOGLE_ID=
AUTH_GOOGLE_SECRET=

# Database
DATABASE_PATH=data/app.db
```

Validate all env vars at startup:

```typescript
// lib/env.ts
import { z } from 'zod';

const envSchema = z.object({
  NEXT_PUBLIC_APP_URL: z.string().url(),
  AUTH_SECRET: z.string().min(32),
  DATABASE_PATH: z.string().min(1),
});

export const env = envSchema.parse(process.env);
```
