# Project: Next.js 15 SaaS with SQLite

## Stack & Versions
- **Runtime**: Node.js 20+
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript 5.x (strict mode)
- **Database**: SQLite via `better-sqlite3` or Turso (libSQL)
- **ORM**: Drizzle ORM
- **Auth**: NextAuth.js v5
- **Styling**: Tailwind CSS 4
- **Package Manager**: pnpm 9

## Folder Structure
```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/             # Auth group (login, register, forgot-password)
│   ├── (dashboard)/        # Dashboard group (protected routes)
│   │   ├── settings/       # User settings
│   │   └── billing/        # Billing & subscription
│   ├── api/                # API routes (route handlers)
│   │   ├── auth/[...nextauth]/route.ts
│   │   └── webhooks/       # Stripe/webhook handlers
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Landing page
├── components/
│   ├── ui/                 # Primitive UI components (Button, Input, Modal)
│   ├── forms/              # Form components
│   └── features/           # Feature-specific components
├── lib/
│   ├── db/                 # Database client & schema
│   │   ├── schema.ts       # Drizzle schema definitions
│   │   ├── migrate.ts      # Migration runner
│   │   └── seed.ts         # Seed data
│   ├── auth.ts             # Auth configuration
│   ├── stripe.ts           # Stripe client
│   └── utils.ts            # Shared utilities
├── hooks/                  # React hooks
├── actions/                # Server actions
└── types/                  # TypeScript type definitions
```

## Naming Conventions

### Files
- Components: `PascalCase.tsx` (e.g., `UserProfile.tsx`, `BillingCard.tsx`)
- Utilities: `camelCase.ts` (e.g., `formatCurrency.ts`, `parseDate.ts`)
- Server actions: `camelCase.ts` in `actions/` (e.g., `updateSettings.ts`)
- API routes: `route.ts` in `app/api/` directories

### Database
- Tables: `snake_case` (e.g., `user_accounts`, `subscription_plans`)
- Columns: `snake_case` (e.g., `created_at`, `is_active`, `user_id`)
- Primary keys: `id` (autoincrement integer or cuid text)
- Foreign keys: `{table}_id` (e.g., `user_id`, `workspace_id`)
- Timestamps: `created_at` and `updated_at` on every table (datetime text, ISO 8601)
- Booleans: prefix with `is_` or `has_` (e.g., `is_active`, `has_subscription`)
- Soft deletes: `deleted_at` column, never hard-delete

### Variables
- React state: `camelCase` with `set` prefix (e.g., `isLoading`, `setIsLoading`)
- Constants: `SCREAMING_SNAKE_CASE` (e.g., `MAX_RETRY_COUNT`)
- Types/Interfaces: `PascalCase` (e.g., `UserProfile`, `SubscriptionPlan`)

## SQL / Migration Conventions

### Rules
1. **Never modify a migration after it runs.** Create a new migration instead.
2. **Always use transactions** in migrations that modify data.
3. **Add indexes** for any column used in WHERE, JOIN, or ORDER BY clauses.
4. **Use TEXT for dates** in SQLite (ISO 8601 format: `2026-04-14T12:00:00Z`).
5. **No raw SQL in application code.** Use Drizzle ORM query builder exclusively.
6. **Every schema change** requires a corresponding migration file.
7. **Seed data** goes in `db/seed.ts`, not in migrations.

### Migration File Format
```typescript
// src/lib/db/migrations/0003_add_subscription_table.ts
import { sql } from 'drizzle-kit';

export default async function migrate(db: Database) {
  await db.run(sql`
    CREATE TABLE IF NOT EXISTS subscription_plans (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      price_cents INTEGER NOT NULL,
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now'))
    )
  `);
}
```

## Component Patterns

### Server Components (default)
- All components are Server Components unless explicitly marked `'use client'`
- Fetch data directly in Server Components, no `useEffect` for data fetching
- Pass server data to Client Components via props

### Client Components
- Only use `'use client'` when you need: browser APIs, event handlers, React hooks (useState, useEffect)
- Keep Client Components small — push logic to Server Components when possible
- Never import Server Actions directly into Client Components; use `action` prop on forms

### Data Fetching
- **Server Components**: Fetch directly with Drizzle (no API layer needed)
- **Client Components**: Use Server Actions or API routes
- **Streaming**: Use `loading.tsx` files and `Suspense` boundaries for progressive loading

### Error Handling
- Use `error.tsx` boundaries for route-level error handling
- Wrap async operations in try/catch with user-friendly error messages
- Never expose stack traces or internal error details to the client

## Dev Commands
```bash
pnpm dev              # Start dev server
pnpm build            # Production build
pnpm start            # Start production server
pnpm lint             # Run ESLint
pnpm lint:fix         # Auto-fix ESLint issues
pnpm type-check       # Run TypeScript type checking
pnpm db:generate      # Generate Drizzle migration
pnpm db:migrate       # Run pending migrations
pnpm db:seed          # Seed database
pnpm db:studio        # Open Drizzle Studio (DB GUI)
pnpm test             # Run tests
pnpm test:watch       # Run tests in watch mode
```

## What We Don't Do (And Why)

1. **No `any` type.** Use `unknown` and narrow, or define the proper type. `any` defeats TypeScript's purpose.
2. **No CSS-in-JS libraries.** Tailwind handles everything. Adding styled-components or emotion increases bundle size for no benefit.
3. **No Prisma.** Drizzle is lighter, faster for SQLite, and gives us full control over SQL. Prisma's engine binary causes deployment issues on serverless platforms.
4. **No API routes for internal data.** If both caller and callee are in this app, use Server Actions or direct Drizzle queries in Server Components. API routes are for external consumers (webhooks, third-party integrations).
5. **No barrel exports (`index.ts` re-exports).** They break tree-shaking and make dependency graphs opaque. Import directly from the source file.
6. **No `// @ts-ignore`.** Fix the type error. If the external library's types are wrong, use a type assertion on the specific expression, not a blanket ignore.
7. **No environment variables in client code.** Server-only values stay in Server Components/Actions. Client-safe values go in `NEXT_PUBLIC_*` prefix.
8. **No polling for data freshness.** Use Server Actions with `revalidatePath` or `revalidateTag`. Polling wastes bandwidth and battery.
9. **No nested ternaries.** Use early returns, extracted variables, or a helper function. Nested ternaries are unreadable.
10. **No `fetch` in Client Components for app data.** Use Server Components or Server Actions. Client-side `fetch` is for external APIs only.
