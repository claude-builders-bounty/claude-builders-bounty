# CLAUDE.md — Next.js + SQLite SaaS Project

This file tells Claude Code everything it needs to know to work effectively in this codebase.

---

## Project Overview

**Type**: SaaS web application
**Stack**: Next.js 15 (App Router) · TypeScript · SQLite (via Drizzle ORM) · Tailwind CSS
**Auth**: NextAuth.js v5
**Payments**: Stripe (subscription billing)
**Deployment**: Vercel (frontend) · Fly.io or Railway (SQLite persistence)

---

## Repository Structure

```
.
├── app/                    # Next.js App Router pages & layouts
│   ├── (auth)/             # Login, register, forgot-password
│   ├── (dashboard)/        # Authenticated app shell
│   │   ├── settings/       # Account & billing settings
│   │   └── [feature]/      # Your main SaaS feature pages
│   ├── api/                # API route handlers
│   │   ├── auth/           # NextAuth route handler
│   │   ├── stripe/         # Stripe webhooks
│   │   └── [resource]/     # REST-style API routes
│   └── layout.tsx          # Root layout
├── components/             # Shared React components
│   ├── ui/                 # shadcn/ui primitives
│   └── [feature]/          # Feature-specific components
├── lib/                    # Shared utilities
│   ├── db/                 # Drizzle client + schema
│   │   ├── index.ts        # Database connection
│   │   └── schema.ts       # Table definitions
│   ├── auth.ts             # NextAuth configuration
│   ├── stripe.ts           # Stripe client
│   └── utils.ts            # General helpers
├── drizzle/                # Migration files (auto-generated)
├── public/                 # Static assets
├── .env.local              # Local environment variables (never commit)
├── drizzle.config.ts       # Drizzle Kit configuration
├── next.config.ts          # Next.js configuration
└── tailwind.config.ts      # Tailwind configuration
```

---

## Common Commands

```bash
# Development
pnpm dev                   # Start dev server on http://localhost:3000

# Database
pnpm db:generate           # Generate Drizzle migration from schema changes
pnpm db:migrate            # Apply pending migrations
pnpm db:studio             # Open Drizzle Studio (GUI browser for the DB)
pnpm db:seed               # Seed database with test data

# Code quality
pnpm lint                  # ESLint
pnpm typecheck             # tsc --noEmit
pnpm test                  # Vitest unit tests
pnpm test:e2e              # Playwright end-to-end tests

# Build & deploy
pnpm build                 # Production build
pnpm start                 # Run production build locally
```

---

## Database Rules

- **ORM**: Drizzle ORM only — never write raw SQL unless inside a `sql\`...\`` tagged template in a Drizzle query
- **Schema changes**: Always edit `lib/db/schema.ts`, then run `pnpm db:generate` to create a migration — never edit migration files by hand
- **SQLite file**: Lives at `sqlite.db` locally and at the persistent volume path in production. Never delete it.
- **Transactions**: Use `db.transaction()` for multi-table writes
- **No N+1**: Always use Drizzle `with()` relations or explicit joins — never query inside a loop

---

## Authentication Rules

- Auth is handled entirely by NextAuth.js v5
- Session is accessed via `auth()` in Server Components / Route Handlers; via `useSession()` in Client Components
- Protect pages using middleware (`middleware.ts`) or `auth()` guard at the top of server components
- Never expose `session.user.id` or email to the client unless explicitly needed
- Password hashing: bcrypt via `@auth/core`

---

## API Conventions

- Route handlers live in `app/api/[resource]/route.ts`
- Always validate request bodies with Zod before processing
- Return consistent JSON: `{ data, error, meta? }`
- Use `NextResponse.json()` with explicit status codes
- Stripe webhooks must verify the signature via `stripe.webhooks.constructEvent()`

---

## Component Conventions

- UI primitives come from `components/ui/` (shadcn/ui) — don't re-invent buttons, dialogs, etc.
- Server Components by default; add `"use client"` only when the component needs interactivity or browser APIs
- Co-locate component-specific types inside the component file
- Props interfaces are named `[ComponentName]Props`

---

## Stripe / Billing

- Products and prices are defined in the Stripe Dashboard, not in code
- `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` must be set in `.env.local`
- Use Stripe Customer Portal for subscription management — don't build your own cancellation UI
- Webhook handler at `app/api/stripe/route.ts` handles: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`
- Sync subscription status to the `subscriptions` table after every webhook event

---

## Environment Variables

```bash
# App
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Auth
AUTH_SECRET=                    # generate with: openssl rand -base64 32
AUTH_GITHUB_ID=                 # GitHub OAuth app client ID
AUTH_GITHUB_SECRET=             # GitHub OAuth app secret

# Database
DATABASE_URL=file:./sqlite.db   # local; change to absolute path in prod

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

Never commit `.env.local`. The `.env.example` file (committed) lists all required keys with placeholder values.

---

## Testing

- **Unit tests**: Vitest — live alongside the source file as `*.test.ts`
- **E2E tests**: Playwright — live in `tests/e2e/`
- Mock the database in unit tests using `vi.mock('~/lib/db')`
- Stripe webhooks are tested using `stripe-mock` in CI

---

## Error Handling

- Use typed `Result<T, E>` pattern for business logic (not try/catch everywhere)
- Log errors server-side with `console.error` (replace with a real logger in production)
- Display user-facing errors via toast notifications using the `useToast()` hook
- Never expose raw error messages from the server to the client

---

## Do / Don't

| Do | Don't |
|---|---|
| Use `pnpm` as the package manager | Use `npm` or `yarn` |
| Keep business logic in `lib/` | Put business logic in components |
| Validate all inputs with Zod | Trust raw request bodies |
| Use `db.transaction()` for multi-step writes | Make multiple sequential writes without a transaction |
| Follow the existing file structure | Create top-level directories without discussion |
| Add tests for new API routes | Skip tests for "simple" routes |
| Use Tailwind classes | Write custom CSS unless absolutely necessary |
| Check for an existing shadcn component first | Build a new UI component from scratch |
