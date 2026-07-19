# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated, production-ready context for Claude Code on Next.js + SQLite projects.

## Stack & Versions

- **Next.js 15** (App Router only, no `pages/`)
- **SQLite** via `better-sqlite3` (local dev) or **Turso** (production)
- **Drizzle ORM** for migrations and queries — no raw SQL in application code
- **Tailwind CSS v4** for styling — no CSS modules, no styled-components
- **TypeScript** strict mode — `noUncheckedIndexedAccess: true`, `exactOptionalPropertyTypes: false`
- **Auth**: NextAuth.js v5 (Auth.js) with credentials + OAuth providers
- **Zod** for all validation (server actions, API routes, form schemas)

## Folder Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/             # Auth pages (login, register)
│   ├── (dashboard)/        # Protected dashboard routes
│   ├── api/                # API route handlers
│   └── layout.tsx          # Root layout
├── components/
│   ├── ui/                 # shadcn/ui primitives (Button, Input, etc.)
│   └── features/           # Feature-specific composites (UserMenu, BillingCard)
├── db/
│   ├── schema.ts           # Drizzle schema definitions
│   ├── migrations/         # Auto-generated migration files
│   └── index.ts            # DB client singleton
├── lib/
│   ├── auth.ts             # NextAuth configuration
│   ├── validations.ts      # Zod schemas (shared between client/server)
│   └── utils.ts            # Pure utility functions
├── server/
│   └── actions/            # Server actions (one file per domain)
└── types/
    └── index.ts            # Shared TypeScript types
```

## SQL / Migration Conventions

- **Table names**: `snake_case`, plural (`users`, `team_members`)
- **Column names**: `snake_case` (`created_at`, `stripe_customer_id`)
- **Primary keys**: always `id` as `text('id').primaryKey().default(crypto.randomUUID())` — never auto-increment integers
- **Timestamps**: every table gets `created_at` and `updated_at` with defaults
- **Soft deletes**: `deleted_at timestamp` — never hard-delete user data
- **Migrations**: run `npx drizzle-kit generate` after schema changes, then `npx drizzle-kit migrate` to apply
- **Never** edit migration files manually. Always regenerate from schema.

**Migration rules:**
1. Add nullable columns first (no default needed)
2. Add NOT NULL columns with a default, then remove default in a second migration
3. Never rename a column — add new, migrate data, drop old
4. Test migrations against a production clone before deploying

## Component Patterns

### Server Components First
- Default to Server Components. Only add `'use client'` when you need interactivity.
- Fetch data directly in Server Components — no useEffect for data fetching.
- Pass data down as props; never lift state higher than needed.

### Client Component Rules
- Keep Client Components as leaf nodes when possible.
- Extract interactive parts into small, focused Client Components.
- Use `useOptimistic` for instant UI updates before server confirmation.

### Form Handling
- Use Server Actions for form submissions (no API routes for forms).
- Validate with Zod in the server action, return `{ error: string }` or `{ success: true }`.
- Client shows loading state via `useFormStatus` and errors via returned state.

## Dev Commands

```bash
pnpm dev              # Start dev server (Turbo mode)
pnpm build            # Production build
pnpm db:generate      # Generate Drizzle migrations
pnpm db:migrate       # Apply migrations
pnpm db:studio        # Open Drizzle Studio (DB GUI)
pnpm lint             # ESLint + Prettier check
pnpm lint:fix         # Auto-fix lint issues
pnpm test             # Run Vitest tests
pnpm typecheck        # TypeScript check (no emit)
```

## Anti-Patterns — What We DONT Do

- **NO `pages/` directory** — everything is App Router
- **NO `any` types** — use `unknown` and narrow with Zod
- **NO raw SQL strings in application code** — use Drizzle query builder
- **NO `useEffect` for data fetching** — use Server Components or SWR/React Query for client fetches
- **NO API routes for forms** — use Server Actions instead
- **NO `process.env` in client code** — prefix with `NEXT_PUBLIC_` or use server-only context
- **NO barrel exports from `components/`** — import directly from `@/components/ui/button` to avoid bundling the entire UI library
- **NO hardcoded URLs** — use environment variables or Next.js `headers()` for dynamic host detection
- **NO `Date.now()` in server code without `server-only` import** — ensures it runs only server-side

## When In Doubt

1. Check if Next.js docs have a pattern for it first
2. Prefer composition over inheritance
3. Keep files under 200 lines — split aggressively
4. One server action file per domain (`users.ts`, `teams.ts`, `billing.ts`)
5. Every PR must include a migration if it touches the schema
