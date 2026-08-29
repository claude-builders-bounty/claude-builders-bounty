 # CLAUDE.md — Next.js 15 + SQLite SaaS
 
 ## Stack & Versions
 - **Runtime**: Node.js 20 LTS (ESM only)
 - **Framework**: Next.js 15 App Router (`app/` directory, no `pages/`)
 - **Database**: SQLite via `better-sqlite3` (synchronous, zero-config, file-based)
 - **ORM**: Drizzle ORM with `drizzle-orm/better-sqlite3` driver
 - **Styling**: Tailwind CSS 4 + shadcn/ui components
 - **Validation**: Zod for all API inputs and env vars
 - **Auth**: lucia-auth with SQLite session adapter
 
 ## Folder Structure
 ```
 app/
   (auth)/          # Auth routes grouped, no layout nesting with main app
   (dashboard)/     # Protected routes, shared dashboard layout
   api/             # Route handlers only, no business logic
   layout.tsx       # Root layout: fonts, metadata, providers
 db/
   schema.ts        # Single source of truth for all tables
   migrate.ts       # Migration runner (drizzle-kit generates SQL)
   seed.ts          # Dev/test seed data
 lib/
   db.ts            # Singleton better-sqlite3 instance + drizzle export
   auth.ts          # Lucia initialization + helpers
   validators.ts    # Shared Zod schemas
   utils.ts         # Pure utility functions
 components/
   ui/              # shadcn primitives (button, input, dialog…)
   forms/           # Form components with react-hook-form + zod
   dashboard/       # Feature-specific composite components
 ```
 
 ## Database & Migration Rules
 - **Never** write raw SQL in route handlers or components. Use Drizzle queries only.
 - All schema changes go through `drizzle-kit generate` → review SQL → `drizzle-kit migrate`.
 - No `ALTER TABLE DROP COLUMN` in production migrations. Deprecate first, remove in next release.
 - Every table must have `id TEXT PRIMARY KEY` (nanoid), `createdAt INTEGER NOT NULL`, `updatedAt INTEGER NOT NULL`.
 - Foreign keys: always `ON DELETE CASCADE` unless business rule requires restrict. Document exceptions.
 - Indexes: add for every foreign key column and any column used in WHERE/ORDER BY on lists >100 rows.
 - Use `INTEGER` for timestamps (Unix ms). Never store Date objects or ISO strings.
 - Connection: single `better-sqlite3` instance in `lib/db.ts`. Do not create new connections per request.
 - WAL mode enabled at startup: `PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000;`
 
 ## Component Patterns
 - Server Components by default. Add `"use client"` only when interactivity is required.
 - Data fetching: server components call Drizzle directly. No API routes for internal data reads.
 - Mutations: Server Actions for form submissions. Validate with Zod before DB write. Return typed result or throw.
 - Forms: `react-hook-form` + `@hookform/resolvers/zod`. Never trust client-side validation alone.
 - Loading states: use `loading.tsx` files and Suspense boundaries. No spinners in components.
 - Error handling: `error.tsx` boundaries per route segment. Log errors server-side, show generic message to user.
 - Lists: paginate server-side with `LIMIT/OFFSET`. Never fetch-all-and-filter-client.
 
 ## What We Don't Do (And Why)
 - ❌ **No Prisma**: adds binary bloat and async overhead for SQLite. better-sqlite3 is sync and faster.
 - ❌ **No tRPC**: unnecessary abstraction layer. Server Actions + route handlers cover all cases.
 - ❌ **No Redis/cache layer**: SQLite WAL handles concurrent reads. Add cache only after profiling proves need.
 - ❌ **No environment variables without Zod validation**: fail fast at startup, not at runtime.
 - ❌ **No inline styles**: Tailwind classes only. Consistency and purgeability.
 - ❌ **No barrel exports (`index.ts`) in `lib/` or `components/`**: kills tree-shaking and slows IDE.
 - ❌ **No `any` types**: strict TypeScript. If typing is hard, the abstraction is wrong.
 - ❌ **No direct `fetch()` to own API routes from server components**: import the function instead. Avoids HTTP overhead.
 - ❌ **No mutations in GET requests**: idempotent reads only. Side effects go in POST/PATCH/DELETE or Server Actions.
 
 ## Dev Commands
 ```bash
 pnpm dev              # Start dev server (Turbopack)
 pnpm build            # Production build
 pnpm db:generate      # Generate migration from schema changes
 pnpm db:migrate       # Apply pending migrations
 pnpm db:seed          # Seed development data
 pnpm db:studio        # Open Drizzle Studio for DB inspection
 pnpm lint             # ESLint + type check
 pnpm test             # Vitest (unit + integration)
 ```
 
 ## Naming Conventions
 - Files: kebab-case (`user-profile.tsx`, `create-invoice.ts`)
 - Components: PascalCase export, kebab-case file (`UserProfile` in `user-profile.tsx`)
 - DB columns: camelCase in schema, snake_case in SQL (Drizzle handles mapping)
 - Env vars: UPPER_SNAKE_CASE, prefixed (`DB_PATH`, `AUTH_SECRET`)
 - Types: PascalCase with descriptive suffix (`InvoiceCreateInput`, `UserSession`)
 - Server Actions: verb-noun (`createInvoice`, `updateUserProfile`)
 
 ## Testing
 - Unit tests for `lib/` utilities: pure functions, no DB.
 - Integration tests for DB operations: use in-memory SQLite (`:memory:`) per test.
 - E2E for critical flows only (auth, payment): Playwright against dev server.
 - Mock nothing that can be tested with real SQLite. It's fast enough.
