# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Project Overview
This is a Next.js 15 SaaS application using SQLite (via better-sqlite3 or Turso), Drizzle ORM, and Tailwind CSS v4.
Hosted on a single VPS with PM2, no Docker in production.

## Commands
- `npm run dev` — Start dev server on localhost:3000
- `npm run build` — Production build with type checking
- `npm run start` — Start production server
- `npm run lint` — Run ESLint + Prettier check
- `npm run test` — Run Vitest test suite
- `npm run test:watch` — Watch mode for tests
- `npm run db:push` — Push Drizzle schema to SQLite
- `npm run db:generate` — Generate Drizzle migrations
- `npm run db:migrate` — Run pending migrations
- `npm run db:studio` — Open Drizzle Studio for DB inspection
- `npm run typecheck` — Run `tsc --noEmit` for type checking
- `npm run format` — Format with Prettier
- `npm run analyze` — Build and analyze bundle with @next/bundle-analyzer

## Code Style
- TypeScript strict mode — no `any`, no `@ts-ignore`
- Functional components with hooks, no class components
- Server components by default, `'use client'` only when interactivity needed
- Prefer `async` server actions over API routes for form submissions
- Path aliases: `@/` maps to `src/`
- Use `cn()` from `clsx` + `tailwind-merge` for conditional classes
- Named exports only (no default exports except pages/layouts)

## Architecture
- `/src/app/` — Next.js App Router pages and API routes
- `/src/components/` — Reusable UI components (shadcn/ui based)
- `/src/db/` — Drizzle schema, migrations, connection
- `/src/actions/` — Server Actions
- `/src/lib/` — Utility functions, auth, email, payments
- `/src/hooks/` — Custom React hooks
- `/src/types/` — Shared TypeScript types
- `/prisma/` — Reserved for future Prisma migration path (currently Drizzle)

## Database
- SQLite via Turso (prod) or better-sqlite3 (dev)
- Drizzle ORM with `drizzle-orm/sqlite` driver
- All schema in `/src/db/schema/`
- Migrations in `/src/db/migrations/`
- Foreign keys enabled via `PRAGMA foreign_keys = ON`
- WAL mode for better concurrent read performance

## Authentication
- NextAuth.js v5 with credentials + OAuth providers
- Session stored in SQLite via Drizzle adapter
- Session cookie: `__Secure-authjs.session-token` (prod) / `authjs.session-token` (dev)

## Payments & Subscriptions
- Stripe for payment processing
- Webhook handler at `/api/webhooks/stripe`
- Subscription tiers stored in `subscriptions` table
- Customer ID mapping in `stripe_customers` table

## Testing
- Vitest for unit and integration tests
- Playwright for E2E tests (`/e2e/`)
- Test files co-located with source: `*.test.ts` or `*.spec.ts`
- Mock external services (Stripe, email) with `vi.mock()`
- SQLite in-memory database for test isolation

## Deployment
- Single VPS (Ubuntu 24.04), PM2 cluster mode
- Caddy or Nginx as reverse proxy with automatic SSL
- Database: Turso for production, local SQLite for development
- Backup: daily `sqlite3 .dump` to S3-compatible storage
- Monitoring: `pm2 monit` + Sentry for error tracking

## Important Rules
- NEVER commit `.env` or `.env.local` files
- NEVER expose DB credentials in client components
- ALWAYS use parameterized queries via Drizzle (no raw SQL strings)
- ALWAYS validate user input with Zod before processing
- Rate limit API routes and server actions
- Use `next/cache` tags for ISR where appropriate
- Keep bundle size under 200KB (gzipped) for initial load

## Git Workflow
- `main` branch is production — always deployable
- Feature branches: `feat/description`
- Bug fixes: `fix/description`
- Commit messages: conventional commits (`feat:`, `fix:`, `chore:`, `docs:`)
- PRs require lint + test + build to pass before merge
