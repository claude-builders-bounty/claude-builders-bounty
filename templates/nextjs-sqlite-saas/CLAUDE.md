# CLAUDE.md — Next.js 15 + SQLite SaaS

## Project Architecture
- **Framework**: Next.js 15 (App Router), React 19, TypeScript strict
- **Database**: SQLite via better-sqlite3 (local dev) / Turso (production)
- **ORM**: Drizzle ORM with schema-first approach
- **Auth**: NextAuth.js v5 with credentials + OAuth providers
- **UI**: shadcn/ui + Tailwind CSS v4, server components by default
- **Payments**: Stripe (subscriptions, webhooks)

## Commands
- `pnpm dev` — start dev server on :3000
- `pnpm build` — production build
- `pnpm lint` — ESLint + Prettier check
- `pnpm test` — Vitest (unit) + Playwright (e2e)
- `pnpm db:push` — push Drizzle schema to DB
- `pnpm db:generate` — generate Drizzle migrations
- `pnpm db:migrate` — apply pending migrations
- `pnpm type-check` — tsc --noEmit

## Conventions
- **Components**: `@/components/{name}/index.tsx` with co-located styles and tests
- **Server Actions**: `@/lib/actions/{resource}.ts`, always validate with Zod
- **API Routes**: Use Next.js route handlers unless you need server actions
- **Database Queries**: Drizzle queries in `@/lib/db/queries/{resource}.ts`
- **Pages**: `@/app/{route}/page.tsx`, keep thin — delegate logic to lib
- **Error Handling**: Always return `{ success: boolean; data?: T; error?: string }`
- **Naming**: kebab-case for files, camelCase for functions, PascalCase for components/types

## Database Rules
1. NEVER use `DELETE FROM` without a WHERE clause
2. Always use Drizzle migrations — never raw SQL for schema changes
3. Wrap multi-row mutations in transactions
4. Index foreign keys and frequently-queried columns
5. Use `text` for strings (SQLite has no varchar limit)

## Anti-Patterns
- ❌ `'use client'` unless you need hooks, event handlers, or browser APIs
- ❌ Fetching in client components — use server components + Suspense
- ❌ Storing sessions in the database — use JWT or NextAuth adapter
- ❌ `rm -rf node_modules` without first checking `pnpm store prune`

## Testing
- Unit tests for all server actions and DB queries
- Integration tests for API routes
- E2E for critical user flows (signup, payment, CRUD)
- Run `pnpm test` before every PR

## Deployment (Vercel)
- Environment variables in `.env.local` for local, Vercel dashboard for prod
- Enable Edge Functions only for truly global middleware
- Use ISR for public pages, SSR for authenticated pages
