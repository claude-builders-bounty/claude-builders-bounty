# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack
- **Framework**: Next.js 15 (App Router), React 19, TypeScript 5 (strict)
- **Database**: SQLite via `better-sqlite3` (local dev / single-server) or Turso/libsql (edge/distributed)
- **ORM**: Drizzle ORM — schema-first, type-safe, no codegen step
- **Auth**: Lucia Auth v3 with session cookies (not JWT in localStorage)
- **Styling**: Tailwind CSS v4 + shadcn/ui (Radix primitives)
- **Validation**: Zod — shared types between client and server
- **Payments**: Stripe Checkout + webhooks
- **Email**: Resend (React Email templates)
- **Testing**: Vitest + React Testing Library + Playwright (E2E)
- **Package manager**: pnpm

## Project Structure
```
src/
  app/                  # Next.js App Router (routes, layouts, loading, error)
    (auth)/             # Auth route group — login, register, verify-email
    (dashboard)/        # Protected dashboard group — layout checks session
    api/                # Route handlers (REST or tRPC)
  components/
    ui/                 # shadcn/ui primitives — never edit manually
    forms/              # React Hook Form + Zod validation
    layout/             # Shell, sidebar, header (server components by default)
  db/
    schema.ts           # Drizzle table definitions
    migrations/         # Auto-generated SQL migration files
    index.ts            # DB client singleton
  lib/
    auth.ts             # Lucia config, session helpers
    email.ts            # Resend client + React Email templates
    stripe.ts           # Stripe client + webhook handler
    utils.ts            # cn(), formatDate(), slugify()
  actions/              # Server Actions (useActionState / useOptimistic)
  hooks/                # Client hooks (useAuth, useDebounce, etc.)
  server/               # tRPC routers (if using tRPC)
.env.local              # NEVER commit; use .env.example with dummy values
drizzle.config.ts
tailwind.config.ts
```

## SQL / Migration Conventions

### Rules
- **Every schema change gets a migration.** Run `pnpm db:generate` then `pnpm db:migrate`.
- **Migrations are append-only.** Never edit a committed migration file.
- **No raw SQL in application code.** Use Drizzle query builder. If you must use raw SQL, put it in a named function in `db/queries/` with a comment explaining why it cannot be expressed in Drizzle.
- **Foreign keys** on every relation, with `onDelete: cascade` for child rows where it makes sense.
- **Timestamps**: every table gets `createdAt` and `updatedAt` columns (auto-managed via Drizzle defaults).

### Anti-patterns
- Do NOT call DB directly from a React Server Component — use a Server Action or tRPC procedure.
- Do NOT do DB migrations in CI — migrations always run before deploy.
- Do NOT use `better-sqlite3` directly — always go through `db/index.ts`.

## Component Patterns

### Server Components (default)
- Fetch data directly (no useEffect for data loading).
- Pass data down to client components as props.
- Keep data-fetching functions in `lib/data/` so both RSCs and Server Actions can reuse them.

### Client Components (opt-in)
- Mark with `"use client"` only when you need interactivity, hooks, or browser APIs.
- Extract the interactive part — keep the parent a Server Component.
- Use Server Actions for mutations, not fetch() to API routes.

### Forms
- React Hook Form + `@hookform/resolvers/zod`.
- Define Zod schema in a shared file (`lib/validations/`), reuse type with `z.infer`.
- Show loading state while action is pending (useFormStatus / useOptimistic).

## Dev Commands
| Command | What |
|---|---|
| `pnpm dev` | Start Next.js dev server (Turbopack) |
| `pnpm build` | Production build |
| `pnpm db:studio` | Open Drizzle Studio (GUI) |
| `pnpm db:generate` | Generate migration from schema changes |
| `pnpm db:migrate` | Apply pending migrations |
| `pnpm db:push` | Push schema directly (dev only, no migration file) |
| `pnpm test` | Run Vitest unit tests |
| `pnpm test:e2e` | Run Playwright E2E tests |
| `pnpm lint` | ESLint + Prettier check |
| `pnpm format` | Prettier write |
| `pnpm typecheck` | tsc --noEmit |

## What We Don't Do (And Why)

- **No ORM other than Drizzle.** Prisma adds a codegen step and a runtime binary that complicates edge deployment. Kysely is viable for raw-SQL-first teams but adds overhead for typical SaaS CRUD.
- **No API routes for mutations.** Use Server Actions. They are simpler, typesafe end-to-end, and progressively enhanced.
- **No `any` in TypeScript.** If a type is truly complex, use `unknown` + narrowing, or write a comment with `// TODO: type properly (ticket #X)`.
- **No `useEffect` for data fetching.** It causes waterfall requests and hydration mismatches.
- **No environment variables on the client** without `NEXT_PUBLIC_` prefix. If you need a secret on the client, rethink your architecture.
- **No barrel exports (`index.ts` re-exporting everything).** They break tree-shaking and slow down HMR. Import directly from the file.
- **No inline styles or CSS modules.** Tailwind only. Exceptions: shadcn/ui component overrides in `globals.css` with `@layer base`.
- **No `console.log` in production code.** Use a logger (`lib/logger.ts`) with levels (debug, info, warn, error) that is silenced in production for debug/info.

## File Naming
- **Components**: `PascalCase.tsx` — `SignInForm.tsx`, `UserAvatar.tsx`
- **Utilities / lib**: `kebab-case.ts` — `format-currency.ts`, `validate-email.ts`
- **Pages / routes**: Next.js convention — `page.tsx`, `layout.tsx`, `loading.tsx`
- **Database**: singular table names — `user`, `team`, `subscription` (Drizzle infers plural)

## Auth Patterns
- Session check happens in middleware (`src/middleware.ts`) — redirect to `/login` if unauthenticated.
- Server Components read session via `auth()` from `lib/auth.ts`.
- Client Components use a `useAuth()` hook that calls a Server Action to get the session (safe to call from client since it returns no secrets).
- Never trust `localStorage` or cookies read directly on the client for auth state.