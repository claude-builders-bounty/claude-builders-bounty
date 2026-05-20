# CLAUDE.md - Next.js + SQLite SaaS Template

> Opinionated context for Claude Code to build production-ready Next.js + SQLite SaaS applications.

## Stack & Versions

```
Next.js: 15.x (App Router)
React: 19.x
SQLite: better-sqlite3 or Turso
TypeScript: 5.x
Node.js: 20.x LTS
```

## Folder Structure

```
project/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (auth)/            # Auth route group
│   │   │   ├── login/
│   │   │   ├── signup/
│   │   │   └── forgot-password/
│   │   ├── (dashboard)/       # Protected routes
│   │   │   ├── dashboard/
│   │   │   ├── settings/
│   │   │   └── api/           # API routes
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Landing page
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/                # shadcn/ui components
│   │   ├── forms/             # Form components
│   │   └── layouts/           # Layout components
│   ├── lib/
│   │   ├── db.ts              # SQLite connection
│   │   ├── auth.ts            # Authentication logic
│   │   ├── validators.ts     # Zod schemas
│   │   └── utils.ts           # Helper functions
│   └── types/
│       └── index.ts          # TypeScript types
├── migrations/                # SQL migrations
├── public/                    # Static assets
├── tests/                     # Test files
├── .env.local                # Environment variables
├── drizzle.config.ts         # Drizzle ORM config
├── next.config.ts            # Next.js config
├── tailwind.config.ts        # Tailwind config
└── package.json
```

## Database Conventions

### Migrations

- Use sequential numbering: `001_create_users.sql`, `002_add_sessions.sql`
- Each migration must be idempotent (use `IF NOT EXISTS`)
- Include rollback SQL in comments at the bottom

```sql
-- Migration: 001_create_users
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at INTEGER DEFAULT (unixepoch()),
    updated_at INTEGER DEFAULT (unixepoch())
);

-- Rollback:
-- DROP TABLE IF EXISTS users;
```

### Query Patterns

```typescript
// ✅ Always use parameterized queries
const user = db.prepare('SELECT * FROM users WHERE id = ?').get(userId);

// ❌ Never concatenate strings
const user = db.prepare(`SELECT * FROM users WHERE id = ${userId}`); // DANGEROUS
```

### Schema Rules

- Use `TEXT` for IDs (UUIDs)
- Use `INTEGER` for timestamps (Unix epoch seconds)
- Use `INTEGER DEFAULT 0` for booleans (SQLite has no native bool)
- Add `created_at` and `updated_at` to every table
- Use triggers for `updated_at` auto-update:

```sql
CREATE TRIGGER update_users_timestamp
AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = unixepoch() WHERE id = NEW.id;
END;
```

## Component Patterns

### Server Components (Default)

```tsx
// ✅ Fetch data in Server Components
export default async function DashboardPage() {
    const user = await getCurrentUser();
    const data = await getDashboardData();
    
    return <DashboardView data={data} />;
}
```

### Client Components (When Needed)

```tsx
'use client';

// ✅ Use for interactivity
export function Counter({ initialValue }: { initialValue: number }) {
    const [count, setCount] = useState(initialValue);
    return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

### Form Pattern with Zod

```tsx
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

const schema = z.object({
    email: z.string().email('Invalid email'),
    password: z.string().min(8, 'Must be at least 8 characters'),
});

type FormData = z.infer<typeof schema>;

export function LoginForm() {
    const form = useForm<FormData>({
        resolver: zodResolver(schema),
    });
    
    // ...
}
```

## API Routes

### Route Handler Pattern

```tsx
// app/api/users/route.ts
import { NextResponse } from 'next/server';
import { z } from 'zod';

const createSchema = z.object({
    name: z.string().min(1),
    email: z.string().email(),
});

export async function POST(request: Request) {
    try {
        const body = await request.json();
        const data = createSchema.parse(body);
        
        // Create user
        const user = await createUser(data);
        
        return NextResponse.json({ user }, { status: 201 });
    } catch (error) {
        if (error instanceof z.ZodError) {
            return NextResponse.json(
                { error: 'Validation failed', details: error.errors },
                { status: 400 }
            );
        }
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        );
    }
}
```

## Dev Commands

```bash
# Development
pnpm dev              # Start dev server on :3000

# Database
pnpm db:migrate       # Run migrations
pnpm db:generate      # Generate Drizzle schema
pnpm db:studio        # Open Drizzle Studio

# Build & Deploy
pnpm build            # Production build
pnpm start            # Start production server

# Testing
pnpm test             # Run tests
pnpm test:watch       # Watch mode
pnpm test:e2e         # E2E tests

# Linting
pnpm lint             # Run ESLint
pnpm lint:fix         # Fix lint issues
```

## What We DON'T Do (And Why)

| Pattern | Reason |
|---------|--------|
| No ORM query builders | Raw SQL is more predictable; SQLite is simple |
| No Redux/complex state | Server Components + React Query handle most cases |
| No CSS-in-JS | Tailwind is faster and more maintainable |
| No serverless functions for DB | SQLite needs persistent connections; use containers |
| No client-side data fetching | Prefer Server Components for data loading |
| No `any` types | TypeScript strict mode catches bugs early |
| No `.env` files in repo | Security risk; use `.env.local` and secrets |
| No direct `fetch` in components | Create lib functions for data fetching |
| No inline styles | Breaks Tailwind's purging; use utility classes |
| No `useEffect` for data fetching | Use Server Components or SWR/React Query |

## Environment Variables

```bash
# .env.local (never commit this)
DATABASE_URL="file:./data.db"
NEXTAUTH_SECRET="generate-with-openssl-rand-base64-32"
NEXTAUTH_URL="http://localhost:3000"
GITHUB_CLIENT_ID="..."
GITHUB_CLIENT_SECRET="..."
```

## Security Checklist

- [ ] All queries use parameterized statements
- [ ] Environment variables never logged
- [ ] Auth tokens stored in httpOnly cookies
- [ ] CSRF protection enabled
- [ ] Rate limiting on auth endpoints
- [ ] Input validation with Zod on all forms
- [ ] Content Security Policy headers set

## Quick Reference

```tsx
// Import patterns
import { db } from '@/lib/db';           // Database
import { auth } from '@/lib/auth';       // Auth
import { Button } from '@/components/ui/button';  // UI

// Server action pattern
'use server';
export async function createUser(data: FormData) {
    'use server';
    // ...
}
```

---

*This context helps Claude Code build consistent, production-ready Next.js + SQLite applications.*