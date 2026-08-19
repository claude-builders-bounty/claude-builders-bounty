# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack

- **Runtime**: Node.js 22+
- **Framework**: Next.js 15 (App Router, `src/` layout)
- **Language**: TypeScript 5.6+ (strict mode, no `any`)
- **Database**: SQLite via `better-sqlite3` (synchronous driver — no async DB code)
- **Migrations**: `drizzle-kit` with Drizzle ORM
- **Styling**: Tailwind CSS 4 (no custom CSS files unless component-specific)
- **Auth**: NextAuth.js v5 (Auth.js) with credentials provider
- **Package manager**: pnpm 9+
- **Testing**: Vitest + React Testing Library

## Folder Structure

```
src/
  app/                  # Next.js App Router pages
    (auth)/login/
    (auth)/register/
    (dashboard)/
      layout.tsx         # Shared dashboard shell (sidebar, header)
      page.tsx           # Redirects to /dashboard/overview
      overview/
      settings/
    api/                # Route handlers (no pages here)
      auth/[...nextauth]/route.ts
      trpc/[trpc]/route.ts
    layout.tsx           # Root layout (fonts, providers)
    globals.css          # Tailwind directives ONLY
  components/
    ui/                 # Primitives (Button, Input, Modal — no business logic)
    features/           # Feature-specific components (BillingCard, UserTable)
    layouts/            # Page-level layouts (DashboardShell, AuthShell)
  lib/
    db/
      index.ts         # Drizzle client + connection singleton
      schema/           # One file per table (users.ts, accounts.ts)
      migrations/       # Auto-generated, NEVER edit manually
    auth.ts             # NextAuth config
    auth-config.ts      # Auth options (providers, callbacks, session)
    trpc.ts             # tRPC init
    utils.ts            # General utilities (cn, formatDate, formatCurrency)
    validators.ts       # Zod schemas (input validation ONLY, not DB schemas)
  hooks/               # React hooks (useDebounce, useMediaQuery)
  types/               # TypeScript type definitions
  server/              # Server-only code (actions, services)
    actions/            # Server actions (one per feature domain)
    services/           # Business logic (user.service.ts, billing.service.ts)

public/
  images/
drizzle.config.ts
tailwind.config.ts
vitest.config.ts
```

## Naming Conventions

| Element              | Pattern                    | Example                  |
|----------------------|----------------------------|--------------------------|
| Files (components)   | PascalCase.tsx             | `BillingCard.tsx`        |
| Files (utilities)    | camelCase.ts               | `formatCurrency.ts`      |
| Files (server)       | kebab-case.ts              | `user.service.ts`        |
| DB tables            | PascalCase (class) / snake_case (column) | `UserAccount`, `created_at` |
| DB schema files      | snake_case.ts              | `user_accounts.ts`       |
| API routes           | kebab-case folders         | `api/billing/invoices/`  |
| Environment vars     | UPPER_SNAKE_CASE           | `DATABASE_URL`           |
| Components folder    | PascalCase (features) / camelCase (ui) | `features/BillingCard/` |
| CSS classes          | Tailwind only              | `flex items-center gap-2`|

## SQL / Migration Rules

1. **Every schema change** goes through `pnpm drizzle-kit generate`. Never write SQL by hand.
2. **Column naming**: `snake_case` always. `createdAt` in TS → `created_at` in SQL.
3. **Primary keys**: `id INTEGER PRIMARY KEY AUTOINCREMENT` for all tables.
4. **Timestamps**: `created_at INTEGER NOT NULL DEFAULT (unixepoch())` and `updated_at INTEGER NOT NULL DEFAULT (unixepoch())` on every table.
5. **Foreign keys**: `ON DELETE CASCADE` by default. Use `ON DELETE SET NULL` only when the referenced row must survive.
6. **Indexes**: Add an index for every foreign key and every column used in `WHERE` or `JOIN` clauses.
7. **Migrations are append-only**: Never modify a generated migration. Create a new one.
8. **SQLite limits**: No `ALTER TABLE DROP COLUMN` before SQLite 3.35.0. Use `drizzle-kit push` for dev, migrations for prod.

## Component Patterns

### UI Primitives (`components/ui/`)
- Accept only primitive props + `className` for Tailwind merge
- No state, no side effects, no business logic
- Export a single component per file
- Use `forwardRef` for components that wrap native elements

### Feature Components (`components/features/`)
- Can use hooks, server actions, and tRPC
- One folder per feature: `components/features/billing/InvoiceTable.tsx`
- Co-locate types: `InvoiceTable.types.ts` if complex

### Server Actions (`server/actions/`)
- One file per domain: `server/actions/billing.ts`, `server/actions/user.ts`
- Always use `zod` for input validation at the action boundary
- Return `{ success: boolean, data?: T, error?: string }` shape
- Never call server actions from other server actions — use services instead

### Data Fetching
- **Server components**: call services directly, no `use client`
- **Client components**: use tRPC hooks (`useQuery`, `useMutation`)
- **No** `fetch` in client components — route through tRPC or server actions

## What We Don't Do (and Why)

| Anti-pattern              | Why                                                    |
|--------------------------|--------------------------------------------------------|
| `any` type               | Defeats TypeScript. Use `unknown` and narrow.          |
| `useEffect` for data     | Causes waterfall + stale data. Use server components.   |
| CSS modules / styled-components | Tailwind covers everything. No extra CSS pipeline. |
| Barrel exports (`index.ts`) | Breaks tree-shaking. Import directly from source.    |
| `console.log` in prod    | Use a logger with levels. `console.log` is for dev.   |
| Business logic in components | Components render. Services think.                    |
| ORM queries in components | Goes in `server/services/`.                            |
| Dynamic imports for pages | App Router handles code splitting automatically.      |
| `eslint-disable` comments | Fix the lint error or add a justified `.eslintrc` rule.|

## Dev Commands

```bash
pnpm dev                  # Start dev server (localhost:3000)
pnpm build                # Production build
pnpm start                # Start production server
pnpm test                 # Run all tests (Vitest)
pnpm test:watch            # Tests in watch mode
pnpm lint                  # ESLint + Prettier check
pnpm lint:fix              # Auto-fix lint issues
pnpm db:generate           # Generate migration from schema changes
pnpm db:migrate            # Run pending migrations
pnpm db:studio             # Open Drizzle Studio (DB GUI)
pnpm db:seed               # Seed database with fixtures
```

## Environment Variables

Required in `.env.local`:

```env
DATABASE_URL=./local.db
NEXTAUTH_SECRET=<generate-with-openssl-rand-base64-32>
NEXTAUTH_URL=http://localhost:3000
```

Optional:

```env
SMTP_HOST=smtp.resend.com
SMTP_FROM=noreply@yourapp.com
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```