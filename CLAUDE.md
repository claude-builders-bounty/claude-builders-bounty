# Claude Rules: Next.js 15 + SQLite SaaS

This is our opinionated blueprint. Follow these rules strictly to maintain a highly cohesive, robust, and maintainable codebase.

## Stack & Versions
- **Framework**: Next.js 15 (App Router only)
- **Language**: TypeScript (Strict Mode)
- **Database**: SQLite (via `better-sqlite3` or Turso)
- **ORM/Query Builder**: Drizzle ORM (Zero-dependency, SQL-like)
- **Styling**: Tailwind CSS + shadcn/ui

## Dev Commands
- `npm run dev`: Start local development server
- `npm run build`: Production build
- `npm run db:push`: Push Drizzle schema changes to SQLite directly (local dev)
- `npm run db:migrate`: Run generated SQL migrations (production)
- `npm run db:studio`: Open Drizzle Studio to inspect SQLite data

## Folder Structure
We use a feature-sliced architecture. Do not dump everything into a global `components` folder.

```text
src/
├── app/               # Next.js App Router (Routing only, no business logic)
├── features/          # Domain-driven feature modules
│   ├── auth/          # e.g., auth components, actions, queries
│   └── billing/       # e.g., Stripe integrations, billing tables
├── db/                # Database configuration
│   ├── schema.ts      # Drizzle schema definitions
│   └── index.ts       # DB connection instance
├── lib/               # Shared utilities (date formatting, fetch wrappers)
└── components/ui/     # Dumb, generic UI components ONLY (shadcn/ui)
```

## SQL / Migration Conventions
1. **Never use raw SQL strings.** Always use Drizzle ORM to prevent SQL injection and maintain type safety.
2. **Schema defines truth.** Define all tables in `src/db/schema.ts`. Export the inferred TypeScript types (`InferSelectModel`, `InferInsertModel`) alongside the table definitions.
3. **Migration flow:** When modifying schema, run `npm run db:generate` to create the `.sql` migration file, then review the SQL before running `npm run db:migrate`.
4. **Boolean types in SQLite:** SQLite does not have a native boolean. Use `integer({ mode: 'boolean' })` in Drizzle.
5. **Timestamps:** Always use `integer('created_at', { mode: 'timestamp' }).default(sql`(strftime('%s', 'now'))`)`.

## Component Patterns
1. **Server Components by Default:** Assume every component is a Server Component. Only add `"use client"` at the very top of the file when interactivity (hooks, event listeners) is strictly required.
2. **Push state to the URL:** Use Next.js `useSearchParams` for UI state (e.g., active tabs, filters) instead of `useState` so that URLs are shareable and SSR works natively.
3. **Colocation:** If a component is only used by one specific page, keep it in the `app/` directory alongside the `page.tsx` or in the specific `features/` folder. Do not pollute `src/components/ui/`.
4. **Server Actions for Mutations:** Handle form submissions and DB writes using Next.js Server Actions. Do not build API routes (`route.ts`) unless exposing a public API to third parties.

## What We Don't Do (And Why)
- **❌ No Client-Side Data Fetching (SWR/React Query)**
  - *Why:* Next.js App Router fetches data on the server seamlessly. Client-side fetching introduces waterfalls and loading spinners. Use Server Components and pass data as props.
- **❌ No Global State Managers (Redux/Zustand)**
  - *Why:* With Server Components handling data fetching, and URL search params handling UI state, global state is an anti-pattern. If you absolutely need it for a complex client widget, use React Context scoped to that specific tree.
- **❌ No `any` Types**
  - *Why:* We use strict TypeScript. If you don't know the type, use `unknown` and narrow it down with type guards, or rely on Drizzle's inferred types for DB models.
- **❌ No Prisma**
  - *Why:* Prisma's Rust engine adds unnecessary bloat and cold starts for SQLite/Turso deployments. Drizzle is much lighter and executes raw SQL faster.