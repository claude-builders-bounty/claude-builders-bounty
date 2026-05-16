# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Stack & Versions

- **Runtime**: Node.js 22+ (LTS)
- **Framework**: Next.js 15 App Router (React 19)
- **Language**: TypeScript 5.7+, strict mode
- **Database**: SQLite via better-sqlite3 (local) or Turso (production)
- **ORM**: Drizzle ORM (NOT Prisma, NOT raw SQL)
- **Auth**: NextAuth.js v5 (Auth.js) with credentials + OAuth
- **UI**: shadcn/ui + Tailwind CSS v4
- **Package Manager**: pnpm (NOT npm, NOT yarn)
- **Testing**: Vitest + Playwright
- **Linting**: Biome (NOT ESLint, NOT Prettier)
- **Validation**: Zod (all API inputs, form data, env vars)

## Project Structure

```
project-root/
├── .env.local              # Local env vars (gitignored)
├── .env.example            # Documented env template
├── drizzle.config.ts       # Drizzle kit config
├── next.config.ts          # Next.js config
├── src/
│   ├── app/                # Next.js App Router pages
│   │   ├── (auth)/         # Auth-required routes (layout group)
│   │   ├── (public)/       # Public routes
│   │   ├── api/            # Route handlers (NOT pages router)
│   │   └── layout.tsx      # Root layout
│   ├── components/         # React components
│   │   ├── ui/             # shadcn/ui components
│   │   └── features/       # Feature-specific components
│   ├── db/                 # Database layer
│   │   ├── schema/         # Drizzle schema files
│   │   ├── migrations/     # Auto-generated migrations
│   │   ├── index.ts        # DB client export
│   │   └── seed.ts         # Seed data script
│   ├── lib/                # Shared utilities
│   │   ├── auth.ts         # NextAuth config
│   │   ├── actions.ts      # Server Actions
│   │   └── utils.ts        # Helper functions
│   └── types/              # TypeScript type definitions
├── tests/                  # Test files (mirrors src/ structure)
│   ├── unit/
│   └── e2e/
```

## SQL / Migration Conventions

1. **Every schema change gets a migration file**. Never modify the SQLite file directly.
   ```bash
   pnpm drizzle-kit push        # Dev: sync schema
   pnpm drizzle-kit generate    # Generate migration
   pnpm drizzle-kit migrate     # Apply migration
   ```

2. **Migrations are reviewed in PRs**. Check for:
   - Breaking column changes (rename → migrate data first)
   - Missing indexes on foreign keys
   - NOT NULL columns without defaults on existing tables

3. **Schema naming**:
   - Tables: plural snake_case (`users`, `team_members`)
   - Columns: snake_case (`created_at`, `updated_at`)
   - Junction tables: alphabetic (`team_members` not `members_teams`)
   - Timestamps: `created_at` (NOT `createdAt`), `updated_at`

4. **Always include**: `id INTEGER PRIMARY KEY AUTOINCREMENT`, `created_at TEXT NOT NULL DEFAULT (datetime('now'))`, `updated_at TEXT NOT NULL DEFAULT (datetime('now'))`

5. **Soft deletes**: Add `deleted_at TEXT DEFAULT NULL` column. Filter with `WHERE deleted_at IS NULL`.

## Component Patterns

1. **Server Components by default**. Only add `'use client'` when you need:
   - Browser APIs (localStorage, clipboard, etc.)
   - React hooks (useState, useEffect, useContext)
   - Event handlers (onClick, onSubmit)
   - Custom context providers

2. **Client Components at the leaves**. Push `'use client'` as deep as possible.

3. **Server Actions for mutations**. NOT API routes for CRUD.
   ```typescript
   // src/lib/actions.ts — good
   'use server'
   export async function createTeam(formData: FormData) { ... }
   ```
   ```typescript
   // src/app/api/teams/route.ts — avoid (unless webhook)
   export async function POST(req: Request) { ... }
   ```

4. **Data fetching**: Use `async component` directly, NOT `useEffect` + `fetch`.
   ```typescript
   // ✅ Good
   export default async function Page() {
     const data = await db.query.users.findMany();
     return <List data={data} />;
   }
   ```

5. **Loading states**: Use `loading.tsx` files, NOT `isLoading` state variables.

## What We Don't Do (And Why)

| Don't | Why |
|-------|-----|
| ❌ Don't use `any` | TypeScript strict mode is on. Use `unknown` + type guards |
| ❌ Don't use `redux` | Next.js App Router + Server Components replace global state |
| ❌ Don't use `useEffect` for data fetching | Server Components handle this natively |
| ❌ Don't use `process.env` directly in components | Use `env.ts` with Zod validation |
| ❌ Don't store files in SQLite | Use S3/R2/Cloudflare Images + store URL in DB |
| ❌ Don't use `alert()` or `confirm()` | Use shadcn/ui toast or dialog components |
| ❌ Don't write raw SQL without Drizzle | Drizzle provides type safety and migration management |
| ❌ Don't use `npm` or `yarn` | pnpm is faster and handles monorepos better |
| ❌ Don't commit `.env.local` | Use `.env.example` with documented defaults |

## Dev Commands

```bash
pnpm dev                    # Start dev server (localhost:3000)
pnpm build                  # Production build
pnpm test                   # Run Vitest
pnpm test:e2e              # Run Playwright E2E
pnpm db:push               # Push schema to local DB
pnpm db:generate           # Generate migration
pnpm db:migrate            # Apply migrations
pnpm db:seed               # Seed database
pnpm lint                  # Biome lint + format check
pnpm typecheck             # tsc --noEmit
pnpm env:validate          # Validate .env against Zod schema
```

## API Design

1. **Route Handlers** are only for:
   - Webhooks (Stripe, GitHub, etc.)
   - 3rd-party API proxies (CORS avoidance)
   - File upload endpoints
   
2. **Server Actions** handle all app mutations:
   - Form submissions
   - Button clicks
   - Background jobs

3. **All routes are typed**. Use Zod to validate:
   - Request body/params for route handlers
   - `formData` for Server Actions
   - Search params in page components

## Error Handling

1. **Server Actions**: Return `{ success: boolean, error?: string }` — NEVER throw in actions
2. **Route Handlers**: Return `NextResponse.json({ error: string }, { status: N })`
3. **Pages**: Use `error.tsx` boundary files (one per route segment)
4. **Not Found**: Use `not-found.tsx` and `notFound()` function
5. **DB errors**: Wrap in try/catch, log to console, return user-friendly message
