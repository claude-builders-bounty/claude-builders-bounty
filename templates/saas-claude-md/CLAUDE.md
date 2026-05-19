# CLAUDE.md — Next.js 15 + SQLite SaaS Template

## Stack & Versions

- **Runtime**: Node.js 20+ (LTS), TypeScript 5.x
- **Framework**: Next.js 15 (App Router, not Pages Router)
- **Database**: SQLite via better-sqlite3 or Turso (libSQL)
- **ORM**: Drizzle ORM (type-safe, zero runtime overhead)
- **Auth**: NextAuth.js v5 (Auth.js)
- **Styling**: Tailwind CSS v4 + shadcn/ui components
- **Package Manager**: pnpm (required — never use npm or yarn)
- **Validation**: Zod schemas, shared between client and server

## Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Auth route group (login, register)
│   ├── (dashboard)/       # Protected route group
│   │   ├── layout.tsx     # Shared dashboard shell + auth guard
│   │   ├── page.tsx       # Default dashboard
│   │   └── settings/      # User settings
│   ├── api/               # Route handlers
│   │   ├── auth/[...nextauth]/route.ts
│   │   ├── webhooks/      # Stripe, etc.
│   │   └── trpc/[trpc]/
│   ├── layout.tsx         # Root layout (fonts, providers)
│   └── globals.css
├── components/
│   ├── ui/                # shadcn/ui components (do not edit manually)
│   ├── forms/             # Form components with react-hook-form + zod
│   └── features/          # Feature-specific components
├── db/
│   ├── schema.ts          # All Drizzle schema definitions (single file)
│   ├── migrations/        # Generated migration files (never edit manually)
│   ├── index.ts           # DB client export
│   └── seed.ts            # Dev seed data
├── lib/
│   ├── auth.ts            # NextAuth config
│   ├── stripe.ts          # Stripe helpers
│   ├── utils.ts           # Shared utilities (cn, formatters)
│   └── validations/       # Shared Zod schemas
├── actions/               # Server Actions (one file per feature)
│   ├── billing.ts
│   └── user.ts
├── hooks/                 # React hooks
├── middleware.ts          # Auth protection + rate limiting
├── env.ts                 # Type-safe env vars (via @t3-oss/env-nextjs)
└── types/                 # Shared TypeScript types
```

## Naming Conventions

- **Files**: kebab-case (`user-settings.tsx`, `billing-action.ts`)
- **Components**: PascalCase, file matches export (`UserProfile` → `user-profile.tsx`)
- **Server Actions**: verb-noun pattern (`cancelSubscription`, `updateProfile`)
- **DB Tables**: snake_case plural (`users`, `subscription_plans`, `api_keys`)
- **DB Columns**: snake_case (`created_at`, `user_id`, `is_active`)
- **Environment Variables**: UPPER_SNAKE (`DATABASE_URL`, `STRIPE_SECRET_KEY`)
- **API Routes**: kebab-case plural (`/api/api-keys`, `/api/subscription-plans`)

## SQL & Migration Rules

1. **One migration per schema change** — never bundle unrelated changes
2. **Always use ` createdAt TEXT NOT NULL DEFAULT (datetime('now'))` ** — no separate timestamp columns
3. **Foreign keys** — always `ON DELETE CASCADE` for child tables, never soft-delete via FK
4. **Indexes** — add an index for every column used in `WHERE`, `JOIN`, or `ORDER BY`
5. **Columns**: use `TEXT` for everything except numbers. SQLite is dynamically typed — don't fight it
6. **Booleans**: use `INTEGER` with 0/1, not `BOOLEAN`
7. **JSON columns**: use `TEXT` with `JSON()` in queries — SQLite has no native JSON type
8. **Never edit migrations** — generate a new one to fix a mistake
9. **Seed file** — must be idempotent (`INSERT OR IGNORE`)

## Component Patterns

### Server Components by Default
Every component is a Server Component unless it needs interactivity. Add `"use client"` only when:
- Using hooks (`useState`, `useEffect`, etc.)
- Event handlers (`onClick`, `onChange`, etc.)
- Browser APIs

### Data Fetching
```typescript
// ✅ Do: Fetch in Server Component or Server Action
async function DashboardPage() {
  const user = await currentUser(); // Server-side
  return <UserCard user={user} />;
}

// ❌ Don't: Fetch in useEffect
useEffect(() => {
  fetch('/api/user').then(...); // Use Server Component instead
}, []);
```

### Form Handling
Use `react-hook-form` + `zodResolver` for all forms. Server Actions for submission.

### Loading & Error States
Use Next.js `loading.tsx` files for route-level, `<Suspense>` for component-level.
Use `error.tsx` files for route-level error boundaries.

## What We Don't Do (Anti-Patterns)

- ❌ **No Pages Router** — always use App Router (`src/app/`, not `src/pages/`)
- ❌ **No Prisma** — use Drizzle ORM (lighter, type-safe, no engine)
- ❌ **No REST API calls from Server Components** — query DB directly
- ❌ **No `fetch` in client components for data** — use Server Components or Server Actions
- ❌ **No CSS-in-JS** — Tailwind only
- ❌ **No `any` type** — use `unknown` and narrow, or proper types
- ❌ **No barrel exports** (`index.ts` re-exports) — import from exact files
- ❌ **No `console.log` in production** — use structured logging
- ❌ **No environment variables without validation** — all env vars go through Zod schema
- ❌ **No `SELECT *`** — always specify columns in Drizzle queries
- ❌ **No inline SQL strings** — always use Drizzle query builder
- ❌ **No storing secrets in DB** — use environment variables or a secrets manager

## Dev Commands

```bash
pnpm dev              # Start dev server
pnpm build            # Production build
pnpm db:generate      # Generate Drizzle migration
pnpm db:migrate       # Run migrations
pnpm db:seed          # Seed development data
pnpm db:studio        # Open Drizzle Studio (DB GUI)
pnpm lint             # ESLint
pnpm type-check       # TypeScript check (no emit)
pnpm test             # Run tests (vitest)
```

## Security Checklist

- All API routes behind `middleware.ts` auth check
- Rate limit on auth endpoints (5 req/min)
- Input validation on every Server Action and API route
- CSP headers configured in `next.config.ts`
- No sensitive data in client components or URL params
- CSRF protection on all mutations (NextAuth handles this)
- SQL injection prevention: Drizzle parameterizes all queries by default
