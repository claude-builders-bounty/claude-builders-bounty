# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions
- Next.js 15 (App Router), React 19, TypeScript 5.7+
- SQLite via better-sqlite3 (dev) → Turso/libsql (prod), Drizzle ORM
- Tailwind CSS v4, shadcn/ui (new-york style)
- Zod for runtime validation, next-safe-action for server actions
- Vitest + React Testing Library, Playwright for E2E
- Biome for lint/format (no Prettier, no ESLint)

## Folder Structure
`
src/
  app/          # App Router — routes only, no business logic
  components/   # Shared UI — shadcn primitives + composed features
  features/     # Domain modules: auth/, billing/, dashboard/
  lib/          # Shared utilities, DB client, env schema
  server/       # Server-only code: TRPC routers, background jobs
drizzle/        # Migration files, schema definitions
`

## Rules

### SQL / Migrations
- Every migration gets a *.sql file in drizzle/. Drizzle generates.
- Never alter a merged migration — create a new one.
- Foreign keys enforced at DB level, never rely on app-level only.
- Soft-delete: add deleted_at, never hard-delete user data.
- Seed data via drizzle/seed.ts with idempotent upserts.

### Component Patterns
- Server Components by default. Client Components only when needed.
- Isolate client interactivity: one boundary per feature, not per button.
- Form: react-hook-form + zod resolver + next-safe-action. No useActionState.
- Data fetch: server component fetches at top, passes via props. No useEffect-fetch.
- Loading states: Suspense boundary + loading.tsx, not isSpinning state.

### Dev Commands
`
npm run dev        # local dev (Turso remote or local SQLite)
npm run build      # production build
npm run check      # Biome lint + TypeScript check
npm test           # Vitest unit tests
npm run test:e2e   # Playwright against local build
npm run db:push    # Drizzle push to dev DB
npm run db:migrate # Apply migrations
npm run db:studio  # Drizzle Studio GUI
`

## What We Don't Do (and why)

- **No ORM raw queries in components** — DB access through server layer only. Prevents leaking credentials to client bundles.
- **No API routes folder** — Server Actions + tRPC. /api/ route handlers are legacy.
- **No global state** — URL searchParams for filters, server state via TanStack Query on client boundaries only.
- **No auth on the client** — Cookies + middleware, never localStorage tokens. XSS-resistant.
- **No barrel exports (index.ts)** — Turbopack tree-shakes better with direct imports.
- **No env on the client unless NEXT_PUBLIC_ prefix** — enforced by Zod schema validation at startup.