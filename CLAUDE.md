# CLAUDE.md — Next.js 15 + SQLite SaaS Project Guide

## Project Structure

```
my-saas/
├── src/
│   ├── app/                    # Next.js 15 App Router
│   │   ├── (auth)/             # Auth route group
│   │   │   ├── login/
│   │   │   ├── register/
│   │   │   └── layout.tsx
│   │   ├── (dashboard)/        # Protected route group
│   │   │   ├── dashboard/
│   │   │   ├── settings/
│   │   │   └── layout.tsx      # Auth middleware wrapper
│   │   ├── api/                # API routes (Route Handlers)
│   │   │   ├── trpc/           # tRPC router (if used)
│   │   │   └── webhooks/
│   │   ├── layout.tsx          # Root layout
│   │   └── page.tsx            # Landing page
│   ├── components/             # Reusable UI components
│   │   ├── ui/                 # Primitive UI (shadcn/ui)
│   │   ├── forms/              # Form components
│   │   └── layout/             # Layout components
│   ├── lib/                    # Shared utilities
│   │   ├── db/                 # Database layer
│   │   │   ├── schema.ts       # Drizzle ORM schema
│   │   │   ├── migrations/     # Drizzle kit migrations
│   │   │   └── index.ts        # DB client
│   │   ├── auth.ts             # Auth helpers (NextAuth/Auth.js v5)
│   │   ├── utils.ts            # General utilities
│   │   └── validations.ts      # Zod schemas
│   ├── styles/                 # Global styles
│   └── middleware.ts           # Next.js middleware
├── public/                     # Static assets
├── drizzle.config.ts           # Drizzle ORM config
├── next.config.ts
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── .env.local                  # Environment variables
```

## Naming Conventions

### Files & Folders
- **Components**: `PascalCase.tsx` — `UserProfileCard.tsx`
- **Hooks**: `useCamelCase.ts` — `useDebounce.ts`
- **Utilities**: `camel-case.ts` — `format-date.ts`
- **API routes**: `kebab-case` — `stripe-webhook/route.ts`
- **DB schema**: `snake_case` for columns, `camelCase` for JS

### Code Style
- **React components**: Default export, named function
- **Utilities**: Named exports only
- **Types/Interfaces**: `PascalCase` with `Type` prefix for API types
- **Constants**: `UPPER_SNAKE_CASE`

## Database Migration Rules

### Drizzle ORM (recommended)
```bash
# Generate migration after schema changes
pnpm drizzle-kit generate

# Apply migration
pnpm drizzle-kit push

# Open Drizzle Studio
pnpm drizzle-kit studio
```

### Rules
1. **Never edit migration files directly** — always use Drizzle Kit to generate them
2. **One migration per schema change** — generate and apply before making more changes
3. **Test migrations locally** before pushing to production
4. **Use transactions** for multi-table operations
5. **Add indexes** on frequently queried columns
6. **Soft deletes** preferred over hard deletes (add `deletedAt` column)

## Development Commands

```bash
pnpm dev          # Start dev server (localhost:3000)
pnpm build        # Production build
pnpm lint         # Run ESLint
pnpm type-check   # Run TypeScript checks
pnpm test         # Run tests (Vitest)
pnpm test:e2e     # Run Playwright E2E tests
pnpm db:generate  # Generate Drizzle migrations
pnpm db:push      # Push migrations to database
pnpm db:studio    # Open Drizzle Studio
```

## Recommended Patterns

### ✅ Do
- Use **Server Components** by default, Client Components only when needed
- Colocate tests with components: `Component.tsx` + `Component.test.tsx`
- Use **tRPC** or **Server Actions** for data mutations
- Validate all inputs with **Zod** schemas
- Use **Next.js <Link>** for client-side navigation
- Handle errors with **error.tsx** boundaries
- Use **loading.tsx** for streaming SSR

### ❌ Avoid
- `useEffect` for data fetching — use Server Components or React Query
- Direct `localStorage` access in Server Components
- Importing server code into client components
- Large client bundles — use `next/dynamic` for heavy components
- `any` types — always use proper TypeScript types
- Bare SQL strings — use Drizzle ORM query builder

## Environment Variables (.env.local)

```env
# Database (SQLite)
DATABASE_URL="file:./data/local.db"

# Auth (NextAuth.js v5)
AUTH_SECRET="your-secret-here"
AUTH_GITHUB_ID=""
AUTH_GITHUB_SECRET=""

# App
NEXT_PUBLIC_APP_URL="http://localhost:3000"
```

## Git Workflow

```bash
main          # Production branch
  ├── staging # Pre-production
  ├── dev     # Development branch
  └── feat/*  # Feature branches
```

- Commit messages: [Conventional Commits](https://www.conventionalcommits.org/)
  - `feat:` — new feature
  - `fix:` — bug fix
  - `refactor:` — code change without fix/feature
  - `docs:` — documentation only
  - `chore:` — maintenance tasks
