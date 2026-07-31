# CLAUDE.md — Next.js 15 + SQLite SaaS

## Project Stack
- Next.js 15 App Router with React Server Components
- SQLite via better-sqlite3 (local dev) / Turso (production)
- TypeScript strict mode, Tailwind CSS, shadcn/ui
- Auth via next-auth v5 with email/password provider

## Project Structure
```
src/
  app/           # App Router pages & API routes
  components/    # React components (shadcn/ui)
  lib/           # Shared utilities
    db.ts        # Database client singleton
    auth.ts      # Auth configuration
    utils.ts     # General helpers
  db/
    migrations/  # SQL migration files (numbered: 001_, 002_, ...)
    schema.ts    # Drizzle ORM schema definitions
    seed.ts      # Development seed data
  actions/       # Server actions (one file per domain)
prisma/          # (if using Prisma instead of Drizzle)
```

## Naming Conventions
- **Files**: kebab-case for components (`user-profile.tsx`), camelCase for utilities (`formatDate.ts`)
- **Database tables**: `snake_case` plural (`user_sessions`, `team_members`)
- **Server actions**: one file per domain (`actions/users.ts`, `actions/billing.ts`)
- **API routes**: RESTful patterns (`/api/users/[id]/route.ts`)

## Database Rules
1. **NEVER drop a column** — add new columns with `ALTER TABLE ... ADD COLUMN`, never rename or drop
2. **Migrations are append-only** — each migration file only goes forward; no editing past migrations
3. **No raw SQL in components** — all queries go through Drizzle ORM or `lib/db.ts` prepared statements
4. **Foreign keys always** — every relation gets a FK constraint with `ON DELETE CASCADE` or `ON DELETE RESTRICT`
5. **Timestamps mandatory** — every table must have `created_at` and `updated_at` columns

## Dev Commands
```bash
npm run dev          # Start Next.js dev server
npm run build        # Production build
npm run db:migrate   # Run pending migrations
npm run db:seed      # Seed development data
npm run db:studio    # Open Drizzle Studio (browser DB GUI)
npm run lint         # ESLint + Prettier
npm run test         # Vitest
npm run typecheck    # tsc --noEmit
```

## Patterns to Follow
- **Server Components by default** — only add `'use client'` when you need interactivity, browser APIs, or state
- **Server Actions for mutations** — use `useActionState` + server actions for forms, not API routes
- **Optimistic updates** — call `revalidatePath` / `revalidateTag` after mutations, use `useOptimistic` for instant UI
- **Streaming for slow data** — wrap async components in `<Suspense>` with skeleton fallbacks
- **Cache invalidation** — use `revalidatePath` for page-level, `revalidateTag` for data-level, never force-dynamic globally
- **Environment variables** — use `t3-env` for type-safe env vars, prefix client-side vars with `NEXT_PUBLIC_`

## Anti-Patterns to Avoid
- **Don't use `useEffect` for data fetching** — use Server Components or SWR/React Query for client-side
- **Don't import server code into client components** — `import { db } from '@/lib/db'` in a client component leaks credentials
- **Don't use API routes for mutations** — use Server Actions; API routes are for webhooks, OAuth callbacks, and external integrations only
- **Don't use Prisma unless already chosen** — this project uses Drizzle; mixing ORMs creates schema drift
- **Don't skip error boundaries** — every data-dependent route segment should have `error.tsx` and `loading.tsx`
- **No `any` types** — use `unknown` and narrow with type guards if the shape is uncertain

## When Adding a Feature
1. Check if a migration is needed → create `src/db/migrations/NNN_description.sql`
2. Update Drizzle schema in `src/db/schema.ts`
3. Create the server action in `src/actions/domain.ts`
4. Build the UI with Server Component wrapping a Client Component
5. Add loading/error states (`loading.tsx`, `error.tsx`)
6. Run `npm run typecheck && npm run test` before committing
