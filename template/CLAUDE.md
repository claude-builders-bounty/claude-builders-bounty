# CLAUDE.md — Next.js 15 + SQLite SaaS Project Guide

This file tells Claude Code everything it needs to know about this project. Follow these rules exactly.

## Stack & Versions

- **Framework:** Next.js 15 (App Router, NOT Pages Router)
- **Runtime:** Node.js 20+ (ESM only — `"type": "module"` in package.json)
- **Database:** SQLite via `better-sqlite3` (synchronous, no ORMs)
- **Auth:** Session-based (cookie + DB session table, no JWTs)
- **Styling:** Tailwind CSS v4 + CSS Modules for complex components
- **Testing:** Vitest + React Testing Library
- **Package Manager:** pnpm (NOT npm or yarn)

## Folder Structure

```
/app
  /api          — Route handlers (one file per route, POST/GET/PUT/DELETE exports)
  /(auth)       — Auth pages (login, register, forgot-password)
  /(dashboard)  — Authenticated pages (grouped layout with sidebar)
  /layout.tsx   — Root layout (NEVER put business logic here)
  /page.tsx     — Landing page
/components
  /ui           — Generic reusable (Button, Input, Modal) — NO business logic
  /features     — Feature-specific (UserProfile, BillingCard) — can import ui/
/lib
  /db           — Database connection, migrations, queries (raw SQL only)
  /auth         — Session management, password hashing
  /utils        — Pure functions, no side effects
/migrations     — Sequential SQL migration files (001_init.sql, 002_add_x.sql)
/public         — Static assets only
```

## Database Rules

1. **Raw SQL only.** No Prisma, Drizzle, or ORMs. Use `better-sqlite3` directly.
2. **Migrations are sequential files** in `/migrations/`. Never modify existing migrations.
3. **Every table gets:** `id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16))))`, `created_at TEXT DEFAULT (datetime('now'))`, `updated_at TEXT DEFAULT (datetime('now'))`.
4. **Run migrations on app startup** via `lib/db/migrate.ts` — check which have run, apply the rest.
5. **Foreign keys must use `ON DELETE CASCADE`** unless there's a documented reason not to.
6. **Never use `SELECT *`** — always list columns explicitly.

## Component Patterns

- **Server Components by default.** Add `"use client"` ONLY when you need hooks, event handlers, or browser APIs.
- **Props interfaces** go ABOVE the component, named `{Component}Props`.
- **Loading/error states:** Use Next.js `loading.tsx` and `error.tsx` files in route groups, not inline conditionals.
- **Form handling:** Use Server Actions (`"use server"` in a separate file under `/app/actions/`). Never use fetch() to POST to your own API routes.
- **Styling:** Tailwind classes. Extract to CSS Modules only when class count > 8 or for animations.

## API Route Rules

- One file per resource: `/app/api/users/route.ts` (GET all, POST create), `/app/api/users/[id]/route.ts` (GET one, PUT, DELETE).
- Always validate input with a schema (use `zod`).
- Return `{ data, error }` shape. Never throw in route handlers.
- Auth check at the TOP of every protected route: `const session = await getSession(); if (!session) return unauthorized();`

## Commands

```bash
pnpm dev          # Start dev server (port 3000)
pnpm build        # Production build
pnpm test         # Run all tests
pnpm test:watch   # Tests in watch mode
pnpm lint         # ESLint + TypeScript check
pnpm migrate      # Run pending migrations
pnpm seed         # Seed database with test data
```

## Anti-Patterns (DO NOT DO THESE)

- ❌ `useEffect` for data fetching — use Server Components or Server Actions
- ❌ `any` type — if you need it, write a proper type or use `unknown`
- ❌ CSS-in-JS (styled-components, emotion) — use Tailwind
- ❌ Client-side state management libraries (Redux, Zustand) — use React Server Components + URL state
- ❌ `console.log` in production — use a logger or remove it
- ❌ Importing from `@/app/` — app directory is NOT importable
- ❌ Middleware for auth checks — use route-level session validation instead
- ❌ Storing secrets in `.env.local` committed to git — use environment variables in deployment

## What We Don't Do (And Why)

- **No GraphQL** — REST is simpler for this scale, and SQLite doesn't benefit from GraphQL's query flexibility.
- **No Redis** — SQLite is fast enough for single-instance SaaS. Add Redis only when you have multiple server instances.
- **No Docker for dev** — SQLite is a file. Just run `pnpm dev`. Docker adds complexity for zero benefit here.
- **No monorepo** — This is a single app. Turborepo/Nx overhead isn't worth it until you have 3+ deployable services.
