# CLAUDE.md — Next.js 15 + SQLite SaaS

## Project Overview
Next.js 15 App Router · SQLite (better-sqlite3 or Turso) · TypeScript · Tailwind CSS · pnpm

## Architecture Rules

### App Router (MUST)
- Use `app/` directory, NOT `pages/`. Pages Router is legacy and incompatible.
- Layouts: one `layout.tsx` per route segment. Nest layouts, don't repeat shells.
- Server Components by default. Only add `"use client"` when you need interactivity.
- Data fetching: use `async` Server Components or React Server Actions. No `useEffect` for initial data.

### Database (MUST)
- **No ORM migrations in production without review.** SQLite is a file — a bad migration destroys data.
- Migration pattern: create `db/migrations/XXXX_description.sql` files. Run them with a script, not auto.
- Use `better-sqlite3` for local/single-server. Use `@libsql/client` (Turso) for edge/cloud.
- Connection pool: EXACTLY ONE connection for better-sqlite3. SQLite is single-writer. Pooling causes `SQLITE_BUSY`.
- Never use `WAL` mode without understanding it — it creates extra files.

### Naming Conventions
- Files: `kebab-case.tsx`. Components: `PascalCase`. Functions: `camelCase`.
- DB tables: `snake_case` plural (e.g., `user_sessions`, `billing_events`).
- Route params: semantic names — `[orgSlug]`, not `[id]`.

### Anti-Patterns to Avoid
- ❌ `useEffect` for data fetching. Use Server Components or SWR/React Query for client-side refetch only.
- ❌ `SELECT *` in production queries. Name your columns.
- ❌ Nested ternaries in JSX. Extract to a function or use `if/return` pattern.
- ❌ Storing secrets in `.env` without `.env.example`. Always provide a template.
- ❌ Direct `fs` writes to SQLite file while DB is open. Use the driver.

## Commands
```bash
pnpm dev          # Start dev server (turbo + HMR)
pnpm build        # Production build
pnpm lint         # ESLint + Prettier
pnpm typecheck    # tsc --noEmit
pnpm db:migrate   # Run pending migrations
pnpm db:seed      # Seed dev data
pnpm test         # vitest (unit + integration)
```

## When Adding Features
1. Start with the DB schema (add migration file)
2. Add server-side data access function in `lib/data/`
3. Create the Server Component page in `app/`
4. Add loading.tsx and error.tsx per route
5. Write tests BEFORE opening a PR

## File Structure (SaaS-specific)
```
app/
  (marketing)/     # Landing, pricing, blog — public. Lightweight, no DB.
  (dashboard)/     # Authenticated app. All DB access here.
  api/             # Public API routes (rate-limited)
lib/
  data/            # Server-side data access functions (one file per entity)
  auth/            # Auth config (NextAuth or Clerk)
  billing/         # Stripe integration
db/
  migrations/      # Numbered SQL files
  schema.ts        # Drizzle or Kysely schema definitions
```
