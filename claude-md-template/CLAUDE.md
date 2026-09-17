# CLAUDE.md - Next.js 15 + SQLite SaaS Template

> This file provides context for Claude Code to understand and work with this project.
> Copy this to your project root and customize as needed.

## Stack & Versions

- **Framework:** Next.js 15 (App Router)
- **Runtime:** Node.js 20+
- **Database:** SQLite via better-sqlite3
- **ORM:** Drizzle ORM
- **Auth:** NextAuth.js v5
- **Styling:** Tailwind CSS
- **Testing:** Vitest + Testing Library
- **Package Manager:** pnpm

## Project Structure

```
├── app/                    # Next.js App Router
│   ├── (auth)/             # Auth routes (login, register)
│   ├── (dashboard)/        # Protected dashboard routes
│   ├── api/                # API routes
│   └── layout.tsx          # Root layout
├── components/             # Shared React components
│   ├── ui/                 # Base UI components (Button, Input, etc.)
│   └── features/           # Feature-specific components
├── lib/                    # Utility functions and helpers
│   ├── db/                 # Database schema and queries
│   ├── auth.ts             # Auth configuration
│   └── utils.ts            # General utilities
├── public/                 # Static assets
├── drizzle/                # Database migrations
├── types/                  # TypeScript type definitions
└── tests/                  # Test files
```

## Naming Conventions

### Files & Folders
- **Components:** PascalCase (`UserProfile.tsx`)
- **Utilities:** camelCase (`formatDate.ts`)
- **Routes:** lowercase (`/dashboard/settings`)
- **Database:** snake_case for tables (`user_sessions`)

### Code
- **Components:** PascalCase function names (`UserProfile`)
- **Functions:** camelCase (`getUserById`)
- **Constants:** UPPER_SNAKE_CASE (`MAX_RETRY_COUNT`)
- **Types/Interfaces:** PascalCase with `I` prefix optional (`User` or `IUser`)

## SQL & Migration Conventions

### Schema Definition
```typescript
// lib/db/schema.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const users = sqliteTable('users', {
  id: text('id').primaryKey(),
  email: text('email').notNull().unique(),
  name: text('name'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull(),
});
```

### Migration Rules
1. **Always** create migrations for schema changes
2. **Never** modify existing migrations
3. **Use** `drizzle-kit generate` to create migrations
4. **Test** migrations roll back cleanly

### Query Patterns
```typescript
// Always use parameterized queries
const user = await db.select().from(users).where(eq(users.id, userId));

// Use transactions for multi-table operations
await db.transaction(async (tx) => {
  await tx.insert(orders).values(orderData);
  await tx.update(inventory).set({ stock: sql`${stock} - 1` });
});
```

## Component Patterns

### Server Components (Default)
```typescript
// app/dashboard/page.tsx
export default async function DashboardPage() {
  const session = await getServerSession();
  if (!session) redirect('/login');
  
  const data = await getData();
  
  return <Dashboard data={data} />;
}
```

### Client Components (When Needed)
```typescript
// components/features/user-profile.tsx
'use client';

import { useState } from 'react';

export function UserProfile({ user }: Props) {
  const [editing, setEditing] = useState(false);
  // Client-side interactivity
}
```

### API Routes
```typescript
// app/api/users/route.ts
import { NextResponse } from 'next/server';
import { z } from 'zod';

const UserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1),
});

export async function POST(req: Request) {
  const body = await req.json();
  const validated = UserSchema.parse(body);
  
  // Create user...
  
  return NextResponse.json({ user }, { status: 201 });
}
```

## Dev Commands

```bash
# Development
pnpm dev                    # Start dev server
pnpm build                  # Build for production
pnpm start                  # Start production server

# Database
pnpm drizzle:generate       # Generate migration
pnpm drizzle:migrate        # Run migrations
pnpm drizzle:studio         # Open Drizzle Studio

# Testing
pnpm test                   # Run tests
pnpm test:watch             # Watch mode
pnpm test:coverage          # With coverage

# Linting
pnpm lint                   # ESLint
pnpm typecheck              # TypeScript check
```

## Patterns to Follow

### 1. Always Validate Input
```typescript
// Good: Validate at API boundary
const data = RequestSchema.parse(await req.json());

// Bad: Trust client input
const data = await req.json();
```

### 2. Use Server Components by Default
```typescript
// Good: Server component
export default async function Page() {
  const data = await fetchData(); // Runs on server
  return <UI data={data} />;
}

// Bad: Unnecessary client component
'use client';
export function Page() {
  const [data, setData] = useState(null);
  useEffect(() => { fetchData().then(setData); }, []);
}
```

### 3. Colocate Related Code
```typescript
// Good: Feature folder structure
components/features/auth/
  ├── login-form.tsx
  ├── register-form.tsx
  └── auth-utils.ts

// Bad: Scattered files
components/login-form.tsx
components/register-form.tsx
lib/auth-utils.ts
```

### 4. Use TypeScript Strictly
```typescript
// Good: Explicit types
function getUser(id: string): Promise<User | null> {
  return db.select().from(users).where(eq(users.id, id)).get();
}

// Bad: Any types
function getUser(id: any): Promise<any> {
  return db.select().from(users).where(eq(users.id, id)).get();
}
```

## Anti-Patterns to Avoid

### ❌ Don't: Fetch Data in Client Components When Possible
```typescript
// Bad: Client-side data fetching
'use client';
export function UserList() {
  const [users, setUsers] = useState([]);
  useEffect(() => {
    fetch('/api/users').then(r => r.json()).then(setUsers);
  }, []);
}
```

### ❌ Don't: Skip Error Handling
```typescript
// Bad: No error handling
const user = await getUser(id);

// Good: Handle errors
const user = await getUser(id);
if (!user) {
  notFound();
}
```

### ❌ Don't: Use Environment Variables Directly
```typescript
// Bad: Direct access
const dbUrl = process.env.DATABASE_URL;

// Good: Validated config
import { env } from '@/lib/env';
const dbUrl = env.DATABASE_URL;
```

### ❌ Don't: Skip Database Migrations
```typescript
// Bad: Manual schema changes
db.exec('ALTER TABLE users ADD COLUMN avatar TEXT');

// Good: Use migrations
// drizzle/0001_add_avatar.sql
```

### ❌ Don't: Mix Server and Client Code
```typescript
// Bad: Server code in client component
'use client';
import { getServerSession } from 'next-auth'; // This won't work!

// Good: Pass as props
export default async function Page() {
  const session = await getServerSession();
  return <ClientComponent session={session} />;
}
```

## Database Best Practices

### 1. Always Use Transactions
```typescript
await db.transaction(async (tx) => {
  await tx.insert(orders).values(order);
  await tx.update(inventory).set({ 
    stock: sql`${stock} - ${quantity}` 
  });
});
```

### 2. Index Frequently Queried Columns
```typescript
export const orders = sqliteTable('orders', {
  id: text('id').primaryKey(),
  userId: text('user_id').notNull(),
  // ...
}, (table) => ({
  userIdIdx: index('user_id_idx').on(table.userId),
}));
```

### 3. Use Prepared Statements
```typescript
// Good: Prepared statement
const stmt = db.prepare('SELECT * FROM users WHERE id = ?');
const user = stmt.get(userId);

// Bad: String interpolation
const user = db.prepare(`SELECT * FROM users WHERE id = '${userId}'`).get();
```

## Security Checklist

- [ ] Validate all input at API boundaries
- [ ] Use parameterized queries (never string interpolation)
- [ ] Implement rate limiting on API routes
- [ ] Use CSRF protection for forms
- [ ] Sanitize user output (prevent XSS)
- [ ] Store secrets in environment variables
- [ ] Use HTTPS in production
- [ ] Implement proper authentication checks

## Performance Tips

1. **Use Server Components** - Reduce client-side JavaScript
2. **Implement Caching** - Use Next.js caching strategies
3. **Optimize Images** - Use Next.js Image component
4. **Lazy Load** - Use dynamic imports for heavy components
5. **Database Indexing** - Index columns used in WHERE clauses

## When Working with Claude

### Do
- Ask Claude to explain unfamiliar code
- Request refactoring suggestions
- Have Claude write tests for new features
- Use Claude to review security concerns

### Don't
- Ask Claude to execute destructive commands
- Let Claude modify database without migrations
- Allow Claude to skip error handling
- Accept untyped code from Claude

## Resources

- [Next.js 15 Docs](https://nextjs.org/docs)
- [Drizzle ORM Docs](https://orm.drizzle.team/)
- [Better SQLite3 Docs](https://github.com/WiseLibs/better-sqlite3/blob/master/docs/api.md)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)

---

*Last updated: 2026-09-16*
*Version: 1.0.0*
