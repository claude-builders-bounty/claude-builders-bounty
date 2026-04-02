# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

## Stack & Versions

- **Runtime:** Node.js 20+ (use `node --version` to confirm)
- **Framework:** Next.js 15 (App Router, not Pages Router)
- **Database:** SQLite via [better-sqlite3](https://www.npmjs.com/package/better-sqlite3) or [@libsql/client](https://turso.tech/libsql-client-ts) (Turso)
- **ORM:** None — raw SQL only. Sequelize/Prisma add unnecessary overhead for SQLite SaaS.
- **Styling:** Tailwind CSS v4 with CSS variables. No CSS Modules for global patterns.
- **Auth:** NextAuth.js v5 with credentials provider (or JWT sessions for simple cases)
- **Validation:** [Zod](https://zod.dev) for all input validation — request bodies, query params, environment variables
- **Deployment:** Vercel (default) or any Node-compatible host

## Project Structure

```
/
├── app/                    # Next.js App Router pages
│   ├── (auth)/            # Auth routes: login, register, logout
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/       # Protected routes (require session)
│   │   ├── layout.tsx     # Dashboard shell with sidebar
│   │   ├── page.tsx      # Main dashboard
│   │   └── [slug]/        # Dynamic dashboard pages
│   ├── api/               # API Route Handlers
│   │   ├── auth/         # NextAuth handlers
│   │   └── v1/           # Versioned API (future-proof)
│   ├── layout.tsx        # Root layout (providers, fonts)
│   └── page.tsx          # Landing / marketing redirect
├── components/
│   ├── ui/               # Primitive UI components (Button, Input, Card, etc.)
│   │   └── *.tsx
│   ├── forms/            # Form components bound to Zod schemas
│   │   └── *.tsx
│   └── layout/           # Shell components: Sidebar, Header, Footer
├── lib/
│   ├── db.ts             # SQLite connection singleton (better-sqlite3)
│   ├── migrations/       # Sequential numbered migration files
│   │   └── 0001_*.sql
│   ├── auth.ts           # NextAuth config
│   └── utils.ts          # Shared utilities (cn(), formatDate(), etc.)
├── public/               # Static assets
├── scripts/
│   └── migrate.ts        # CLI migration runner (see below)
├── .env.local            # Secrets (never commit)
├── .env.example          # Template for .env.local
├── next.config.ts        # Next.js config (TypeScript)
├── tailwind.config.ts    # Tailwind config
└── package.json
```

### Rules

- **One route segment per file.** Don't export multiple page components from one file.
- **Co-locate related files.** If `page.tsx` needs a sub-component that is only used there, keep it in the same folder — don't abstract prematurely.
- **`lib/` is for shared code only.** If code is used in only one route, keep it in the route folder.

## SQL / Migration Conventions

### Migration File Naming

```
scripts/migrations/
├── 0001_initial_schema.sql
├── 0002_add_users_preferences.sql
├── 0003_add_soft_delete.sql
└── 0004_backfill_email_indexes.sql
```

Format: `NNNN_description.sql` — 4-digit sequence number, lowercase snake_case description.

### Migration Runner

Use the `scripts/migrate.ts` CLI. **Never run raw SQL against the database in production** without a migration file.

```bash
# Run pending migrations
npx tsx scripts/migrate.ts

# Check status
npx tsx scripts/migrate.ts --dry-run
```

### SQL Rules

- **Always include a `WHERE` clause in `DELETE` statements.** No exceptions. A `DELETE FROM users` without a `WHERE` fails linting.
- **Use transactions for multi-step writes.** If a write touches two tables, wrap it.
- **No raw string interpolation in SQL.** Always use `?` placeholders: `db.prepare('SELECT * FROM users WHERE id = ?').get(id)`.
- **Soft delete by default.** Add `deleted_at DATETIME DEFAULT NULL` to user-facing tables. Filter in base queries.
- **Indexes on foreign keys and frequently queried columns.** Add in the same migration as the column.

### Table Naming

- Tables: **plural snake_case** — `users`, `post_comments`, `subscription_plans`
- Columns: **snake_case** — `created_at`, `stripe_customer_id`, `is_active`
- Primary key: always `id INTEGER PRIMARY KEY AUTOINCREMENT` unless you have a specific reason otherwise
- No prefix tables (no `tbl_users`)

## Naming Conventions

### Files

| Thing | Convention | Example |
|-------|-----------|---------|
| Page components | `page.tsx` | `app/dashboard/page.tsx` |
| Layout components | `layout.tsx` | `app/dashboard/layout.tsx` |
| Route groups | `(groupname)/` | `app/(auth)/login/page.tsx` |
| API routes | `route.ts` | `app/api/v1/users/route.ts` |
| Server Actions | `actions.ts` | `app/dashboard/actions.ts` |
| UI components | PascalCase | `DataTable.tsx`, `UserAvatar.tsx` |
| Utility files | kebab-case | `db-utils.ts`, `auth-helpers.ts` |

### Variables & Functions

- **React components:** PascalCase (`UserProfile`)
- **Functions & variables:** camelCase (`fetchUserById`, `isAuthenticated`)
- **Constants:** SCREAMING_SNAKE_CASE for config constants (`MAX_RETRY_COUNT`, `DEFAULT_PAGE_SIZE`)
- **TypeScript types/interfaces:** PascalCase, suffix with `Type` only if ambiguous (`UserType`, `CreateUserInput`)

## Component Patterns

### Server vs Client Components

- **Default to Server Components.** If you need interactivity (useState, useEffect, event handlers), add `'use client'` — but push this to leaf components, not page-level layouts.
- **Data fetching happens in Server Components** or Route Handlers. Never fetch data in a Client Component's `useEffect` for initial render.

### Component File Structure

```tsx
// components/forms/UserLoginForm.tsx
'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { type z } from 'zod';
import { loginSchema } from '@/lib/schemas'; // Zod schema lives in lib
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { FormField, FormLabel, FormMessage } from '@/components/ui/FormField';

// Infer TypeScript type from Zod schema
type FormData = z.infer<typeof loginSchema>;

export function UserLoginForm() {
  const form = useForm<FormData>({ resolver: zodResolver(loginSchema) });

  async function onSubmit(data: FormData) {
    // Call Server Action or API
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      <FormField>
        <FormLabel>Email</FormLabel>
        <Input {...form.register('email')} type="email" />
        <FormMessage>{form.formState.errors.email?.message}</FormMessage>
      </FormField>
      {/* ... */}
    </form>
  );
}
```

### What We Do

- **Colocate Zod schemas with their domain** — `lib/schemas/user.ts` exports `loginSchema`, `registerSchema`, `updateUserSchema`
- **Use Server Actions for form mutations** — define `async function` in `actions.ts`, call with `startTransition`
- **Handle errors at the boundary** — show user-friendly messages; never expose raw error strings
- **Skeleton loaders for async data** — use `React.suspense` with a `Skeleton` component

### What We Don't Do (and Why)

| Anti-Pattern | Why | Instead |
|---|---|---|
| Fetching in Client `useEffect` for initial data | Delays render, exposes data to client JS, hurts SEO | Server Components + `fetch` with `{ cache: 'no-store' }` |
| CSS Modules for global styles | Namespace collision is subtle, hard to debug | Tailwind utility classes + CSS variables |
| Mutating state directly | Harder to trace, breaks time-travel debugging | `useReducer` or functional `setState` |
| `any` types | Bypasses TypeScript safety, spreads type errors | `unknown` + type narrowing, or Zod `z.infer` |
| Console.log in production | Clutters server logs, no structured alerting | Use `lib/logger.ts` (pino or winston) |
| Storing secrets in `.env` (not `.env.local`) | `.env` gets committed; `.env.local` is gitignored by default | `.env.local` for all secrets |

## Dev Commands

```bash
# Install dependencies
npm install

# Run database migrations
npx tsx scripts/migrate.ts

# Start dev server (http://localhost:3000)
npm run dev

# Run type checking
npm run type-check   # or: npx tsc --noEmit

# Run linter
npm run lint

# Run tests
npm run test

# Build for production
npm run build
```

## Environment Variables

Required in `.env.local`:

```
DATABASE_URL=./data/app.db
NEXTAUTH_SECRET=<generate with: openssl rand -base64 32>
NEXTAUTH_URL=http://localhost:3000
```

## Patterns to Follow

### Error Handling

```typescript
// API Route Handler pattern
export async function POST(req: Request) {
  try {
    const body = await req.json();
    const validated = createUserSchema.parse(body);
    const user = await createUser(validated);
    return Response.json({ data: user }, { status: 201 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return Response.json({ errors: error.errors }, { status: 400 });
    }
    console.error('[createUser]', error);
    return Response.json({ error: 'Internal server error' }, { status: 500 });
  }
}
```

### Database Query Pattern

```typescript
// lib/db.ts
import Database from 'better-sqlite3';
import { join } from 'path';

const DB_PATH = process.env.DATABASE_URL ?? './data/app.db';

let _db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!_db) {
    _db = new Database(DB_PATH);
    _db.pragma('journal_mode = WAL');
    _db.pragma('foreign_keys = ON');
  }
  return _db;
}

// Usage in queries (always with ? placeholders)
const user = getDb().prepare('SELECT * FROM users WHERE id = ?').get(userId);
```

## What We Don't Do (Summary)

1. **No Pages Router** — App Router only
2. **No ORM** — raw SQLite with prepared statements
3. **No Prisma/TypeORM/Drizzle** — adds compile-time overhead for marginal DX gain on a single DB
4. **No `DELETE FROM table` without WHERE** — soft delete only
5. **No `any` types** — Zod inference for all external data
6. **No client-side initial data fetching** — Server Components for all initial data
7. **No CSS Modules for shared styles** — Tailwind + CSS variables
8. **No secrets in `.env`** — `.env.local` only
9. **No global mutable singletons** — dependency injection via module-level `let` (like `getDb()`)
10. **No mixing Server/Client logic in one component** — `'use client'` boundary is explicit
