# Claude Code Guide for Next.js + SQLite SaaS

Opinionated, production-ready instructions for Claude Code agents working with this stack.

## Stack & Versions

- **Next.js 15** - App Router (not pages)
- **React 19** - Concurrent features enabled
- **SQLite** - `better-sqlite3` or `Turso` for production
- **TypeScript** - Strict mode, no implicit any
- **Tailwind CSS** - Utility-first styling
- **Zod** - Runtime validation

## Folder Structure

```
/app          # App Router routes (server + client components)
  /[feature]  # Feature folders (colocated)
  /api        # Route handlers
/lib          # Shared utilities, db client, helpers
/components   # Reusable UI components
/hooks          # Custom React hooks
/server         # Server-only files (not imported in client)
/public         # Static assets
/db/migrations  # SQL migration files (sequentially numbered)
/types          # TypeScript type definitions
```

## SQL / Migration Rules

- **All DB changes go through migrations** - never manual SQL
- **Migration naming**: `001_initial.sql`, `002_add_users.sql`
- **Always use transactions** for multi-step migrations
- **Turso**: Use `auth.schemaVersion` to track schema
- **Local SQLite**: Use `PRAGMA user_version` 
- **Never store passwords in plain text** - bcrypt or argon2

## Dev Commands

```bash
# Start dev server
npm run dev

# Run tests
npm run test        # Jest
npm run test:e2e    # Playwright

# Type check
npm run typecheck

# Lint
npm run lint
npm run lint:fix

# Build
npm run build

# DB operations
npm run db:migrate
npm run db:seed
npm run db:studio
```

## Component Patterns

### Server Components First
- Default to Server Components
- Only add `'use client'` when interactivity needed
- Fetch data directly in Server Components

### Form Handling
```tsx
// Always use useActionState for forms
'use client'
const [state, formAction] = useActionState(action, initialState)
```

### Error Boundaries
- Use error.tsx for route-level boundaries
- Never let errors bubble to root

## Anti-Patterns (and Why)

### ❌ Don't: Use client components for data fetching
- **Why**: Kills performance, defeats SSR

### ❌ Don't: Store blobs in SQLite
- **Why**: Use S3 or filesystem, SQLite is for metadata

### ❌ Don't: Put server code in /lib without guard
- **Why**: Gets bundled into client, breaks builds

### ❌ Don't: Use `any` type
- **Why**: Breaks TypeScript's value proposition

## Where to Start

- **New feature**: `/app/[feature]/page.tsx` first
- **New API**: `/app/api/route.ts` with handler
- **New component**: `/components/ui/` for shared, else colocate
- **DB changes**: `/db/migrations/` then `/lib/db.ts`