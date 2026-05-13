# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack

- **Framework**: Next.js 15 App Router (RSC-first)
- **Database**: SQLite via better-sqlite3 (synchronous, zero-config)
- **Auth**: Session cookies + bcrypt (no NextAuth — we roll our own)
- **Styling**: Tailwind CSS 4 (no component libraries)
- **Language**: TypeScript strict mode
- **Runtime**: Node.js 20+ (no Edge — SQLite needs Node)

## Commands

```bash
npm run dev          # Start dev server (http://localhost:3000)
npm run build        # Production build
npm run start        # Start production server
npm run db:migrate   # Run pending migrations
npm run db:seed      # Seed development data
npm run lint         # ESLint + Prettier check
npm run test         # Vitest (unit + integration)
```

## Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/             # Auth group (login, register)
│   ├── (dashboard)/        # Protected dashboard group
│   ├── api/                # API routes (only when RSC won't work)
│   ├── layout.tsx          # Root layout (providers, fonts)
│   └── page.tsx            # Landing page
├── components/
│   ├── ui/                 # Primitive UI (Button, Input, Card)
│   └── features/           # Feature components (UserTable, BillingCard)
├── lib/
│   ├── db.ts               # Database connection singleton
│   ├── auth.ts             # Session management
│   ├── errors.ts           # Typed error classes
│   └── utils.ts            # Pure utility functions
├── migrations/             # SQL migration files (001_init.sql, etc.)
└── types/                  # Shared TypeScript types
```

## Database Rules

### Migrations

- One file per migration: `migrations/001_init.sql`, `002_add_users.sql`
- Never modify an existing migration — create a new one
- Always include `IF NOT EXISTS` / `IF EXISTS` for idempotency
- Migrations run in order by filename (use numeric prefixes)

### Queries

- Use `db.prepare()` for all queries — never string concatenation
- Always use `?` parameter placeholders — never template literals
- Use `db.transaction()` for multi-step writes
- Return typed results: `db.prepare(...).get() as User | undefined`

### Schema Conventions

- Table names: plural, snake_case (`users`, `billing_events`)
- Column names: snake_case (`created_at`, `user_id`)
- Every table has `id TEXT PRIMARY KEY` (nanoid)
- Every table has `created_at TEXT DEFAULT (datetime('now'))`
- Foreign keys: `REFERENCES users(id) ON DELETE CASCADE`
- Indexes: `idx_tablename_column` naming

### Example Migration

```sql
-- migrations/001_init.sql
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  name TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
```

## Component Patterns

### Server Components (default)

- Fetch data directly in the component
- Use `async/await` — no useEffect for data loading
- Pass serializable props to client components

```tsx
// app/(dashboard)/page.tsx
export default async function DashboardPage() {
  const user = await getUser(); // direct DB call
  return <DashboardClient user={user} />;
}
```

### Client Components

- Mark with `'use client'` only when needed (interactivity, hooks)
- Keep client components thin — logic stays in server components
- Never import `better-sqlite3` in client components

```tsx
// components/features/DashboardClient.tsx
'use client';
export function DashboardClient({ user }: { user: User }) {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

### API Routes

- Only use when RSC won't work (webhooks, file uploads, third-party APIs)
- Always validate input with zod
- Return typed responses
- Use `NextResponse.json()` consistently

```tsx
// app/api/users/route.ts
import { z } from 'zod';
import { NextResponse } from 'next/server';

const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
});

export async function POST(req: Request) {
  const body = await req.json();
  const parsed = CreateUserSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error }, { status: 400 });
  }
  const user = await createUser(parsed.data);
  return NextResponse.json(user, { status: 201 });
}
```

## Auth Pattern

```tsx
// lib/auth.ts
import { cookies } from 'next/headers';
import { db } from './db';

export async function getUser() {
  const session = (await cookies()).get('session')?.value;
  if (!session) return null;
  const row = db.prepare('SELECT * FROM users WHERE id = ?').get(session) as User | undefined;
  return row ?? null;
}

// In a server component:
const user = await getUser();
if (!user) redirect('/login');
```

## Anti-Patterns (Don't Do These)

| Don't | Do Instead |
|-------|-----------|
| `useEffect` for data fetching | Fetch in server component |
| `'use client'` on every component | Default to server components |
| ORM (Prisma, Drizzle) | Direct `better-sqlite3` queries |
| `fetch('/api/...')` from RSC | Direct function call |
| Edge Runtime | Node.js Runtime (SQLite needs it) |
| Global middleware for auth | Per-layout/per-page auth check |
| `any` type | Proper typing or `unknown` |
| String concatenation in SQL | Parameterized queries |
| Component libraries (shadcn) | Custom `ui/` primitives |

## Error Handling

```tsx
// lib/errors.ts
export class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public status: number = 500
  ) {
    super(message);
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string) {
    super(`${resource} not found`, 'NOT_FOUND', 404);
  }
}

export class ValidationError extends AppError {
  constructor(message: string) {
    super(message, 'VALIDATION_ERROR', 400);
  }
}
```

## Environment Variables

```bash
# .env.local (never commit)
DATABASE_URL=./data/app.db
SESSION_SECRET=<random-32-chars>
```

## Testing

- Unit tests: `lib/` functions (pure logic)
- Integration tests: API routes (use test DB)
- No E2E tests unless explicitly requested
- Test file naming: `*.test.ts` next to source file

## What We Don't Use

- ~~Prisma / Drizzle~~ — better-sqlite3 is simpler
- ~~NextAuth~~ — custom session cookies
- ~~Tailwind components (shadcn)~~ — custom primitives
- ~~State management (Zustand, Redux)~~ — server state + React context
- ~~GraphQL~~ — REST or server actions
- ~~Edge Runtime~~ — Node.js for SQLite
- ~~Middleware for auth~~ — per-layout checks
