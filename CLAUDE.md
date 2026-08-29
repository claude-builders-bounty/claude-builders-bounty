 # CLAUDE.md — Next.js 15 + SQLite SaaS

 ## Stack & Versions
 - **Runtime**: Node.js 20 LTS, TypeScript 5.5+
 - **Framework**: Next.js 15 (App Router only — no Pages Router)
 - **Database**: SQLite via `better-sqlite3` (local/dev) or Turso (prod)
 - **ORM**: Drizzle ORM 0.30+ with `drizzle-kit` for migrations
 - **Styling**: Tailwind CSS 4, shadcn/ui components
 - **Validation**: Zod for all API inputs and env vars
 - **Auth**: Better Auth or Lucia v3 (no NextAuth)

 ## Folder Structure
 ```
 src/
   app/               # App Router routes, layouts, error boundaries
     (auth)/          # Route group for login/register (no layout leak)
     (dashboard)/     # Protected route group with shared layout
     api/             # Route handlers only — no business logic here
   components/        # Reusable UI; co-locate with feature when possible
     ui/              # shadcn primitives (button, input, dialog…)
   db/
     schema.ts        # Single source of truth for tables
     migrate.ts       # Migration runner
     connection.ts    # DB client factory (better-sqlite3 / turso)
   lib/               # Pure utilities, validators, helpers
   features/          # Feature modules (billing, teams, settings…)
     <feature>/
       actions.ts     # Server Actions for this feature
       components.tsx # Feature-specific components
       queries.ts     # Read-only DB queries
       mutations.ts   # Write operations (always in transactions)
 ```

 ## Naming Conventions
 - Files: `kebab-case.ts(x)` for components/utilities, `camelCase.ts` for server actions
 - Components: PascalCase export (`export function UserCard()`)
 - Server Actions: named exports with verb prefix (`createTeam`, `updateBilling`)
 - DB columns: `snake_case`; TS types: `camelCase` via Drizzle aliases
 - Env vars: `NEXT_PUBLIC_` only for client-safe values; everything else is server-only

 ## Database & Migration Rules
 1. **Never edit existing migration files.** Create new ones via `pnpm drizzle-kit generate`.
 2. All tables must have `id text primary key` (nanoid), `created_at`, `updated_at`.
 3. Foreign keys are mandatory; use `onDelete('cascade')` unless soft-delete is explicit.
 4. No raw SQL in application code — use Drizzle query builder exclusively.
 5. Migrations run at deploy time, not at runtime. Fail-fast on migration error.
 6. Seed data lives in `src/db/seed.ts`, never in migrations.

 ## Component Patterns
 - Prefer composition over inheritance; extract sub-components at 80+ lines.
 - Client components (`'use client'`) only when interactivity is required.
 - Data fetching happens in Server Components or Server Actions, never in useEffect.
 - Forms use `react-hook-form` + Zod resolver + Server Action submission.
 - Loading states: use Suspense boundaries with skeleton fallbacks.
 - Error states: use `error.tsx` boundaries, not try/catch in components.

 ## What We Don't Do (And Why)
 - ❌ **No Prisma** — too heavy for SQLite; Drizzle is type-safe and lightweight.
 - ❌ **No tRPC** — Server Actions replace it in App Router with less boilerplate.
 - ❌ **No Redux/Zustand for server state** — use React Query/SWR only for client-cached data.
 - ❌ **No barrel exports (`index.ts`)** — they break tree-shaking and slow down IDEs.
 - ❌ **No `any` types** — use `unknown` + Zod validation at boundaries.
 - ❌ **No inline styles** — Tailwind classes only; extend theme if needed.
 - ❌ **No direct `fetch()` in components** — wrap in cached functions or Server Actions.
 - ❌ **No environment variable access without Zod parsing** — fail at startup, not at runtime.

 ## Dev Commands
 ```bash
 pnpm dev              # Start dev server (Turbopack)
 pnpm build            # Production build
 pnpm db:generate      # Generate new migration from schema changes
 pnpm db:migrate       # Apply pending migrations
 pnpm db:studio        # Open Drizzle Studio for DB inspection
 pnpm lint             # ESLint + Prettier check
 pnpm test             # Vitest (unit + integration)
 ```

 ## Anti-Patterns to Avoid
 - Putting business logic in route handlers → move to `features/<feat>/actions.ts`
 - Fetching data in client components → lift to parent Server Component
 - Using `process.env` directly → parse with Zod in `src/lib/env.ts`
 - Committing `.db` files → add to `.gitignore`; use seeds for reproducible state
 - Ignoring TypeScript strict mode → enable `strict: true` in tsconfig
