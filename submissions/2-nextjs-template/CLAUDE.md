# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions
- **Framework:** Next.js 15 App Router (React 19)
- **Language:** TypeScript 5.7+, strict mode
- **Database:** SQLite via `better-sqlite3` (local dev) / Turso (production)
- **ORM:** Drizzle ORM (never raw SQL except for migrations)
- **Auth:** lucia-auth v4 (session-based, not JWT)
- **Styling:** Tailwind CSS v4 + shadcn/ui (never mix raw CSS)
- **Validation:** Zod (share schemas between client and server)
- **Payments:** Stripe (use `@stripe/stripe-js` for client, `stripe` for server)

## Folder Structure

```
src/
├── app/           # App Router pages and API routes
│   ├── (auth)/    # Auth group (login, signup)
│   ├── (dashboard)/ # Protected routes
│   └── api/       # Route handlers (no Express, no tRPC)
├── components/    # React components (PascalCase)
│   ├── ui/        # shadcn/ui primitives (never edit manually)
│   └── features/  # Business-logic components
├── db/
│   ├── schema.ts  # Drizzle table definitions
│   ├── migrate.ts # Migration runner
│   └── seed.ts    # Dev seed data
├── lib/           # Pure utilities (never import 'server-only' here)
│   ├── db.ts      # Database singleton
│   ├── auth.ts    # lucia-auth config
│   └── stripe.ts  # Stripe server client
├── actions/       # Server Actions (one file per domain)
└── types/         # Shared TypeScript types
```

## Naming Conventions
- Components: `PascalCase.tsx` → `<UserProfile />`
- Server actions: `kebab-case.ts` → `create-project.ts`
- DB tables: `snake_case` → `user_projects`, `billing_plans`
- API routes: RESTful nouns → `POST /api/projects`, `GET /api/projects/[id]`
- Zod schemas: suffix `Schema` → `createProjectSchema`

## SQL / Migration Rules
- **Every schema change gets a migration.** Run `pnpm db:generate` then `pnpm db:migrate`
- **Never drop a column directly.** Add a new column, migrate data, drop old column in next migration
- **Foreign keys are mandatory.** Every relation gets `references(() => table.id)`
- **Index every WHERE column.** If you query by `email`, index `email`
- **Use `integer` for booleans.** SQLite has no native boolean — Drizzle maps `integer({mode: 'boolean'})`
- **Seed file must be idempotent.** Use `ON CONFLICT DO NOTHING`

## Component Patterns
- **Server-first.** Every component starts as a Server Component. Only add `'use client'` when you need interactivity
- **Co-locate loading states.** `loading.tsx` next to `page.tsx`, never a global spinner
- **Use `Suspense` boundaries at the route level**, not inside deeply nested components
- **Forms use Server Actions + `useActionState`**, never `useEffect` for mutations
- **Error boundaries per route segment.** `error.tsx` handles unexpected failures

## Dev Commands
```bash
pnpm dev          # Next.js dev server
pnpm db:generate  # Generate Drizzle migrations from schema
pnpm db:migrate   # Apply pending migrations
pnpm db:studio    # Open Drizzle Studio (visual DB editor)
pnpm db:seed      # Reset and seed development database
pnpm lint         # Biome lint (never ESLint + Prettier)
pnpm typecheck    # tsc --noEmit
pnpm test         # vitest (unit), playwright (e2e)
```

## What We Don't Do (and Why)
- **No ORMs other than Drizzle.** Prisma adds 300MB to node_modules and its generated client breaks tree-shaking
- **No tRPC.** App Router + Server Actions handle type safety without the abstraction
- **No API middlewares.** Use `middleware.ts` for edge logic, inline checks for route-specific auth
- **No `any` in TypeScript.** Not even for "quick hacks" — use `unknown` + type guard
- **No `useEffect` for data fetching.** Use Server Components, `fetch()` directly, or React Query on the client
- **No `.env` in the repo.** `.env.example` documents required vars with dummy values
