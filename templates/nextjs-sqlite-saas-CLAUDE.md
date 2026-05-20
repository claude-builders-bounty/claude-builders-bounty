# CLAUDE.md — Next.js 15 + SQLite SaaS Starter

## Project Overview
Next.js 15 App Router with SQLite (better-sqlite3) for SaaS. TypeScript, Tailwind CSS, next-auth v5, Prisma ORM.

## Commands
```bash
npm run dev          # Dev server (localhost:3000)
npm run build        # Production build
npm run lint         # ESLint
npm run test         # Vitest suite
npm run typecheck    # tsc --noEmit
npx prisma generate  # Regenerate Prisma client
npx prisma db push   # Push schema to SQLite (no migrations in dev)
npx prisma migrate dev --name <name>  # Create migration
```

## Architecture
```
app/           → Next.js App Router (pages, layouts, API routes)
components/    → React components (shadcn/ui)
lib/           → Utils, DB client, auth config
prisma/        → schema.prisma + migrations/
```

## Conventions
- **TypeScript strict mode** — zero `any`, prefer `unknown` + type guards
- **Server Components by default** — `'use client'` only for interactivity
- **Server Actions** for mutations — `'use server'` in `app/actions/`
- **Route Handlers** for webhooks/external APIs — `export async function POST`
- **Auth** via `auth()` from `lib/auth.ts` — never `getServerSession()`
- **Styling** Tailwind + shadcn/ui — no custom CSS files
- **Prisma singleton** — single `PrismaClient` in `lib/db.ts`, cached via `globalThis`

## Anti-patterns (NEVER do these)
1. ❌ `prisma.$queryRaw` for user input — use parameterized queries
2. ❌ `getServerSession()` — use `auth()` (next-auth v5)
3. ❌ `useEffect` for data fetching — use Server Components or React Query
4. ❌ Direct `fetch()` in client components — use Server Actions
5. ❌ `any` type — always use proper types from Prisma or define interfaces
6. ❌ SQLite enums — use string fields with CHECK constraints
7. ❌ Missing `revalidatePath()` after mutations — Next.js 15 caches aggressively

## Gotchas
- **SQLite no enums**: Use `String` + `@default("value")` in Prisma
- **Cache invalidation**: Call `revalidatePath('/dashboard')` after every mutation
- **better-sqlite3 bindings**: `npm rebuild` after Node version changes
- **Middleware**: `middleware.ts` for auth gating, runs on Edge (no Prisma!)
- **Prisma in middleware**: Don't — use JWT verification instead

## Testing
- Unit: `vitest` for pure logic in `lib/`
- Component: `@testing-library/react` for UI
- E2E: Playwright (when added)
- Mock Prisma: `vitest.mock('@/lib/db')` with in-memory SQLite

## File Naming
- Components: `PascalCase.tsx` (e.g., `UserProfile.tsx`)
- Utilities: `camelCase.ts` (e.g., `formatCurrency.ts`)
- Routes: `kebab-case` folders (e.g., `user-settings/`)
- API: `route.ts` in feature folder (e.g., `app/api/users/route.ts`)
