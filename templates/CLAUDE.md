# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated project conventions for Claude Code. Every rule has a reason.

## Stack & Versions

- **Framework**: Next.js 15 (App Router only — Pages Router is not used)
- **Runtime**: Node.js 20+
- **Database**: SQLite via `better-sqlite3` (local) or Turso/libSQL (production)
- **ORM**: Drizzle ORM — type-safe, SQL-first, zero overhead
- **Auth**: `better-auth` — lightweight, self-hosted, no vendor lock-in
- **Styling**: Tailwind CSS 4 — utility-first, no CSS modules
- **UI Components**: shadcn/ui — copy-pasted, not installed as dependency
- **Package Manager**: pnpm — fast, strict, disk-efficient
- **Language**: TypeScript (strict mode) — no `any`, no `as` casts unless unavoidable

## Dev Commands

```bash
pnpm dev          # Start dev server (port 3000)
pnpm build        # Production build
pnpm db:push      # Push schema changes to SQLite
pnpm db:studio    # Open Drizzle Studio (database browser)
pnpm db:generate  # Generate migration files from schema diff
pnpm db:migrate   # Run pending migrations
pnpm lint         # ESLint + type check
pnpm test         # Run Vitest
```

## Folder Structure

```
src/
├── app/                    # Next.js App Router — routes only
│   ├── (auth)/             # Route group: login, register, forgot-password
│   ├── (dashboard)/        # Route group: authenticated pages
│   ├── api/                # API routes (route handlers)
│   │   └── [resource]/route.ts
│   ├── layout.tsx          # Root layout (providers, fonts, metadata)
│   └── page.tsx            # Landing page
├── components/
│   ├── ui/                 # shadcn/ui primitives (button, input, card...)
│   └── [feature]/          # Feature-scoped components (e.g., billing/, settings/)
├── lib/
│   ├── db/
│   │   ├── schema.ts       # Drizzle schema (single file until >20 tables)
│   │   ├── index.ts        # Database connection (singleton)
│   │   └── migrations/     # Generated SQL migration files
│   ├── auth.ts             # Auth configuration
│   ├── utils.ts            # Shared utilities (cn, formatDate, etc.)
│   └── validators.ts       # Zod schemas for input validation
├── hooks/                  # Custom React hooks
├── types/                  # Shared TypeScript types (not duplicating Drizzle schema)
└── config/                 # App-wide constants (plans, limits, feature flags)
```

**Why this structure**: Feature grouping inside `components/` keeps related UI together. `lib/` is for non-React code. Route groups `(auth)` and `(dashboard)` share layouts without affecting URL paths.

## SQL & Migration Conventions

- **Schema file**: All tables live in `src/lib/db/schema.ts` until the project exceeds ~20 tables. Then split by domain (`schema/users.ts`, `schema/billing.ts`).
- **Migrations**: Always generate with `pnpm db:generate`, never write SQL by hand. Drizzle tracks the diff.
- **Naming**: Tables are `snake_case` plural (`user_sessions`, not `UserSession`). Columns are `snake_case`. Drizzle maps to camelCase in TypeScript.
- **IDs**: Use `text('id').primaryKey().$defaultFn(() => createId())` with `@paralleldrive/cuid2`. Not autoincrement — CUIDs are URL-safe, sortable, and won't leak row counts.
- **Timestamps**: Every table gets `created_at` and `updated_at` columns. Use `integer('created_at', { mode: 'timestamp' })`.
- **Soft deletes**: Add a `deleted_at` column instead of actually deleting rows. Filter with `.where(isNull(table.deletedAt))` by default.
- **No raw SQL in application code**: Always use Drizzle's query builder. Raw SQL only in migration files.

**Why**: Drizzle generates migrations deterministically from schema diffs. Hand-written SQL drifts from the schema and breaks `db:push`.

## Component Patterns

### Server Components (default)
```tsx
// src/app/(dashboard)/projects/page.tsx
import { db } from '@/lib/db';
import { projects } from '@/lib/db/schema';

export default async function ProjectsPage() {
  const allProjects = await db.select().from(projects);
  return <ProjectList projects={allProjects} />;
}
```
**Rule**: Pages and layouts are always Server Components. Data fetching happens here, not in client components.

### Client Components (opt-in)
```tsx
'use client';
// Only add 'use client' when you need: useState, useEffect, event handlers, browser APIs
```
**Rule**: Keep client components as leaf nodes. Never make a layout or page a client component.

### Forms & Mutations
```tsx
// Use Server Actions for mutations
export async function createProject(formData: FormData) {
  'use server';
  const name = formData.get('name') as string;
  // validate with Zod, then insert
  await db.insert(projects).values({ id: createId(), name });
  revalidatePath('/projects');
}
```
**Rule**: Server Actions for writes. No API routes for CRUD unless you need them for external consumers.

### Loading & Error States
- Every route group gets a `loading.tsx` (skeleton UI) and `error.tsx` (error boundary).
- Use `Suspense` boundaries around async server components that fetch data.

### Validation
```tsx
import { z } from 'zod';
// Define in lib/validators.ts, import everywhere
export const createProjectSchema = z.object({
  name: z.string().min(1).max(100),
});
```
**Rule**: Validate on the server (in Server Actions / API routes). Client-side validation is UX sugar, not security.

## Anti-Patterns — Do Not Do These

| Anti-Pattern | Why It's Wrong | Do This Instead |
|-------------|----------------|-----------------|
| `"use client"` on pages or layouts | Disables streaming, SSR, and server-side data fetching | Keep pages as Server Components, extract interactive parts into client leaf components |
| Fetching data in client components with `useEffect` | Creates waterfalls, loading spinners, no SEO | Fetch in Server Components or use Server Actions |
| Using Prisma with SQLite | Prisma's SQLite support is second-class; no edge runtime | Use Drizzle ORM — built for SQLite, runs everywhere |
| `autoincrement` integer IDs | Leaks row count, breaks distributed inserts, not URL-safe | Use CUID2 (`createId()`) for all primary keys |
| Creating API routes for internal CRUD | Unnecessary network hop when Server Actions exist | Use Server Actions for mutations from your own UI |
| `any` or `as` type casts | Defeats TypeScript's purpose, hides bugs | Fix the type, use generics, or narrow with guards |
| Installing shadcn/ui as a package | It's designed to be copy-pasted so you own the code | Use `npx shadcn@latest add [component]` |
| Putting business logic in components | Untestable, unreusable, hard to refactor | Extract to `lib/` functions, call from components |
| Multiple database connections | SQLite allows one writer at a time; multiple connections cause SQLITE_BUSY | Use a singleton connection in `lib/db/index.ts` |
| Storing secrets in `.env.local` committed to git | Security breach | Use `.env.local` (gitignored) for secrets, `.env.example` for shape |
