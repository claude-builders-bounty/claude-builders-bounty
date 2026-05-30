# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

## Stack

- **Runtime**: Node.js 20+ (via `.nvmrc`)
- **Framework**: Next.js 15 (App Router)
- **Database**: SQLite via `better-sqlite3` (local) or Turso (production)
- **ORM**: Drizzle ORM (`drizzle-orm` + `drizzle-kit`)
- **Auth**: NextAuth.js v5 (Auth.js) with credentials + OAuth providers
- **Validation**: Zod (schemas co-located with routes or actions)
- **Styling**: Tailwind CSS v4 + `shadcn/ui`
- **Package manager**: `pnpm`
- **Testing**: Vitest + @testing-library/react
- **CI**: GitHub Actions (lint, typecheck, test on every PR)

## Folder structure

```
src/
├── app/                    # App Router (routes, layouts, error boundaries)
│   ├── (auth)/             # Auth group (login, register)
│   ├── (dashboard)/        # Authenticated routes
│   ├── api/                # Route handlers (REST endpoints)
│   └── layout.tsx
├── components/             # Shared React components
│   ├── ui/                 # shadcn/ui primitives
│   └── forms/              # Form components (react-hook-form + Zod)
├── db/                     # Database
│   ├── schema/             # Drizzle table definitions
│   ├── migrations/         # Auto-generated (never edit manually)
│   ├── index.ts            # Client instance
│   └── seed.ts             # Seed data
├── lib/                    # Utilities (auth, email, helpers)
├── actions/                # Server actions
├── validators/             # Zod schemas (mirror DB schema shape)
└── middleware.ts           # Next.js middleware (auth, redirects)
```

## SQL / migration conventions

- **All schema changes go through Drizzle Kit**: `pnpm db:generate`
- **Never edit migration files** — regenerate if wrong
- **Every table gets**: `id` (text, prefixed), `createdAt`, `updatedAt`
- **Soft deletes** via `deletedAt: timestamp` column
- **Foreign keys**: always use `references()` in Drizzle schema
- **Indexes**: add for every `WHERE`, `ORDER BY`, or `JOIN` column
- **Run**: `pnpm db:push` in development, `pnpm db:migrate` in production

## Component patterns

- **Server components by default** — only add `"use client"` when using hooks, events, or browser APIs
- **Pages are async server components** — fetch data directly, no `getServerSideProps`
- **Form components** use `react-hook-form` + `@hookform/resolvers/zod`
- **Loading states** use Next.js `loading.tsx` files (not client state)
- **Error boundaries** use `error.tsx` files per route segment

## What we don't do (and why)

- **No `any` types** — every DB query, API response, and form value gets a dedicated Zod schema or type
- **No raw SQL strings** — Drizzle ORM gives type safety and migration automation
- **No client-side data fetching for initial load** — App Router streams from the server
- **No `useEffect` for data loading** — use server components or React Server Actions
- **No barrel exports** (`index.ts` re-exports) — they break tree-shaking and slow HMR
- **No `pg` or `mysql2`** — we use SQLite; if you need Postgres, create a new project

## Dev commands

```bash
pnpm dev            # Start dev server
pnpm build          # Production build
pnpm lint           # ESLint + Prettier
pnpm typecheck      # tsc --noEmit
pnpm test           # Vitest
pnpm db:generate    # Generate migration after schema change
pnpm db:push        # Push schema to local SQLite
pnpm db:studio      # Open Drizzle Studio
pnpm db:seed        # Run seed script
```
