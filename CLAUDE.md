# CLAUDE.md — Next.js 15 + SQLite SaaS

## Project Structure

```
src/
├── app/                    # Next.js 15 App Router
│   ├── (auth)/             # Auth route group
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/        # Protected route group
│   │   ├── layout.tsx      # Dashboard layout with sidebar
│   │   └── page.tsx
│   ├── api/                # API routes
│   │   └── [action]/route.ts
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Landing page
├── components/
│   ├── ui/                 # Shadcn/ui primitives (button, card, dialog)
│   ├── forms/              # Form components with react-hook-form + zod
│   └── layout/             # Sidebar, header, footer
├── lib/
│   ├── db.ts               # Database connection (better-sqlite3)
│   ├── auth.ts             # Session management
│   ├── errors.ts           # Custom error classes
│   └── utils.ts            # Utility functions (cn, formatDate, etc.)
├── types/                  # TypeScript type definitions
└── hooks/                  # Custom React hooks
```

## Naming Conventions

- **Files:** `kebab-case.tsx` (components), `kebab-case.ts` (utils)
- **Components:** `PascalCase` (e.g., `UserProfile`, `DataTable`)
- **Functions:** `camelCase` (e.g., `getUserById`, `formatCurrency`)
- **Database tables:** `snake_case` (e.g., `user_sessions`, `payment_history`)
- **API routes:** `kebab-case` (e.g., `/api/user-profile`)

## Database Rules (SQLite + better-sqlite3)

```typescript
// ALWAYS use WAL mode for concurrent reads
import Database from 'better-sqlite3';
const db = new Database('app.db');
db.pragma('journal_mode = WAL');

// ALWAYS use prepared statements for repeated queries
const getUser = db.prepare('SELECT * FROM users WHERE id = ?');
const user = getUser.get(userId);

// NEVER use string interpolation in SQL
// BAD:  db.prepare(`SELECT * FROM users WHERE id = ${userId}`)
// GOOD: db.prepare('SELECT * FROM users WHERE id = ?').get(userId)

// ALWAYS use transactions for multi-table writes
const createOrder = db.transaction((items: Item[]) => {
  const order = db.prepare('INSERT INTO orders ...').run(...);
  for (const item of items) {
    db.prepare('INSERT INTO order_items ...').run(...);
  }
  return order;
});
```

## Migration Rules

```typescript
// migrations/001_initial.ts
export function up(db: Database) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT UNIQUE NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `);
}

export function down(db: Database) {
  db.exec('DROP TABLE IF EXISTS users');
}
```

- One file per migration, numbered sequentially
- Always include `down()` for rollback
- Test migrations against empty database AND existing data

## Dev Commands

```bash
npm run dev          # Start dev server (port 3000)
npm run build        # Production build
npm run start        # Start production server
npm run lint         # ESLint + Prettier check
npm run test         # Vitest run
npm run db:migrate   # Run pending migrations
npm run db:seed      # Seed development data
npm run db:studio    # Open database viewer
```

## Patterns to Follow

### API Routes (App Router)
```typescript
// app/api/users/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';

const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1),
});

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const data = CreateUserSchema.parse(body);
    
    const user = createUser(data);
    return NextResponse.json(user, { status: 201 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ errors: error.errors }, { status: 400 });
    }
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
```

### Server Components
```typescript
// Always async, fetch data directly
export default async function DashboardPage() {
  const user = await getUser();
  const stats = await getStats(user.id);
  
  return <Dashboard user={user} stats={stats} />;
}
```

### Client Components
```typescript
'use client';
// Only when you need: useState, useEffect, event handlers, browser APIs
export function InteractiveForm({ onSubmit }: { onSubmit: (data: FormData) => void }) {
  return <form onSubmit={...}>...</form>;
}
```

## Anti-Patterns to Avoid

1. **NEVER** put business logic in components — use lib/ functions
2. **NEVER** fetch data in client components when server components work
3. **NEVER** use `any` type — always define proper types
4. **NEVER** commit `.env` files — use `.env.example`
5. **NEVER** use `console.log` in production code — use structured logging
6. **NEVER** store secrets in database — use environment variables
7. **NEVER** skip error handling — every API route needs try/catch
8. **NEVER** use `setTimeout` for data fetching — use SWR or React Query

## Testing

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
  },
});
```

- Test database operations with in-memory SQLite
- Mock external APIs in integration tests
- Test error paths as thoroughly as happy paths

## Security

- Sanitize all user inputs with Zod
- Use parameterized queries (never string interpolation)
- Implement CSRF protection on forms
- Rate limit API routes (use `@upstash/ratelimit`)
- Validate JWT tokens on every protected route
- Hash passwords with `argon2` (not bcrypt)
