# CLAUDE.md — Next.js + SQLite SaaS Project

## Project Overview
This is a SaaS application built with Next.js (App Router) and SQLite (via better-sqlite3/Drizzle ORM). It follows a monorepo-lite structure with the database layer co-located in the same Next.js project.

## Tech Stack
- **Framework**: Next.js 14+ (App Router, Server Components, Server Actions)
- **Database**: SQLite via better-sqlite3, managed with Drizzle ORM
- **Auth**: NextAuth.js v5 (Auth.js) with email/password + OAuth providers
- **Styling**: Tailwind CSS + shadcn/ui components
- **Payments**: Stripe (subscriptions + one-time payments)
- **Deployment**: Vercel (or any Node.js host with persistent filesystem for SQLite)

## Directory Structure
```
├── app/                    # Next.js App Router pages and layouts
│   ├── (auth)/             # Auth routes (login, register, forgot-password)
│   ├── (dashboard)/        # Protected dashboard routes
│   ├── (marketing)/        # Public marketing pages
│   ├── api/                # API routes (webhooks, REST endpoints)
│   │   ├── stripe/         # Stripe webhook handler
│   │   └── auth/           # NextAuth API routes
│   └── layout.tsx          # Root layout
├── components/             # React components
│   ├── ui/                 # shadcn/ui primitives (Button, Dialog, etc.)
│   └── forms/              # Form components with validation
├── db/                     # Database layer
│   ├── schema.ts           # Drizzle ORM schema definitions
│   ├── migrations/         # SQL migration files
│   ├── index.ts            # Database connection singleton
│   └── queries/            # Query functions grouped by domain
├── lib/                    # Shared utilities
│   ├── auth.ts             # Auth configuration
│   ├── stripe.ts           # Stripe client and helpers
│   └── utils.ts            # General utilities
├── public/                 # Static assets
└── drizzle.config.ts       # Drizzle ORM configuration
```

## Key Conventions

### Database
- All database access goes through `db/queries/` — never import `db/index.ts` directly in components
- Use Drizzle ORM for all queries (no raw SQL except in migrations)
- Run migrations with `npx drizzle-kit push` (development) or `npx drizzle-kit migrate` (production)
- SQLite file lives at `./data/app.db` — this path is set in `db/index.ts`
- Always use transactions for multi-step writes: `db.transaction(async (tx) => { ... })`

### Authentication
- Protected routes use the `(dashboard)` route group with a shared layout that checks session
- Auth middleware in `middleware.ts` redirects unauthenticated users to `/login`
- Use `auth()` from `lib/auth.ts` in Server Components to get the current session
- Use `useSession()` from `next-auth/react` in Client Components

### API Routes
- Stripe webhooks go to `app/api/stripe/webhook/route.ts` — verify signature with `stripe.webhooks.constructEvent()`
- All API routes return `NextResponse.json()` with appropriate status codes
- Use `z.object()` (Zod) for request body validation in every API route

### Styling
- Use shadcn/ui components from `components/ui/` — do not create custom primitives
- Tailwind classes only — no CSS modules or styled-components
- Responsive: mobile-first with `sm:`, `md:`, `lg:` breakpoints
- Dark mode: use `dark:` variant, theme toggle in dashboard header

### Payments (Stripe)
- Subscription plans defined in `lib/stripe.ts` with price IDs from env vars
- Webhook handler updates user subscription status in SQLite on `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`
- Use `stripe.checkout.sessions.create()` for new subscriptions
- Never trust client-side subscription status — always verify server-side

### Error Handling
- Server Actions: return `{ error: string }` on failure, redirect or return `{ success: true }` on success
- API routes: return appropriate HTTP status codes (400, 401, 403, 404, 500)
- Client: use `toast()` from shadcn/ui for user-facing error messages
- Log errors with `console.error()` — structured logging in production

### Testing
- Unit tests: Vitest for utility functions and database queries
- Component tests: React Testing Library for form components
- E2E tests: Playwright for critical user flows (signup, login, subscribe, use feature)
- Run tests: `npm test` (unit), `npx playwright test` (e2e)

## Environment Variables
```
# Database
DATABASE_URL=./data/app.db

# Auth
AUTH_SECRET=<random-32-char-string>
AUTH_URL=http://localhost:3000

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_PRICE_ID_PRO=price_...

# OAuth (optional)
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

## Common Commands
```bash
npm run dev          # Start development server (port 3000)
npm run build        # Production build
npm run start        # Start production server
npm test             # Run unit tests
npx drizzle-kit push # Apply schema changes to database
npx drizzle-kit studio # Open Drizzle Studio (database GUI)
npx playwright test  # Run E2E tests
```

## Do NOT
- Import database connection directly in components — use `db/queries/` functions
- Store secrets in code — use environment variables
- Use raw SQL outside of migration files
- Skip Stripe webhook signature verification
- Trust client-side session data for authorization decisions
- Use `any` type — prefer `unknown` with type narrowing
- Create new UI primitives when shadcn/ui has an equivalent
