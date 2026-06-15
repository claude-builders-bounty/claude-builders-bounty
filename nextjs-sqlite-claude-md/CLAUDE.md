# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions
- Next.js 15 App Router (React 19, Server Components by default)
- SQLite via `better-sqlite3` (local dev) or Turso `@libsql/client` (prod/edge)
- TypeScript 5.x strict mode
- Tailwind CSS v4 + shadcn/ui (Radix primitives)
- Drizzle ORM for migrations and queries
- Auth via NextAuth.js v5 (Auth.js)
- Zod for validation (shared between client and server)
- Vitest for testing

## Project Structure
```
src/
  app/           # Next.js App Router pages (file-based routing)
  components/    # Shared React components
    ui/          # shadcn/ui primitives (Button, Input, Dialog...)
    forms/       # Form components with react-hook-form + zod
  lib/           # Pure functions, utilities, shared logic
    db/          # Drizzle schema, migrations, query helpers
    auth/        # NextAuth config, callbacks, session helpers
    validators/  # Zod schemas (one file per domain: auth.ts, billing.ts...)
  actions/       # Server Actions (one file per feature)
  hooks/         # Client-side React hooks (useLocalStorage, useDebounce...)
  server/        # Server-only code (never imported from client components)
    queries/     # Database query functions (cached where appropriate)
    mutations/   # Database write operations
  types/         # Shared TypeScript types/interfaces
drizzle/
  schema.ts      # Drizzle schema definitions
  migrations/    # Auto-generated migration files
```

## SQL / Migration Conventions
- **Every schema change gets a migration.** Run `npx drizzle-kit generate` then `npx drizzle-kit migrate`.
- **Never use raw SQL in routes.** All queries live in `src/server/queries/`.
- **Foreign keys are non-optional** except for nullable relations. Always use `onDelete: 'cascade'` or explicit.
- **Timestamps on every table:** `createdAt` (default now), `updatedAt` (auto-update trigger).
- **Soft delete** for user-facing data. Hard delete only for internal/transient records.
- **Migration rollback:** Write a `.sql` downgrade file alongside each migration. Test it before deploying.

## Component Patterns
- **Server Components by default.** Only add `'use client'` when you need state, effects, or browser APIs.
- **Data fetching in Server Components**, not in client hooks. Pass data as props.
- **One component per file.** Exceptions: co-located sub-components used only by the parent (< 50 lines).
- **Props interface exported** and named `{ComponentName}Props`.
- **No inline styles.** Use Tailwind classes or CSS modules for component-specific styles.
- **Forms use react-hook-form + zod resolver.** Validation schema lives in `src/lib/validators/`.

## Server Actions
- **One action file per feature** (e.g., `src/actions/billing.ts`, `src/actions/team.ts`).
- **Always validate input** with Zod at the top of the action.
- **Revalidate paths** after mutations: `revalidatePath('/dashboard')`.
- **Return typed results:** `{ success: true, data: T } | { success: false, error: string }`.
- **Check auth** with `auth()` or `getServerSession()` at the top. Never trust a client-side auth check.

## What We Don't Do (and Why)
- **No API routes** (`/api/...`). Use Server Actions instead — they're type-safe, no CORS, no REST boilerplate.
- **No `useEffect` for data fetching.** That's what Server Components are for.
- **No ORM relationship magic.** Drizzle explicitly joins — it's more code but you always know what SQL runs.
- **No `any` types.** Use `unknown` and narrow with Zod or type guards.
- **No `process.env` in client code.** Use `NEXT_PUBLIC_` prefix or pass env vars through Server Components.
- **No barrel exports from `components/ui/`.** Tree-shaking works better with direct imports.
- **No giant migration files.** If a migration touches > 5 tables, split it.

## Dev Commands
```bash
pnpm dev           # Next.js dev server (Turbopack)
pnpm build         # Production build
pnpm db:generate   # Drizzle: generate migration from schema changes
pnpm db:migrate    # Drizzle: apply pending migrations
pnpm db:studio     # Drizzle Studio (visual DB explorer)
pnpm test          # Vitest (run all)
pnpm test:watch    # Vitest watch mode
pnpm lint          # ESLint + Prettier
pnpm typecheck     # tsc --noEmit
```
