# CLAUDE.md — Next.js (App Router) + SQLite (Drizzle ORM) SaaS Project Guide

## 1. Tech Stack & Architecture
- **Framework:** Next.js 15+ (App Router, React Server Components by default, Server Actions for mutations)
- **Database:** SQLite via `better-sqlite3` (or LibSQL/Turso) with **Drizzle ORM** (`src/db/schema.ts`, `src/db/index.ts`)
- **Authentication:** Auth.js / Better-Auth session cookies (`src/lib/auth.ts`)
- **Payments:** Stripe Checkout + Webhook handler (`src/app/api/webhooks/stripe/route.ts`)
- **Styling & UI:** Tailwind CSS + shadcn/ui (`src/components/ui/`)
- **Testing:** Vitest for unit/integration (`tests/unit/`), Playwright for E2E (`tests/e2e/`)

## 2. Essential Commands
```bash
npm run dev              # Start Next.js dev server on http://localhost:3000
npm run build            # Typecheck + production build
npm run lint             # ESLint + Prettier check
npm run test             # Run Vitest unit & DB integration tests (uses :memory: SQLite)
npm run db:generate      # Generate Drizzle SQL migrations from src/db/schema.ts
npm run db:migrate       # Apply pending SQLite migrations (WAL mode enabled)
npm run db:studio        # Launch Drizzle Studio
```

## 3. Non-Negotiable Engineering Rules
1. **SQLite Concurrency & WAL Mode:** Always keep `PRAGMA journal_mode = WAL;` and `PRAGMA busy_timeout = 5000;` enabled in `src/db/index.ts`. Never open multiple separate `better-sqlite3` connections per request; reuse the singleton instance.
2. **Server vs. Client Boundary:** Never import `src/db/*` inside `"use client"` components. All database reads belong in Server Components or `src/server/queries/*`; all writes belong in validated Server Actions (`src/server/actions/*`) using `zod`.
3. **Multi-Tenant Isolation:** Every tenant-scoped query MUST filter by `organizationId` / `userId` from the verified session (`await requireAuth()`), never from untrusted client parameters.
4. **Migrations:** Never edit generated files in `drizzle/migrations/` manually. Modify `src/db/schema.ts` and run `npm run db:generate`.
5. **Stripe Webhooks:** Always verify `stripe-signature` using the raw request body (`await req.text()`) and enforce idempotency via an `events_processed` table before mutating subscription state.
