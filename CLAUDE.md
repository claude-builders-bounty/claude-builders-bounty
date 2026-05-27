# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Stack & Versions
- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript 5.x, strict mode
- **Database:** SQLite via better-sqlite3 (local) / Turso (production)
- **ORM:** Drizzle ORM (not Prisma — see Why below)
- **Auth:** NextAuth.js v5 / Auth.js
- **Styling:** Tailwind CSS v4
- **UI:** shadcn/ui components
- **Validation:** Zod (both client & server)
- **Package Manager:** pnpm

## Folder Structure
```
src/
├── app/                  # Next.js App Router pages
│   ├── (auth)/           # Auth-required routes group
│   ├── (public)/         # Public routes group
│   ├── api/              # Route handlers (no separate backend)
│   └── layout.tsx        # Root layout
├── components/
│   ├── ui/               # shadcn/ui primitives
│   └── features/         # Feature-specific components
├── db/
│   ├── schema/           # Drizzle schema definitions
│   ├── migrations/       # Auto-generated
│   ├── queries/          # Reusable query functions
│   └── index.ts          # DB connection (better-sqlite3/Turso)
├── lib/
│   ├── utils.ts          # Shared utilities
│   └── auth.ts           # Auth.js config
└── types/                # Shared TypeScript types
```

## SQL & Migration Conventions
- **All schema changes** go through Drizzle Kit (`pnpm db:generate`, `pnpm db:push`)
- **Never edit migration files directly** — always regenerate
- **Foreign keys:** always name them explicitly: `fk_{table}_{reference}`
- **Indexes:** add for columns used in WHERE, JOIN, ORDER BY
- **Soft deletes:** use `deleted_at TIMESTAMP` column, not DROP
- **Timestamps:** every table gets `created_at` and `updated_at`

## Component Patterns
- **Server components by default** — only add `'use client'` when you need:
  - useState/useEffect/user interactions
  - Browser-only APIs
  - Event handlers
- **Props typing:** always define and export interfaces
- **Loading states:** use `loading.tsx` (App Router) not client-side spinners
- **Error boundaries:** use `error.tsx` files per route segment

## What We Don't Do (And Why)
- ❌ **No Prisma** — It adds 100MB+ to serverless deployments. Drizzle is lighter, SQL-native, and gives us full control over queries.
- ❌ **No tRPC** — For a single-developer SaaS, the App Router's built-in route handlers + server actions are simpler and sufficient.
- ❌ **No separate backend** — The whole point of Next.js is one codebase. If we need background jobs, we add them via Vercel Cron Jobs or a single worker file.
- ❌ **No `any` types** — If TypeScript is hard, use `unknown` + type guards. `any` is technical debt.
- ❌ **No inline styles** — Tailwind or nothing. No CSS modules, no styled-components.

## Dev Commands
```bash
pnpm dev              # Local dev server
pnpm build            # Production build
pnpm lint             # ESLint + type-check
pnpm test             # Vitest (unit + integration)
pnpm db:generate      # Generate Drizzle migrations
pnpm db:push          # Push schema to database
pnpm db:studio        # Drizzle Studio (GUI DB viewer)
```

## Anti-Patterns Checklist
- [ ] No `useEffect` for data fetching — use Server Components or React Query
- [ ] No `fetch` in client components — use Server Actions or route handlers
- [ ] No hardcoded strings — use a `constants.ts` file
- [ ] No `console.log` in production — use a logger utility
- [ ] No secrets in `.env` files committed to git
- [ ] No nested ternaries — extract into functions
