# CLAUDE.md - Next.js 15 + SQLite SaaS Template

## Project Identity

**Stack:** Next.js 15 (App Router) + SQLite (better-sqlite3) + TypeScript
**Philosophy:** Opinionated defaults, zero-config development, production-ready patterns
**Target:** SaaS applications with auth, billing, and user data

---

## Stack Versions (Pinned)

```json
{
  "next": "^15.0.0",
  "react": "^19.0.0",
  "better-sqlite3": "^11.0.0",
  "typescript": "^5.0.0",
  "tailwindcss": "^4.0.0",
  "zod": "^3.0.0"
}
```

---

## Folder Structure

```
app/
├── (auth)/                    # Auth route group
│   ├── login/page.tsx
│   ├── register/page.tsx
│   └── layout.tsx            # Auth layout (no nav)
├── (dashboard)/               # Dashboard route group
│   ├── dashboard/page.tsx
│   ├── settings/page.tsx
│   └── layout.tsx            # Dashboard layout (with nav)
├── api/                       # API routes
│   ├── auth/[...nextauth]/route.ts
│   ├── users/route.ts
│   └── webhook/stripe/route.ts
├── lib/
│   ├── db.ts                 # Database singleton
│   ├── auth.ts               # Auth configuration
│   └── stripe.ts             # Stripe client
├── components/
│   ├── ui/                   # shadcn/ui components
│   └── app/                  # App-specific components
├── hooks/
├── types/
└── styles/
data/                         # SQLite database directory
├── sqlite.db
└── migrations/
public/
scripts/
├── migrate.ts                # Database migrations
└── seed.ts                   # Development seeding
```

---

## Database Conventions

### Naming
- Tables: `snake_case`, plural (`users`, `subscriptions`)
- Columns: `snake_case` (`created_at`, `stripe_customer_id`)
- Foreign keys: `table_name_id` (`user_id` references `users(id)`)
- Indexes: `idx_table_column`

### Required Columns (Every Table)
```sql
id INTEGER PRIMARY KEY AUTOINCREMENT,
created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
```

### Migration Rules
1. **Never** modify existing migrations
2. **Always** create new migrations for schema changes
3. **Always** provide a down migration
4. **Test** migrations on a copy of production data

### Migration Template
```typescript
// scripts/migrate.ts
const migrations = [
  {
    name: '001_create_users',
    up: `
      CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        stripe_customer_id TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );
      CREATE INDEX idx_users_email ON users(email);
    `,
    down: `DROP TABLE users;`
  }
];
```

---

## Component Patterns

### Server Components (Default)
```typescript
// app/dashboard/page.tsx
export default async function DashboardPage() {
  const session = await auth();
  if (!session) redirect('/login');
  
  const data = await db.prepare('SELECT * FROM items WHERE user_id = ?').all(session.user.id);
  
  return <DashboardView data={data} />;
}
```

### Client Components (Interactivity Required)
```typescript
'use client';

// components/app/CreateItemForm.tsx
export function CreateItemForm() {
  const [isPending, startTransition] = useTransition();
  
  async function onSubmit(formData: FormData) {
    startTransition(async () => {
      await createItem(formData);
    });
  }
  
  return <form action={onSubmit}>...</form>;
}
```

### Component Naming
- **Pages:** `NamePage.tsx` (`DashboardPage.tsx`)
- **Layout:** `NameLayout.tsx` (`DashboardLayout.tsx`)
- **UI Components:** PascalCase, specific (`PrimaryButton`, `UserCard`)
- **Hooks:** `useFeature.ts` (`useAuth.ts`)

---

## API Route Patterns

### Required Structure
```typescript
// app/api/resource/route.ts
import { NextResponse } from 'next/server';
import { z } from 'zod';
import { auth } from '@/app/lib/auth';
import { db } from '@/app/lib/db';

const CreateSchema = z.object({
  name: z.string().min(1).max(255),
});

export async function POST(request: Request) {
  try {
    const session = await auth();
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
    const body = await request.json();
    const validated = CreateSchema.parse(body);
    
    const result = db.prepare(
      'INSERT INTO items (name, user_id) VALUES (?, ?) RETURNING *'
    ).get(validated.name, session.user.id);
    
    return NextResponse.json(result, { status: 201 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ error: error.errors }, { status: 400 });
    }
    console.error('POST /api/resource error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
```

### API Conventions
- **Validation:** Always use Zod
- **Auth:** Check session on every protected route
- **Errors:** Return `{ error: string }` with appropriate status code
- **Logging:** Always log errors with context

---

## What We Do

### ✅ DO

- Use Server Components by default
- Keep data fetching in Server Components
- Use `better-sqlite3` for sync database operations
- Use transactions for multi-step operations
- Use optimistic UI with `useTransition`
- Use environment variables with `process.env.VAR_NAME`
- Use TypeScript strict mode
- Use early returns for guard clauses
- Use `async/await` over `.then()`
- Use SQL parameters (never string interpolation)

### ❌ DON'T

- Use `console.log` in production code (use a logger)
- Use `any` type (use `unknown` with type guards)
- Store secrets in client-side code
- Use `eval()` or `new Function()`
- Write raw SQL without parameterization
- Mix database logic with UI components
- Use `var` (use `const`/`let`)
- Leave `console.error` without context
- Use default exports (use named exports)
- Add dependencies without reviewing bundle size

---

## Development Commands

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Run database migrations
npm run migrate

# Seed development data
npm run seed

# Build for production
npm run build

# Start production server
npm start

# Type checking
npm run typecheck

# Linting
npm run lint
```

---

## Environment Variables

```bash
# Required
DATABASE_URL="file:./data/sqlite.db"
NEXTAUTH_SECRET="your-secret-key-min-32-chars"
NEXTAUTH_URL="http://localhost:3000"

# Optional (for SaaS features)
STRIPE_SECRET_KEY="sk_test_..."
STRIPE_WEBHOOK_SECRET="whsec_..."
STRIPE_PRICE_ID="price_..."
```

---

## Anti-Patterns (With Reasons)

| Anti-Pattern | Why Not | Do Instead |
|--------------|---------|------------|
| `useEffect` for data fetching | Waterfall requests, no SSR | Server Components with async/await |
| Prisma ORM | Heavy bundle, complex for SQLite | `better-sqlite3` with typed wrappers |
| `useState` for forms | Boilerplate, no validation | Server Actions with Zod |
| Storing passwords plain | Security risk | bcrypt with 12+ rounds |
| `SELECT *` | Brittle schema changes | Explicit column selection |
| API routes for internal data | Unnecessary HTTP overhead | Direct DB calls in Server Components |

---

## Quick Start Checklist

- [ ] `npm create next-app@latest myapp --typescript --tailwind --eslint`
- [ ] `npm install better-sqlite3 zod next-auth`
- [ ] `npm install -D @types/better-sqlite3`
- [ ] Create `data/` directory with `.gitignore` for `*.db`
- [ ] Copy this CLAUDE.md to project root
- [ ] Set up `app/lib/db.ts` with singleton pattern
- [ ] Create first migration with `scripts/migrate.ts`
- [ ] Configure NextAuth with `app/lib/auth.ts`
- [ ] Test: `npm run dev` → should start without errors

---

## Testing Philosophy

- **Unit tests:** Business logic, utilities
- **Integration tests:** API routes, database operations
- **E2E tests:** Critical user flows (auth, payment)
- **No snapshot tests** (brittle, low value)

---

## Performance Targets

- First Contentful Paint: < 1.5s
- Time to Interactive: < 3.5s
- API response time (p95): < 200ms
- Database query time (p95): < 50ms

---

## Security Checklist

- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (React auto-escapes, but validate inputs)
- [ ] CSRF protection (NextAuth handles this)
- [ ] Rate limiting on API routes
- [ ] Environment variables validated at startup
- [ ] No secrets in client bundles

---

## This Is Not Generic

Every rule here exists because:
1. We've shipped 10+ SaaS products with this stack
2. Each anti-pattern came from real production pain
3. These defaults prevent common mistakes
4. The structure scales from MVP to $10k MRR

**If Claude Code follows this file, no clarifying questions should be needed.**
