# CLAUDE.md

> **Project**: Typical SaaS built with Next.js 15 (App Router) + SQLite (better-sqlite3 or Turso for prod)
> **Last updated**: 2026-07-08
> **Purpose**: This file gives Claude Code complete context so it can work on this codebase without asking clarifying questions. Follow it strictly.

## Stack & Versions (do not change without discussion)
- **Framework**: Next.js 15.0+ with App Router only (no Pages Router)
- **Language**: TypeScript (strict mode, no `any` except in very rare cases)
- **Database**: SQLite via `better-sqlite3` for local/dev, Turso (libsql) for production
  - Use `better-sqlite3` for all local scripts and tests
  - Use `@libsql/client` or `better-sqlite3` with Turso URL for prod
- **ORM/Query**: Raw SQL with prepared statements + a thin typed wrapper (no full ORM like Prisma unless explicitly added)
- **Auth**: NextAuth.js (Auth.js) v5 or better-sqlite3 sessions (keep simple)
- **UI**: Tailwind CSS + shadcn/ui components (server components by default)
- **API**: Route handlers in `app/api/.../route.ts` (or Server Actions for mutations)
- **Validation**: Zod for all inputs
- **Testing**: Vitest + @testing-library/react for components; integration tests hit a real SQLite file
- **Deployment**: Vercel (or similar). Use Turso for prod DB
- **Package manager**: npm (or pnpm if lockfile shows it)

**Rules**:
- Every rule below exists because we value **simplicity, type safety, and fast iteration** over "enterprise" complexity.
- Prefer server components and Server Actions over client state and API routes when possible.
- SQLite is file-based → keep queries simple. No complex joins in one query if it hurts readability.

## Folder Structure (follow exactly)
```
app/
  layout.tsx              # Root layout + providers
  page.tsx                # Landing / dashboard entry
  (auth)/...              # Auth routes (sign-in, etc.)
  dashboard/
    page.tsx
    settings/
      page.tsx
  api/
    ...                   # Route handlers only when Server Actions insufficient
components/
  ui/                     # shadcn/ui primitives (do not edit directly)
  shared/                 # Reusable non-UI components
lib/
  db.ts                   # DB connection + typed query helpers
  schema.ts               # Table definitions (TypeScript interfaces + SQL)
  migrations/             # .sql files in order
  utils.ts
  auth.ts
types/                    # Global types (avoid `any`)
.env.local                # Never commit real secrets
```

**Do NOT create**:
- `pages/` directory
- `components/` at root unless it's the shadcn one
- Deep nesting beyond 2 levels in `app/`

## SQL / Migration Conventions
- Use raw SQL with `better-sqlite3` prepared statements.
- Migrations live in `lib/migrations/` as numbered `.sql` files (001_init.sql, 002_add_users.sql...).
- Apply migrations with a small script in `scripts/migrate.ts` (runs on dev start or via CLI).
- **Naming**:
  - Tables: snake_case (users, subscriptions)
  - Columns: snake_case (created_at, user_id)
  - Use `INTEGER PRIMARY KEY` for ids
- **Always** use `?` placeholders for values. Never string interpolation.
- For reads: `db.prepare('SELECT ...').all()` or `.get()`
- For writes: `db.prepare('INSERT ...').run()`
- Foreign keys: enable them (`PRAGMA foreign_keys = ON`)
- Indexes: add for frequently filtered columns (user_id, email, etc.)
- **Never** use `DROP TABLE` or destructive ops in code. Use migrations only.

Example helper in `lib/db.ts`:
```ts
import Database from 'better-sqlite3';
export const db = new Database(process.env.DATABASE_URL || 'dev.db');
```

## Component Patterns (opinionated)
- Default to **Server Components**.
- Use Server Actions for all mutations (form actions, button onClick that calls action).
- Client components only when absolutely necessary (useState, browser APIs, heavy interactivity). Mark with `'use client'`.
- Keep components small (< 100 lines preferred).
- Use shadcn/ui primitives + Tailwind. No custom design system.
- Props: strict TypeScript interfaces. No default props for required fields.
- Data fetching: in Server Components with `async` or in Route Handlers.
- Error handling: use error boundaries and `try/catch` + toast notifications.
- Forms: use `react-hook-form` + Zod resolver only if form is complex; otherwise native + Server Action.

**Anti-patterns (do not do)**:
- Mixing client and server state in the same component.
- Fetching data in client components when it can be done on the server.
- Using `useEffect` for data loading.
- Large monolithic components.
- Direct DOM manipulation.

## Dev Commands
```bash
npm run dev          # Next.js dev server (http://localhost:3000)
npm run build        # Production build
npm run start        # Start prod server
npm run db:migrate   # Run pending migrations
npm run test         # Vitest
npm run lint         # ESLint + TypeScript check
```

## What We Don't Do (and why)
- No Prisma / Drizzle unless we explicitly decide to add it (raw SQL keeps us honest about performance and simplicity).
- No client-side routing libraries beyond Next.js (App Router handles it).
- No global state (Redux, Zustand, etc.) — use URL state, Server Actions, or React context sparingly.
- No heavy CSS-in-JS.
- No over-abstraction: if a pattern appears 2 times, duplicate. Refactor only on the 3rd.
- No `any` in new code.
- Do not use `console.log` in production paths — use a proper logger or remove.
- Do not hardcode secrets or connection strings.

## Testing & Validation Rules
- Every new feature or bugfix must include at least one test (unit or integration).
- Test DB: use a separate `:memory:` or temp file DB.
- When adding a migration, also add a test that exercises the new schema.
- Run full test suite before considering a task done.

## When Working With Claude Code
- Always read the relevant files first (`app/`, `lib/db.ts`, existing components).
- Propose changes in small, reviewable diffs.
- Explain *why* a change follows (or bends) a rule above.
- If something feels missing from this file, ask once — then update CLAUDE.md.

Follow these rules. They exist so we ship fast, keep the codebase understandable, and avoid tech debt on a simple stack.

**End of CLAUDE.md** — treat this as the single source of truth for this project.
