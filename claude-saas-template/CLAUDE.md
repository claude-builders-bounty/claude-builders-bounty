# CLAUDE.md — Next.js 15 + SQLite SaaS Template

## Project Overview

Production SaaS application built with Next.js 15 App Router and SQLite (Turso/libSQL).
Standard multi-tenant architecture with team management and subscription billing.

## Tech Stack

- **Framework**: Next.js 15 (App Router, React Server Components)
- **Database**: SQLite via Drizzle ORM (Turso/libSQL for production, better-sqlite3 for dev)
- **Auth**: Auth.js / NextAuth.js v5
- **UI**: Tailwind CSS v4 + shadcn/ui
- **Forms**: React Hook Form + Zod
- **Payments**: Stripe (subscription management)
- **Email**: Resend / React Email
- **Testing**: Vitest + Playwright
- **Package Manager**: pnpm

## Commands

```bash
pnpm dev          # Start dev server (localhost:3000)
pnpm build        # Production build
pnpm start        # Start production server
pnpm lint         # Run ESLint
pnpm test         # Run Vitest
pnpm test:e2e     # Run Playwright E2E tests
pnpm db:generate  # Generate Drizzle migrations
pnpm db:push      # Push schema to database
pnpm db:studio    # Open Drizzle Studio
pnpm type-check   # Run TypeScript type checking
```

## Coding Conventions

### File Structure
- `app/` — Next.js App Router pages and API routes
- `components/` — Reusable React components
- `lib/` — Business logic, utilities, database
- `lib/db/` — Drizzle schema, queries, migrations
- `lib/auth/` — Auth.js configuration
- `lib/stripe/` — Stripe integration
- `lib/email/` — Email templates
- `actions/` — Server Actions
- `types/` — Shared TypeScript types

### Component Patterns
- Default to Server Components; use `"use client"` only when needed
- Use Next.js `<Link>` for navigation, not `<a>` tags
- Fetch data in Server Components, pass down as props
- Use Server Actions for form submissions and mutations
- Keep pages thin; extract logic into `lib/` modules

### Database
- Use Drizzle ORM for all database access
- Schema in `lib/db/schema/` with per-feature files
- Raw SQL only through Drizzle `sql` template literal
- All queries go through service functions in `lib/db/queries/`

### TypeScript
- Strict mode enabled
- Prefer `interface` over `type` for public APIs
- Use `type` for unions, intersections, and computed types
- No `any` — use `unknown` and narrow with type guards
- Export types from feature-level barrel files

### API Routes
- Prefer Server Actions over API routes for app-internal mutations
- Use API routes only for webhooks (Stripe, Resend) and external integrations
- Return `NextResponse.json()` with consistent error shape: `{error: string, details?: unknown}`

### Naming
- Files: `kebab-case.ts` for utilities, `PascalCase.tsx` for components
- Functions: `camelCase` for regular functions, `snake_case` for database columns
- Constants: `SCREAMING_SNAKE_CASE`
- Components: PascalCase matching file name

## Architecture Decisions

- **Multi-tenant**: `req.headers.host` or `slug` subdomain → tenant lookup
- **Auth session**: Database session strategy via Auth.js
- **Subscription**: Stripe Checkout → webhook → update `Subscription` table
- **Team invites**: JWT-based invite links with expiration
- **Background jobs**: Use `page router` API routes or Vercel Cron Jobs
- **Rate limiting**: Upstash Redis Ratelimit for API routes and actions

## Environment Variables

Key variables template in `.env.example`:
- `DATABASE_URL`, `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`
- `AUTH_SECRET`, `AUTH_GITHUB_ID`, `AUTH_GITHUB_SECRET`
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `NEXT_PUBLIC_STRIPE_KEY`
- `RESEND_API_KEY`
- `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`

## Testing

- Unit tests with Vitest alongside source files: `*.test.ts`
- E2E tests in `e2e/` directory with Playwright
- Test database: in-memory SQLite via `better-sqlite3`
- Stripe tests: use `stripe-test-clock` and `webhook` forwarding
