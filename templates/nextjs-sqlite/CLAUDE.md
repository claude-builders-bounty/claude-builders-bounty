# CLAUDE.md — Next.js + SQLite SaaS

## Stack & Versions
- **Framework**: Next.js 15 (App Router)
- **Database**: SQLite via better-sqlite3 (production) / Turso (edge)
- **ORM**: Drizzle ORM
- **Auth**: NextAuth.js v5 / Lucia v3
- **UI**: shadcn/ui + Tailwind CSS v4
- **Package Manager**: pnpm
- **Runtime**: Node.js 20+

## Project Structure
```
src/
├── app/              # Next.js App Router pages
│   ├── (auth)/       # Auth-required routes (group)
│   ├── (public)/     # Public routes
│   ├── api/          # API routes (route handlers)
│   └── layout.tsx    # Root layout
├── components/
│   ├── ui/           # shadcn/ui components (generated)
│   └── features/     # Feature-specific components
├── db/
│   ├── schema/       # Drizzle schema files
│   ├── migrations/   # Auto-generated migrations
│   └── index.ts      # DB connection
├── lib/
│   ├── auth.ts       # Auth configuration
│   ├── utils.ts      # Utility functions
│   └── validations.ts # Zod schemas
└── actions/          # Server actions (one file per domain)
```

## Naming Conventions
- **Files**: kebab-case for files (`user-settings.tsx`)
- **Components**: PascalCase for React components
- **Functions**: camelCase
- **DB tables**: snake_case
- **DB columns**: snake_case
- **Route groups**: Parentheses `(auth)`, `(public)`
- **API routes**: RESTful plural nouns `/api/users`, `/api/teams/:id`

## SQL / Migration Rules
- **Always use Drizzle migrations** — never raw SQL files
- **One migration per schema change** — generate with `pnpm db:generate`
- **Migration naming**: `pnpm db:generate <descriptive-name>`
- **Rollbacks**: Drizzle supports `down` — always verify before applying
- **NEVER edit migration files manually** — they are auto-generated
- **Indexes**: Add for foreign keys and frequently queried columns
- **Soft deletes**: Use `deleted_at` timestamp column instead of hard deletes

## Component Patterns
- **Server-first**: Default to Server Components; only add `"use client"` when you need interactivity
- **Loading states**: Use `loading.tsx` for route segments
- **Error handling**: Use `error.tsx` with retry capability
- **Forms**: Use Server Actions with Zod validation
- **Data fetching**: Fetch in Server Components; pass down as props
- **State management**: URL params > React context > Zustand (avoid Redux)

## Dev Commands
```bash
pnpm dev           # Start dev server
pnpm build         # Production build
pnpm lint          # ESLint check
pnpm test          # Run tests
pnpm db:generate   # Generate migration
pnpm db:push       # Push schema to local DB
pnpm db:studio     # Open Drizzle Studio
pnpm typecheck     # TypeScript check (tsc --noEmit)
```

## Patterns to Follow
- **Validate all inputs** with Zod before processing
- **Use Server Actions** for mutations (not API routes unless external access needed)
- **Cache wisely**: use `unstable_cache` for expensive queries, `revalidateTag` for invalidation
- **Error boundaries**: wrap each route segment with error.tsx
- **Database transactions**: wrap multi-step operations in Drizzle transactions
- **Audit logging**: log all destructive operations (deletes, role changes, payments)

## Anti-Patterns to Avoid
- ❌ `"use client"` on every page — only when needed
- ❌ Fetching data in client components when Server Components work
- ❌ Raw SQL queries — always use Drizzle
- ❌ Storing secrets in `.env.local` without documenting them
- ❌ Mutating DB schema without generating migrations
- ❌ Using `any` types — prefer Zod inferred types

## This Project Does NOT Do
- **No GraphQL** — REST API routes + Server Actions cover all needs
- **No Redis** — SQLite with WAL mode covers caching for single-region SaaS
- **No microservices** — this is a monolith until proven otherwise
- **No WebSockets** — use polling or Server-Sent Events if real-time needed
- **No CMS** — content is managed through the database or markdown files

## Token Budget
- **Soft limit**: 2000 tokens for the entire CLAUDE.md
- **Hard limit**: 3000 tokens — CI will fail the PR if exceeded
- **Review cadence**: Every 3 months, audit each section for drift
- **What to remove**: Delete sections that Claude no longer references (check chat logs)
- **Why this matters**: Every token in CLAUDE.md is sent with every request. A file that grows to 6000 tokens silently adds cost and dilutes attention. Keep it lean.
