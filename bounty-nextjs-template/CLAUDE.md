# CLAUDE.md - Next.js + SQLite SaaS Project

> Production-ready project context for AI-assisted development

## Project Overview

This is a SaaS application built with **Next.js 15 App Router** and **SQLite** (better-sqlite3). The goal is to build a fast, type-safe, and maintainable codebase that leverages modern React patterns.

---

## Tech Stack

| Layer | Technology | Why |
|-------|------------|-----|
| Framework | Next.js 15 (App Router) | Server Components, streaming, partial rendering |
| Database | SQLite (better-sqlite3) | Zero-config, file-based, perfect for SaaS MVPs |
| ORM | Kysely or Drizzle | Type-safe SQL, no magic |
| Auth | NextAuth.js v5 | Industry standard, session-based |
| Styling | Tailwind CSS v4 | Utility-first, JIT compilation |
| Forms | React Hook Form + Zod | Schema validation, minimal re-renders |
| Testing | Vitest + Playwright | Fast unit tests, reliable E2E |

---

## Project Structure

```
app/
├── (auth)/           # Auth-related pages (login, register)
│   ├── login/
│   └── register/
├── (dashboard)/      # Protected dashboard routes
│   ├── layout.tsx    # Auth check wrapper
│   └── page.tsx
├── api/              # API routes (REST endpoints)
│   └── [...]/route.ts
├── layout.tsx        # Root layout
└── page.tsx          # Landing page

components/
├── ui/               # Generic, reusable UI components
│   ├── button.tsx
│   └── input.tsx
├── features/         # Feature-specific components
│   └── user-profile.tsx
└── layouts/          # Layout components

lib/
├── db/               # Database layer
│   ├── schema.ts     # SQLite schema definitions
│   ├── index.ts      # Database connection
│   └── migrations/   # SQL migration files
├── auth.ts           # NextAuth configuration
└── utils.ts          # Shared utilities

types/
└── index.ts          # Global TypeScript types
```

---

## Naming Conventions

### Files
- **Components**: `kebab-case.tsx` → `user-profile.tsx`
- **Routes**: `kebab-case/` → `api/webhooks/`
- **Utils**: `kebab-case.ts` → `date-utils.ts`

### Code
- **Components**: PascalCase → `UserProfile`
- **Functions**: camelCase → `getUserById`
- **Types**: PascalCase with prefix → `User`, `UserRow`
- **Constants**: SCREAMING_SNAKE → `MAX_RETRY_COUNT`
- **Database columns**: snake_case → `created_at`, `user_id`

### Database
- **Tables**: plural, snake_case → `users`, `user_sessions`
- **Primary keys**: `id` (integer, auto-increment)
- **Foreign keys**: `{table}_id` → `user_id`
- **Timestamps**: `created_at`, `updated_at` (Unix epoch, INTEGER)

---

## Database Rules

### Migrations
1. **Always use SQL files** in `lib/db/migrations/`
2. **Never edit existing migrations** — create new ones
3. **Include rollback SQL** in comments

```sql
-- Migration: 001_create_users.sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at INTEGER DEFAULT (strftime('%s', 'now')),
  updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);

-- Rollback: DROP TABLE users;
```

### Schema Changes
- Run migrations manually: `sqlite3 db.sqlite < lib/db/migrations/001_create_users.sql`
- Use transactions for data migrations

### Query Patterns
```typescript
// ✅ Good: Parameterized queries
const user = db.prepare('SELECT * FROM users WHERE id = ?').get(userId);

// ❌ Bad: String concatenation (SQL injection risk)
const user = db.prepare(`SELECT * FROM users WHERE id = ${userId}`).get();
```

---

## Development Commands

```bash
# Install dependencies
npm install

# Start dev server (http://localhost:3000)
npm run dev

# Build for production
npm run build

# Run production build
npm start

# Run database migrations
npm run db:migrate

# Open SQLite CLI
sqlite3 db.sqlite

# Run tests
npm test

# Run E2E tests
npm run test:e2e

# Type check
npm run type-check

# Lint
npm run lint
```

---

## Patterns to Follow

### Server Components by Default
```tsx
// ✅ Default: Server Component
export default async function Page() {
  const data = await getData(); // Direct DB access
  return <div>{data}</div>;
}

// ✅ Only when needed: Client Component
'use client';
export function InteractiveButton() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

### Data Fetching
```tsx
// ✅ Good: Fetch in Server Component
async function getUser(id: string) {
  return db.prepare('SELECT * FROM users WHERE id = ?').get(id);
}

// ✅ Use in page
export default async function UserProfile({ params }) {
  const user = await getUser(params.id);
  return <div>{user.name}</div>;
}
```

### Error Handling
```tsx
// ✅ Use error.tsx for error boundaries
// app/dashboard/error.tsx
'use client';
export default function Error({ error, reset }) {
  return (
    <div>
      <h2>Something went wrong!</h2>
      <button onClick={reset}>Try again</button>
    </div>
  );
}
```

---

## Anti-Patterns to Avoid

| ❌ Don't | ✅ Do Instead |
|----------|---------------|
| Use `useEffect` for data fetching | Fetch in Server Components |
| Create huge `useContext` stores | Use Server Components + props |
| Add `'use client'` everywhere | Only where interactivity is needed |
| Use Prisma with SQLite | Use better-sqlite3 directly or Drizzle |
| Fetch data in layout | Fetch in page components |
| Create generic `utils.ts` | Create purpose-specific files |

---

## Auth Pattern (NextAuth.js v5)

```typescript
// lib/auth.ts
import NextAuth from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import { db } from './db';

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Credentials({
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        const user = db.prepare('SELECT * FROM users WHERE email = ?')
          .get(credentials.email);
        
        if (!user) return null;
        
        // Verify password with bcrypt
        const isValid = await bcrypt.compare(
          credentials.password,
          user.password_hash
        );
        
        return isValid ? { id: user.id, email: user.email } : null;
      },
    }),
  ],
  session: { strategy: 'jwt' },
});

// app/(dashboard)/layout.tsx
import { auth } from '@/lib/auth';
import { redirect } from 'next/navigation';

export default async function DashboardLayout({ children }) {
  const session = await auth();
  if (!session) redirect('/login');
  return <>{children}</>;
}
```

---

## Testing Strategy

### Unit Tests (Vitest)
```typescript
// __tests__/lib/utils.test.ts
import { describe, it, expect } from 'vitest';
import { formatDate } from '@/lib/utils';

describe('formatDate', () => {
  it('formats Unix timestamp', () => {
    expect(formatDate(1712620800)).toBe('2024-04-08');
  });
});
```

### E2E Tests (Playwright)
```typescript
// e2e/login.spec.ts
import { test, expect } from '@playwright/test';

test('user can login', async ({ page }) => {
  await page.goto('/login');
  await page.fill('input[name="email"]', 'test@example.com');
  await page.fill('input[name="password"]', 'password');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL('/dashboard');
});
```

---

## Security Checklist

- [ ] All SQL queries use parameterized statements
- [ ] Passwords hashed with bcrypt (cost ≥ 12)
- [ ] CSRF protection enabled (NextAuth default)
- [ ] Input validated with Zod schemas
- [ ] No secrets in client components
- [ ] Rate limiting on auth endpoints
- [ ] HTTPS only in production

---

## Environment Variables

```bash
# .env.local (never commit!)
DATABASE_URL="file:./db.sqlite"
NEXTAUTH_SECRET="your-secret-here"
NEXTAUTH_URL="http://localhost:3000"
SMTP_HOST="smtp.example.com"
SMTP_USER="noreply@example.com"
SMTP_PASS="smtp-password"
```

---

## Deployment (Vercel)

1. Push to GitHub
2. Import project in Vercel
3. Set environment variables
4. Deploy

For SQLite: Use Vercel's ephemeral file system for dev, or migrate to Turso/PlanetScale for production.

---

## Bounty

Created for [$75 Bounty #2](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2).

## License

MIT
