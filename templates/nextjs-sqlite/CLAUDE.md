# CLAUDE.md — Next.js 15 (App Router) + SQLite SaaS Project Guide

This document is the single source of truth for Claude Code when working in this codebase.
Follow all rules, conventions, and architectural boundaries without deviation.

---

## 1. Stack & Versions

- **Framework**: Next.js 15.x (App Router only, React 19)
- **Language**: TypeScript 5.x (Strict mode: `noImplicitAny: true`, `strictNullChecks: true`)
- **Database**: SQLite via `better-sqlite3` (local/Node runtime) or `@libsql/client` (Turso / edge compatible)
- **ORM & Migrations**: Drizzle ORM (`drizzle-orm` + `drizzle-kit`)
- **Styling**: Tailwind CSS v4
- **Schema Validation**: Zod (`zod`)
- **Icons**: Lucide React (`lucide-react`)
- **Package Manager**: `pnpm` (default; use `npm` or `bun` only if explicitly specified)

---

## 2. Project Directory Structure

```text
├── actions/             # Server Actions (mutations, form handlers with Zod validation)
├── app/                 # Next.js App Router (pages, layouts, route handlers)
│   ├── (auth)/          # Route group: login, register, password reset
│   ├── (dashboard)/     # Route group: authenticated app views
│   ├── api/             # Webhooks and external REST endpoints only
│   ├── layout.tsx       # Root layout (fonts, providers)
│   └── page.tsx         # Landing / marketing page
├── components/
│   ├── ui/              # Reusable primitive UI components (buttons, dialogs, inputs)
│   └── dashboard/       # Feature-specific dashboard components
├── db/
│   ├── migrations/      # Drizzle generated SQL migrations (never edit manually)
│   ├── index.ts         # Database client connection and PRAGMA configuration
│   ├── schema.ts        # Database schema definitions and relations
│   └── seed.ts          # Seed data script for local development
├── lib/
│   ├── auth.ts          # Authentication session handling and helpers
│   ├── env.ts           # Type-safe environment variable validation (Zod)
│   └── utils.ts         # Shared pure helper functions (cn, formatters)
└── types/               # Shared cross-domain TypeScript interfaces
```

---

## 3. Development Commands

```bash
# Development
pnpm dev                 # Start Next.js development server on localhost:3000
pnpm build               # Build production Next.js bundle
pnpm start               # Start production server
pnpm lint                # Run ESLint validation
pnpm typecheck           # Run TypeScript compiler check (tsc --noEmit)

# Database & Migrations (Drizzle ORM)
pnpm db:generate         # Generate SQL migration files from schema changes
pnpm db:migrate          # Apply pending migrations to SQLite database
pnpm db:push             # Directly push schema changes (local prototype only)
pnpm db:studio           # Open Drizzle Studio UI to inspect SQLite data
pnpm db:seed             # Run database seed script (ts-node or tsx db/seed.ts)

# Testing
pnpm test                # Run test suite (vitest / jest)
pnpm test:watch          # Run tests in watch mode
```

---

## 4. SQLite & Migration Conventions

1. **Mandatory PRAGMA Settings**:
   Every SQLite connection instance in `db/index.ts` MUST enforce these pragmas immediately on initialization:
   ```typescript
   sqlite.pragma("journal_mode = WAL");      // Write-Ahead Logging for high concurrency
   sqlite.pragma("foreign_keys = ON");       // Enforce relational integrity
   sqlite.pragma("busy_timeout = 5000");     // Prevent lock errors under concurrent writes
   sqlite.pragma("synchronous = NORMAL");    // Optimal durability/throughput balance in WAL mode
   ```

2. **Migration Rules**:
   - Always edit `db/schema.ts` first, then run `pnpm db:generate`.
   - Never write raw `ALTER TABLE` migrations manually. Let `drizzle-kit` track schema state.
   - Run `pnpm db:migrate` in deployment pipelines prior to app launch.
   - For cloud/distributed deployment (e.g. Vercel, Fly.io), use `@libsql/client` pointing to Turso or an attached persistent volume. Do not store SQLite on ephemeral, non-persistent container disks.

3. **Query Conventions**:
   - Always use Drizzle query builders (`db.select()`, `db.insert()`, `db.update()`, `db.delete()`).
   - If raw SQL is strictly required, always use parameterized queries with `sql` tags (`sql` template tag with bindings). Never concatenate user input strings into SQL.

---

## 5. Component & Data Flow Patterns

1. **Server Components by Default**:
   - Fetch data directly inside `async` Server Components using Drizzle queries.
   - Never create API routes solely to fetch data for your own Server Components.
   - Handle loading states with `loading.tsx` or `<Suspense fallback={<Skeleton />}>`.
   - Handle runtime errors with `error.tsx`.

2. **Client Components at the Leaves**:
   - Add `'use client'` only when using React hooks (`useState`, `useEffect`), event listeners (`onClick`, `onChange`), or browser APIs.
   - Keep Client Components small and pass server-fetched data down as props.

3. **Server Actions for Mutations**:
   - Place all database mutations in `actions/` files marked with `'use server'`.
   - Always parse input arguments with Zod schemas before performing database operations.
   - Always return a standard result shape:
     ```typescript
     export type ActionResult<T = unknown> =
       | { success: true; data: T }
       | { success: false; error: string };
     ```
   - Call `revalidatePath('/path')` or `revalidateTag('tag')` on successful mutations.

---

## 6. What We DON'T Do (and Why)

- **DO NOT use Prisma**:
  *Why*: Prisma relies on a heavyweight Rust engine binary that significantly increases deployment sizes, adds latency to serverless cold starts, and complicates SQLite connection pooling. Drizzle is lightweight, zero-dependency, and compiles directly to SQL.
- **DO NOT use `useEffect` for data fetching**:
  *Why*: Causes client-side request waterfalls, loading flickers, and unneeded client bundle weight. Fetch data in Server Components.
- **DO NOT use `any` in TypeScript**:
  *Why*: Destroys type safety across the database-to-UI pipeline. Use Drizzle's inferred schema types: `type User = typeof users.$inferSelect;`.
- **DO NOT mix `'use client'` and `'use server'` in the same file**:
  *Why*: Next.js build boundary restrictions enforce clean separation. Keep actions in dedicated `actions/` files.
- **DO NOT commit `.sqlite` or `.db` files to Git**:
  *Why*: Database files are local runtime state and will cause git merge conflicts and potential leakage of test/production data. Include `*.db`, `*.sqlite`, `*.sqlite-wal`, `*.sqlite-shm` in `.gitignore`.
- **DO NOT store unhashed passwords**:
  *Why*: Always hash credentials using `argon2` or `bcrypt` before writing to SQLite.
- **DO NOT perform raw string interpolation in SQL**:
  *Why*: Vulnerable to SQL injection. All inputs must be bound parameters.

---

## 7. Claude Code Operational Protocol

When assisting in this codebase:
- Proactively check `db/schema.ts` before creating new database queries.
- When adding a feature that touches the database, provide both the schema change and instructions to run `pnpm db:generate && pnpm db:migrate`.
- Maintain clean file boundaries: UI components in `components/`, server logic in `actions/`, schema in `db/`.
- Ensure all created components use accessible semantic HTML and Tailwind utility classes.
