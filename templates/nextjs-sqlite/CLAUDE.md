# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript (strict mode)
- **Database**: SQLite via `better-sqlite3` (local dev / single-server prod) or Turso (edge/distributed)
- **ORM**: Drizzle ORM (type-safe, lightweight)
- **Auth**: NextAuth.js v5 with credentials + OAuth providers
- **Styling**: Tailwind CSS v4 + shadcn/ui
- **Validation**: Zod (shared schemas between client and server)
- **Testing**: Vitest + Playwright (E2E)
- **Package Manager**: pnpm

## Folder Structure

```
src/
├── app/            # Next.js App Router pages & API routes
│   ├── (auth)/     # Auth-required routes group
│   ├── api/        # Route handlers
│   └── layout.tsx  # Root layout
├── components/     # React components
│   ├── ui/         # shadcn/ui primitives (don't modify)
│   └── features/   # Domain-specific components
├── db/
│   ├── schema.ts   # Drizzle schema definitions
│   ├── migrations/ # Auto-generated migration files
│   └── index.ts    # DB connection singleton
├── lib/            # Shared utilities (no React)
│   ├── auth.ts     # NextAuth config
│   ├── db.ts       # Drizzle client
│   └── validators/ # Zod schemas
└── server/         # Server-only code (never imported from client components)
    └── actions/    # Server actions
```

## SQL / Migration Conventions

1. **Always use Drizzle migrations.** Never modify the SQLite file directly.
2. Run `pnpm db:generate` after schema changes, then `pnpm db:migrate`.
3. Migration files are committed — they are the source of truth for schema history.
4. **No raw SQL in application code.** Use the Drizzle query builder. The only exception is migration files.
5. Foreign keys: always define `.references()` in Drizzle. SQLite needs `PRAGMA foreign_keys = ON` (we enable this in the connection singleton).
6. Index everything you query with a `WHERE` clause in production.

## Component Patterns

- **Server-first by default.** Start with Server Components. Only add `"use client"` when you need interactivity, browser APIs, or hooks.
- **Co-locate data fetching.** Use server components to fetch data directly. Don't create a separate API route unless the endpoint is consumed by external clients.
- **Server Actions for mutations.** Forms use server actions, not API routes. Import `"use server"` files from `src/server/actions/`.
- **Loading UI**: Every async page gets a `loading.tsx` sibling. Every server action shows optimistic UI via `useOptimistic`.

## What We Don't Do (and Why)

- ❌ **REST API routes for internal mutations.** Use server actions. API routes are only for webhooks and external integrations.
- ❌ **Raw SQL queries in application code.** Drizzle or bust. One exception: migration SQL files.
- ❌ **Client-side data fetching for initial render.** This causes layout shift and waterwall. Server components do the first render.
- ❌ **`.env` committed to git.** Use `.env.example` with dummy values. Real secrets go in your deployment platform.
- ❌ **Monolithic components.** If a component has more than one responsibility, split it.
- ❌ **Any-to-any imports from `src/server/` into client components.** Server code must never leak to the client bundle.

## Dev Commands

```bash
pnpm dev          # Start dev server
pnpm build        # Production build
pnpm db:generate  # Generate Drizzle migration
pnpm db:migrate   # Apply migration
pnpm db:studio    # Open Drizzle Studio
pnpm test         # Run Vitest
pnpm test:e2e     # Run Playwright
pnpm lint         # ESLint + Prettier
pnpm typecheck    # tsc --noEmit
```
