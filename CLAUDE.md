# CLAUDE.md - Next.js 15 App Router + SQLite SaaS

## Stack and Versions
- Framework: Next.js 15 (App Router, not Pages)
- Language: TypeScript 5.x
- Database: SQLite via better-sqlite3 (sync, no connection pool needed)
- ORM: None - raw SQL with type-safe helpers
- Styling: Tailwind CSS 4 + @tailwindcss/forms
- Auth: Clerk or NextAuth v5 (pick one and stick to it)
- Payments: Stripe Checkout + Webhooks
- Deployment: Vercel (recommended) or Railway

## Folder Structure
app/(auth)/          # Clerk/NextAuth routes
app/(dashboard)/     # Protected routes
app/api/             # REST endpoints
components/ui/       # Reusable atoms (Button, Input, Card)
components/layouts/  # Page layouts
db/schema.sql        # Single source of truth for migrations
db/seeds/            # Development seed data
lib/db.ts            # better-sqlite3 instance + typed queries
lib/stripe.ts        # Stripe client + webhook handler
lib/auth.ts          # Session helpers
lib/validation.ts    # Zod schemas
tests/db.test.ts
tests/api.test.ts
scripts/migrate.ts   # Run schema.sql against DB
scripts/seed.ts

## SQL Migration Rules
- One schema.sql file - full DDL, not incremental. Rerunnable via DROP IF EXISTS + CREATE.
- Never use ALTER TABLE in production. Swap the table, update references, drop old.
- All timestamps are TEXT in ISO-8601, never DATETIME.
- Soft deletes via deleted_at TEXT, hard-delete only after 30 days.
- Foreign keys enabled (PRAGMA foreign_keys = ON) - enforce at DB level.

## Component Patterns
- Server Components by default. Only use use client when you need interactivity.
- Props are typed interfaces, not any.
- No inline styles. Tailwind classes only.
- Button component accepts variant (primary|secondary|ghost) and size (sm|md|lg).

## Anti-Patterns
- Do not put business logic in components - extract to lib/ functions.
- Do not use getServerSideProps - this is App Router, use server components.
- Do not create a new SQLite connection per request - singleton in lib/db.ts.
- Do not store session data in the database - use JWT or provider sessions.
- Do not write raw SQL strings without Zod validation on inputs.
- Do not use console.log in production - use a structured logger.

## Dev Commands
npm run dev          # Start dev server
npm run migrate      # Apply schema.sql to dev DB
npm run seed         # Load seed data
npm run test         # Run tests (vitest)
npm run build        # Production build
npm run start        # Start production server

## What We Do Not Do (And Why)
- No Prisma - SQLite does not need an ORM. Raw SQL is faster and more transparent.
- No Redis - SQLite handles concurrency fine for a SaaS with under 10K concurrent users.
- No monorepo - Keep it simple. One repo, one deploy.
- No GraphQL - REST plus typed responses is sufficient and simpler to debug.
- No TypeScript any - Every type matters. Use zod for runtime validation.