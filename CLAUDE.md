# CLAUDE.md - Next.js 15 + SQLite SaaS Project

## Stack

- **Next.js 15** (App Router) - pages, layouts, server components, server actions, route handlers
- **SQLite** via better-sqlite3 (local dev) or Turso (production)
- **Drizzle ORM** - schema definition, migrations, queries
- **Tailwind CSS** + **shadcn/ui** - styling and component library
- **Auth.js** (v5) - authentication with credentials, OAuth, and magic links
- **Stripe** - subscription billing, webhooks
- **Resend** - transactional emails
- **Vercel** / **Docker** - deployment

## Dev Commands

| Command | Description |
|---------|-------------|
| pnpm dev | Start dev server on :3000 |
| pnpm build | Production build |
| pnpm db:generate | Generate Drizzle migration |
| pnpm db:migrate | Apply pending migrations |
| pnpm db:studio | Open Drizzle Studio |
| pnpm lint | ESLint + Prettier check |
| pnpm test | Vitest (unit) + Playwright (e2e) |
| pnpm typecheck | tsc --noEmit |

## Folder Structure

app/                  # Next.js App Router pages and API routes
  (auth)/           # Auth pages (login, register, forgot-password)
  (dashboard)/      # Authenticated app pages (layout with sidebar)
  api/              # API route handlers (webhooks, server endpoints)
  layout.tsx        # Root layout
components/           # Shared UI components
  ui/               # shadcn/ui primitives (button, input, card, etc.)
  forms/            # Form components (react-hook-form wrappers)
db/                   # Database layer
  schema/           # Drizzle schema definitions
  migrations/       # Generated migration files
  queries/          # Reusable query helpers
  index.ts          # DB connection (better-sqlite3 / Turso)
lib/                  # Utility functions
  auth.ts           # Auth.js configuration
  stripe.ts         # Stripe client + helpers
  email.ts          # Resend email client
  utils.ts          # General utilities
actions/              # Server Actions (mutations)
public/               # Static assets
types/                # Shared TypeScript types
.env.local            # Environment variables
next.config.ts
tailwind.config.ts
tsconfig.json
## Database Rules

- All schema changes go through Drizzle Kit migrations
- Foreign keys are always indexed for query performance
- Soft deletes use a deletedAt nullable timestamp column
- Timestamps are stored as integer Unix seconds
- User-facing IDs are CUID2 (not auto-increment)
- Migrations: edit schema -> pnpm db:generate -> review -> pnpm db:migrate

## Component Patterns

- **Server Components (default)**: Fetch data directly, pass to client children
- **Client Components**: Mark with use client only when using useState, useEffect, event handlers
- **Server Actions**: Define in actions/, validate with Zod, use useActionState

## Authentication

- Auth.js v5 configured in lib/auth.ts
- Read session via auth() helper in server components
- Protect pages with middleware.ts
- Admin-only routes redirect to /403

## State Management

- **Server state**: React Server Components
- **URL state**: Search params for filters, pagination, tabs
- **Form state**: react-hook-form + zod + Server Actions
- **No global state library** - no Redux, no Zustand, no Jotai

## What We Don't Do

1. No useEffect for data fetching - use Server Components instead
2. No prop drilling - server components fetch at every level
3. No raw SQL outside db/queries/ - use Drizzle query builder
4. No any types - strict TypeScript with strict: true
5. No client-side routing libraries - use Next.js Link and useRouter
6. No separate API server - use Route Handlers or Server Actions
7. No Docker for local dev - pnpm dev is sufficient

## Environment Variables

DATABASE_URL=file:./data/dev.db
AUTH_SECRET=...
AUTH_GITHUB_ID=...
STRIPE_SECRET_KEY=...
NEXT_PUBLIC_APP_URL=http://localhost:3000

## Performance Rules

- Images use next/image with explicit width/height
- Large lists use React Virtualizer (@tanstack/react-virtual)
- DB queries always include .limit() - no unbounded results
- API routes return NextResponse.json() with proper caching headers
