# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Stack & Versions
- **Runtime:** Node.js 20+ (LTS)
- **Framework:** Next.js 15 App Router (stable, not canary)
- **Database:** SQLite via better-sqlite3 (production) / Turso (edge)
- **ORM:** Drizzle ORM (not Prisma — lighter, sqlite-native)
- **Auth:** NextAuth.js v5 (Auth.js) with credentials + OAuth providers
- **UI:** Tailwind CSS 4 + shadcn/ui
- **TypeScript:** strict mode enabled
- **Package manager:** pnpm (not npm or yarn)

## Folder Structure
```
src/
├── app/           # App Router pages & API routes
│   ├── (auth)/    # Auth-related pages (login, register)
│   ├── (dashboard)/  # Protected dashboard pages
│   └── api/       # API route handlers
├── components/    # Shared React components
│   ├── ui/       # shadcn/ui components (do not edit directly)
│   └── forms/    # Form components with react-hook-form
├── db/           # Database related code
│   ├── schema/   # Drizzle schema definitions
│   └── queries/  # Database query functions (no raw SQL outside here)
├── lib/          # Utility functions and shared logic
│   ├── auth.ts   # Auth.js configuration
│   └── utils.ts  # General utilities
└── types/        # Shared TypeScript type definitions
```

## Naming Conventions
- **Files:** kebab-case (`user-profile.tsx`, `api-keys.ts`)
- **Components:** PascalCase (`UserProfile.tsx`)
- **Functions:** camelCase (`fetchUserData()`)
- **Database tables:** snake_case (`user_sessions`)
- **Database columns:** snake_case (`created_at`, `updated_at`)
- **API routes:** kebab-case (`/api/user/profile`)
- **Environment variables:** UPPER_SNAKE_CASE (`DATABASE_URL`)

## SQL / Migration Conventions
- **All migrations via Drizzle Kit** (`drizzle-kit push` for dev, `drizzle-kit generate` then `drizzle-kit migrate` for prod)
- **No raw SQL migrations** — use Drizzle schema files only
- **Every table must have:** `id` (integer primary key), `created_at` (text, ISO 8601), `updated_at` (text, ISO 8601)
- **Soft deletes preferred** — add `deleted_at` column instead of DELETE
- **Foreign keys** — use Drizzle relations, not raw SQL constraints
- **Indexes** — add for columns used in WHERE, JOIN, ORDER BY

## Dev Commands
```bash
pnpm dev          # Start dev server (localhost:3000)
pnpm build        # Production build
pnpm lint         # Run ESLint
pnpm test         # Run Vitest
pnpm db:push      # Push schema changes to local DB
pnpm db:generate  # Generate migration files
pnpm db:migrate   # Apply migrations to production
pnpm db:studio    # Open Drizzle Studio (GUI DB viewer)
```

## Component Patterns
- **Server components by default** — only add 'use client' when needed
- **Form handling:** react-hook-form + zod validation
- **Data fetching:** server components with async/await (no useEffect for data fetching)
- **Loading states:** use Next.js loading.tsx and Suspense boundaries
- **Error handling:** error.tsx pages per route segment
- **API routes:** return `NextResponse` with consistent error format: `{ error: string, code: number }`

## What We Don't Do (And Why)
- **No Redux/Zustand** — Next.js Server Components + URL state handle 95% of cases; unnecessary complexity
- **No raw SQL outside db/queries/** — keeps migration safety and type safety
- **No barrel exports** (`index.ts` that re-exports everything) — causes circular deps and slow builds
- **No `any` type** — use `unknown` and type guards instead
- **No client-side data fetching for initial page load** — use server components
- **No hardcoded secrets** — use `NEXT_PUBLIC_*` prefix ONLY for client-safe values

## Anti-Patterns to Avoid
- ❌ Importing server-only code (db, tokens) into client components
- ❌ Fetching the same data in multiple places without caching
- ❌ Putting business logic in API route handlers (extract to lib/)
- ❌ Using `useEffect` + `useState` when server component + searchParams works
- ❌ Committing without running `pnpm lint` first
