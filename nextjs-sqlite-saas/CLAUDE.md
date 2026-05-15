# CLAUDE.md — Next.js + SQLite SaaS

## Stack & Versions

- **Runtime:** Node.js 22 LTS
- **Framework:** Next.js 15 App Router (React 19, RSC first)
- **Language:** TypeScript 5.7+, `strict: true`
- **Database:** SQLite via `better-sqlite3` (local dev / single-server) or `@libsql/client` (Turso for edge)
- **Migrations:** Drizzle ORM with `drizzle-kit push` (dev) / `drizzle-kit generate` + `migrate` (prod)
- **Auth:** NextAuth v5 with JWT strategy (no database sessions — stateless)
- **Styling:** Tailwind CSS v4 + shadcn/ui primitives
- **Validation:** Zod on both client (forms) and server (API boundaries)
- **Payments:** Stripe via `@stripe/stripe-js` (client) + `stripe` (server RSC actions)

## Folder Structure

```
app/
  (auth)/           # auth-guarded layout group (no auth check at layout)
    dashboard/       # page.tsx = server component by default
    settings/        # nested under (auth), shared layout
  (marketing)/       # public pages, no auth
    page.tsx         # landing
    pricing/page.tsx
  api/
    stripe/          # webhook route → Stripe signature verif.
    auth/            # NextAuth catch-all
  layout.tsx         # root layout (providers, font, html head)
  globals.css        # Tailwind directives only
components/
  ui/                # shadcn primitives: Button, Input, Dialog…
  forms/             # domain forms + Zod schemas
  layouts/           # Sidebar, Navbar, Shell
lib/
  db/
    schema.ts        # Drizzle table definitions
    index.ts         # db singleton (cached on import)
    migrate.ts       # programmatic migration runner
  auth.ts            # NextAuth config + callbacks
  stripe.ts           # server-side Stripe SDK
  utils.ts            # cn(), formatCurrency(), slugify()…
  validations/        # Zod schemas re-exported
server/
  actions/            # "use server" — mutations
  queries/             # server-only data fetchers (called from RSC)
public/
  favicon.ico
  og-image.png
hooks/                 # client-side hooks ("use client")
  use-mutation.ts
  use-optimistic.ts
.env.local             # DB_FILE_NAME, STRIPE_SECRET_KEY, AUTH_SECRET…
drizzle.config.ts
next.config.ts
tailwind.config.ts
tsconfig.json
```

## SQL / Migration Conventions

- **Always use Drizzle.** Never write raw DDL unless Drizzle can't express it.
- Table names are `snake_case`; column names match JavaScript `camelCase`.
- Every table has `id: integer("id").primaryKey({ autoIncrement: true })`.
- Timestamps: `createdAt` (set once), `updatedAt` (updated in trigger or app). Use `integer("created_at", { mode: "timestamp" })`.
- **Migration rules:**
  1. `pnpm db:generate` creates migration SQL from schema diffs.
  2. Review the generated `.sql` files — never assume they're safe.
  3. `pnpm db:migrate` applies pending migrations.
  4. **Never** `drizzle-kit push` in production. It drops data.
  5. Add `.notNull().default()` to new non-nullable columns.

## Component Patterns

- **Server-first:** Every page starts as a server component. Only add `"use client"` when you need interactivity (state, effects, event handlers).
- **Data flow:** RSC queries DB directly (no API layer) → passes data to client components as props.
- **Mutations:** `server actions` in `server/actions/` → function is exported and called from Client Component `action={myAction}` or form `action` prop.
- **Optimistic updates:** `useOptimistic` + `startTransition` — never use `router.refresh()` as a crutch.
- **Loading states:** Every page exports `loading.tsx` (RSC suspense boundary). Every form shows `pending = useFormStatus()`.
- **Error boundaries:** Every route exports `error.tsx`. Wrap data-dependent sections in `<ErrorBoundary>`.
- **shadcn/ui**: All UI primitives come from `components/ui/`. Add new primitives with `npx shadcn@latest add [name]`.

## Dev Commands

```bash
pnpm dev           # next dev --turbo
pnpm build         # next build (catches type errors)
pnpm db:studio     # drizzle-kit studio → http://localhost:4983
pnpm db:generate   # diff schema → SQL migration
pnpm db:migrate     # apply pending migrations
pnpm db:push       # schema → DB directly (DEV ONLY)
pnpm check         # tsc --noEmit
pnpm lint          # next lint + eslint
pnpm fmt           # prettier --write
```

## What We Don't Do (And Why)

- **No REST/GraphQL API layer.** RSC queries DB directly. Adding an API adds latency, complexity, and an attack surface — for zero benefit when all rendering happens server-side.
- **No `pages/` router.** App Router only. Dual-router projects confuse AI assistants and teammates.
- **No `any` in production code.** Handles `string | undefined` or `Record<string, unknown>` explicitly.
- **No environment variables in client components** (except `NEXT_PUBLIC_*`). Use server components or Route Handlers to inject them.
- **No `useContext` for derived server data.** Server Component passes props; context is for client-only state (theme, toast queue, sidebar toggle).
- **No ORM magic.** Drizzle is the lowest-level typed ORM we trust. No Prisma (binary RPC overhead), no raw Knex (unless you love boilerplate).
- **No `useEffect` for data fetching.** RSC or TanStack Query on client side. useEffect + fetch is an anti-pattern in Next.js 15.
- **No `dangerouslySetInnerHTML` outside a sanitizer.** Always run through `DOMPurify.sanitize()`.
- **No console.log in production.** Use a logger (e.g., `pino`) with levels.

## Verified

To confirm this CLAUDE.md works, create a new Next.js 15 project:
```bash
npx create-next-app@latest myapp --ts --app --tailwind --eslint
cd myapp
# paste this CLAUDE.md
# Ask Claude Code:"What's the folder structure?" — should answer without follow-up questions.
```