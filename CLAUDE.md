# CLAUDE.md - Next.js 15 App Router + SQLite SaaS Project

## Stack & Versions

- **Runtime:** Node.js 20+ (use `node --version` to verify)
- **Framework:** Next.js 15 (App Router, NOT Pages Router)
- **Database:** SQLite via `better-sqlite3` (synchronous, for SSR) or `@libsql/client` for Turso
- **ORM:** Drizzle ORM (lightweight, type-safe, SQL-like)
- **Styling:** Tailwind CSS 4 (CSS-first configuration)
- **Deployment:** Vercel (Node.js adapter) or Railway/Render

```bash
# Required versions
node --version  # Must be >= 20.0.0
npm --version   # Should be >= 10.0.0
```

## Project Structure

```
/
├── app/                    # Next.js 15 App Router (NOT pages/)
│   ├── layout.tsx         # Root layout (auth providers, fonts)
│   ├── page.tsx           # Landing page
│   ├── (auth)/            # Auth route group (no layout)
│   │   ├── login/page.tsx
│   │   └── signup/page.tsx
│   ├── (dashboard)/        # Dashboard route group
│   │   ├── layout.tsx     # Dashboard layout (sidebar, header)
│   │   ├── page.tsx       # Dashboard home
│   │   └── [id]/page.tsx  # Dynamic routes
│   └── api/               # API routes (Route Handlers)
│       └── [...slug]/route.ts
├── components/
│   ├── ui/               # shadcn/ui components (DO NOT modify directly)
│   ├── forms/            # React Hook Form + Zod schemas
│   └── shared/           # Shared components (Button, Input, Card)
├── lib/
│   ├── db/              # Database client & schema
│   │   ├── index.ts     # DB connection (singleton pattern)
│   │   ├── schema.ts    # Drizzle schema definitions
│   │   └── migrations/   # Drizzle migration files
│   ├── auth/            # Auth utilities (NextAuth config, JWT helpers)
│   └── utils.ts         # Utility functions (cn(), formatDate(), etc.)
├── public/              # Static assets
├── .env.local           # Local env vars (NEVER commit)
├── drizzle.config.ts    # Drizzle ORM config
└── next.config.ts       # Next.js config
```

## SQL / Migration Conventions

### Writing Migrations

1. **ALWAYS use Drizzle migrations, never raw SQL in code**
2. Create migration: `npx drizzle-kit generate`
3. Apply migration: `npx drizzle-kit migrate`
4. Check migration status: `npx drizzle-kit status`

### Schema Rules

```typescript
// ✅ CORRECT: Use Drizzle schema definitions
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const users = sqliteTable('users', {
  id: text('id').primaryKey(),  // UUID, not auto-increment
  email: text('email').notNull().unique(),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull(),
});

// ❌ WRONG: Raw SQL in application code
// db.run('CREATE TABLE...')  // NEVER do this
```

### Query Rules

```typescript
// ✅ CORRECT: Use Drizzle query builder
const user = await db.select().from(users).where(eq(users.id, id));

// ✅ CORRECT: Use transactions for multi-table operations
await db.transaction(async (tx) => {
  await tx.insert(posts).values({ ... });
  await tx.update(users).set({ postCount: increment(postCount) }).where(eq(users.id, userId));
});

// ❌ WRONG: String interpolation for user input
// db.run(`SELECT * FROM users WHERE id = '${id}'`)  // SQL injection risk!
```

## Component Patterns

### File Naming

- Pages: `kebab-case/page.tsx` (e.g., `user-profile/page.tsx`)
- Components: `PascalCase.tsx` (e.g., `UserProfile.tsx`)
- Utilities: `camelCase.ts` (e.g., `formatCurrency.ts`)

### Server vs Client Components

```
┌─────────────────────────────────────────────────────────────┐
│ Server Components (default)                                 │
│ - Data fetching, API routes                                 │
│ - Direct database access                                    │
│ - No useState, useEffect                                    │
│ - No event handlers                                         │
└─────────────────────────────────────────────────────────────┘
                              ↓ add 'use client' to cross boundary
┌─────────────────────────────────────────────────────────────┐
│ Client Components                                            │
│ - Interactivity, event handlers                             │
│ - useState, useEffect, useRef                              │
│ - Browser APIs                                              │
│ - Third-party client libraries                              │
└─────────────────────────────────────────────────────────────┘
```

### Component Template

```tsx
// components/shared/UserCard.tsx
import { User } from '@/lib/db/schema';
import { formatDate } from '@/lib/utils';

interface Props {
  user: Pick<User, 'id' | 'email' | 'createdAt'>;
}

export function UserCard({ user }: Props) {
  return (
    <div className="rounded-lg border p-4">
      <p className="font-medium">{user.email}</p>
      <p className="text-sm text-muted-foreground">
        Joined {formatDate(user.createdAt)}
      </p>
    </div>
  );
}
```

## What We DON'T Do (And Why)

### ❌ NO: `any` types
```typescript
// WRONG
function handleData(data: any) { ... }

// RIGHT - Use Zod for runtime validation
import { z } from 'zod';
const schema = z.object({ name: z.string(), email: z.string().email() });
const data = schema.parse(rawData);
```

### ❌ NO: Class components
```tsx
// WRONG - Classes are verbose and harder to test
class UserCard extends Component { ... }

// RIGHT - Functional components with hooks
export function UserCard({ user }: Props) { ... }
```

### ❌ NO: Default exports from components
```tsx
// WRONG
export default function UserCard() { ... }

// RIGHT - Named exports (better for refactoring)
export function UserCard() { ... }
```

### ❌ NO: Inline styles
```tsx
// WRONG
<div style={{ padding: '1rem', color: 'red' }}>

// RIGHT - Tailwind classes
<div className="p-4 text-red-500">
```

### ❌ NO: Mutating state directly
```tsx
// WRONG
items.push(newItem);

// RIGHT - Functional state update
setItems(prev => [...prev, newItem]);
```

## Development Commands

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Type checking
npm run typecheck

# Linting
npm run lint

# Database migrations
npm run db:generate    # Generate migration from schema changes
npm run db:migrate     # Apply migrations
npm run db:studio      # Open Drizzle Studio (DB browser)

# Build for production
npm run build

# Run tests
npm run test
```

## Database Connection Pattern

```typescript
// lib/db/index.ts - SINGLETON PATTERN
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import * as schema from './schema';

const globalForDb = globalThis as unknown as { db: ReturnType<typeof drizzle> | undefined };

function getDb() {
  if (globalForDb.db) return globalForDb.db;
  
  const sqlite = new Database(process.env.DATABASE_URL!);
  globalForDb.db = drizzle(sqlite, { schema });
  return globalForDb.db;
}

export const db = getDb();
```

## Anti-Patterns to Avoid

1. **No `new Date()` in components** - Use `formatDate()` from utils
2. **No magic numbers** - Use constants: `const PAGE_SIZE = 20`
3. **No deeply nested ternaries** - Extract to variables or components
4. **No prop drilling > 2 levels** - Use Context or Zustand
5. **No big components** - Extract at ~100 lines or when doing multiple things

## Testing Conventions

```bash
# Run tests
npm run test          # Vitest (default)
npm run test:e2e     # Playwright E2E tests

# Test file location
user-profile.test.ts      # Unit tests
user-profile.e2e.ts      # E2E tests
```

## Environment Variables

```bash
# .env.local (NEVER commit this file)
DATABASE_URL=./data/app.db
NEXTAUTH_SECRET=your-secret-here
NEXTAUTH_URL=http://localhost:3000
```

## Claude Code Usage

When working in this project:

1. **Ask clarifying questions** if requirements are unclear
2. **Use the schema** - check `lib/db/schema.ts` before writing queries
3. **Run migrations** if schema changes: `npm run db:generate && npm run db:migrate`
4. **Check types** before committing: `npm run typecheck`
5. **Test your changes** - `npm run dev` and verify manually

## File Modification Rules

- **UI components** (`components/ui/`): Do NOT modify directly. Use shadcn CLI: `npx shadcn@latest add button`
- **Schema changes**: Must be done through Drizzle migrations
- **Environment**: Always use `.env.local`, never hardcode secrets
