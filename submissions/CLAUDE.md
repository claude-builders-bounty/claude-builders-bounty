# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions

- **Runtime:** Node.js 20+ (LTS)
- **Framework:** Next.js 15 App Router (React 19)
- **Database:** SQLite via `better-sqlite3` (local dev) or Turso (production)
- **ORM:** Drizzle ORM (schema-first, no magic)
- **Auth:** NextAuth.js v5 with credentials + OAuth providers
- **UI:** Tailwind CSS v4 + shadcn/ui
- **Language:** TypeScript strict mode throughout
- **Package manager:** pnpm

## Folder Structure

```
├── src/
│   ├── app/            # Next.js App Router pages & API routes
│   │   ├── (auth)/     # Auth-required layout group
│   │   ├── api/        # API route handlers
│   │   └── layout.tsx  # Root layout
│   ├── components/     # React components (ui/, forms/, layout/)
│   ├── db/             # Drizzle schema, migrations, queries
│   │   ├── schema/     # Table definitions
│   │   └── queries/    # Reusable SQL/drizzle query functions
│   ├── lib/            # Shared utilities (auth, email, payments)
│   └── config/         # App configuration & env validation
├── drizzle/            # Generated migration files (do not edit manually)
├── public/             # Static assets
├── .env.local          # Local env vars (gitignored)
└── drizzle.config.ts   # Drizzle CLI config
```

## Commands

| Command | Purpose |
|---------|---------|
| `pnpm dev` | Start dev server on :3000 |
| `pnpm build` | Production build |
| `pnpm start` | Start production server |
| `pnpm lint` | ESLint + TypeScript check |
| `pnpm test` | Vitest (unit) |
| `pnpm test:e2e` | Playwright (E2E) |
| `pnpm db:generate` | Generate Drizzle migration |
| `pnpm db:migrate` | Apply pending migrations |
| `pnpm db:studio` | Open Drizzle Studio (GUI) |

## Database & Migration Rules

1. **Schema-first:** Edit `src/db/schema/*.ts`, then run `pnpm db:generate`
2. **Never edit migration files** in `drizzle/` — they are auto-generated
3. **One migration per feature** — squash related changes into a single migration
4. **Foreign keys:** Always cascade on delete for user-owned rows
5. **Timestamps:** Every table gets `createdAt` and `updatedAt` (use `$defaultFn` and `$onUpdateFn`)
6. **Soft deletes preferred** — add `deletedAt: timestamp()` nullable column instead of hard delete

## Component Patterns

- **Server Components** by default — only add `'use client'` when you need hooks, event handlers, or browser APIs
- **Co-locate tests** — `Component.test.tsx` lives next to `Component.tsx`
- **Shadcn/ui components** go in `components/ui/` — customize via `tailwind.config.ts`
- **Form components** go in `components/forms/` — use `react-hook-form` + `zod` validation
- **Page components** are async Server Components that fetch data directly from the database

## API Route Patterns

- **Route handlers** in `src/app/api/[resource]/route.ts`
- **Validate input** with zod before processing
- **Return consistent JSON** shape: `{ data?, error?, message? }`
- **Auth-protected routes** wrap with `middleware.ts` — check `auth()` from NextAuth
- **Rate limit** public endpoints with `@upstash/rate-limit` or in-memory limiter

## What We Don't Do (And Why)

| Anti-pattern | Reason |
|-------------|--------|
| `any` type | Breaks type safety. Use `unknown` + type guards |
| Direct SQL strings | Drizzle gives type-safe queries. Raw SQL only for performance-critical paths |
| Client-side data fetching as default | Server Components eliminate waterfall requests |
| `useEffect` for data fetching | React Query / Server Actions handle this better |
| Mixing migration systems | Drizzle only — never Knex, Prisma, or raw SQL files |
| Hard-coded secrets | Always use `process.env.*` validated by `src/config/env.ts` |

## Example: Adding a New Feature

1. Define schema in `src/db/schema/feature.ts`
2. Run `pnpm db:generate` + `pnpm db:migrate`
3. Create Server Component in `src/app/(auth)/features/page.tsx`
4. Add API route if needed: `src/app/api/features/route.ts`
5. Write tests: `src/app/(auth)/features/__tests__/page.test.tsx`
6. Run `pnpm lint && pnpm test` before commit
