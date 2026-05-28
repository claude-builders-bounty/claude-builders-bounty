# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & Versions

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js 15 (App Router) | ^15.0 |
| Database | SQLite via better-sqlite3 | ^11.0 |
| ORM | Drizzle ORM | ^0.35 |
| Auth | NextAuth.js v5 (Auth.js) | ^5.0 |
| UI | shadcn/ui + Tailwind CSS v4 | latest |
| Forms | React Hook Form + Zod | latest |
| Language | TypeScript (strict mode) | ^5.6 |
| Package Mgr | pnpm | ^9.0 |
| Runtime | Node.js | ^20 LTS |

## Folder Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── (auth)/            # Auth-optional layouts
│   ├── (dashboard)/       # Authenticated layouts
│   ├── api/               # Route handlers (NO server actions here)
│   └── layout.tsx
├── components/
│   ├── ui/                # shadcn/ui primitives (do NOT edit directly)
│   └── features/          # Feature-specific components
├── db/
│   ├── schema.ts          # Drizzle schema definitions (single source of truth)
│   ├── migrations/        # Auto-generated (do NOT edit manually)
│   ├── queries/           # Reusable DB query functions
│   └── seed.ts            # Development seed data
├── lib/
│   ├── auth.ts            # NextAuth config
│   ├── db.ts              # DB client singleton
│   ├── utils.ts           # Shared utilities (cn(), formatters)
│   └── validations/       # Zod schemas (mirror DB schema)
├── hooks/                 # Shared React hooks
├── types/                 # Shared TypeScript types
└── middleware.ts          # Next.js middleware (auth redirects)
```

## SQL & Migration Conventions

### Schema Rules
- **Every table MUST have**: `id TEXT PRIMARY KEY` (use `cuid2()`), `createdAt`, `updatedAt`
- **Foreign keys** use TEXT references, enable `foreign_keys` in SQLite
- **Indexes** on: foreign keys, `email`, `slug`, any column used in WHERE
- **NO default values** on TEXT columns unless truly constant
- Run `drizzle-kit push` in dev; generate migration files for prod

### Migration Workflow
```bash
pnpm db:generate   # Generate migration from schema changes
pnpm db:migrate    # Apply pending migrations
pnpm db:seed       # Seed development data (idempotent)
```

### Anti-patterns (Blocked)
- ❌ Raw SQL strings in components (use Drizzle queries)
- ❌ Migrations edited by hand (regenerate instead)
- ❌ Schema types defined outside `schema.ts`
- ❌ `DELETE` without a WHERE clause (use soft-delete column)

## Component Patterns

### Server Components (default)
- Fetch data directly in the component using Drizzle
- Pass plain props to Client Components
- Use `searchParams` for list filtering/sorting/pagination

### Client Components
- Add `'use client'` ONLY when needed (hooks, event handlers, browser APIs)
- Keep data fetching in Server Components; pass fetched data as props
- Forms: use `react-hook-form` + Zod validation, call Server Actions
- Avoid `useEffect` for data fetching (use Server Components + Server Actions)

### Naming Conventions
- Files: `kebab-case.tsx`
- Components: PascalCase
- Functions: camelCase
- DB columns: camelCase (Drizzle handles conversion)
- Routes: `/api/[resource]/[action]`

## What We DON'T Do (And Why)

| Don't | Why |
|-------|-----|
| ❌ Redux / Zustand / global state | Server Components + URL state cover 95% of cases |
| ❌ Prisma | Drizzle is lighter, has better SQLite support, and generates cleaner types |
| ❌ tRPC | Next.js Server Actions + Route Handlers replace this completely |
| ❌ Custom API clients | Server Components fetch directly; no need for a client layer |
| ❌ `any` types | strict mode is on for a reason — use `unknown` + narrowing |
| ❌ Barrel exports (`index.ts`) | They cause circular deps and slow HMR in Next.js |

## Dev Commands

```bash
pnpm dev              # Start dev server
pnpm build            # Production build
pnpm lint             # ESLint + TypeScript check
pnpm test             # Vitest (unit) + Playwright (e2e)
pnpm db:push          # Push schema to dev DB (no migration file)
pnpm db:studio        # Open Drizzle Studio (GUI DB browser)
pnpm type-check       # tsc --noEmit (strict check)
```

## Environment Variables

```env
# Required
DATABASE_URL="file:./data/dev.db"
AUTH_SECRET="..."
AUTH_GITHUB_ID="..."
AUTH_GITHUB_SECRET="..."

# Optional
NEXT_PUBLIC_APP_URL="http://localhost:3000"
```

## Git Conventions

- Commits: `feat:`, `fix:`, `chore:`, `refactor:`, `docs:`, `db:`
- Branch: `feat/description`, `fix/issue-number`
- PR description must include: What, Why, Testing steps
