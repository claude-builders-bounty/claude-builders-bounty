# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Stack & Versions

- **Framework**: Next.js 15 (App Router, RSC-first)
- **Database**: SQLite via better-sqlite3 (local) or Turso (production), using Drizzle ORM
- **Language**: TypeScript (strict mode)
- **Package Manager**: pnpm
- **Auth**: NextAuth.js v5 (Auth.js)
- **UI**: shadcn/ui + Tailwind CSS v4
- **Validation**: Zod (shared between server & client)
- **Testing**: Vitest + Playwright

## Folder Structure

```
src/
  app/              # App Router pages & API routes
    (auth)/         # Auth-related pages (login, signup)
    (dashboard)/    # Authenticated dashboard pages
    api/            # API route handlers
  components/
    ui/             # shadcn/ui primitives
    forms/          # Form components (react-hook-form)
    layout/         # Shell, sidebar, nav components
  db/
    schema/         # Drizzle schema definitions
    migrations/     # Auto-generated migrations
    queries/        # Reusable query functions
    seed.ts         # Development seed data
  lib/
    auth.ts         # NextAuth config
    db.ts           # DB client singleton
    utils.ts        # Shared utilities (cn, formatDate, etc.)
  features/         # Feature modules (billing, teams, etc.)
  types/            # Shared TypeScript types
  actions/          # Server Actions
```

## Database & Migration Conventions

### DO
- Define ALL schemas in `src/db/schema/` one file per domain
- Use Drizzle `push` during development, `generate` + `migrate` for production
- Add `createdAt` and `updatedAt` timestamps to every table
- Use `text` for IDs (cuid2 or nanoid), never auto-increment integers
- Wrap multi-table operations in Drizzle transactions
- Name foreign keys explicitly: `userId` not `user_id` (camelCase)

### DON'T
- Never write raw SQL migrations — always use Drizzle
- Never store secrets or tokens in the database unencrypted
- Never delete migration files — create new ones to reverse, never modify existing

## Component Patterns

### DO
- Server Components by default, Client Components only when you need interactivity
- Use `"use client"` minimally — extract interactive parts into isolated components
- Fetch data in Server Components and pass down as props
- Use React Server Actions for form mutations (no exposed API routes for CRUD)
- Use `Suspense` boundaries for streaming and loading states
- Colocate component CSS with Tailwind utility classes

### DON'T
- Don't fetch data in Client Components unless absolutely necessary
- Don't use `useEffect` for data fetching — use Server Components + SearchParams
- Don't create wrapper components around shadcn/ui without good reason
- Don't mix Pages Router and App Router patterns

## Auth Conventions

- Use NextAuth.js middleware for route protection
- Session data: userId, email, role — nothing else in the JWT
- Database sessions via the Auth.js SQLite adapter
- Server Actions check `auth()` at the top, redirect on unauthenticated
- Use middleware.ts for route-level auth checks, not per-page

## API Route Rules

- Only create API routes when you need webhooks or external service callbacks
- All internal mutations go through Server Actions
- All API routes validate input with Zod before processing
- Return consistent `{ data, error }` shape from all routes
- Use Next.js revalidatePath/revalidateTag for cache invalidation, not manual headers

## Dev Commands

```bash
pnpm dev          # Start dev server
pnpm db:push      # Push schema changes to local DB
pnpm db:generate  # Generate migration files
pnpm db:migrate   # Run pending migrations
pnpm db:seed      # Seed development data
pnpm test         # Run Vitest
pnpm test:e2e     # Run Playwright
pnpm lint         # ESLint + Prettier check
pnpm typecheck    # tsc --noEmit
```

## Anti-patterns to Avoid

| Anti-pattern | Why |
|---|---|
| Using `fetch` in `useEffect` | Breaks RSC streaming, no caching, waterfall requests |
| Storing binary files in SQLite | Use S3/R2 for file uploads and media |
| Mixing ORM styles | Pick Drizzle or Prisma, not both |
| Running migrations on every app startup | Use CI migration step, never app init |
| Over-abstracting before 3 occurrences | Premature abstraction makes refactoring harder |
| Ignoring SQLite WAL mode | Always enable WAL for concurrent reads in production |
| Global catch-all API routes | Keep API routes focused — one route, one responsibility |
