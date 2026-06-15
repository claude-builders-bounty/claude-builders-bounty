# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions
- **Framework**: Next.js 15 (App Router, Turbopack)
- **Runtime**: Node.js 22+
- **Database**: SQLite via `better-sqlite3` (local dev) / Turso (production)
- **ORM**: Prisma with `prisma-client-lite` (no engine files)
- **Auth**: Auth.js v5 (NextAuth)
- **Payments**: Stripe Node SDK
- **Testing**: Vitest + @testing-library/react
- **Styling**: Tailwind CSS v4

## Project Structure
```
app/
  api/
    auth/[...nextauth]/route.ts   # Auth.js route handler
    users/route.ts                # REST endpoints
    billing/webhook/route.ts       # Stripe webhook
  dashboard/
    overview/page.tsx             # Authenticated dashboard
    settings/page.tsx
  layout.tsx                      # Root layout (font, ThemeProvider)
  page.tsx                        # Landing / signup
  not-found.tsx

components/
  ui/                             # Shadcn-style primitives ONLY
  forms/                          # Domain-specific form components
  layouts/                        # Shell, sidebar, navbar

lib/
  auth.ts                         # Auth.js config
  db.ts                           # SQLite client singleton
  stripe.ts                       # Stripe client singleton
  validators.ts                   # Zod schemas shared across routes

prisma/
  schema.prisma                   # SQLite-compatible schema
  migrations/

scripts/
  seed.ts                         # Seed dev data
  migrate.ts                      # Run Prisma push + seed

sql/
  triggers/                       # SQLite triggers (audit, soft-delete)
  views/                          # Pre-computed views for dashboards

tests/
  api/                            # API route tests (Vitest + supertest)
  components/                     # Component tests
```

## SQL / Migration Conventions
- **Never** use `prisma migrate dev` in production. Use `prisma db push` for prototyping, then export to SQL.
- SQLite doesn't support `ALTER TABLE DROP COLUMN`. If you need to drop a column:
  1. Create new table with correct schema
  2. Copy data over
  3. Drop old table
  4. Rename new table
- All tables MUST have: `id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16))))`, `createdAt INTEGER DEFAULT (unixepoch())`, `updatedAt INTEGER DEFAULT (unixepoch())`
- Soft deletes: add `deletedAt INTEGER DEFAULT NULL`. Never `DELETE FROM`.
- Indexes: every foreign key column AND every column in `WHERE` clauses must be indexed.

## Component Patterns
- **Server Components by default**. Only add `'use client'` when you need hooks or browser APIs.
- **No props drilling > 2 levels**. Use React context or compose via children.
- **Shadcn/ui as base**. Never write raw CSS. All primitives in `components/ui/`.
- **Forms**: Use `react-hook-form` + `@hookform/resolvers/zod`. Never controlled inputs for simple forms.
- **Error boundaries**: Wrap every `page.tsx` in `error.tsx`. Never let errors bubble to the root layout.

## API Route Patterns
- All routes in `app/api/` MUST:
  1. Validate input with Zod
  2. Check authentication via `getServerSession()`
  3. Wrap logic in `try/catch` returning `{ error: string }` on failure
- **Never** return raw Prisma errors to the client. Map to user-friendly messages.
- Rate limiting: every `POST/PUT/DELETE` route MUST check `RATE_LIMIT` key in SQLite (simple sliding window).

## Naming Conventions
- **Files**: kebab-case for routes (`user-profile.tsx`), PascalCase for components (`UserProfile.tsx`)
- **Database**: `snake_case` for tables/columns, plural tables (`users`, `billing_events`)
- **Variables**: `camelCase` everywhere. Exception: SQL queries use `snake_case` for column aliases.
- **Env vars**: `UPPER_SNAKE_CASE` with prefix: `NEXT_PUBLIC_` for client, `STRIPE_` / `AUTH_` / `DB_` for server.

## What We Don't Do (and why)
- ❌ **No ORM joins in hot paths**. SQLite is single-threaded; N+1 kills perf. Use `sql/views/` for pre-computed joins.
- ❌ **No `useState` for server state**. Use SWR or React Query. We don't ship a caching layer twice.
- ❌ **No `any` type**. Use `unknown` + type guards, or `satisfies` for loose checks.
- ❌ **No `console.log` in production**. Use a logger utility (`lib/logger.ts`) that respects `NODE_ENV`.
- ❌ **No barrel exports** (`index.ts` re-exporting everything). Breaks tree-shaking. Import from specific files.

## Dev Commands
```bash
pnpm dev            # Start Turbopack dev server
pnpm test           # Vitest watch mode
pnpm test:run      # Single run (CI)
pnpm typecheck      # tsc --noEmit
pnpm lint           # ESLint
pnpm db:push       # prisma db push (dev only)
pnpm db:seed       # pnpm tsx scripts/seed.ts
pnpm stripe:listen # Forward Stripe webhooks to localhost
```

## Anti-Patterns to Avoid
- Don't `await` unrelated promises sequentially. Use `Promise.all()`.
- Don't put secrets in `NEXT_PUBLIC_` env vars. They end up in the client bundle.
- Don't use `useEffect` for data fetching. Use Server Components or SWR.
- Don't commit `prisma/migrations/` for SQLite. They don't port across environments. Use `db push` + track `schema.prisma` only.
- Don't use `Math.random()` for IDs. Use `crypto.randomUUID()` or the SQLite `hex(randomblob(16))` pattern.

## Testing Strategy
- **API routes**: Integration tests with `supertest`. Mock Stripe, don't hit real API.
- **Components**: Snapshot tests are OK for UI primitives. Avoid for business logic components.
- **SQLite**: Use `better-sqlite3` in-memory mode (`:memory:`) for tests. Seed before each test, wipe after.
- **Auth**: Mock `getServerSession()` to return a test user. Don't test Auth.js itself.

## Deployment Notes
- **Turso** for production SQLite (edge-compatible, global replication)
- **Vercel** for hosting (ensure `maxDuration` is set for API routes that touch SQLite)
- **Stripe webhooks**: Must be accessible via HTTPS. Use `stripe listen --forward-to` for local dev.
- **Env vars**: Document ALL required vars in `.env.example`. Never commit real secrets.
