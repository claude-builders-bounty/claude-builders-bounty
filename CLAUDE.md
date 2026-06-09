# CLAUDE.md — Next.js 15 + SQLite SaaS

## Project Identity
You are working on a SaaS web application built with Next.js 15 App Router, TypeScript, and SQLite (Turso/libsql). The project prioritizes type safety, simplicity, and shipping velocity. Avoid over-engineering; prefer boring technology that works.

## Project Structure
```
src/
  app/          # Next.js App Router — routes, layouts, loading, error boundaries
  components/   # Shared React components (Server Components by default)
  lib/          # Business logic, utilities, shared constants
  db/           # Database: schema, migrations, seed scripts, query helpers
  actions/      # Server Actions — mutations called from forms
  hooks/        # Client-side React hooks (`"use client"` required)
  types/        # Shared TypeScript types and Zod schemas
tests/
  unit/         # Vitest unit tests, mirror src/ structure
  e2e/          # Playwright end-to-end tests
public/         # Static assets
prisma/         # Prisma schema (optional, if using Prisma instead of Drizzle)
```
**Rule:** New files go in the directory that matches their role. If a file serves multiple roles, split it.

## Dev Commands
```bash
npm run dev          # Start dev server (localhost:3000)
npm run build        # Production build
npm run lint         # ESLint + Prettier check
npm run format       # Prettier auto-fix
npm test             # Vitest unit tests
npm run test:e2e     # Playwright E2E tests
npm run db:push      # Push schema changes to SQLite
npm run db:studio    # Open Drizzle Studio (or Prisma Studio)
npm run db:generate  # Generate migration from schema changes
```

## Database Rules
- Use Drizzle ORM or Prisma — never raw SQL in application code.
- All schema changes require a migration file. Run `npm run db:generate` before committing.
- Never drop a column in a migration — deprecate first, drop in a follow-up.
- Query helpers go in `src/db/queries/`. One file per domain (e.g., `users.ts`, `billing.ts`).
- Use transactions for any operation touching multiple rows.
- Seed data lives in `src/db/seed.ts`. It must be idempotent (safe to run multiple times).

## Naming Conventions
- **Files:** kebab-case (`user-profile.tsx`, `billing-service.ts`)
- **Components:** PascalCase, named exports (`export function UserProfile() {}`)
- **Functions:** camelCase, verb-first (`getUserById`, `createSubscription`)
- **Types/Interfaces:** PascalCase (`UserProfile`, `BillingPlan`)
- **Database tables:** snake_case, plural (`user_profiles`, `billing_plans`)
- **Routes:** kebab-case directories (`/app/user-profile/page.tsx`)
- **Server Actions:** verbNoun naming (`createProject`, `updateSettings`)

## Patterns to Follow
- **Server Components first.** Only add `"use client"` when you need interactivity (state, effects, event handlers).
- **Server Actions for mutations.** Forms submit to `src/actions/` via `action={myAction}`. No API routes for CRUD.
- **Zod for validation.** Every Server Action validates input with Zod before touching the database.
- **Co-locate loading states.** Every async page gets a `loading.tsx` sibling.
- **Error boundaries per route.** Add `error.tsx` alongside `page.tsx` for graceful failure.
- **Optimistic updates.** Use `useOptimistic` for instant UI feedback on mutations.
- **Cache deliberately.** Use `revalidatePath()` after mutations, not `cache: "no-store"` everywhere.

## Anti-Patterns to Avoid
- **No API routes for data mutations.** Use Server Actions. API routes are only for webhooks and external callbacks.
- **No prop drilling beyond 2 levels.** Extract to context, hook, or component composition.
- **No `any` in TypeScript.** If you can't type it, add a `// TODO` with the reason.
- **No inline SQL.** All database access goes through query helpers in `src/db/queries/`.
- **No direct `process.env` access in client code.** Use `NEXT_PUBLIC_` prefix or server-only config.
- **No large barrel exports.** Import from specific files. Barrel files cause tree-shaking failures in Next.js.
- **No `useEffect` for data fetching.** Use Server Components, Server Actions, or React Query on the client.
- **No raw password hashing.** Use `bcryptjs` (synchronous, works in Edge) or `@node-rs/argon2`.

## Testing Convention
- Unit test every query helper and utility function.
- E2E test every critical user flow (signup, login, core feature usage).
- Test file names: `*.test.ts` alongside source, or mirror in `tests/unit/`.
- Mock external services (email, payments) in unit tests. Use real SQLite in-memory for DB tests.
