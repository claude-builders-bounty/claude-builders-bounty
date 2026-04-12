# CLAUDE.md — Next.js 15 App Router + SQLite SaaS Project

## Stack & Versions

```
Next.js: 15.x (App Router)
React: 19.x
TypeScript: 5.x (strict mode)
SQLite: better-sqlite3 ^11.x or Turso ^3.x
ORM: Drizzle ORM ^0.36.x
Auth: Auth.js v5 (next-auth@beta)
Validation: Zod ^3.x
Styling: Tailwind CSS ^4.x
Deployment: Vercel / Node.js server
```

## Project Structure

```
/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── (auth)/            # Auth route group (login, register, etc.)
│   │   ├── (dashboard)/       # Protected dashboard routes
│   │   ├── api/               # API routes
│   │   │   ├── auth/          # Auth.js handlers
│   │   │   └── [...trpc]/     # tRPC routes
│   │   ├── layout.tsx         # Root layout
│   │   └── page.tsx           # Landing page
│   ├── components/
│   │   ├── ui/               # Primitive UI components (buttons, inputs)
│   │   ├── forms/            # Form components with react-hook-form
│   │   └── features/         # Feature-specific components
│   ├── lib/
│   │   ├── db/              # Database client, schema, migrations
│   │   │   ├── schema.ts    # Drizzle schema definitions
│   │   │   ├── index.ts     # DB client singleton
│   │   │   └── migrations/  # SQL migration files
│   │   ├── auth/            # Auth utilities
│   │   └── utils.ts         # Shared utilities
│   ├── hooks/               # Custom React hooks
│   └── types/               # Shared TypeScript types
├── drizzle.config.ts        # Drizzle configuration
├── tailwind.config.ts      # Tailwind configuration
└── package.json
```

**Why this structure?**
- Route groups `(auth)` and `(dashboard)` separate public and protected pages without affecting URLs
- `components/ui` contains only primitive components — no business logic
- `lib/db` is the single source of truth for database operations

## SQL / Migration Conventions

### Schema Definition (Drizzle)

```typescript
// Always use snake_case for DB columns
// Always use camelCase for TypeScript interfaces

export const users = sqliteTable('users', {
  id: text('id').primaryKey(),           // UUID, not auto-increment
  email: text('email').notNull().unique(),
  hashedPassword: text('hashed_password').notNull(),
  createdAt: integer('created_at', { mode: 'timestamp' })
    .notNull()
    .$defaultFn(() => new Date()),
  updatedAt: integer('updated_at', { mode: 'timestamp' })
    .notNull()
    .$defaultFn(() => new Date()),
});

// Add indexes for frequently queried columns
export const usersEmailIndex = index('users_email_idx').on(users.email);
```

### Migration Rules

1. **Never modify existing migrations** — always create new ones
2. **Use meaningful migration names**: `2024_01_15_001_add_users_table.sql`
3. **Test migrations locally before deployment**:
   ```bash
   npm run db:push    # Push schema to local DB
   npm run db:studio  # Open Drizzle Studio to verify
   ```
4. **Soft deletes over hard deletes** for user data:
   ```typescript
   deletedAt: integer('deleted_at', { mode: 'timestamp' }).default(null),
   ```
5. **Use Unix timestamps (integers)** — not ISO strings, for SQLite performance

### Query Patterns

```typescript
// ✅ DO: Use parameterized queries
const user = await db.select().from(users).where(eq(users.email, email));

// ❌ DON'T: String interpolation in queries
const user = await db.select().from(users).where(sql`email = ${email}`);
```

## Component Patterns

### Server vs Client Components

```typescript
// ✅ Server Component (default) — for data fetching, layouts
// src/app/dashboard/page.tsx
export default async function DashboardPage() {
  const user = await getCurrentUser(); // Direct DB call
  return <Dashboard user={user} />;
}

// ✅ Client Component — only when you need interactivity
// src/components/forms/CreatePostForm.tsx
'use client';
export function CreatePostForm() {
  // useState, useEffect, event handlers allowed here
}
```

**Rule**: Start with Server Components. Add `'use client'` only when necessary.

### Component Organization

```typescript
// ✅ DO: Colocate related files
// src/components/features/posts/
//   ├── PostList.tsx        # Component
//   ├── PostList.test.tsx   # Tests
//   ├── PostItem.tsx
//   └── index.ts            # Barrel export

// ❌ DON'T: Flat structure with hundreds of files
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Components | PascalCase | `UserProfile.tsx` |
| Utilities | camelCase | `formatDate.ts` |
| Hooks | camelCase, prefixed `use` | `useAuth.ts` |
| Types/Interfaces | PascalCase | `UserProfile.ts` |
| Database Schema | camelCase (TS), snake_case (SQL) | `createdAt` / `created_at` |

## What We Don't Do (And Why)

### ❌ No Direct Database Access from Client Components
```typescript
// BAD — exposes DB to client
'use client';
const db = require('@/lib/db');

// GOOD — API route as intermediary
// Client calls /api/posts
// API route queries DB
```

### ❌ No `any` Types
```typescript
// BAD
const data: any = fetchData();

// GOOD — use Zod for runtime validation
const data = z.object({ ... }).parse(fetchData());
```

### ❌ No Prop Drilling Beyond 2 Levels
```typescript
// BAD — hard to track, easy to break
<Parent><Child><Grandchild><DeepChild /></DeepChild></Grandchild></Child></Parent>

// GOOD — use Context or Zustand for global state
// Or split into smaller components
```

### ❌ No Business Logic in Components
```typescript
// BAD — component doing too much
function CheckoutPage() {
  const [cart, setCart] = useState([]);
  const [user, setUser] = useState(null);
  const [coupon, setCoupon] = useState('');
  const [shipping, setShipping] = useState({});
  // 500 lines later...
}

// GOOD — extract to custom hook
function CheckoutPage() {
  const { cart, user, applyCoupon, setShipping } = useCheckout();
  // Component is now 50 lines
}
```

### ❌ No Global CSS Classes for Styling
```typescript
// BAD — couples UI to styling
<div className="flex items-center p-4 bg-white rounded-lg shadow-md">

// GOOD — use design system components
<div className={cn("flex items-center", styles.card)}>
```

### ❌ No Synchronous setState in Event Handlers
```typescript
// BAD — race conditions
onClick={() => {
  setLoading(true);
  submit();
  setLoading(false); // Might run before submit() completes
}};

// GOOD — async/await
onClick={async () => {
  setLoading(true);
  await submit().finally(() => setLoading(false));
}};
```

## Development Commands

```bash
# Setup
npm install
cp .env.example .env.local  # Configure database URL

# Development
npm run dev          # Start dev server (http://localhost:3000)
npm run db:studio    # Open Drizzle Studio (GUI for DB)

# Database
npm run db:generate  # Generate migrations from schema changes
npm run db:migrate   # Run pending migrations
npm run db:push      # Push schema (dev only, skips migrations)
npm run db:studio    # GUI database explorer

# Type Safety
npm run typecheck    # Run TypeScript without emitting
npm run lint         # ESLint checks
npm run lint:fix     # Auto-fix linting issues

# Testing
npm run test         # Run all tests
npm run test:watch   # Watch mode for development
npm run test:e2e     # Playwright E2E tests
```

## Database Setup

### Environment Variables

```env
DATABASE_URL=file:./dev.db          # Local SQLite file
# OR for Turso
DATABASE_URL=libsql://your-db.turso.io
DATABASE_AUTH_TOKEN=your-token

NEXTAUTH_SECRET=your-secret          # Generate: openssl rand -base64 32
NEXTAUTH_URL=http://localhost:3000
```

### Initial Setup

```bash
# 1. Create the database
npm run db:push

# 2. Verify in Drizzle Studio
npm run db:studio

# 3. Seed initial data if needed
npm run db:seed  # If you have a seed script
```

## Testing Strategy

### Unit Tests (Vitest)
```typescript
// src/lib/__tests__/auth.test.ts
describe('hashPassword', () => {
  it('should hash password', async () => {
    const hash = await hashPassword('secret123');
    expect(hash).not.toBe('secret123');
    expect(await verifyPassword(hash, 'secret123')).toBe(true);
  });
});
```

### Integration Tests
```typescript
// src/app/api/__tests__/posts.test.ts
describe('POST /api/posts', () => {
  it('should create post with valid data', async () => {
    const res = await POST('/api/posts', {
      title: 'Test Post',
      body: 'Content',
    });
    expect(res.status).toBe(201);
  });
});
```

## Deployment Checklist

- [ ] `npm run typecheck` passes
- [ ] `npm run lint` passes
- [ ] All tests pass (`npm run test`)
- [ ] Database migrations are committed
- [ ] Environment variables are set in production
- [ ] `NEXTAUTH_SECRET` is a strong, unique value
- [ ] `DATABASE_URL` points to production database (Turso recommended for production)
