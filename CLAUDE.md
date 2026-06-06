# CLAUDE.md — Next.js 15 + SQLite SaaS Starter

> Opinionated, production-ready context file. Drop into any Next.js + SQLite project.

## Stack & Versions
- **Runtime**: Node.js 22 LTS, pnpm 9
- **Framework**: Next.js 15 (App Router), React 19
- **Language**: TypeScript 5.7+ (strict mode, `noUncheckedIndexedAccess: true`)
- **Styling**: Tailwind CSS v4, `cn()` from `clsx` + `tailwind-merge`
- **Database**: SQLite via `better-sqlite3` (local dev) or Turso (production)
- **ORM**: Drizzle ORM — all schema, migrations, and queries
- **Auth**: NextAuth.js v5 (Credentials + OAuth), session in JWT
- **Validation**: Zod — shared types between client and server
- **Testing**: Vitest (unit), Playwright (e2e)
- **CI/CD**: GitHub Actions, deploy to Vercel

## Folder Structure
```
src/
  app/                    # Next.js App Router pages & API
    (auth)/               # Auth route group (login, register)
    (dashboard)/          # Authenticated route group
    api/                  # API route handlers
  components/
    ui/                   # shadcn/ui primitives (Button, Input, Card, Dialog...)
    forms/                # Form components with react-hook-form + zod
    layouts/              # Shell, Sidebar, Header
  lib/
    db/
      schema.ts           # Drizzle schema definitions
      index.ts            # DB connection singleton
      migrations/         # Auto-generated SQL migrations
    auth.ts               # NextAuth config
    auth-client.ts        # Client-side auth helpers
    validations.ts        # Shared Zod schemas
    utils.ts              # cn(), formatters, helpers
  server/
    actions.ts            # Server Actions (use server)
    queries.ts            # DB query functions
  hooks/                  # Custom React hooks
  types/                  # Shared TypeScript types
```

## SQL / Migration Conventions
- **Always** use Drizzle for schema changes: edit `src/lib/db/schema.ts`, then `pnpm db:generate && pnpm db:migrate`
- **Never** write raw SQL migrations by hand — Drizzle generates them
- Table names: `snake_case`, plural (e.g., `users`, `api_keys`, `team_members`)
- Column names: `snake_case` (e.g., `created_at`, `updated_at`, `user_id`)
- Every table must have: `id` (text/primary), `created_at` (text, default `datetime('now')`), `updated_at` (text, default `datetime('now')`)
- Foreign keys: always define via Drizzle `references()` — never raw
- Indexes: add explicit indexes on `user_id`, `team_id`, and any column used in WHERE clauses
- Soft deletes preferred: `deleted_at` column instead of hard DELETE
- Seed files go in `src/lib/db/seed.ts`, run via `pnpm db:seed`

## Component Patterns
- **Server-first**: prefer Server Components; `use client` only when you need interactivity
- **Data fetching**: co-locate queries in `server/queries.ts` for reusability
- **Forms**: use `react-hook-form` + `@hookform/resolvers/zod`, always validate on both client AND server
- **Loading states**: use `loading.tsx` per route segment; use `Suspense` for granular loading
- **Error boundaries**: `error.tsx` per route segment; wrap data-dependent components
- **Empty states**: always render an empty state component before mapping over arrays
- **Optimistic updates**: use `useOptimistic` for immediate UI feedback, revalidate via `revalidatePath`

## Commands
```bash
pnpm dev              # Start dev server on port 3000
pnpm build            # Production build
pnpm start            # Start production server
pnpm lint             # ESLint + Prettier check
pnpm lint:fix         # Auto-fix
pnpm typecheck        # tsc --noEmit
pnpm test             # Vitest unit tests
pnpm test:e2e         # Playwright e2e tests
pnpm db:generate      # Generate Drizzle migrations
pnpm db:migrate       # Run pending migrations
pnpm db:push          # Push schema directly (dev only, no migration file)
pnpm db:studio        # Open Drizzle Studio at localhost:4983
pnpm db:seed          # Seed database with test data
```

## What We Do
- Keep route handlers thin — extract logic to `server/queries.ts` or service functions
- Use Zod schemas for every API input — never trust `req.body` directly
- Use `revalidatePath` after mutations, not `router.refresh` in server components
- Prefer Tailwind utility classes over custom CSS — `@layer` for shared patterns only
- Log structured JSON to stdout — never `console.log` objects directly
- Return typed responses from server actions: `{ success: true, data } | { success: false, error: string }`

## What We Don't Do (and Why)
- **No ORM bypass**: never write raw SQL in route handlers — all queries must go through Drizzle or `server/queries.ts`. Ensures single source of truth for DB access.
- **No client-side auth checks**: auth gates live in middleware and server components — never rely on `useSession` alone for protection. Client state can be spoofed.
- **No inline API routes as server actions for public endpoints**: use `route.ts` files for public APIs, server actions for authenticated mutations. Clear contract boundaries.
- **No environment variables on the client without `NEXT_PUBLIC_`**: Vercel strips everything else. Wrap in Zod validation before use.
- **No `any` types**: use `unknown` and narrow with Zod or type guards. `any` defeats the purpose of TypeScript.
- **No `useEffect` for data fetching**: use Server Components or SWR/React Query on the client. useEffect data fetching causes waterfall requests.
- **No `dangerouslySetInnerHTML` without sanitization**: always run through DOMPurify first.
