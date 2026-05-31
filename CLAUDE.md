# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> Opinionated guide for Claude Code to understand and work with this SaaS project.

## Stack & Versions

- **Runtime**: Node.js 20+
- **Framework**: Next.js 15 (App Router, `src/` layout)
- **Language**: TypeScript 5.x (strict mode)
- **Database**: SQLite via `better-sqlite3` (dev) / Turso (prod)
- **ORM**: Drizzle ORM
- **Auth**: NextAuth.js v5 (Auth.js)
- **Styling**: Tailwind CSS 4 + `tailwind-merge` for class conflicts
- **Package Manager**: pnpm (never use npm or yarn)
- **Testing**: Vitest + Testing Library

## Folder Structure

```
src/
  app/              # Next.js App Router pages & layouts
    (auth)/         # Auth route group (login, register)
    (dashboard)/    # Protected dashboard routes
    api/            # Route handlers (backend API)
    layout.tsx      # Root layout
    page.tsx        # Home page
  components/       # Shared UI components
    ui/             # Primitive components (Button, Input, Card)
    forms/          # Form components
    layout/         # Layout components (Sidebar, Header)
  lib/              # Core utilities & configurations
    db/             # Database client, schema, migrations
      schema.ts     # Drizzle schema definitions
      migrate.ts    # Migration runner
      client.ts     # DB client singleton
    auth.ts         # NextAuth configuration
    utils.ts        # Shared helpers (cn, formatters)
  hooks/            # Custom React hooks
  middleware.ts     # Auth middleware
  types/            # TypeScript type definitions
drizzle/            # Generated Drizzle migrations
public/             # Static assets
tests/              # Test files (mirrors src/ structure)
```

## Naming Conventions

- **Files**: `kebab-case.tsx` for components, `PascalCase.tsx` only for React component exports
- **Components**: One component per file, named export matches filename
- **Functions**: `camelCase` — verbs first (`getUserById`, `calculateTotal`)
- **DB Tables**: `snake_case` (`user_accounts`, `subscription_plans`)
- **DB Columns**: `snake_case` (`created_at`, `is_active`)
- **Environment Variables**: `UPPER_SNAKE_CASE` with `NEXT_PUBLIC_` prefix for client vars
- **CSS Classes**: Use `cn()` from `lib/utils.ts` — never concatenate strings directly

## SQL / Migration Rules

1. **Every schema change requires a migration file** — never edit `schema.ts` without generating a migration
2. Migration command: `pnpm drizzle-kit generate`
3. Run migrations: `pnpm drizzle-kit migrate`
4. **Always add `created_at` and `updated_at` timestamps** to every new table
5. Use `TEXT` for dates (ISO 8601 strings), not SQLite `DATETIME`
6. Foreign keys must have `ON DELETE CASCADE` or `ON DELETE SET NULL` — never leave dangling references
7. Indexes: Add indexes on all foreign key columns and frequently queried fields
8. **Never use `ALTER TABLE DROP COLUMN` in SQLite** — it is not fully supported; create a new table instead

## Component Patterns

### Server vs Client Components
- **Default to Server Components** — only add `"use client"` when you need:
  - Interactivity (onClick, onChange, state)
  - Browser APIs (localStorage, geolocation)
  - React hooks (useState, useEffect)
- Data fetching: Always use Server Components with `drizzle` directly — never `fetch()` in client components

### Component Structure
```tsx
// src/components/ui/button.tsx
import { cn } from "@/lib/utils"

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost"
  size?: "sm" | "md" | "lg"
}

export function Button({ variant = "primary", size = "md", className, ...props }: ButtonProps) {
  return (
    <button
      className={cn(baseStyles, variantStyles[variant], sizeStyles[size], className)}
      {...props}
    />
  )
}
```

### Form Handling
- Use React Hook Form + Zod for all forms
- Server actions for mutations — never client-side API calls for data changes
- Validation schemas in `lib/validators/` — co-located with the form, not in components

## Dev Commands

```bash
pnpm dev              # Start dev server (port 3000)
pnpm build            # Production build
pnpm start            # Start production server
pnpm lint             # ESLint + Prettier check
pnpm lint:fix         # Auto-fix lint issues
pnpm test             # Run all tests
pnpm test:watch       # Watch mode
pnpm test:coverage    # Coverage report
pnpm drizzle-kit generate  # Generate migration from schema changes
pnpm drizzle-kit migrate   # Run migrations
pnpm drizzle-kit studio    # DB GUI (dev only)
```

## Patterns to Follow

1. **Colocate related files** — keep API route, schema, and types in the same feature area
2. **Use `cn()` for all className merging** — `twMerge("bg-white", className)` not template literals
3. **Error boundaries** — wrap every route segment in an `error.tsx` boundary
4. **Loading states** — every `page.tsx` should have a paired `loading.tsx`
5. **Environment validation** — use `zod` to validate `env` at startup in `env.ts`
6. **Redirect after mutation** — use `router.push()` or `revalidatePath()` after server actions
7. **Type-safe DB queries** — always use Drizzle's typed query builder, never raw SQL strings

## Anti-Patterns to Avoid

1. **No `any` types** — use `unknown` and narrow, or define proper interfaces
2. **No `console.log` in production code** — use a proper logger (`pino` or `winston`)
3. **No direct `fetch()` to own API** — call server actions or Drizzle directly in Server Components
4. **No CSS-in-JS or inline styles** — use Tailwind utilities exclusively
5. **No barrel exports (`index.ts`)** — import directly from the source file for tree-shaking
6. **No shared mutable state** — use URL search params or server state, not global variables
7. **No `// @ts-ignore`** — fix the type error or use `// @ts-expect-error` with a reason comment
8. **No API routes for page rendering** — use Server Components to fetch data directly
9. **No `useEffect` for data fetching** — use Server Components or `useSWR`/`react-query` in client components
10. **No hardcoded secrets** — all secrets in `.env.local` (never commit), validated at startup

## What We Don't Do (and Why)

| Don't | Do Instead | Reason |
|-------|-----------|--------|
| Use Prisma | Use Drizzle ORM | Better SQLite support, lighter bundle |
| Use `pages/` router | Use App Router | Better streaming, layouts, Server Components |
| Use Redux/Zustand | Use Server State + URL state | Less boilerplate, better for SaaS |
| Use CSS Modules | Use Tailwind CSS | Faster development, consistent design system |
| Use MongoDB | Use SQLite/Turso | Simpler, zero-config, file-based for dev |
| Use JWT-only auth | Use NextAuth v5 session | Built-in CSRF protection, session management |
| Use REST for mutations | Use Server Actions | Type-safe, progressive enhancement |