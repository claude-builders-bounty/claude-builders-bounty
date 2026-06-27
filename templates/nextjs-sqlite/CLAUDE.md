# CLAUDE.md — Next.js + SQLite SaaS Project

> This file provides Claude Code with context about your project structure, conventions, and patterns. It ensures consistent, high-quality code generation.

## Stack & Versions

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript 5.x
- **Database**: SQLite via better-sqlite3 or Turso
- **ORM**: Drizzle ORM
- **Styling**: Tailwind CSS 4.x
- **State Management**: React 19 with Server Components
- **Authentication**: NextAuth.js v5
- **Testing**: Vitest + React Testing Library

## Project Structure

```
├── app/                    # Next.js App Router
│   ├── (auth)/             # Auth route group
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/        # Dashboard route group
│   │   ├── layout.tsx      # Dashboard layout with sidebar
│   │   └── page.tsx        # Main dashboard page
│   ├── api/                # API routes
│   │   ├── auth/           # NextAuth endpoints
│   │   └── trpc/           # tRPC API handler
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Landing page
├── components/
│   ├── ui/                 # Reusable UI components (shadcn/ui)
│   ├── forms/              # Form components with validation
│   └── layouts/            # Layout components
├── lib/
│   ├── db/                 # Database connection & schema
│   │   ├── index.ts        # Database connection singleton
│   │   ├── schema.ts       # Drizzle schema definitions
│   │   └── migrations/     # SQL migration files
│   ├── auth.ts             # NextAuth configuration
│   ├── trpc/               # tRPC router setup
│   │   ├── router.ts       # Main router
│   │   └── routers/        # Individual routers
│   └── utils.ts            # Utility functions
├── hooks/                  # Custom React hooks
├── types/                  # TypeScript type definitions
└── public/                 # Static assets
```

## Naming Conventions

### Files
- **Components**: PascalCase (`UserProfile.tsx`)
- **Hooks**: camelCase with `use` prefix (`useAuth.ts`)
- **Utilities**: camelCase (`formatDate.ts`)
- **Types**: PascalCase with `.types.ts` suffix (`User.types.ts`)
- **Database**: camelCase (`users.ts`, `posts.ts`)

### Variables & Functions
- **Components**: PascalCase (`UserProfile`)
- **Functions**: camelCase (`getUserById`)
- **Constants**: UPPER_SNAKE_CASE (`API_BASE_URL`)
- **Types/Interfaces**: PascalCase (`User`, `Post`)

### Database
- **Tables**: Plural, snake_case (`users`, `user_posts`)
- **Columns**: snake_case (`created_at`, `user_id`)
- **Indexes**: `idx_{table}_{column}` (`idx_users_email`)

## SQL / Migration Conventions

### Schema Definition (Drizzle)
```typescript
// lib/db/schema.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const users = sqliteTable('users', {
  id: text('id').primaryKey(),
  email: text('email').notNull().unique(),
  name: text('name'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull(),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull(),
});
```

### Migration Rules
1. **Always** create migrations for schema changes
2. **Never** modify production database directly
3. **Use** `drizzle-kit generate` to create migrations
4. **Test** migrations on a copy of production data
5. **Include** rollback instructions in migration comments

### Query Patterns
```typescript
// Good: Use Drizzle query builder
const users = await db.select().from(users).where(eq(users.email, email));

// Bad: Raw SQL (avoid unless necessary)
const users = await db.all(`SELECT * FROM users WHERE email = '${email}'`);
```

## Component Patterns

### Server Components (Default)
```typescript
// app/dashboard/page.tsx
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';

export default async function DashboardPage() {
  const allUsers = await db.select().from(users);
  
  return (
    <div>
      <h1>Dashboard</h1>
      {/* Render users */}
    </div>
  );
}
```

### Client Components (When Needed)
```typescript
// components/Counter.tsx
'use client';

import { useState } from 'react';

export function Counter() {
  const [count, setCount] = useState(0);
  
  return (
    <button onClick={() => setCount(count + 1)}>
      Count: {count}
    </button>
  );
}
```

### Form Handling
```typescript
// components/forms/UserForm.tsx
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { userSchema } from '@/lib/validations';

export function UserForm() {
  const form = useForm({
    resolver: zodResolver(userSchema),
  });
  
  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      {/* Form fields */}
    </form>
  );
}
```

## API Patterns

### tRPC Routes
```typescript
// lib/trpc/routers/user.ts
import { router, publicProcedure } from '../router';
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';

export const userRouter = router({
  getAll: publicProcedure.query(async () => {
    return db.select().from(users);
  }),
  
  getById: publicProcedure
    .input(z.object({ id: z.string() }))
    .query(async ({ input }) => {
      return db.select().from(users).where(eq(users.id, input.id));
    }),
});
```

### API Routes (App Router)
```typescript
// app/api/users/route.ts
import { NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';

export async function GET() {
  const allUsers = await db.select().from(users);
  return NextResponse.json(allUsers);
}
```

## Dev Commands

```bash
# Development
npm run dev              # Start dev server
npm run build            # Build for production
npm run start            # Start production server

# Database
npm run db:generate      # Generate migration files
npm run db:migrate       # Run migrations
npm run db:studio        # Open Drizzle Studio
npm run db:push          # Push schema changes

# Testing
npm run test             # Run tests
npm run test:watch       # Run tests in watch mode
npm run test:coverage    # Generate coverage report

# Linting
npm run lint             # Run ESLint
npm run typecheck        # Run TypeScript check
```

## Patterns to Follow

### 1. Always Use Server Components by Default
- Only add `'use client'` when you need interactivity, browser APIs, or React hooks
- Keep client components small and focused

### 2. Colocate Related Files
- Keep components, hooks, and utilities close to where they're used
- Use `index.ts` files for clean imports

### 3. Type Safety
- Always define TypeScript types for API responses
- Use Zod for runtime validation
- Prefer interfaces over types for object shapes

### 4. Error Handling
- Use React Error Boundaries for component errors
- Handle API errors gracefully with user-friendly messages
- Log errors to your monitoring service

### 5. Database Safety
- Always use parameterized queries (Drizzle handles this)
- Validate inputs before database operations
- Use transactions for multi-step operations

## Anti-Patterns to Avoid

### ❌ Don't: Use Client Components Unnecessary
```typescript
// Bad: Client component for static content
'use client';
export function StaticText() {
  return <p>This could be a server component</p>;
}
```

### ✅ Do: Use Server Components by Default
```typescript
// Good: Server component for static content
export function StaticText() {
  return <p>This is a server component</p>;
}
```

### ❌ Don't: Expose Database Details
```typescript
// Bad: Exposing internal schema
export const userRouter = router({
  getAll: publicProcedure.query(async () => {
    return db.select().from(users); // Exposes all columns
  }),
});
```

### ✅ Do: Use Selective Queries
```typescript
// Good: Select only needed fields
export const userRouter = router({
  getAll: publicProcedure.query(async () => {
    return db.select({
      id: users.id,
      name: users.name,
      email: users.email,
    }).from(users);
  }),
});
```

### ❌ Don't: Ignore TypeScript Errors
```typescript
// Bad: Using any type
function processData(data: any) {
  return data.value;
}
```

### ✅ Do: Use Proper Types
```typescript
// Good: Explicit types
interface ProcessDataInput {
  value: string;
}

function processData(data: ProcessDataInput) {
  return data.value;
}
```

### ❌ Don't: Skip Database Migrations
```typescript
// Bad: Direct database modification
await db.run(`ALTER TABLE users ADD COLUMN phone TEXT`);
```

### ✅ Do: Use Migration Files
```typescript
// Good: Proper migration
// 0001_add_phone_to_users.sql
// ALTER TABLE users ADD COLUMN phone TEXT;
```

### ❌ Don't: Hardcode Configuration
```typescript
// Bad: Hardcoded values
const API_URL = 'https://api.example.com';
const JWT_SECRET = 'my-secret-key';
```

### ✅ Do: Use Environment Variables
```typescript
// Good: Environment variables
const API_URL = process.env.NEXT_PUBLIC_API_URL;
const JWT_SECRET = process.env.JWT_SECRET;
```

## Performance Tips

1. **Use Server Components** for data fetching (no client-side waterfalls)
2. **Implement Proper Caching** with `revalidate` options
3. **Optimize Images** with Next.js `Image` component
4. **Lazy Load** heavy components with `dynamic()` imports
5. **Index Database Columns** used in WHERE clauses

## Security Checklist

- [ ] Validate all user inputs with Zod
- [ ] Use parameterized queries (Drizzle handles this)
- [ ] Implement CSRF protection
- [ ] Set appropriate CORS headers
- [ ] Use HTTPS in production
- [ ] Store secrets in environment variables
- [ ] Implement rate limiting
- [ ] Sanitize user-generated content

## Resources

- [Next.js 15 Documentation](https://nextjs.org/docs)
- [Drizzle ORM Documentation](https://orm.drizzle.team/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [TypeScript Documentation](https://www.typescriptlang.org/docs)