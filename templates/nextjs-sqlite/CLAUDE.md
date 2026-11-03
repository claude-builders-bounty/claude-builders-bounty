# CLAUDE.md — Next.js 15 + SQLite (Turso / Drizzle) SaaS Standards

> Opinionated, production-grade instructions for Claude Code on greenfield Next.js 15 App Router + SQLite projects. Every architectural rule in this document carries an explicit technical rationale.

---

## Stack & versions

- **Framework**: Next.js 15.1+ (App Router with Turbopack, React 19)
- **Language**: TypeScript 5.7+ (strict mode, `noImplicitAny: true`, `exactOptionalPropertyTypes: true`)
- **Database Engine**: SQLite 3 via `better-sqlite3` 11.8+ (local development) / `@libsql/client` 0.14+ (Turso edge/cloud replication)
- **ORM & Migrations**: Drizzle ORM 0.38+ with `drizzle-kit`
- **Styling & UI**: Tailwind CSS v4, Radix UI primitives, Lucide React icons
- **Validation**: Zod 3.24+ for all API, Server Action, and environment variable schemas
- **Testing**: Vitest for unit/integration tests, Playwright for end-to-end user flows

---

## Folder structure

```
├── src/
│   ├── app/                      # Next.js 15 App Router
│   │   ├── (auth)/               # Unauthenticated auth routes (login, signup, reset)
│   │   ├── (dashboard)/          # Authenticated app shell and views
│   │   ├── api/                  # Inbound webhooks (Stripe, Resend) & public JSON APIs
│   │   ├── layout.tsx            # Root layout with HTML shell & theme provider
│   │   ├── page.tsx              # Public marketing / root landing page
│   │   ├── loading.tsx           # Global suspense fallback
│   │   └── error.tsx             # Global client error boundary
│   ├── actions/                  # Server Actions (mutations and forms, 'use server')
│   ├── components/               # React components
│   │   ├── ui/                   # Primitive, unstyled design tokens (button, dialog, input)
│   │   └── shared/               # Domain-specific compositions (nav-bar, billing-card)
│   ├── db/                       # Database layer
│   │   ├── index.ts              # SQLite connection pool singleton (WAL + foreign keys)
│   │   ├── schema.ts             # Drizzle table schemas and relation graphs
│   │   └── migrations/           # Generated SQL migration files (immutable in git)
│   ├── lib/                      # Core business logic and third-party SDK clients
│   │   ├── auth.ts               # Session token validation & password hashing
│   │   ├── env.ts                # Validated runtime environment variables via Zod
│   │   └── utils.ts              # Pure helper functions (classNames, currency)
│   └── types/                    # Shared TypeScript interfaces and utility types
├── drizzle.config.ts             # Drizzle kit configuration for schema & migrations
├── next.config.ts                # Next.js configuration (typed config)
└── tsconfig.json                 # Strict TypeScript configuration
```

---

## Dev commands

```bash
# Development & Build
pnpm dev              # Launch local dev server with Turbopack on http://localhost:3000
pnpm build            # Compile production bundle with strict type & lint checking
pnpm start            # Start production server
pnpm lint             # Run ESLint check
pnpm format           # Run Prettier code formatting

# Database Workflows (Drizzle ORM)
pnpm db:generate      # Generate new SQL migration files from src/db/schema.ts
pnpm db:migrate       # Apply pending migrations to the local/remote SQLite database
pnpm db:push          # Push schema changes directly during rapid prototype iterations
pnpm db:studio        # Launch Drizzle Studio web GUI on http://local.drizzle.studio

# Testing & Quality
pnpm test             # Run Vitest unit & integration test suite
pnpm test:e2e         # Execute Playwright end-to-end integration tests
```

---

## SQL / migration conventions

1. **Foreign Keys Enforcement (`PRAGMA foreign_keys = ON;`)**:
   - *Why*: SQLite does not enforce relational integrity or foreign key cascades by default. Every database connection factory **must** run `PRAGMA foreign_keys = ON;` upon initialization.
2. **Write-Ahead Logging (`PRAGMA journal_mode = WAL;`)**:
   - *Why*: Standard rollback journal blocks readers during writes. WAL mode permits concurrent readers without locking the single writer, increasing concurrent web throughput by over 10x.
3. **Integer Millisecond Timestamps**:
   - *Why*: ISO-8601 strings cause subtle timezone comparison bugs and slow down range indexing. Store all timestamps as `integer('created_at', { mode: 'timestamp_ms' })` representing Unix epoch milliseconds.
4. **Parameterized Prepared Statements**:
   - *Why*: String concatenation in SQL exposes the application to fatal SQL injection vulnerabilities and prevents SQLite from caching parsed query bytecodes. Use Drizzle query builders or parameterized `sql` tagged template literals exclusively.
5. **Strict Migration Governance**:
   - *Why*: Manual edits to generated SQL migrations cause schema drift and break replication rollouts. Migrations in `src/db/migrations/` must be generated through `pnpm db:generate` and tested on fresh staging databases.

---

## Component patterns

- **Server Components as Default (RSC)**: Keep components on the server (`page.tsx`, `layout.tsx`, static widgets) to reduce client bundle size, eliminate waterfall client fetches, and preserve secrets.
- **Client Boundaries Only for Interactive Leaves**: Add `'use client'` only at the lowest possible leaf component requiring state (`useState`, `useReducer`), browser events, or window APIs.
- **Server Actions for All Mutations**: Form submissions and mutations must reside in `src/actions/`, declared with `'use server'`, and strictly parse inputs using Zod before performing database writes.
- **Suspense & Streaming**: Wrap slow asynchronous server data fetches in `<Suspense fallback={<Skeleton />}>` rather than blocking the initial HTML streaming of the page.
- **Optimistic UI Updates**: Combine Server Actions with React's `useOptimistic` hook for instant client updates on latency-sensitive actions (e.g. toggling bookmarks or completing tasks).

---

## What we don't do (and why)

- ❌ **No `useEffect` data fetching**:
  - *Why*: Client-side fetching in `useEffect` creates severe network waterfalls, layout shifts, uncacheable requests, and bloats client JS. Fetch data directly in React Server Components or Route Handlers.
- ❌ **No `db:push` in production**:
  - *Why*: `db:push` mutates database schema out-of-band without generating an immutable, trackable migration script. It risks data loss when dropping or renaming columns. Use `pnpm db:migrate` in production CI/CD.
- ❌ **No raw queries without explicit `.limit()`**:
  - *Why*: SQLite loads result rows into process memory. An unconstrained `SELECT * FROM table` on growing production datasets can exhaust Node.js heap memory (`ERR_WORKER_OUT_OF_MEMORY`).
- ❌ **No client-side database credentials**:
  - *Why*: SQLite file paths, encryption keys, and Turso auth tokens must never leak to the browser. Any file importing the database instance must remain strictly server-side.
- ❌ **No `any` types in TypeScript**:
  - *Why*: `any` disables typechecking cascadingly across connected callers, introducing runtime `TypeError: undefined is not a function`. Use explicit types, generics, or `unknown` with Zod type guards.

---

## Naming conventions

- **Files & Directories**: Kebab-case (`user-profile.tsx`, `invoice-table.tsx`, `auth-guard.ts`).
- **Components**: PascalCase matching the file concept (`UserProfile`, `InvoiceTable`).
- **Server Actions**: CamelCase ending with `Action` (`createTeamAction`, `updateBillingAction`).
- **Database Tables**: Snake_case plural (`users`, `organizations`, `audit_logs`).
- **Database Columns**: Snake_case (`user_id`, `created_at`, `stripe_customer_id`).
