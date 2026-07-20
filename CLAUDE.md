# CLAUDE.md — Next.js 15 App Router + SQLite SaaS Template

This project is a production-grade SaaS application built with **Next.js 15** (App Router), **TypeScript**, **better-sqlite3** (or Turso), **Tailwind CSS**, **Zod**, **Drizzle ORM**, and **Vercel**.

## Stack & Versions

- **Next.js 15** — App Router, Server Components by default
- **TypeScript 5** — strict mode enabled
- **better-sqlite3** — local dev; **Turso** — production
- **Drizzle ORM** — migrations via `drizzle-kit`
- **Tailwind CSS 4** — utility-first styling
- **Zod** — schema validation on all inputs/outputs
- **Vercel** — deployment target
- **Node.js 20+** — required runtime

## Folder Structure

```
src/
├── app/                    # App Router pages + layouts
│   ├── (auth)/            # Auth route group
│   ├── (dashboard)/       # Protected dashboard
│   └── api/               # Route handlers
├── components/            # Shared React components
│   ├── ui/                # Primitive UI atoms
│   └── layout/            # Layout wrappers
├── lib/                   # Pure utilities
│   ├── db/                # Drizzle schema + migration helpers
│   ├── auth/              # Session + permission logic
│   └── validation/        # Zod schemas
├── hooks/                 # Custom React hooks
├── types/                 # Global TypeScript types
└── styles/                # Tailwind config + global CSS
prisma/                     # Only if using Prisma (not here)
migrations/                 # Drizzle SQL dumps
tests/                      # Playwright + Vitest
package.json
next.config.ts
drizzle.config.ts
tailwind.config.ts
tsconfig.json
```

## Naming Conventions

- **Files**: kebab-case (`user-profile.tsx`, `get-orders.ts`)
- **Components**: PascalCase (`UserAvatar.tsx`)
- **Types/Interfaces**: PascalCase (`UserProfile`, `OrderItem`)
- **Database tables**: snake_case (`user_accounts`, `subscription_plans`)
- **Columns**: snake_case (`created_at`, `is_active`)
- **Functions**: camelCase (`getActiveUsers()`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_UPLOAD_SIZE`)

Every name must describe intent, not implementation. Prefer `getActiveSubscriptions()` over `fetchData()`.

## Database Rules

### Schema Design

- Use **Drizzle ORM** exclusively. Never write raw SQL in application code except inside migration files.
- Every table must have:
  - `id` (text, UUID v4)
  - `created_at` (timestamp, default now())
  - `updated_at` (timestamp, default now(), auto-update trigger)
- Foreign keys must be explicitly named: `fk_orders_user_id`

### Migrations

```bash
npm run db:generate   # Generate migration from schema changes
npm run db:migrate    # Apply pending migrations
npm run db:push       # Dev-only: push schema to local DB (never in CI/production)
```

- **One change per migration.** No bulk refactors.
- Migrations are **immutable once applied**. To fix a bad migration, create a new corrective migration, never edit old ones.
- Always test migrations against an empty database before deploying.

### Queries

- Use **parameterized queries only**. No string interpolation.
- Wrap every mutation in a transaction when it touches multiple tables.
- Prefer `select` over raw `query` unless Drizzle cannot express the operation.
- Index foreign keys and frequently filtered columns.

### Anti-Patterns

- ❌ Do NOT use `any` in database layer.
- ❌ Do NOT bypass Drizzle for performance — profile first, optimize second.
- ❌ Do NOT store secrets in `.env.local`; use Vercel Environment Variables.
- ❌ Do NOT use `@prisma/client` alongside Drizzle.

## Component Patterns

### Server Components First

- Default to **Server Components**. Only convert to Client Components when you need:
  - `useState`, `useEffect`, event handlers
  - Browser APIs (`localStorage`, `window`)
  - Third-party client libraries

### Data Flow

```
Client Component → Server Action / Route Handler → Drizzle Query → Response
```

- Keep business logic in **Server Actions** or **Route Handlers**.
- Pass only serialized data to Client Components.
- Use **React Query** or **SWR** for cache invalidation on mutations.

### Form Handling

- Use **Zod schemas** for validation on both client and server.
- Server Actions handle submission; Client Components handle UX feedback.
- Display errors via **React Hook Form** + Zod resolver.

### Anti-Patterns

- ❌ Do NOT put database calls directly in Client Components.
- ❌ Do NOT pass entire user objects to clients — send only what's needed.
- ❌ Do NOT use `getServerSideProps` — this is App Router.

## Dev Commands

```bash
npm run dev          # Start dev server on :3000
npm run build        # Production build
npm run start        # Start production server
npm run lint         # ESLint + TSC check
npm run test         # Run Vitest unit tests
npm run test:e2e     # Run Playwright E2E tests
npm run db:generate  # Generate Drizzle migration
npm run db:migrate   # Apply migrations
npm run db:studio    # Open Drizzle Studio
```

## What We Don't Do

- **No class components** — functional components only.
- **No Redux/Zustand** — use React Context or Server State libraries.
- **No manual SQL joins** — let Drizzle handle relations.
- **No `console.log` in production** — use structured logging (`pino` or `next-logger`).
- **No unvalidated user input** — every external input passes through Zod.
- **No direct `fs` access in Next.js** — use environment variables or Vercel KV/Blob.

## Why These Rules?

- **Server Components first** reduces bundle size and improves security by keeping sensitive logic server-side.
- **Drizzle + migrations** ensures schema changes are version-controlled and reversible.
- **Zod everywhere** prevents type mismatches between client and server.
- **One migration per change** makes rollbacks and audits trivial.
- **No raw SQL in app code** keeps the ORM layer consistent and portable.

## Testing Checklist

Before merging any PR:

- [ ] All new routes have Zod validation.
- [ ] Database migrations are tested against empty DB.
- [ ] Server Actions return typed responses.
- [ ] No `any` types in `lib/` or `app/`.
- [ ] E2E tests cover critical user flows.
- [ ] Lint passes with zero warnings.
