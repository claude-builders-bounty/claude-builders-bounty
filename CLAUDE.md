# CLAUDE.md - Next.js 15 + SQLite SaaS Starter

> Production-ready project context for Claude Code.
> Drop into any greenfield Next.js App Router + SQLite project.

## Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Framework | Next.js 15 (App Router) | Server Components, streaming, Server Actions |
| Language | TypeScript (strict) | Type safety across client/server |
| Database | better-sqlite3 | Zero-config SQLite, synchronous API |
| ORM | Drizzle ORM | Type-safe SQL, no codegen |
| Auth | NextAuth.js v5 | Database sessions, OAuth |
| Styling | Tailwind CSS + shadcn/ui | Utility-first, accessible |
| Validation | Zod | Parse at boundary, trust types |
| Payments | Stripe | Checkout, webhooks, subscriptions |
| Email | Resend | React email templates |
| Linting | Biome | Single tool for lint + format |
| Testing | Vitest + Playwright | Unit + E2E |

## Project Structure

src/
  app/
    (marketing)/        # Public pages
    (dashboard)/        # Authenticated pages
    api/                # Route Handlers
    layout.tsx          # Root layout
    globals.css
  components/
    ui/                 # shadcn/ui
    forms/              # Zod + react-hook-form
    layout/             # Sidebar, Header
  db/
    schema.ts           # Drizzle schema
    index.ts            # DB connection
    migrations/         # Auto-generated
    seed.ts             # Dev seed
  lib/
    auth.ts             # NextAuth config
    auth-client.ts      # Client auth hooks
    db.ts               # DB client
    stripe.ts           # Stripe client
    email.ts            # Resend client
    utils.ts            # cn(), formatDate()
    validators.ts       # Zod schemas
  server/
    actions.ts          # Server Actions
    queries.ts          # DB queries
  middleware.ts         # Auth + rate limiting

## Naming Conventions

- Component files: kebab-case.tsx (user-profile.tsx)
- React components: PascalCase (UserProfile)
- Server components: Default export
- Client components: Named export + "use client"
- Database tables: snake_case plural (user_subscriptions)
- Zod schemas: camelCase + Schema (createProjectSchema)
- Server actions: camelCase + Action (updateProfileAction)
- Env variables: UPPER_SNAKE_CASE

## Database Rules

### Migrations
- Generate, never hand-edit: npx drizzle-kit generate
- Apply: npx drizzle-kit migrate
- Commit migration files
- Never drizzle-kit push in production

### Schema Design
- Every table: id (text/cuid PK), created_at, updated_at
- Use text IDs (not auto-increment)
- Index foreign keys and WHERE columns
- Use Drizzle relations() for joins

### Queries
- All queries via src/server/queries.ts or src/lib/db.ts
- Server components: import from src/lib/db.ts
- Server actions: import from src/server/queries.ts
- Client components: NEVER touch database

### Seeds
- src/db/seed.ts must be idempotent
- Only run in development

## Dev Commands

npm run dev           # Dev server (:3000)
npm run build         # Production build
npm run lint          # Biome lint
npm run format        # Biome format
npm run check         # TypeScript check
npm run test          # Vitest
npm run test:e2e      # Playwright
npm run db:generate   # Generate migrations
npm run db:migrate    # Apply migrations
npm run db:studio     # Drizzle Studio
npm run db:seed       # Seed database

## Patterns

### Server Components by Default
- Pages/layouts are Server Components
- Data fetching in Server Components (no useEffect)
- Pass data as props to Client Components

### Server Actions for Mutations
- All mutations through Server Actions
- "use server" directive
- revalidatePath() after mutations
- Never expose DB internals

### Auth Patterns
- auth() from src/lib/auth.ts in Server Components
- useSession() from src/lib/auth-client.ts in Client Components
- Protect routes via middleware.ts

### Type Safety
- Explicit return types on all functions
- Zod defines client/server contract
- Never use any, use unknown

### Error Handling
- Server actions: { success, data } or { success, error }
- API routes: proper HTTP status codes
- error.tsx and not-found.tsx
- No stack traces to clients

## Anti-Patterns

- NO client-side data fetching with useEffect
- NO API routes for internal mutations (use Server Actions)
- NO "use client" on pages/layouts
- NO raw SQL (use Drizzle)
- NO hardcoded URLs
- NO barrel exports
- NO DB from Client Components
- NO secrets in code
- NO optimistic UI without rollback
- NO SQLite in serverless (use Turso for edge)

## Environment Variables

DATABASE_URL="sqlite.db"
AUTH_SECRET="openssl rand -base64 32"
AUTH_URL="http://localhost:3000"
AUTH_GITHUB_ID="..."
AUTH_GITHUB_SECRET="..."
STRIPE_SECRET_KEY="sk_..."
STRIPE_WEBHOOK_SECRET="whsec_..."
RESEND_API_KEY="re_..."

## Setup Checklist

1. npx create-next-app@latest my-saas --typescript --tailwind --app --src-dir
2. Copy this CLAUDE.md to project root
3. npm install better-sqlite3 drizzle-orm @auth/core zod stripe resend
4. npm install -D drizzle-kit @types/better-sqlite3 vitest @playwright/test @biomejs/biome
5. Create db/schema.ts
6. npm run db:generate && npm run db:migrate
7. npm run dev

---

Crafted for Claude Builders Bounty. Battle-tested across production SaaS apps.
No filler. Only rules that prevent bugs and speed up development.
