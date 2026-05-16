# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions

- **Next.js**: 15.x (App Router)
- **React**: 19.x
- **SQLite**: better-sqlite3 (sync) or @libsql/client (Turso)
- **Node.js**: 20.x LTS
- **Package Manager**: npm (no bun/yarn/pnpm)

## Project Structure

```
/
├── src/
│   ├── app/              # Next.js App Router pages
│   │   ├── (auth)/       # Auth-related routes (login, register, etc.)
│   │   ├── (dashboard)/  # Protected dashboard routes
│   │   ├── api/          # API routes
│   │   └── layout.tsx    # Root layout
│   ├── components/       # React components
│   │   ├── ui/           # Shadcn/ui primitives only
│   │   └── features/     # Feature-specific components
│   ├── lib/
│   │   ├── db.ts         # SQLite connection singleton
│   │   ├── migrations/   # DB migration files
│   │   └── auth.ts       # Auth utilities
│   └── types/            # TypeScript types
├── migrations/           # SQL migration files
├── public/               # Static assets
└── scripts/              # Dev scripts (seed, migrate, etc.)
```

## SQL / Migration Conventions

### Always Use Transactions

```sql
BEGIN;
-- your changes
COMMIT;
```

### Migration File Naming

```
YYYY-MM-DD-HHMMSS_description.sql
```

Example: `2025-05-13-143000_add_users_table.sql`

### Column Naming

- **Tables**: plural, snake_case (e.g., `users`, `post_comments`)
- **Columns**: snake_case (e.g., `created_at`, `user_id`)
- **Primary Keys**: `id` (INTEGER PRIMARY KEY)
- **Foreign Keys**: `{table_singular}_id` (e.g., `user_id`)
- **Timestamps**: `created_at`, `updated_at` (Unix timestamps)

### What We Don't Do

❌ NO `ALTER TABLE` in migrations — always create new tables
❌ NO `DROP TABLE` in migrations — create new tables instead
❌ NO `SELECT *` — always specify columns
❌ NO string concatenation in SQL — use parameterized queries
❌ NO `DATETIME('now')` — use Unix timestamps (Date.now() / 1000)

## Component Patterns

### File Naming

- **Pages**: `kebab-case/page.tsx` (e.g., `settings/page.tsx`)
- **Components**: `PascalCase.tsx` (e.g., `UserProfile.tsx`)
- **Utilities**: `camelCase.ts` (e.g., `formatCurrency.ts`)

### Component Structure

```tsx
// DO: Colocate small components
// DON'T: Create tiny components that are never reused

// DO: Use explicit prop types
interface Props {
  userId: string;
  name: string;
}

// DON'T: Use 'any' or vague types
```

### State Management

1. **Server Components** by default — no 'use client'
2. **URL state** for shareable filters/search
3. **useState** only when component-level state is needed
4. **Zustand** for global client state (auth, theme)

## Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Variables | camelCase | `userId`, `isLoading` |
| Functions | camelCase | `getUser()`, `createPost()` |
| Constants | SCREAMING_SNAKE | `MAX_RETRY_COUNT` |
| Types/Interfaces | PascalCase | `UserProfile`, `ApiResponse` |
| CSS Classes | kebab-case | `user-profile`, `btn-primary` |

## API Routes

```
/api/{resource}          # GET (list), POST (create)
/api/{resource}/{id}    # GET (one), PATCH (update), DELETE
```

### Response Format

```typescript
// Success
{ "data": { ... } }

// Error
{ "error": { "code": "NOT_FOUND", "message": "User not found" } }
```

## What We Don't Do

🚫 **No Tailwind** — we use CSS Modules with design tokens
🚫 **No SSR for authenticated pages** — use 'use client' with auth check
🚫 **No direct SQLite writes in API routes** — use repository pattern
🚫 **No environment variables in client code** — only NEXT_PUBLIC_ vars
🚫 **No console.log in production** — use structured logging

## Dev Commands

```bash
npm run dev          # Start development server
npm run build         # Production build
npm run db:migrate    # Run pending migrations
npm run db:seed       # Seed database with test data
npm run db:studio     # Open SQLite studio
```

## Anti-Patterns to Avoid

1. **Not validating user input** — always sanitize
2. **Not handling errors** — every async function needs try/catch
3. **Not using indexes** — add indexes for foreign keys and frequently queried columns
4. **Not using transactions** — multi-step DB operations must be atomic
5. **Not handling concurrent writes** — use optimistic locking or transactions
