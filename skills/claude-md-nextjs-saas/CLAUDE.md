# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions

- **Next.js 15** (App Router, React Server Components)
- **React 19** (Server Actions, `use` hook)
- **TypeScript 5.5+** (strict mode, `noUncheckedIndexedAccess`)
- **SQLite** via `better-sqlite3` (local) or `@libsql/client` (Turso)
- **Drizzle ORM** (type-safe queries, migrations)
- **Tailwind CSS 4** + **shadcn/ui** (Radix primitives)
- **Clerk** or **NextAuth v5** (auth)
- **Zod** (runtime validation, all inputs)
- **Vitest** + **Playwright** (unit + e2e)

## Folder Structure

```
src/
├── app/                    # App Router pages & layouts
│   ├── (auth)/             # Auth group (login, signup)
│   ├── (dashboard)/        # Protected dashboard routes
│   ├── api/                # API routes (webhooks, health)
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Landing page
├── components/
│   ├── ui/                 # shadcn/ui components (don't modify)
│   ├── forms/              # Form components with Zod schemas
│   └── shared/             # Shared client components
├── lib/
│   ├── db/                 # Database config, schema, migrations
│   │   ├── schema.ts       # Drizzle schema definitions
│   │   └── migrations/     # Generated migration files
│   ├── auth/               # Auth helpers, middleware
│   └── utils.ts            # Shared utilities (cn, formatDate, etc.)
├── actions/                # Server Actions (use "use server")
├── hooks/                  # Custom React hooks
└── types/                  # Shared TypeScript types
```

## Naming Conventions

- **Files**: `kebab-case.tsx` for components, `kebab-case.ts` for utilities
- **Components**: `PascalCase` — `UserProfile.tsx`
- **Functions**: `camelCase` — `getUserById()`
- **Constants**: `UPPER_SNAKE_CASE` — `MAX_RETRY_COUNT`
- **Database tables**: `snake_case` plural — `user_profiles`
- **API routes**: `kebab-case` — `app/api/user-profiles/route.ts`

## SQL / Migration Rules

1. **Always use Drizzle ORM** — never raw SQL in application code
2. **Migrations are auto-generated**: `drizzle-kit generate` after schema changes
3. **Every migration must be reversible** — test `up` and `down`
4. **Use `text()` for strings, `integer()` for numbers, `blob()` for JSON**
5. **Timestamps**: `integer({ mode: 'timestamp' })` with `defaultNow()`
6. **Foreign keys**: always add `.references()` with `onDelete: 'cascade'`
7. **Index every column used in WHERE, JOIN, or ORDER BY**
8. **Never use `SELECT *`** — always specify columns

## Component Patterns

1. **Server Components by default** — add `"use client"` only when needed
2. **Data fetching in Server Components** — pass data as props to Client Components
3. **Server Actions for mutations** — always with Zod validation
4. **Error boundaries** — wrap route segments in `error.tsx`
5. **Loading states** — use `loading.tsx` (Suspense boundary)
6. **Forms**: Server Action + `useActionState` + Zod schema
7. **Never expose secrets** to client components — use environment variables with `NEXT_PUBLIC_` prefix only for public values

## What We Don't Do (and Why)

- **No `any` types** — use `unknown` + type guards instead. `any` defeats TypeScript.
- **No inline styles** — Tailwind classes only. Keeps consistency.
- **No `useEffect` for data fetching** — Server Components handle this. `useEffect` is for side effects only.
- **No prop drilling beyond 2 levels** — use Context or composition.
- **No client-side auth checks** — middleware handles redirects. Don't check `useUser()` in components.
- **No `console.log` in production** — use a logger with levels (`lib/logger.ts`).
- **No direct database calls from client** — always go through Server Actions or API routes.

## Dev Commands

```bash
# Development
npm run dev              # Start dev server (Turbopack)
npm run build            # Production build
npm run start            # Start production server

# Database
npm run db:generate      # Generate migration from schema changes
npm run db:migrate       # Run pending migrations
npm run db:studio        # Open Drizzle Studio (local DB viewer)

# Testing
npm run test             # Unit tests (Vitest)
npm run test:e2e         # E2E tests (Playwright)
npm run test:coverage    # Coverage report

# Linting
npm run lint             # ESLint
npm run typecheck        # TypeScript check
```

## Environment Variables

```bash
# Required
DATABASE_URL="file:./local.db"          # Local SQLite (dev)
# or
DATABASE_URL="libsql://your-db.turso.io" # Turso (prod)
DATABASE_AUTH_TOKEN="your-turso-token"

# Auth (Clerk example)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY="pk_..."
CLERK_SECRET_KEY="sk_..."

# Optional
STRIPE_SECRET_KEY="sk_..."
STRIPE_WEBHOOK_SECRET="whsec_..."
```

## Testing Requirements

1. **Every Server Action** must have a unit test (mock DB)
2. **Every API route** must have an integration test
3. **Critical user flows** must have E2E tests (signup, login, checkout)
4. **Minimum 80% coverage** on `lib/` and `actions/`
5. **Test files**: `*.test.ts` next to source, `*.spec.ts` for e2e
