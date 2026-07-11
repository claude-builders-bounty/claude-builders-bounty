# Project: Next.js + SQLite SaaS

## Stack & Versions
- **Runtime**: Node.js >= 20
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript 5.x (strict mode)
- **Database**: SQLite via better-sqlite3 (production) / libsql (Turso edge)
- **ORM**: Drizzle ORM (no raw SQL in app code)
- **Auth**: NextAuth.js v5 (Auth.js)
- **Styling**: Tailwind CSS 4 + shadcn/ui
- **Package Manager**: pnpm
- **Testing**: Vitest + Playwright
- **Linting**: Biome (no ESLint)

## Folder Structure
```
src/
├── app/                 # Next.js App Router pages
│   ├── (auth)/          # Auth group (login, register)
│   ├── (dashboard)/     # Protected dashboard routes
│   ├── api/             # Route handlers (API routes)
│   └── layout.tsx       # Root layout
├── components/          # React components
│   ├── ui/              # shadcn/ui primitives
│   └── features/        # Feature-specific components
├── db/
│   ├── schema/          # Drizzle schema definitions
│   ├── migrations/      # Generated migrations (do NOT edit)
│   └── index.ts         # DB client singleton
├── lib/                 # Shared utilities (no React)
│   ├── auth.ts          # Auth.js configuration
│   └── utils.ts         # Generic helpers
├── actions/             # Server Actions (RPC layer)
├── emails/              # React Email templates
└── middleware.ts        # Next.js middleware
```

## SQL / Migration Conventions
- **Schema first**: Define tables in `src/db/schema/` → generate migrations via `pnpm db:generate`
- **Every table gets**: `id` (TEXT primary key, UUIDv7), `created_at` (DEFAULT current_timestamp), `updated_at` (auto-triggered)
- **Soft deletes**: Add `deleted_at TIMESTAMP NULL` column — never DROP rows that reference users.
- **Migration workflow**:
  ```bash
  pnpm db:generate  # Generate migration
  pnpm db:migrate    # Apply locally
  pnpm db:push       # Push to Turso (staging/prod)
  ```
- **Foreign keys**: Always use `REFERENCES` with `ON DELETE CASCADE` or `SET NULL`.
- **Indexes**: Add `CREATE INDEX` for every foreign key and every column in WHERE clauses.
- **No raw SQL in app code**: Use Drizzle query builders everywhere. Raw SQL only in migrations.

## Component Patterns
- **Server Components by default**: Only add `'use client'` when you need: `useState`, `useEffect`, `onClick`, browser APIs.
- **Client boundaries**: Keep `'use client'` as deep as possible — wrap interactive parts, not entire pages.
- **Form handling**: Use Server Actions (not client-state forms). Validate with Zod on both server and client.
- **Data fetching**: Use `fetch` in Server Components (Next.js built-in caching). No SWR/React Query for server data.
- **Loading states**: Use `loading.tsx` and `Suspense` boundaries — never `isLoading` booleans in client state.

## State Management
- **Server state**: React Server Components + URL search params. No Redux/Zustand for server data.
- **Client state**: React context for truly global UI state (theme, sidebar). Everything else is local state.
- **URL as state**: Filtering, pagination, search → URL search params. Never put these in client state.

## API & Server Actions
- **API routes** (external consumption): `src/app/api/` — rate-limited, authenticated via API keys.
- **Server Actions** (internal forms): `src/actions/` — throw `redirect()` on success, return `{error}` on failure.
- **Validation**: Every Server Action starts with Zod schema validation — fail fast, never trust the client.
- **Error handling**: Server Actions return `{error: string}` unions. API routes return standard HTTP codes.

## Auth Rules
- **Session**: JWT strategy (no database sessions).
- **Middleware**: `src/middleware.ts` protects all `/dashboard/*` routes.
- **User ID**: `session.user.id` is always a UUIDv7 string. Never expose internal IDs.

## What We Don't Do (And Why)
- **No `any` types**: Exceptions require a Biome suppression comment with a reason.
- **No `useEffect` for data fetching**: Server Components + Server Actions cover 99% of data needs.
- **No `||` for defaults**: Use `??` (nullish coalescing) exclusively.
- **No barrel files (`index.ts` re-exports)**: They cause circular deps and slow HMR. Import directly from the file.
- **No inline styles**: Tailwind utility classes or `cn()` helper only.
- **No `process.env` in client code**: Use `NEXT_PUBLIC_` prefix or server-only env access.
- **No singletons except DB client**: DB client is the only global singleton. Everything else uses dependency injection or factories.

## Dev Commands
```bash
pnpm dev              # Start dev server (localhost:3000)
pnpm build            # Production build
pnpm lint             # Biome check
pnpm test             # Vitest (unit + integration)
pnpm test:e2e         # Playwright (E2E)
pnpm db:generate      # Generate Drizzle migration
pnpm db:migrate       # Apply migration
pnpm db:studio        # Drizzle Studio (GUI DB browser)
```

## Git Conventions
- **Branch names**: `feat/description`, `fix/description`, `chore/description`
- **Commit messages**: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`)
- **PR scope**: One feature/fix per PR. No mixed-changes PRs.
