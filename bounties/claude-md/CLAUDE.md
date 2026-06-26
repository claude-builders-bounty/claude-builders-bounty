# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

## Stack & versions

- **Next.js 15** (App Router, React 19, Turbopack dev)
- **SQLite** via `better-sqlite3` (local) or Turso (production — libsql HTTP)
- **Drizzle ORM** — schema-first, no migrations in JS, SQL output to `drizzle/`
- **Auth** — Lucia v3 (server-side sessions, no client JWT)
- **UI** — Tailwind CSS 4 + `shadcn/ui` components only (no MUI/Chakra)
- **Forms** — `react-hook-form` + `zod` for client+server validation

## Folder structure

```
src/
├── app/              # Next.js App Router — file-based routes
│   ├── (auth)/       # login, register — grouped, no layout inheritance
│   ├── (dashboard)/  # authenticated pages — shared sidebar layout
│   ├── api/          # Route handlers — /api/*.ts
│   └── layout.tsx    # root layout, providers, fonts
├── components/       # Shared React components
│   ├── ui/           # shadcn/ui primitives — NO custom styles here
│   └── forms/        # Form components with react-hook-form + zod
├── db/               # Database layer
│   ├── schema/       # Drizzle schema files (one per domain)
│   ├── migrations/   # Auto-generated SQL files — committed, never edited
│   └── index.ts      # DB client + connection setup
├── lib/              # Pure utilities, helpers, types
├── actions/          # Server Actions — one file per domain
└── hooks/            # Shared React hooks
```

## SQL / migration conventions

- **Schema-first:** define everything in `db/schema/` with Drizzle. Never raw SQL for schema.
- **Migrations:** `drizzle-kit generate` → review SQL → `drizzle-kit migrate`. SQL files committed.
- **No down migrations.** If a migration is wrong, write a new one that reverses it.
- **Foreign keys:** not enforced at the SQLite level. Use app-level constraints and Drizzle relations for type safety.
- **Full-text search:** `sqlite-vec` extension for embeddings, `FTS5` for text search. Declare in schema, not ad-hoc.
- **Transactions:** wrap multi-table writes in `db.transaction()`.

## Component patterns

- **Server-first.** Every component defaults to a Server Component. Add `"use client"` only when you need interactivity (event handlers, hooks, browser API).
- **Props over context.** Pass data down explicitly. Avoid React Context for data that could be a prop.
- **Server Actions over API routes.** Mutations go in `src/actions/`. API routes are for external integrations (webhooks, OAuth callbacks).
- **Loading states** use `loading.tsx` and `Suspense` boundaries — never manual `isLoading` state.
- **Error boundaries:** `error.tsx` per route segment. Catch, log, show a friendly message.

## What we don't do

- **No Prisma.** Drizzle gives us SQLite-native types and no JS runtime in migrations.
- **No Redux / Zustand.** Server state goes through Server Components + revalidation. Client state is `useState` or URL search params.
- **No cron inside Next.js.** Long-running tasks run as separate workers. Keep request handlers < 500ms.
- **No `N+1` in routes.** Always use Drizzle `with` to eager-load relations. If you see a loop making queries, stop and re-read the docs.
- **No `any`.** Every DB row has a type. Every API response has a zod schema. Every env variable is checked at startup.

## Dev commands

```bash
npm run dev           # turbopack dev server
npm run db:generate   # drizzle-kit generate
npm run db:migrate    # drizzle-kit migrate
npm run db:studio     # drizzle-kit studio (GUI)
npm run lint          # biome check
npm run typecheck     # tsc --noEmit
npm test              # vitest
```
