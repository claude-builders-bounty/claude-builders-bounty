# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Stack & Versions

- **Framework:** Next.js 15 (App Router only, no Pages Router)
- **Language:** TypeScript 5.5+ (strict mode, no `any`)
- **Database:** SQLite via better-sqlite3 (sync) or Turso (async, edge-compatible)
- **ORM:** Drizzle ORM (no Prisma — too heavy for SQLite)
- **Styling:** Tailwind CSS 4 + shadcn/ui components
- **Auth:** Better Auth or Lucia (no NextAuth — overkill for SQLite)
- **Validation:** Zod (shared between client and server)
- **Testing:** Vitest + Playwright (no Jest)

## Folder Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Auth routes group (login, register)
│   ├── (dashboard)/       # Protected dashboard routes
│   ├── api/               # API routes (REST only, no tRPC)
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Landing page
├── components/
│   ├── ui/                # shadcn/ui primitives (button, input, etc.)
│   ├── forms/             # Form components with Zod validation
│   └── layouts/           # Dashboard layouts, sidebars
├── db/
│   ├── schema.ts          # Drizzle schema (tables, relations)
│   ├── migrations/        # SQL migration files (001_*.sql, 002_*.sql)
│   └── index.ts           # Database client export
├── lib/
│   ├── auth.ts            # Auth helpers (getSession, requireAuth)
│   ├── utils.ts           # Shared utilities
│   └── validators.ts      # Zod schemas (shared client/server)
├── services/              # Business logic (no React, pure TS)
└── types/                 # Global TypeScript types
```

## SQL & Migration Conventions

### Migration Rules

1. **Never edit existing migrations** — create new ones
2. **Naming:** `001_create_users.sql`, `002_add_posts_table.sql` (sequential, lowercase, underscores)
3. **Always include:** `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
4. **Soft deletes:** Use `deleted_at TIMESTAMP NULL` (never hard delete)
5. **Indexes:** Add indexes for all foreign keys and frequently queried columns
6. **Test migrations locally** before committing: `npm run db:migrate`

### Schema Design

```typescript
// ✅ GOOD: Explicit types, relations, indexes
export const users = sqliteTable('users', {
  id: text('id').primaryKey(), // UUID, not auto-increment
  email: text('email').notNull().unique(),
  name: text('name'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull(),
  deletedAt: integer('deleted_at', { mode: 'timestamp' }),
}, (table) => ({
  emailIdx: uniqueIndex('email_idx').on(table.email),
}));

// ❌ BAD: No indexes, no timestamps, auto-increment IDs
export const users = sqliteTable('users', {
  id: integer('id').primaryKey({ autoIncrement: true }), // No UUID
  email: text('email').notNull(), // No unique constraint
  // Missing createdAt, deletedAt
});
```

### Query Patterns

```typescript
// ✅ GOOD: Use Drizzle query builder, explicit selects
const user = await db.query.users.findFirst({
  where: eq(users.email, email),
  columns: { id: true, name: true, email: true }, // Explicit columns
});

// ❌ BAD: Raw SQL, select all columns
const user = await db.execute(sql`SELECT * FROM users WHERE email = ${email}`);
```

## Component Patterns

### Server Components (Default)

```typescript
// ✅ GOOD: Server component by default
export default async function DashboardPage() {
  const session = await requireAuth();
  const data = await fetchDashboardData(session.user.id);
  
  return <DashboardClient data={data} />;
}

// ❌ BAD: Client component for data fetching
'use client';
export default function DashboardPage() {
  const [data, setData] = useState(null);
  useEffect(() => { fetch('/api/dashboard').then(...) }, []);
  return <div>...</div>;
}
```

### Client Components (When Needed)

```typescript
'use client';

// ✅ GOOD: Explicit interactivity, form handling
export function SearchForm({ onSearch }: { onSearch: (q: string) => void }) {
  const [query, setQuery] = useState('');
  
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSearch(query); }}>
      <input value={query} onChange={(e) => setQuery(e.target.value)} />
    </form>
  );
}
```

### Form Validation

```typescript
// ✅ GOOD: Shared Zod schema, server + client validation
// lib/validators.ts
export const createUserSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email'),
});

// app/api/users/route.ts
export async function POST(req: Request) {
  const body = await req.json();
  const validated = createUserSchema.parse(body); // Throws if invalid
  // ... create user
}

// components/forms/CreateUserForm.tsx
import { createUserSchema } from '@/lib/validators';

export function CreateUserForm() {
  const form = useForm({
    resolver: zodResolver(createUserSchema), // Same schema
    // ...
  });
}
```

## API Route Patterns

```typescript
// ✅ GOOD: REST, explicit error handling, Zod validation
// app/api/users/route.ts
import { createUserSchema } from '@/lib/validators';
import { requireAuth } from '@/lib/auth';

export async function POST(req: Request) {
  try {
    const session = await requireAuth(); // Throws if not authenticated
    const body = await req.json();
    const validated = createUserSchema.parse(body);
    
    const user = await createUser(validated);
    return Response.json({ user }, { status: 201 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return Response.json({ error: error.errors }, { status: 400 });
    }
    if (error instanceof AuthError) {
      return Response.json({ error: 'Unauthorized' }, { status: 401 });
    }
    return Response.json({ error: 'Internal error' }, { status: 500 });
  }
}

// ❌ BAD: No validation, no error handling, tRPC
export async function POST(req: Request) {
  const body = await req.json();
  const user = await db.insert(users).values(body).returning(); // No validation!
  return Response.json(user);
}
```

## What We Don't Do (and Why)

### ❌ No Pages Router
**Why:** App Router is the future. Pages Router is legacy. Mixing them causes confusion.

### ❌ No Prisma
**Why:** Prisma is overkill for SQLite. It adds 50MB+ to bundle size and doesn't support edge runtime. Drizzle is lightweight, type-safe, and works everywhere.

### ❌ No NextAuth
**Why:** NextAuth is designed for OAuth providers and complex auth flows. For SQLite SaaS, Better Auth or Lucia is simpler, lighter, and more flexible.

### ❌ No tRPC
**Why:** tRPC locks you into React + TypeScript. REST + Zod is more flexible, works with any client, and is easier to debug.

### ❌ No `any` Types
**Why:** TypeScript's `any` defeats the purpose of type safety. Use `unknown` + type guards if you must.

### ❌ No Hard Deletes
**Why:** Soft deletes (`deleted_at`) allow data recovery, audit trails, and prevent accidental data loss.

### ❌ No Client-Side Data Fetching for Initial Load
**Why:** Server components are faster, SEO-friendly, and reduce client bundle size. Only use client-side fetching for infinite scroll, real-time updates, or user-triggered actions.

### ❌ No Raw SQL in Components
**Why:** Raw SQL is error-prone and hard to refactor. Use Drizzle's query builder for type safety and composability.

### ❌ No `console.log` in Production
**Why:** Use a proper logging library (pino, winston) with log levels. `console.log` is unstructured and can't be filtered.

## Dev Commands

```bash
# Development
npm run dev              # Start dev server (http://localhost:3000)
npm run build            # Production build
npm run start            # Start production server

# Database
npm run db:generate      # Generate Drizzle migrations from schema changes
npm run db:migrate       # Run pending migrations
npm run db:studio        # Open Drizzle Studio (database GUI)
npm run db:seed          # Seed database with test data

# Testing
npm run test             # Run Vitest (unit tests)
npm run test:e2e         # Run Playwright (end-to-end tests)
npm run test:coverage    # Run tests with coverage report

# Code Quality
npm run lint             # Run ESLint
npm run lint:fix         # Auto-fix ESLint issues
npm run format           # Format code with Prettier
npm run typecheck        # Run TypeScript type checking
```

## Git Conventions

### Commit Messages

```
feat: add user registration form
fix: prevent duplicate email on signup
refactor: extract auth logic to service layer
docs: update API documentation
test: add unit tests for user creation
chore: upgrade Next.js to 15.0.3
```

### Branch Naming

```
feature/user-registration
fix/duplicate-email-bug
refactor/auth-service
docs/api-documentation
```

### Pull Requests

- **Title:** Follow commit message format
- **Description:** What changed, why, and how to test
- **Screenshots:** Required for UI changes
- **Tests:** Must pass before merge

## Environment Variables

```bash
# .env.local (never commit this file)
DATABASE_URL=file:./db.sqlite  # SQLite file path or Turso URL
AUTH_SECRET=your-secret-key    # Generate with: openssl rand -base64 32
NODE_ENV=development           # development | production | test
```

## Deployment Checklist

- [ ] Run `npm run build` locally (catches type errors)
- [ ] Run `npm run test` (all tests pass)
- [ ] Run `npm run db:migrate` (migrations work)
- [ ] Set environment variables in production
- [ ] Test authentication flow
- [ ] Test database operations
- [ ] Check bundle size (`npm run build` output)
- [ ] Enable Vercel Analytics (if using Vercel)

## Common Pitfalls

### ❌ Forgetting to Handle Loading States
```typescript
// ✅ GOOD: Suspense boundary for async components
import { Suspense } from 'react';

export default function Page() {
  return (
    <Suspense fallback={<Loading />}>
      <AsyncComponent />
    </Suspense>
  );
}
```

### ❌ Not Validating API Input
```typescript
// ✅ GOOD: Always validate with Zod
const validated = schema.parse(body);
```

### ❌ Using `useEffect` for Data Fetching
```typescript
// ✅ GOOD: Use server components or React Query
// Server component:
const data = await fetchData();
// Client component:
const { data } = useQuery({ queryKey: ['data'], queryFn: fetchData });
```

### ❌ Hardcoding Environment Variables
```typescript
// ✅ GOOD: Use process.env with validation
const dbUrl = process.env.DATABASE_URL;
if (!dbUrl) throw new Error('DATABASE_URL is required');
```

## Resources

- [Next.js 15 Docs](https://nextjs.org/docs)
- [Drizzle ORM Docs](https://orm.drizzle.team)
- [shadcn/ui Components](https://ui.shadcn.com)
- [Zod Validation](https://zod.dev)
- [Better Auth](https://better-auth.com)
