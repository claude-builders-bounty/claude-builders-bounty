# CLAUDE.md — Next.js + SQLite SaaS

## Stack & Versions

- **Framework:** Next.js 15 (App Router), React 19, TypeScript 5.x
- **Database:** SQLite via better-sqlite3 (local) or Turso (production)
- **ORM:** Drizzle ORM (not Prisma — avoids binary size and cold-start issues)
- **Auth:** NextAuth.js v5 / Auth.js
- **UI:** shadcn/ui + Tailwind CSS v4
- **Forms:** react-hook-form + zod
- **Payments:** Stripe (lemon-squeezy alternative considered, Stripe preferred for flexibility)
- **Hosting:** Vercel (recommended) or Fly.io (for Turso proximity)

## Folder Structure

```
src/
  app/              # App Router pages & API routes
    (auth)/         # Auth group (login, register)
    (dashboard)/    # Protected dashboard layout
    api/            # Route handlers (trpc or plain handlers)
  components/
    ui/             # shadcn/ui primitives
    forms/          # Form components (one per feature)
    layout/         # Navbar, sidebar, footer
  lib/
    db/             # Drizzle schema, migrations, client
    auth/           # Auth.js config
    stripe/         # Stripe helpers
    utils.ts        # cn(), formatDate(), etc.
  hooks/            # Shared React hooks
  emails/           # React Email templates
public/
  images/
```

## SQL / Migration Conventions

- **All migrations are SQL files** in `src/lib/db/migrations/`
- Naming: `YYYYMMDD_HHMMSS_description.sql`
- Every migration must be reversible (include `-- DOWN` comment with rollback)
- Never edit a committed migration — create a new one
- Drizzle schema files are the source of truth; migrations are generated from them
- Use `drizzle-kit generate` to produce migrations, `drizzle-kit migrate` to apply
- Foreign keys must be explicit (Drizzle requires `references()`)
- Index every foreign key column

## Component Patterns

- **Server components by default.** Only add `'use client'` when you need hooks, event handlers, or browser APIs
- **Data fetching:** Use React Server Components with async/await. Avoid `useEffect` for data
- **Loading states:** Use `loading.tsx` files per route segment (not client-side spinners)
- **Error handling:** Use `error.tsx` boundaries (not try/catch in components)
- **Forms:** Server Actions with `useActionState`. Validate with zod on both client and server
- **Shared UI:** Always use shadcn/ui components. Never write raw Tailwind for modals, buttons, inputs

## Dev Commands

```bash
npm run dev          # Next.js dev server
npm run db:generate  # Generate Drizzle migrations
npm run db:migrate   # Apply migrations
npm run db:studio    # Drizzle Studio (browser-based DB viewer)
npm run lint         # ESLint + Prettier
npm run typecheck    # tsc --noEmit
npm run test         # Vitest
npm run test:e2e     # Playwright
```

## What We Don't Do (And Why)

| Anti-pattern | Reason |
|---|---|
| Redux / Zustand / global state | React Server Components + URL params cover 95% of state needs. The remaining 5% goes in React context |
| `pg` or `mysql2` drivers | SQLite (`better-sqlite3`/Turso) avoids connection pooling complexity and cold-start lag on serverless |
| Prisma | Binary size (150MB+) causes cold-start issues on Vercel. Drizzle is lighter and SQL-centric |
| Monorepo (turborepo/nx) | Unnecessary overhead for a single-page SaaS. Extract shared logic into `src/lib/` packages |
| `any` types | Every external API response gets a zod schema. No `any` — not even in tests |
| Inline styles / CSS modules | Tailwind utility classes + shadcn/ui. Consistent, themeable, small bundle |
| Direct `fetch` in components | Server Actions or route handlers. Keeps data access auditable and testable |

## Naming Conventions

- **Files:** camelCase for utilities (`formatDate.ts`), kebab-case for pages (`user-settings/page.tsx`), PascalCase for components (`UserAvatar.tsx`)
- **Variables:** camelCase. Booleans: `isLoading`, `hasError`, `canSubmit`
- **Database:** snake_case for columns (`created_at`), PascalCase for table names
- **API routes:** `/api/[resource]/[action]` pattern (`/api/teams/create`)
- **Environment variables:** `NEXT_PUBLIC_*` for client-safe, `process.env.*` for server-only

## Testing

- Unit: Vitest for utilities and hooks
- Integration: Vitest + MSW for API route handlers
- E2E: Playwright for critical user flows (signup, payment, team invite)
- Test files sit next to the file they test: `formatDate.ts` → `formatDate.test.ts`
