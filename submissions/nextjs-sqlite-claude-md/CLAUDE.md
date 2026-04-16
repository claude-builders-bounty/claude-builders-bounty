# CLAUDE.md — Project Context for Claude Code

> **Stack:** Next.js 15 (App Router) + SQLite (better-sqlite3 / Turso) + TypeScript
> **Type:** SaaS Application

---

## Architecture Overview

```
app/
├── (auth)/          # Auth routes (login, signup, forgot-password)
├── (dashboard)/     # Protected dashboard routes
│   ├── layout.tsx   # Dashboard layout with sidebar
│   └── [section]/   # Dynamic dashboard sections
├── api/             # Route handlers (app/api/*/route.ts)
├── layout.tsx       # Root layout
└── page.tsx         # Landing page

lib/
├── db/              # Database layer
│   ├── schema.ts    # Table definitions & types
│   ├── migrations/  # Migration files (001_initial.sql, ...)
│   ├── client.ts    # better-sqlite3 singleton
│   └── queries.ts   # Reusable query functions
├── auth/            # Auth utilities
├── utils/           # Shared helpers
└── types/           # Shared TypeScript types

components/
├── ui/              # Design system primitives (Button, Input, Card)
├── forms/           # Form components with validation
├── layout/          # Layout components (Header, Sidebar, Footer)
└── [feature]/       # Feature-specific components
```

## Tech Stack & Conventions

| Layer | Choice | Notes |
|-------|--------|-------|
| Framework | Next.js 15 App Router | Use Server Components by default |
| Language | TypeScript strict | `strict: true` in tsconfig |
| Database | SQLite via better-sqlite3 | Synchronous API, single-file DB |
| Hosting DB | Turso (libSQL) | For production — same SQLite API |
| Styling | Tailwind CSS v4 | Utility-first, no CSS modules |
| Auth | Session-based or NextAuth.js | Store sessions in SQLite |
| Validation | Zod | Schema-first validation |
| Forms | React Hook Form + Zod | Server-side validation too |
| Testing | Vitest + Testing Library | Unit + integration tests |

## Database Rules (SQLite)

### Writing Queries
- Always use parameterized queries — NEVER string interpolation for user input
- Use transactions for multi-statement operations
- Define schemas in `lib/db/schema.ts` with TypeScript types

```typescript
// ✅ Good
db.prepare('SELECT * FROM users WHERE id = ?').get(userId);

// ❌ Bad — SQL injection risk
db.prepare(`SELECT * FROM users WHERE id = ${userId}`).get();
```

### Migrations
- Migration files live in `lib/db/migrations/`
- Naming: `NNN_description.sql` (e.g., `001_create_users.sql`)
- Run on app startup: `lib/db/client.ts` checks `PRAGMA user_version`
- Never modify existing migrations — always add new ones

### Schema Conventions
- Every table needs `id TEXT PRIMARY KEY` (UUID v7)
- Always include `created_at TEXT DEFAULT (datetime('now'))`
- Include `updated_at TEXT` with trigger to auto-update
- Use `INTEGER` for booleans (0/1)
- Index foreign keys and frequently queried columns

## Next.js Patterns

### Server vs Client Components
- **Default to Server Components** — only add `'use client'` when needed
- `'use client'` required for: event handlers, useState, useEffect, browser APIs
- Pass server data as props to client components
- Use Server Actions (`'use server'`) for form submissions

### Route Handlers (API)
```typescript
// app/api/[resource]/route.ts
export async function GET(request: Request) { }
export async function POST(request: Request) { }
export async function PUT(request: Request) { }
export async function DELETE(request: Request) { }
```

### Data Fetching
- Server Components: fetch directly (no useEffect needed)
- Use `cache()` for deduplication within a request
- Revalidate with `revalidatePath()` or `revalidateTag()`

### Error Handling
- Use `error.tsx` for route-level error boundaries
- Use `notFound()` from `next/navigation` for 404s
- Validate all inputs with Zod before database operations

## Code Style

### Naming
- Files: `kebab-case.ts` (components: `kebab-case.tsx`)
- Variables/functions: `camelCase`
- Types/interfaces: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Database tables/columns: `snake_case`

### Imports
```typescript
// Order: node builtins → external → internal → types
import { readFileSync } from 'fs';
import { z } from 'zod';
import { db } from '@/lib/db/client';
import type { User } from '@/lib/types';
```

### Component Pattern
```typescript
// Server component
export default async function UserList() {
  const users = getAllUsers();
  return <UserTable users={users} />;
}

// Client component
'use client';
export function UserForm({ onSubmit }: { onSubmit: (data: FormData) => void }) {
  // ...
}
```

## Common Commands

```bash
npm run dev          # Start dev server (localhost:3000)
npm run build        # Production build
npm run test         # Run Vitest
npm run test:watch   # Vitest in watch mode
npm run lint         # ESLint check
npm run db:migrate   # Run migrations
npm run db:seed      # Seed development data
npm run db:reset     # Drop + recreate + migrate + seed
```

## Testing Guidelines

- Unit tests: `lib/**/*.test.ts` (test business logic)
- Component tests: `components/**/*.test.tsx` (test rendering)
- API tests: `app/api/**/*.test.ts` (test route handlers)
- Use `beforeEach` to reset test database
- Mock external services, not the database

## Security Checklist

- [ ] All SQL uses parameterized queries
- [ ] Auth checks on every protected route/API
- [ ] CORS configured for API routes
- [ ] Rate limiting on auth endpoints
- [ ] Input validation with Zod on all user inputs
- [ ] No secrets in code — use `.env.local`
- [ ] CSRF protection on state-changing operations

## Environment Variables

```bash
# .env.local (never commit)
DATABASE_URL=file:./data/app.db    # SQLite path
TURSO_DATABASE_URL=                # Turso (production)
TURSO_AUTH_TOKEN=                  # Turso auth
NEXTAUTH_SECRET=                   # Auth session secret
NEXTAUTH_URL=http://localhost:3000 # Auth callback URL
```

---

*This CLAUDE.md gives Claude Code full context to write idiomatic, production-ready code for this stack.*
