# CLAUDE.md — Next.js 15 + SQLite SaaS Template

## Stack
- **Framework:** Next.js 15 (App Router), React 19
- **Database:** SQLite via better-sqlite3 (dev) / Turso (prod)
- **ORM:** Drizzle ORM
- **Auth:** NextAuth.js v5
- **Styling:** Tailwind CSS v4 + shadcn/ui
- **Language:** TypeScript (strict mode)

## Project Structure
```
src/
  app/          # App Router pages & API routes
  components/   # Shared React components
  db/           # Drizzle schema, migrations, queries
  lib/          # Utility functions, helpers
  actions/      # Server Actions
types/          # Shared TypeScript types
```

## Naming Conventions
- Components: PascalCase (`UserProfile.tsx`)
- Utils/hooks: camelCase (`useDebounce.ts`)
- DB tables: snake_case (`user_sessions`)
- API routes: kebab-case (`/api/stripe-webhook`)
- Files: match default export name

## Database Rules
- All schema in `src/db/schema/`
- Migrations are immutable — never edit after creation
- Every table needs `id` (integer PK) + `created_at` + `updated_at`
- Soft deletes: add `deleted_at` column, never `DELETE FROM`
- Queries go in `src/db/queries/`, not inline in components

## Component Patterns
- Server components by default; client only when needed
- Forms: use Server Actions + `useActionState` for loading states
- Data fetching: use React Server Components, not useEffect
- Props: use `interface` not `type` for component props

## What We Don't Do
- No `any` types (use `unknown` and narrow)
- No direct database access from client components
- No `useEffect` for data fetching
- No prop drilling (use Server Components composition)
- No barrel exports (hurts tree-shaking)
