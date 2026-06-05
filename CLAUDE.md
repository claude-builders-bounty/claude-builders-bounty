# CLAUDE.md — Next.js + SQLite SaaS Project

## Stack & Versions
- **Runtime:** Node.js 22 LTS
- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript (strict mode)
- **Styling:** Tailwind CSS v4
- **UI Components:** shadcn/ui (Radix primitives)
- **Database:** SQLite via better-sqlite3 (local dev) / Turso (production)
- **ORM:** Drizzle ORM
- **Auth:** NextAuth.js v5 (Auth.js) with JWT strategy
- **Payments:** Stripe Checkout + Webhooks
- **Validation:** Zod
- **Forms:** react-hook-form + @hookform/resolvers
- **Testing:** Vitest + React Testing Library
- **Hosting:** Vercel (or Docker on any VPS)

## Project Structure
```
src/
  app/           # Next.js App Router pages and API routes
    (auth)/      # Auth-grouped routes (login, register)
    (dashboard)/ # Protected dashboard routes
    api/         # API route handlers
  components/
    ui/          # shadcn/ui primitives (Button, Card, Dialog, etc.)
    forms/       # Reusable form components with Zod schemas
    layout/      # Shell, Sidebar, Header, Footer
  lib/
    db/          # Drizzle schema, migrations, seed
    auth/        # NextAuth config, callbacks, middleware
    stripe/      # Stripe client, webhook handler, pricing config
    utils/       # Shared helpers (cn(), formatDate, etc.)
  server/        # Server-only logic (never imported in client components)
    actions.ts   # Server actions (use server)
    queries.ts   # Database queries
  types/         # Shared TypeScript types
drizzle/         # Drizzle migrations (auto-generated)
public/          # Static assets
```

## Conventions

### File Naming
- Components: `PascalCase.tsx` (e.g., `UserDropdown.tsx`)
- Utilities: `kebab-case.ts` (e.g., `format-currency.ts`)
- Route files: follow Next.js conventions (`page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`)
- Database files: `schema.ts`, `0000_migration_name.sql`

### Components
- One component per file. No exceptions.
- Default export for page components; named export for everything else.
- Props interface named `{ComponentName}Props`, always exported.
- Use `"use client"` directive ONLY when needed (state, effects, browser APIs). Prefer server components.
- Extract business logic into `lib/` or `server/` — components should be thin.

### Database / SQL
- Drizzle schema in `src/lib/db/schema.ts` — one file, all tables.
- Migrations generated with `drizzle-kit generate`, applied with `drizzle-kit migrate`.
- Never use raw SQL in application code. All queries go through Drizzle's typed API.
- Every table gets `id` (text, UUID), `createdAt`, `updatedAt`.
- Soft-delete with `deletedAt` column instead of hard-delete for user data.

### API Routes & Server Actions
- All mutations go through server actions (`"use server"`) or API routes, never direct from client.
- Validate input with Zod before any DB operation.
- Return `{ success: true, data }` or `{ success: false, error: string }` — consistent shape.
- API routes: prefix with `/api/`, use `NextResponse.json()`.

### Auth
- Protect dashboard routes with middleware (check JWT session).
- Server-side: `auth()` or `getServerSession()`.
- Client-side: `useSession()` from NextAuth React.
- Never trust `req.body.userId`. Always derive user identity from session.

### Payments (Stripe)
- Create checkout sessions server-side, redirect to Stripe.
- Handle webhooks with raw body (`buffer` config in route).
- Sync subscription status to `subscriptions` table via webhook.
- Pricing config in `src/lib/stripe/pricing.ts` — single source of truth.

## Development Commands
```bash
pnpm dev           # Start dev server (localhost:3000)
pnpm build         # Production build
pnpm start         # Start production server
pnpm db:generate   # Generate Drizzle migrations
pnpm db:migrate    # Apply migrations
pnpm db:studio     # Open Drizzle Studio (DB GUI)
pnpm test          # Run tests (Vitest)
pnpm lint          # Run ESLint
pnpm format        # Run Prettier
pnpm stripe:listen # Forward Stripe webhooks locally
```

## What We Don't Do (And Why)

- **No ORMs other than Drizzle.** We chose Drizzle for its TypeScript-first design and zero runtime overhead over raw SQL. Prisma's client generation and binary dependency add complexity we don't need with SQLite.
- **No client-side data fetching for sensitive data.** React Query goes on public data only. Protected data is fetched server-side and passed as props. This prevents JWT token leaks and simplifies the security model.
- **No API route versioning.** Single-tenant SaaS doesn't need `/v1/` prefixes. If we ever need API versioning, we'll add it then — not before.
- **No monorepo tooling.** This is a single product, not a platform. Turborepo, Nx, and workspaces add cognitive overhead without benefit at this scale.
- **No serverless databases for SQLite.** Turso gives us edge-replicated SQLite without the cold-start problem of serverless Postgres. If we outgrow SQLite, we migrate to Postgres — not before.
- **No CSS-in-JS.** Tailwind + shadcn/ui covers all our styling needs. Runtime CSS-in-JS adds bundle size and complexity for no gain.
- **No GraphQL.** REST + server actions are simpler, use less tooling, and have native Next.js support. We don't have enough interrelated data to justify GraphQL's complexity.
- **No microservices.** Monolith until it hurts. A single Next.js app with SQLite scales surprisingly far. Split services only when we have a team large enough to own them.
