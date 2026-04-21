# CLAUDE.md - Next.js 15 + SQLite SaaS Project

## Project Overview

This is a production-ready SaaS application built with **Next.js 15 App Router** and **SQLite** (using `better-sqlite3` or **Turso** for edge-compatible deployments).

## Tech Stack

### Core
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript 5.x (strict mode)
- **Database**: SQLite via `better-sqlite3` (local) or **Turso** (libsql, edge-compatible)
- **ORM**: Drizzle ORM (preferred) or Prisma
- **Auth**: NextAuth.js v5 (Auth.js) or Lucia Auth
- **Validation**: Zod
- **Forms**: React Hook Form + Zod resolver

### UI & Styling
- **Component Library**: shadcn/ui (Radix UI primitives)
- **Styling**: Tailwind CSS 4.x
- **Icons**: Lucide React
- **Charts**: Recharts or Chart.js

### Backend & API
- **API Routes**: Next.js App Router Route Handlers (`app/api/**`)
- **Server Actions**: For mutations (preferred over API routes when possible)
- **Caching**: React Cache + `unstable_cache`
- **Queue**: Inngest or Trigger.dev (background jobs)

### DevOps
- **Deployment**: Vercel (preferred) or Docker + any host
- **Database Hosting**: Turso Cloud (edge) or local SQLite file
- **CI/CD**: GitHub Actions
- **Monitoring**: Vercel Analytics + Logtail

## Project Structure

```
├── app/
│   ├── (auth)/              # Auth route group (login, signup, forgot-password)
│   ├── (dashboard)/         # Dashboard route group (protected)
│   ├── api/                 # API routes
│   ├── layout.tsx           # Root layout
│   ├── page.tsx             # Landing page
│   └── globals.css
├── components/
│   ├── ui/                  # shadcn/ui components
│   ├── forms/               # Reusable form components
│   └── dashboard/           # Dashboard-specific components
├── lib/
│   ├── db/                  # Database connection & schema
│   │   ├── index.ts         # DB connection singleton
│   │   ├── schema.ts        # Drizzle schema definitions
│   │   └── migrate.ts       # Migration runner
│   ├── auth/                # Auth configuration
│   ├── validators/          # Zod schemas
│   └── utils.ts             # Utility functions
├── hooks/                   # Custom React hooks
├── actions/                 # Server actions
├── emails/                  # Email templates (React Email)
├── public/                  # Static assets
├── tests/                   # Vitest tests
├── .env.local               # Environment variables (gitignored)
├── .env.example             # Environment template
├── drizzle.config.ts        # Drizzle ORM configuration
├── next.config.ts           # Next.js configuration
├── tailwind.config.ts       # Tailwind configuration
├── tsconfig.json            # TypeScript configuration
└── package.json
```

## Coding Conventions

### TypeScript
- **Strict mode**: Always enabled
- **No `any`**: Use `unknown` + type guards instead
- **Explicit return types**: Required for all functions
- **Interface vs Type**: Use `interface` for object shapes, `type` for unions/aliases
- **Generics**: Prefer explicit generics over inference for complex types

```typescript
// ✅ Good
interface User {
  id: string;
  email: string;
  createdAt: Date;
}

async function getUserById(id: string): Promise<User | null> {
  // ...
}

// ❌ Bad
const getUser = async (id: any) => {
  // ...
}
```

### File Naming
- **Components**: PascalCase (`UserProfile.tsx`)
- **Utilities**: camelCase (`formatDate.ts`)
- **Hooks**: camelCase with `use` prefix (`useAuth.ts`)
- **Server Actions**: camelCase with action verb (`createUser.ts`)

### Component Patterns

#### Server Components (Default)
```typescript
// ✅ Default to Server Components
async function UserProfile({ userId }: { userId: string }) {
  const user = await db.query.users.findFirst({ where: eq(users.id, userId) });
  
  if (!user) return <NotFound />;
  
  return (
    <div>
      <h1>{user.name}</h1>
      <p>{user.email}</p>
    </div>
  );
}
```

#### Client Components (When Needed)
```typescript
// ✅ Use 'use client' only when necessary
'use client';

import { useState } from 'react';

export function SearchInput() {
  const [query, setQuery] = useState('');
  
  return (
    <input
      value={query}
      onChange={(e) => setQuery(e.target.value)}
      placeholder="Search..."
    />
  );
}
```

### Server Actions
```typescript
// ✅ Server action with validation
'use server';

import { z } from 'zod';
import { revalidatePath } from 'next/cache';
import { db } from '@/lib/db';

const createUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(2),
});

export async function createUser(formData: FormData) {
  const validated = createUserSchema.parse({
    email: formData.get('email'),
    name: formData.get('name'),
  });
  
  const user = await db.insert(users).values(validated).returning();
  
  revalidatePath('/dashboard/users');
  
  return { success: true, user };
}
```

## Database Patterns

### Schema Definition (Drizzle)
```typescript
// lib/db/schema.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const users = sqliteTable('users', {
  id: text('id').primaryKey(),
  email: text('email').notNull().unique(),
  name: text('name'),
  role: text('role', { enum: ['user', 'admin'] }).default('user'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull(),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull(),
});

export const sessions = sqliteTable('sessions', {
  id: text('id').primaryKey(),
  userId: text('user_id').notNull().references(() => users.id),
  expiresAt: integer('expires_at', { mode: 'timestamp' }).notNull(),
});
```

### Migrations
```bash
# Generate migration
npx drizzle-kit generate

# Run migrations
npx drizzle-kit migrate

# Push schema (dev only)
npx drizzle-kit push
```

### Query Patterns
```typescript
// ✅ Use transactions for related writes
import { db } from '@/lib/db';
import { users, sessions } from '@/lib/db/schema';

async function createUserWithSession(email: string) {
  return await db.transaction(async (tx) => {
    const [user] = await tx.insert(users).values({ email }).returning();
    const [session] = await tx.insert(sessions).values({
      userId: user.id,
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
    }).returning();
    
    return { user, session };
  });
}
```

## API Patterns

### Route Handlers
```typescript
// app/api/users/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { eq } from 'drizzle-orm';
import { users } from '@/lib/db/schema';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  
  const user = await db.query.users.findFirst({
    where: eq(users.id, id),
  });
  
  if (!user) {
    return NextResponse.json({ error: 'User not found' }, { status: 404 });
  }
  
  return NextResponse.json(user);
}
```

### Error Handling
```typescript
// ✅ Consistent error response format
class AppError extends Error {
  constructor(
    public code: string,
    public status: number,
    message: string
  ) {
    super(message);
  }
}

function handleError(error: unknown) {
  if (error instanceof AppError) {
    return NextResponse.json(
      { error: error.message, code: error.code },
      { status: error.status }
    );
  }
  
  // Log to monitoring service
  console.error(error);
  
  return NextResponse.json(
    { error: 'Internal server error', code: 'INTERNAL_ERROR' },
    { status: 500 }
  );
}
```

## Authentication Patterns

### Protected Routes
```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getSession } from '@/lib/auth';

const protectedPaths = ['/dashboard', '/settings'];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  if (protectedPaths.some(path => pathname.startsWith(path))) {
    const session = await getSession();
    
    if (!session) {
      return NextResponse.redirect(new URL('/login', request.url));
    }
  }
  
  return NextResponse.next();
}
```

## Testing Strategy

### Test Stack
- **Runner**: Vitest
- **Component Testing**: React Testing Library
- **E2E**: Playwright
- **Coverage**: c8

### Test Structure
```typescript
// tests/components/UserProfile.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { UserProfile } from '@/components/UserProfile';

describe('UserProfile', () => {
  it('renders user information', async () => {
    const mockUser = { id: '1', name: 'John', email: 'john@example.com' };
    
    render(<UserProfile user={mockUser} />);
    
    expect(screen.getByText('John')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
  });
});
```

### Running Tests
```bash
# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific file
npm test -- UserProfile.test.tsx

# Run E2E tests
npm run test:e2e
```

## Environment Variables

```bash
# .env.example

# Database
DATABASE_URL="file:./dev.db"  # Local SQLite
# or
DATABASE_URL="libsql://your-db.turso.io"  # Turso
TURSO_AUTH_TOKEN="your_auth_token"

# Auth
AUTH_SECRET="your_secret_here"
NEXTAUTH_URL="http://localhost:3000"

# Email (Resend)
RESEND_API_KEY="re_xxxxx"

# Analytics
VERCEL_ANALYTICS_ID="xxxxx"

# Feature Flags
ENABLE_BETA_FEATURES="false"
```

## Deployment Checklist

- [ ] Set all environment variables in Vercel/Turso
- [ ] Run migrations: `npx drizzle-kit migrate`
- [ ] Configure custom domain (if applicable)
- [ ] Enable Vercel Analytics
- [ ] Set up error monitoring (Logtail/Sentry)
- [ ] Configure email templates (Resend)
- [ ] Test authentication flow
- [ ] Verify database connection
- [ ] Run smoke tests

## Common Commands

```bash
# Development
npm run dev              # Start dev server
npm run build            # Production build
npm run start            # Start production server

# Database
npm run db:generate      # Generate migrations
npm run db:migrate       # Run migrations
npm run db:push          # Push schema (dev only)
npm run db:studio        # Open Drizzle Studio

# Testing
npm test                 # Run tests
npm run test:e2e         # Run E2E tests
npm run test:coverage    # Run with coverage

# Linting
npm run lint             # Run ESLint
npm run lint:fix         # Auto-fix issues
npm run typecheck        # Run TypeScript check
```

## Troubleshooting

### Database Connection Issues
```typescript
// Ensure singleton pattern
let dbInstance: ReturnType<typeof createDb>;

export function getDb() {
  if (!dbInstance) {
    dbInstance = createDb(process.env.DATABASE_URL!);
  }
  return dbInstance;
}
```

### Hydration Mismatches
- Check for server/client rendering mismatches
- Use `useEffect` for browser-only code
- Wrap client-only components with `<ClientOnly>` wrapper

### Performance Issues
- Use React Server Components by default
- Implement proper caching with `unstable_cache`
- Add `loading.tsx` for streaming UI
- Use `next/image` for optimized images

## Security Best Practices

### SQL Injection Prevention
```typescript
// ✅ Use parameterized queries with Drizzle
const user = await db.query.users.findFirst({
  where: eq(users.email, email), // Safe
});

// ❌ Never concatenate user input
const user = await db.execute(`SELECT * FROM users WHERE email = '${email}'`);
```

### XSS Prevention
```typescript
// ✅ React automatically escapes content
<div>{userInput}</div>

// ❌ Never use dangerouslySetInnerHTML with user content
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// ✅ If you must, sanitize first
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userInput) }} />
```

### CSRF Protection
- NextAuth.js includes CSRF protection by default
- For custom forms, use CSRF tokens:
```typescript
import { getCsrfToken } from 'next-auth/react';

export default async function Page() {
  const csrfToken = await getCsrfToken();
  return <input name="csrfToken" type="hidden" defaultValue={csrfToken} />;
}
```

### Rate Limiting
```typescript
import { Ratelimit } from '@upstash/ratelimit';

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, '10 s'),
});

export async function POST(request: Request) {
  const ip = request.headers.get('x-forwarded-for');
  const { success } = await ratelimit.limit(ip ?? 'anonymous');
  
  if (!success) {
    return NextResponse.json({ error: 'Too many requests' }, { status: 429 });
  }
  // ...
}
```

## Accessibility (a11y) Guidelines

### Component Requirements
- All interactive elements must have `aria-label` or visible text
- Images must have `alt` text (decorative images use `alt=""`)
- Forms must have associated `<label>` elements
- Color alone cannot convey information
- Focus states must be visible

### Testing
```bash
# Run axe-core accessibility tests
npm run test:a11y

# Lighthouse CI for accessibility score
npm run lighthouse
```

## Git Workflow

### Branch Naming
- `feat/feature-name` - New features
- `fix/bug-name` - Bug fixes
- `chore/task-name` - Maintenance tasks
- `docs/doc-name` - Documentation updates

### Commit Message Format
```
type(scope): subject

body (optional)

footer (optional) - Closes #123
```

Types: `feat`, `fix`, `chore`, `docs`, `style`, `refactor`, `test`, `ci`

Example:
```
feat(auth): add password reset flow

- Add forgot password form
- Add reset token generation
- Send email with reset link

Closes #45
```

---

**Last Updated**: 2026-04-21  
**Maintained By**: Development Team  
**Questions**: Open an issue or contact the team
