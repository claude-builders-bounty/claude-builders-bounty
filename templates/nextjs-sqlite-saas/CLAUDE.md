# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> Opinionated project guide for Claude Code. Place in your project root.

## Project Overview

This is a Next.js 15 SaaS application using SQLite (via better-sqlite3/Drizzle ORM) for data persistence. It follows the App Router pattern with Server Components, Server Actions, and middleware-based auth.

## Tech Stack

- **Framework**: Next.js 15 (App Router, React 19)
- **Database**: SQLite via better-sqlite3
- **ORM**: Drizzle ORM with drizzle-kit migrations
- **Auth**: NextAuth.js v5 (Auth.js) with middleware protection
- **Styling**: Tailwind CSS v4
- **Payments**: Stripe (subscriptions + webhooks)
- **Deployment**: Vercel (with persistent SQLite via Turso or LiteFS)

## Directory Structure

```
app/
  (auth)/          # Auth pages (login, register, forgot-password)
  (dashboard)/     # Protected SaaS dashboard pages
  api/             # API routes (webhooks, cron)
  layout.tsx       # Root layout with providers
components/
  ui/              # Reusable UI components (shadcn/ui)
  forms/           # Form components with validation
  dashboard/       # Dashboard-specific components
lib/
  db/
    schema.ts      # Drizzle schema definitions
    index.ts       # Database connection (singleton)
    migrations/    # SQL migrations (drizzle-kit generate)
  auth.ts          # NextAuth configuration
  stripe.ts        # Stripe client + helpers
  utils.ts         # Shared utilities
middleware.ts      # Auth middleware (protects /dashboard/*)
```

## Commands

```bash
npm run dev          # Start dev server (port 3000)
npm run build        # Production build
npm run db:generate  # Generate migration from schema changes
npm run db:migrate   # Run pending migrations
npm run db:studio    # Open Drizzle Studio (DB browser)
npm run stripe:listen # Forward Stripe webhooks locally
```

## Code Conventions

### Database
- All schema in `lib/db/schema.ts` using Drizzle's `sqliteTable()`
- Use `db.select()`, `db.insert()`, `db.update()`, `db.delete()` — never raw SQL
- Wrap multi-step DB operations in transactions: `db.transaction(async (tx) => { ... })`
- Always use parameterized queries (Drizzle handles this automatically)
- Migrations: change schema.ts, run `db:generate`, commit the migration

### Server Actions
- Place in `app/(dashboard)/actions.ts` or co-located `actions.ts`
- Always validate input with Zod before database operations
- Use `revalidatePath()` after mutations
- Return `{ success: boolean, error?: string }` — never throw from actions

### Auth
- `auth()` in Server Components, `useSession()` in Client Components
- Middleware protects `/dashboard/*` routes automatically
- Check `session.user.subscriptionStatus` for paid features

### Components
- Server Components by default; add `"use client"` only when needed
- Use shadcn/ui components from `components/ui/`
- Forms: react-hook-form + zod resolver + Server Actions

### Error Handling
- Use `error.tsx` boundary files per route segment
- API routes: return `NextResponse.json({ error }, { status })` — never crash
- Log errors server-side; show user-friendly messages client-side

### Environment Variables
- `.env.local` for secrets (never commit)
- `NEXTAUTH_SECRET`, `NEXTAUTH_URL`
- `DATABASE_URL` (SQLite path: `file:./db.sqlite`)
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` (client-safe)

## Do NOT

- Use `prisma` — this project uses Drizzle ORM
- Create API routes for CRUD — use Server Actions instead
- Store files in SQLite — use Vercel Blob or S3
- Skip input validation — always use Zod schemas
- Use `getServerSession()` — use `auth()` from `lib/auth.ts`
- Put business logic in components — extract to `lib/` utilities
- Use `localStorage` for auth state — use NextAuth session
