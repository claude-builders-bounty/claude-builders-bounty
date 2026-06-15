# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15 (App Router) | RSC, server actions, stable |
| Database | SQLite via better-sqlite3 (local) / Turso (production) | Zero-ops, fast, edge-ready |
| ORM | Drizzle ORM | Typesafe, lightweight, SQL-like |
| Auth | Lucia v3 | Clean, framework-agnostic, session-based |
| UI | Tailwind CSS v4 + shadcn/ui | Utility-first, composable |
| Forms | React Hook Form + Zod | Performant, validated |
| Email | Resend | Simple API, reliable delivery |

## Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Auth-required layout group
│   │   ├── dashboard/
│   │   └── settings/
│   ├── (marketing)/       # Public pages
│   │   ├── page.tsx       # Landing
│   │   └── pricing/
│   ├── api/               # Route handlers (webhooks, API endpoints)
│   └── layout.tsx         # Root layout
├── components/
│   ├── ui/                # shadcn/ui primitives (button, input, card, etc.)
│   └── features/          # Feature-specific components
│       ├── auth/          # Sign-in form, OAuth buttons
│       └── billing/       # Pricing card, plan selector
├── db/
│   ├── schema/            # Drizzle schema files (one table per file)
│   │   ├── users.ts
│   │   ├── subscriptions.ts
│   │   └── sessions.ts
│   ├── migrations/        # Auto-generated Drizzle Kit migrations
│   └── index.ts           # DB client singleton
├── lib/
│   ├── auth.ts            # Lucia auth config & helpers
│   ├── email.ts           # Resend email client
│   └── utils.ts           # Shared utilities (cn(), formatDate(), etc.)
├── actions/               # Server Actions (one file per domain)
│   ├── auth.actions.ts
│   └── billing.actions.ts
└── styles/
    └── globals.css        # Tailwind imports + CSS variables
```

## SQL & Migration Conventions

- **One file per table** in `db/schema/` — named after the table (plural).
- **Primary key**: always `id text primary key` (CUID2 or UUIDv7).
- **Timestamps**: `created_at text not null default (datetime('now'))` and `updated_at text not null default (datetime('now'))`.
- **Foreign keys**: explicit `references()` in Drizzle schema.
- **Indexes**: add indexes for every `where`, `order by`, and join column.
- **Migrations**: run `drizzle-kit generate` then `drizzle-kit migrate` — never hand-edit migration files.
- **Seed scripts** go in `db/seed.ts` and use `db.insert(schema).values(...)` — not raw SQL.
- Never use `DELETE` without a `WHERE` — soft deletes via `deleted_at` column where feasible.

## Component Patterns

- **Server Components by default**. Only add `"use client"` when you need interactivity, `useState`, `useEffect`, or browser APIs.
- **shadcn/ui components** live in `components/ui/`. Install via `npx shadcn@latest add` — never vendor them manually.
- **Feature components** in `components/features/` import from `../ui/` for primitives.
- **Server Actions** in `actions/` — one file per domain. Use `"use server"` at the file top.
- **Form validation** with Zod schemas defined next to the action (or in `lib/validations.ts` if reused).
- **Data fetching**: prefer `async` Server Components + search params over `useEffect` + state.

## Dev Commands

```sh
npm run dev          # Next.js dev server
npm run db:generate  # Generate Drizzle migrations
npm run db:migrate   # Apply migrations
npm run db:seed      # Seed database
npm run lint         # ESLint + Prettier
npm run typecheck    # tsc --noEmit
npm run test         # Vitest
```

## Conventions

- **File naming**: kebab-case for files, PascalCase for components.
- **Export pattern**: named exports only (no `export default`).
- **Imports**: use `@/` path alias for all local imports.
- **CSS**: Tailwind utility classes only — no CSS modules, no styled-components.
- **Error handling**: Server Actions return `{ success: boolean; error?: string }`. API routes return `NextResponse` with status codes.
- **Logging**: use `console.error` for server-side errors only. Client errors go through a toast/snackbar.

## What We DON'T Do (And Why)

| Anti-pattern | Why Not |
|---|---|
| `useEffect` for data fetching | RSC + Server Actions handle it. `useEffect` fetch = double render + no type safety. |
| `any` type | Breaks DX. Use `unknown` + narrowing, or generate types from DB schema. |
| Prisma | Heavy binary, slow cold start. Drizzle is SQL-native and 10x faster. |
| Redux / Zustand for server state | Not needed — RSC + search params + URL state cover 95% of cases. |
| Monorepo (turborepo/nx) | Overhead for a single app. Use if you have >1 deployable target. |
| Manual migration files | Always use Drizzle Kit. Hand-written SQL migrations cause drift. |
| Inline styles / CSS modules | Tailwind is faster to write, consistent, and purgeable. |

## Environment Variables

```
# .env.local — required
DATABASE_URL=file:./data/dev.db        # local SQLite
TURSO_DATABASE_URL=                     # production (Turso)
TURSO_AUTH_TOKEN=                       # production (Turso)
RESEND_API_KEY=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
SESSION_SECRET=                         # generate via: openssl rand -hex 32
```
