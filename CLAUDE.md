# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Stack & Versions
- **Framework**: Next.js 15 (App Router) — use `app/` directory, not `pages/`
- **Database**: better-sqlite3 (or Turso for edge) — no ORM, use raw SQL via `drizzle-orm`
- **Language**: TypeScript strict mode — no `any`, no `// @ts-ignore`
- **Styling**: Tailwind CSS v4 — no CSS modules, no styled-components
- **Auth**: NextAuth.js v5 (Auth.js) — credentials provider + magic links
- **Validation**: Zod for all runtime validation — no `yup`, no `joi`

## Folder Structure
```
src/
  app/              # Next.js App Router routes
    (auth)/         # Auth pages (login, register) — grouped layout
    (dashboard)/    # Authenticated pages — grouped layout
    api/            # Route handlers (no separate controllers)
  components/
    ui/             # Reusable primitives (Button, Card, Input)
    features/       # Feature-specific components (BillingForm, TeamList)
  db/
    schema.ts       # Drizzle schema definitions
    migrations/     # Auto-generated SQL migrations
    seed.ts         # Development seed data
  lib/
    auth.ts         # NextAuth config + adapter
    stripe.ts       # Stripe client helpers
    email.ts        # Resend / SendGrid integration
  actions/          # Server actions (colocated by feature)
  types/            # Shared TypeScript types
```

## SQL / Migration Rules
- **NEVER** run migrations in production without a backup
- **ALWAYS** use `ALTER TABLE` over `DROP+CREATE` — data loss is not acceptable
- **ALWAYS** wrap multi-statement migrations in a transaction
- **NEVER** use `SELECT *` in production code — specify columns explicitly
- **ALWAYS** index foreign keys and columns used in WHERE clauses
- Migration naming: `YYYYMMDD_description.sql` (e.g., `20260707_add_billing_cycle.sql`)

## Component Patterns
- Server components by default — only add `'use client'` when you need interactivity
- Form validation: Zod schema → server action → revalidate path → redirect
- Loading states: use `loading.tsx` and `Suspense` boundaries — no manual `isLoading` flags
- Error handling: `error.tsx` at route level — never catch errors silently

## What We Don't Do (And Why)
- ❌ **No `pages/` directory** — App Router is the future, mixing both is tech debt
- ❌ **No Prisma** — Drizzle is lighter, faster, and closer to SQL
- ❌ **No `useEffect` for data fetching** — Server Components + Server Actions handle this
- ❌ **No Redux / Zustand** — URL state + React context covers 99% of SaaS needs
- ❌ **No manual API routes for CRUD** — Server Actions replace the need for REST endpoints
- ❌ **No raw SQL in components** — all queries go through `src/db/` or `src/actions/`

## Dev Commands
```bash
npm run dev          # Start dev server
npm run build        # Production build (must pass with zero errors)
npm run db:migrate   # Apply pending migrations
npm run db:seed      # Seed development data
npm run lint         # ESLint + Prettier check
npm run typecheck    # tsc --noEmit (strict mode)
npm test             # Vitest
```

## Anti-Patterns
- Don't import server-only code in client components
- Don't store secrets in `.env.local` — use `NEXT_PUBLIC_` prefix only for client-safe values
- Don't use `fetch` in client components — use Server Actions or route handlers
- Don't hardcode URLs — use `NEXT_PUBLIC_APP_URL` env var
