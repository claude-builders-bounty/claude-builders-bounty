# CLAUDE.md for Next.js 15 + SQLite SaaS

Stack & versions
- Node.js 20+
- Next.js 15 (App Router)
- SQLite (better-sqlite3 or Turso via libsql)
- TypeScript 5.x

Project structure
- apps/web/          Next.js 15 App Router app (client + server components)
- packages/server/   Next.js API routes and shared server logic
- packages/shared/   shared types, utilities, and database schema
- scripts/migrations/ SQLite migration scripts (numbered TypeScript files)
- docs/              Markdown documentation

Naming conventions
- Files: kebab-case for scripts (e.g. add-users-table.ts), camelCase for JS/TS components
- Folders: short, all lowercase, underscore for multi-word (e.g. user_profiles)
- Database tables: snake_case plural (e.g. user_profiles, migration_log)
- Migration filenames: YYYYMMDDHHmmss-<description>.ts

DB migration rules
- Every migration is a TypeScript script that exports `up(db)` and `down(db)` functions.
- Run with `npx ts-node scripts/migrations/<file>`.
- Schema source of truth: packages/shared/src/schema.ts.
- Never alter production migration files after they have run on a live database.
- Before migrating production, always generate a rollback script in `down()`.

Dev commands
- `pnpm dev`             start Next.js dev server (apps/web)
- `pnpm server`          start API routes (packages/server)
- `pnpm migrate up`      run pending migrations
- `pnpm migrate down`    rollback last migration
- `pnpm test`            run unit + integration tests
- `pnpm lint`            run ESLint + Prettier check

Component patterns
- Prefer React Server Components; keep client components interactive-only.
- Atomic design: atoms > molecules > organisms > templates > pages.
- Colocate styles with components using Tailwind CSS utility classes.
- Export a default export for pages; named exports for components.

Anti-patterns to avoid
- Never import heavy client-side libraries (e.g. charting libs) in server components.
- Avoid inline styles; use Tailwind CSS classes.
- Keep database queries in server-only code (apps/web/server or packages/server).
- Never store PII in plain SQLite columns; use encrypted fields or a dedicated store.
- Do not commit migration scripts that mutate production data without a rollback path.

What we don't do (and why)
- We don't use native browser storage for auth tokens (XSS risk).
- We don't expose internal APIs directly to client-side code (leaks internals).
- We don't use external services without a fallback (resilience).
- We don't store unencrypted PII in SQLite (compliance).
