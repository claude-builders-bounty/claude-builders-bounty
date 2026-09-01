 # CLAUDE.md — Next.js 15 + SQLite SaaS
 
 ## Stack & Versions
 - **Runtime:** Node.js 20 LTS (ESM)
 - **Framework:** Next.js 15 App Router (`app/` directory only; no `pages/`)
 - **Database:** SQLite via `better-sqlite3` (synchronous, zero-config, file-based)
 - **ORM/Query:** Raw SQL with tagged template literals or `sql-template-tag`. No Prisma/Drizzle unless justified.
 - **Styling:** Tailwind CSS 4 + CSS Modules for component isolation
 - **Validation:** Zod for all API inputs and env vars
 - **Auth:** Better Auth or Lucia (session-based, no JWT unless required)
 
 ## Folder Structure
 ```
 src/
 ├── app/                  # Routes, layouts, loading/error boundaries
 │   ├── (marketing)/      # Public pages grouped by layout
 │   ├── (dashboard)/      # Protected app routes
 │   └── api/              # Route handlers (REST only when needed)
 ├── components/           # Shared UI (shadcn/ui base)
 │   ├── ui/               # Primitives (Button, Input, Dialog)
 │   └── features/         # Domain-specific composites
 ├── db/
 │   ├── schema.sql        # Single source of truth for DDL
 │   ├── migrations/       # Numbered .sql files (001_init.sql)
 │   └── queries/          # Named prepared statements per domain
 ├── lib/                  # Pure utilities, validators, auth helpers
 └── types/                # Shared TS interfaces (no `any`)
 ```
 
 ## Naming Conventions
 - **Files:** kebab-case (`user-profile.tsx`, `get-user-by-id.sql`)
 - **Components:** PascalCase exports, default export only for page/layout
 - **DB columns:** snake_case (`created_at`, `user_id`)
 - **API routes:** plural nouns, lowercase (`/api/users`, `/api/billing/invoices`)
 - **Env vars:** `NEXT_PUBLIC_` prefix ONLY for client-safe values; all others server-only
 
 ## Database & Migration Rules
 1. **Never modify `schema.sql` directly.** Create a new migration file.
 2. Migrations are **forward-only**. No down migrations; fix forward.
 3. Every migration must be idempotent where possible (use `IF NOT EXISTS`).
 4. Run migrations at startup via `db/migrate.ts` — no external CLI in prod.
 5. Use WAL mode (`PRAGMA journal_mode=WAL`) for concurrent reads.
 6. All timestamps: `INTEGER` (Unix ms) or `TEXT` (ISO 8601). Pick one per project and stick to it.
 7. Foreign keys ON (`PRAGMA foreign_keys=ON`) in every connection.
 
 ## Component Patterns
 - **Server Components by default.** Add `"use client"` only when interactivity is required.
 - Data fetching happens in Server Components or Route Handlers — never in client components.
 - Use `React.cache` for deduplication within a request; use `unstable_cache` for cross-request.
 - Forms use Server Actions with progressive enhancement (`action` prop, not `onSubmit` alone).
 - Error boundaries at route segment level; global error in `global-error.tsx`.
 
 ## Dev Commands
 ```bash
 pnpm dev          # Start dev server (Turbopack)
 pnpm build        # Production build
 pnpm db:migrate   # Apply pending migrations
 pnpm db:seed      # Seed development data
 pnpm lint         # ESLint + Prettier check
 pnpm typecheck    # tsc --noEmit
 ```
 
 ## Anti-Patterns (Do Not Do)
 - ❌ `getServerSideProps` / `getStaticProps` — App Router replaces these.
 - ❌ ORM abstractions that hide SQL — SQLite is fast because it's simple; don't add layers.
 - ❌ Client-side data fetching for initial page state — causes waterfall + layout shift.
 - ❌ Storing secrets in `NEXT_PUBLIC_*` vars.
 - ❌ Mutable global state (Zustand/Jotai) for server-derived data.
 - ❌ Dynamic imports for code that's always needed on first paint.
 - ❌ Catch-all error swallowing in Server Actions — log and rethrow or return typed errors.
 
 ## Testing Strategy
 - Unit tests for `lib/` pure functions (Vitest)
 - Integration tests for DB queries against temp SQLite file
 - E2E only for critical paths (Playwright, minimal coverage)
 - No snapshot tests for UI — test behavior, not markup
 
 ## Deployment Notes
 - SQLite file lives on persistent volume (Fly.io, Railway, or VPS)
 - No serverless (Vercel/Netlify) unless using Turso/LibSQL remote driver
 - Backup strategy: litestream or rqlite for replication; cron + rclone as fallback
 - Health check endpoint: `/api/health` returns `{ status: "ok", db: true }`
