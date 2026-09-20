# CLAUDE.md - Next.js 15 (App Router) + SQLite (better-sqlite3 / Turso) Production Template

This file provides opinionated guidelines and rules for Claude Code when working in this repository.

## 🏗️ Architecture & Project Structure
- **Framework**: Next.js 15 with App Router (`app/` directory).
- **Language**: TypeScript (strict mode enabled).
- **Database**: SQLite using `better-sqlite3` (local / embedded) or `@libsql/client` (Turso / serverless).
- **ORM / Query Builder**: Drizzle ORM (preferred for type safety and zero overhead).
- **Styling**: Tailwind CSS with Shadcn UI components.
- **Directory Layout**:
  - `app/`: Next.js App Router routes, layouts, and server actions.
  - `app/api/`: Edge & Node.js API route handlers (only when Server Actions do not fit).
  - `components/`: React Server Components (RSC by default) and Client Components (`"use client"`).
  - `db/`: SQLite connection (`db/index.ts`), schema definitions (`db/schema/`), migrations (`drizzle/`).
  - `lib/`: Shared utility functions, auth helpers, and business domain logic.

## ⚡ Development Commands
```bash
# Package manager: pnpm (or npm/yarn)
pnpm dev              # Start local dev server on http://localhost:3000
pnpm build            # Production build
pnpm start            # Start production server
pnpm lint             # Run ESLint check
pnpm typecheck        # Run TypeScript compiler check (tsc --noEmit)

# Database & Migrations
pnpm db:generate      # Generate Drizzle migration SQL from schema changes
pnpm db:migrate       # Apply pending migrations to the local SQLite database
pnpm db:studio        # Launch Drizzle Studio GUI for database inspection
pnpm db:seed          # Seed test fixtures into the SQLite database
```

## 📐 Core Engineering Patterns
1. **Server Components by Default**:
   - Every component in `app/` and `components/` is a React Server Component unless it explicitly requires interactivity, browser APIs, or React state (`useState`, `useEffect`).
   - Add `"use client"` ONLY at the leaf node component level. Never wrap entire page layouts in `"use client"`.
2. **Server Actions for Mutations**:
   - Use Next.js Server Actions (`"use server"`) for form submissions, database updates, and state mutations.
   - Always validate inputs using `zod` schemas before executing database transactions.
3. **SQLite Single-Writer Safety**:
   - SQLite enforces a single-writer concurrency model. Use WAL (Write-Ahead Logging) mode:
     ```typescript
     db.pragma('journal_mode = WAL');
     db.pragma('synchronous = NORMAL');
     ```
   - Always wrap multi-step database mutations inside `db.transaction(...)`.
4. **Database Connection Singleton**:
   - Use a cached singleton connection in development to prevent SQLite file lock leaks during Next.js Hot Module Reloading (HMR):
     ```typescript
     // db/index.ts
     import Database from 'better-sqlite3';
     import { drizzle } from 'drizzle-orm/better-sqlite3';
     
     const globalForDb = globalThis as unknown as { sqlite: Database.Database | undefined };
     const sqlite = globalForDb.sqlite ?? new Database(process.env.DATABASE_URL ?? 'sqlite.db');
     if (process.env.NODE_ENV !== 'production') globalForDb.sqlite = sqlite;
     export const db = drizzle(sqlite);
     ```

## 🚫 Anti-Patterns to Avoid
- **NEVER** expose raw database queries directly in client-side components.
- **NEVER** perform client-side fetching (`fetch()` inside `useEffect`) when data can be fetched in a Server Component.
- **NEVER** run un-parameterized SQL queries. Always use Drizzle prepared statements or parameterized queries to eliminate SQL injection vulnerabilities.
- **NEVER** omit WAL mode on production SQLite setups; default journal mode causes concurrency bottlenecks.
- **NEVER** commit SQLite database files (`*.db`, `*.sqlite`, `*.db-wal`, `*.db-shm`) to version control. Always include them in `.gitignore`.

## 🧪 Migration & Schema Rules
1. Never edit existing applied migration files. Always generate a new migration using `pnpm db:generate`.
2. All foreign keys must specify explicit `onDelete` behavior (`cascade`, `set null`, or `restrict`).
3. Include created_at and updated_at timestamps on all primary entity tables.
