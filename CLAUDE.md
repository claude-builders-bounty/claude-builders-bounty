# CLAUDE.md

## Stack & Versions
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript 5.x (strict mode)
- **Database**: SQLite via better-sqlite3 (server) or Turso/LibSQL (edge)
- **ORM**: Drizzle ORM (schema-first, type-safe)
- **Auth**: NextAuth.js v5 (Auth.js) with SQLite adapter
- **Styling**: Tailwind CSS v4 with shadcn/ui components
- **Validation**: Zod (shared client + server schemas)
- **Package Manager**: pnpm (workspace-aware)
- **Runtime**: Node.js 20+ LTS

## Folder Structure
```
/app                  # Next.js App Router
  /(auth)             # Auth-grouped routes
  /(dashboard)        # Dashboard-grouped routes
  /api                # Route handlers
  layout.tsx          # Root layout
  page.tsx            # Home page
/components
  /ui                 # shadcn/ui primitives (NEVER modify)
  /custom             # Our building blocks
/lib                  # Pure utilities (no React imports)
  /db                 # Drizzle schema, migrations, queries
    schema.ts         # All table definitions
    index.ts          # Connection + query client export
  /auth.ts            # NextAuth config
/server               # Server-only actions (data mutations)
/types                # Shared TypeScript types
/public               # Static assets
/drizzle              # Drizzle migrations (auto-generated, never hand-edit)
```

## SQL / Migration Conventions
- **Migrations are generated**, never hand-edited. Run `pnpm db:generate` after schema changes.
- **Schema file**: `/lib/db/schema.ts`. All tables in ONE file until 10+ tables, then split.
- **Naming**: snake_case columns, plural table names. `created_at` with `defaultNow()` on every table.
- **Indexes**: Add for every FK and every column used in WHERE clauses. Drizzle `index()`.
- **Foreign keys**: Always explicit. Use Drizzle `references()`.
- **Migrations push**: `pnpm db:push` (dev), `pnpm db:migrate` (production).
- **Seeds**: `/lib/db/seed.ts` — run once for dev setup.

## Component Patterns
1. **Server Components by default** — add `"use client"` ONLY when needed (state, effects, event handlers).
2. **Data fetching**: In Server Components, import query functions from `/lib/db/queries/`.
3. **Mutations**: Use Server Actions in `/server/actions/`. Return `{ success, error }` type.
4. **Route protection**: Use `middleware.ts` + `getServerSession()` in layouts, not client-side redirects.
5. **Loading states**: `loading.tsx` siblings for every route, NOT inline spinners.
6. **Error boundaries**: `error.tsx` per route segment.
7. **Form pattern**: `useActionState` + Zod validation in Server Action. Keep form state on server.

## What We DON'T Do
- **No ORM-generated types in client components** — keep DB types server-side.
- **No raw SQL in route handlers** — always through query functions in /lib/db.
- **No `any` or `as` casts** for DB results. Drizzle infers types.
- **No `use client` in layout.tsx** — toasts and dialogs use portals instead.
- **No `NEXT_PUBLIC_` secrets** — server-only env vars have no prefix.
- **No `useEffect` for data fetching** — that's Server Component territory.
- **No barrel exports from /components/ui** — import primitives directly from their file.

## Dev Commands
```bash
pnpm dev          # Next.js dev server (port 3000)
pnpm build        # Production build
pnpm db:generate  # Generate Drizzle migration from schema changes
pnpm db:push     # Push schema to dev SQLite
pnpm db:migrate  # Run pending migrations
pnpm db:studio   # Drizzle Studio UI
pnpm check       # TypeScript check + ESLint
pnpm test        # Vitest
```

## Anti-Patterns (Do NOT Follow)
- ❌ Wrapping everything in client components
- ❌ Calling DB directly in route handler bodies
- ❌ Skipping Zod validation on Server Action input
- ❌ Using `fetch()` in Server Components when DB access is available
- ❌ Creating UI primitives in /components/custom instead of using shadcn
