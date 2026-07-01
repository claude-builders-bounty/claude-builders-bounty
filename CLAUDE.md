# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions

| Tool | Version | Why |
|---|---|---|
| Next.js | 15.x | App Router, server components, React 19 |
| React | 19.x | Latest stable |
| SQLite | better-sqlite3 v11+ | Zero-infrastructure, file-based DB. No Docker, no external services |
| Turso | Optional | If you need edge-read replicas, swap better-sqlite3 for @libsql/client |
| Drizzle ORM | 0.38+ | Lightweight, type-safe, SQL-like syntax. Not Prisma (too heavy for SQLite) |
| Tailwind CSS | 4.x | Utility-first, PostCSS-based |
| Auth | NextAuth v5 (Auth.js) | Session-based for MVP, JWT for scale |
| TypeScript | 5.x | Strict mode always on |

## Folder Structure

```
├── src/
│   ├── app/                  # Next.js App Router (route groups, layouts)
│   │   ├── (auth)/           # Auth routes (login, register)
│   │   ├── (dashboard)/      # Authenticated routes (dash, settings)
│   │   ├── api/              # Route handlers (REST endpoints)
│   │   └── layout.tsx        # Root layout
│   ├── components/           # Shared React components
│   │   ├── ui/               # Generic UI primitives (Button, Input, Modal)
│   │   └── features/         # Feature-specific components (InvoiceTable, UserCard)
│   ├── db/                   # Database layer
│   │   ├── schema/           # Drizzle schema definitions
│   │   ├── migrations/       # Generated migration files
│   │   ├── queries/          # Reusable query functions
│   │   └── index.ts          # DB connection
│   ├── lib/                  # Utilities, helpers, config
│   ├── hooks/                # React hooks (useAuth, useDebounce)
│   └── middleware.ts         # Next.js middleware (auth checks)
├── public/                   # Static assets
├── drizzle.config.ts         # Drizzle config
├── tailwind.config.ts
├── tsconfig.json
└── next.config.ts
```

### Why this structure?

- `src/app` keeps routing visible at a glance (App Router convention)
- `src/db` is isolated — if you switch from SQLite to Postgres later, only this folder changes
- `src/components/ui` vs `features` separates reusable primitives from business-logic components
- No `utils/` dumping ground — `lib/` has sub-modules per concern

## SQL & Migration Conventions

### Rules

1. **Every migration must be reversible.** If a migration deletes a column, the down migration must restore it.
2. **Never edit migration files after they're pushed.** Create a new migration.
3. **Always use Drizzle schema push in dev**, migrations in CI/staging.
4. **Foreign keys are enforced by the application layer, not the DB.** SQLite has limited FK support.
5. **Timestamp columns must include `ON UPDATE CURRENT_TIMESTAMP`** for `updated_at`.

### Pattern

```ts
// src/db/schema/users.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const users = sqliteTable('users', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  email: text('email').notNull().unique(),
  name: text('name').notNull(),
  createdAt: text('created_at').notNull().default('CURRENT_TIMESTAMP'),
  updatedAt: text('updated_at').notNull().default('CURRENT_TIMESTAMP')
    .$onUpdate(() => new Date().toISOString()),
});
```

## Component Patterns

### Do

- **Server components by default.** Only add `"use client"` when you need hooks, event handlers, or browser APIs.
- **Small, focused components.** If a component file exceeds 200 lines, split it.
- **Props interfaces co-located** at the top of each component file.
- **Loading states with `loading.tsx`** at the route segment level.
- **Error boundaries with `error.tsx`** at the route segment level.

### Don't

- ❌ Don't use `useEffect` for data fetching — use server components or React Query.
- ❌ Don't import server-only code in client components (DB, tokens, secrets).
- ❌ Don't use context for auth state — use the session from server component props.
- ❌ Don't use inline styles — Tailwind classes only.

## Dev Commands

```bash
npm run dev          # Next.js dev server (localhost:3000)
npm run build        # Production build
npm run lint         # ESLint + TypeScript check
npx drizzle-kit push # Push schema changes to local DB
npx drizzle-kit generate  # Generate migration files
npx drizzle-kit migrate   # Apply migrations
```

## Anti-Patterns to Avoid

1. **Don't use serverless Postgres for MVP.** SQLite is cheaper, faster, and requires zero setup. You can migrate later.
2. **Don't use `any` in TypeScript.** Use `unknown` + narrowing instead.
3. **Don't store files in the DB.** Use S3/R2 and store the URL.
4. **Don't put secrets in .env.local committed to git.** Use `.env` for defaults, `.env.local` for secrets (gitignored).
5. **Don't use `getServerSideProps` or `getStaticProps`.** App Router replaces both.
6. **Don't make every component async.** Only server components that fetch data need to be async.

## What We Don't Do (And Why)

| Don't | Reason |
|---|---|
| Redux / Zustand | Server components + React Query cover 95% of state needs |
| Storybook | Overhead > benefit for solo devs and small teams |
| Cypress / Playwright E2E | Vitest + MSW for now. Add E2E when you have paying users |
| GraphQL | REST + React Query is simpler. Add GraphQL only when the frontend demands it |
| Monorepo | Workspace-level tsconfig is enough until you have 3+ apps |
