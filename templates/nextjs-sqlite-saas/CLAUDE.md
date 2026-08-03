# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Project Overview
Next.js 15 (App Router) SaaS application with SQLite (via Turso/LibSQL) database.
Styled with Tailwind CSS v4. Deployed on Vercel.

## Commands
- Build: `npm run build`
- Dev: `npm run dev`
- Test: `npm run test`
- Lint: `npm run lint`
- Type check: `npx tsc --noEmit`
- DB migrate: `npm run db:migrate`
- DB studio: `npm run db:studio`
- Format: `npm run format`

## Project Structure
/ \
|-- app/           # Next.js 15 App Router pages and API routes
|-- components/    # Shared React components
|-- lib/           # Utility functions and shared logic
|-- db/            # Database schema, migrations, and client
|-- public/        # Static assets
|-- styles/        # Global CSS and Tailwind configuration
|-- tests/         # Test files (unit, integration, e2e)

## Code Style
- TypeScript strict mode — no `any` unless absolutely necessary
- React Server Components by default — use `"use client"` only when needed
- Database queries: Use Drizzle ORM with typed schemas
- API routes: Next.js Route Handlers with input validation (Zod)
- Error handling: Always use try/catch with user-friendly error messages
- Naming: camelCase for variables/functions, PascalCase for components/types
- File naming: kebab-case for routes, PascalCase for components

## Architecture Decisions
- Authentication: NextAuth.js / Auth.js v5 with credentials + OAuth providers
- Database: SQLite via Turso (edge-ready) with Drizzle ORM
- Caching: Next.js built-in fetch cache + React cache() for DB queries
- Rate limiting: Upstash Redis or Vercel KV
- Background jobs: Vercel Cron Jobs or Inngest
- Payments: Stripe (Checkout Sessions for one-time, Customer Portal for subscriptions)
- Email: Resend or SendGrid

## Best Practices
- Always use `export const dynamic = "force-dynamic"` or `export const revalidate` explicitly
- Keep server actions in `app/actions/` — one file per domain
- Use `useFormState` + `useFormStatus` for form handling
- Avoid client-side data fetching unless streaming or real-time is needed
- Use `next/image` for all images with explicit width/height

## Testing Strategy
- Unit tests: Vitest for pure functions and utilities
- Integration tests: Playwright for critical user flows
- DB tests: Drizzle Kit's push-to-staging workflow
