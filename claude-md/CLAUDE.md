<!--
=====================================================
CLAUDE.md — Next.js 15 App Router + SQLite (better-sqlite3)
SaaS Project Template
=====================================================
Version: 1.0
Target stack: Next.js 15 + App Router + better-sqlite3 + Drizzle ORM + shadcn/ui + Tailwind CSS
-->

# Project Guide — Next.js 15 + SQLite SaaS

## Architecture

### Stack
- **Framework**: Next.js 15 (App Router, Turbopack for dev)
- **Database**: SQLite via `better-sqlite3` (local) / Turso (production)
- **ORM**: Drizzle ORM (schema-first, type-safe SQL)
- **UI**: shadcn/ui + Tailwind CSS 4
- **Auth**: NextAuth.js v5 (Auth.js) with credentials + OAuth providers
- **Validation**: Zod (server) + react-hook-form + zod-resolver (client)
- **Testing**: Vitest (unit) + Playwright (e2e)
- **Package Manager**: pnpm

### Directory Structure
```
my-saas/
├── src/
│   ├── app/               # App Router pages
│   │   ├── api/           # Route Handlers
│   │   ├── (auth)/        # Auth pages (login, register)
│   │   ├── dashboard/     # Protected dashboard
│   │   └── layout.tsx     # Root layout
│   ├── components/        # React components
│   │   ├── ui/            # shadcn/ui primitives
│   │   └── features/      # Feature-specific components
│   ├── db/                # Database layer
│   │   ├── schema/        # Drizzle schema files
│   │   ├── migrations/    # Auto-generated (never hand-edit)
│   │   ├── index.ts       # DB client export
│   │   └── seed.ts        # Development seed data
│   ├── lib/               # Core utilities
│   │   ├── auth.ts        # NextAuth config
│   │   └── utils.ts       # Shared helpers (cn, format, etc.)
│   ├── hooks/             # React hooks
│   ├── actions/           # Server Actions (file-per-domain)
│   └── types/             # Shared TypeScript types
├── drizzle.config.ts      # Drizzle Kit config
├── next.config.ts
├── tailwind.config.ts
└── tsconfig.json
```

## Conventions

### Naming
- **Files**: kebab-case for pages (`user-settings.tsx`), camelCase for hooks (`useAuth.ts`)
- **Components**: PascalCase for exported components, matches file name
- **Functions**: async functions use `_` prefix for internal helpers (`_buildWhereClause`)
- **DB tables**: snake_case, plural (`user_sessions`, `team_members`)
- **API routes**: RESTful naming (`api/teams/[id]/invite`)
- **Environment vars**: `NEXT_PUBLIC_` prefix for client-side only

### Database Rules
1. **All migrations auto-generated** via `drizzle-kit generate`. Never write manual SQL.
2. **Foreign keys** use SQLite-compatible syntax (PRAGMA foreign_keys = ON at connection)
3. **Don't use .env for SQLite path** — default to `./data/dev.db` for dev, `./data/prod.db` for prod
4. **Seed files** must be idempotent (upsert, not insert)
5. **Indexes** on foreign key columns + query hot paths
6. **Migrations are immutable** — never edit generated files. Create new migration for changes.

### Patterns to Follow
1. **Server Actions** for mutations (no API routes unless third-party webhook)
2. **Route Handlers** only for webhooks, file uploads, or external API proxies
3. **Zod** for both client validation (react-hook-form resolver) and server validation (action param)
4. **Loading states** via `loading.tsx` and `useTransition` (not `useState` for loading flags)
5. **Error boundaries** per route group (not global)
6. **Session management** via NextAuth `auth()` helper — never trust `sessionStorage`
7. **Components**: server component by default, sprinkle `"use client"` only when needed
8. **DB queries** in Server Components (not in client components — use Server Actions + revalidation)
9. **Tailwind** for styling — no CSS modules, no styled-components
10. **shadcn/ui** components go in `components/ui/`, customized via `tailwind.config.ts`

### Anti-Patterns to Avoid
1. ❌ Don't put DB queries inside client components (use Server Actions or route handlers)
2. ❌ Don't import server-only code (`cookies()`, `headers()`, `db`) in client files
3. ❌ Don't use `useEffect` for data fetching (use Server Components + Actions)
4. ❌ Don't store secrets in `NEXT_PUBLIC_` vars (they're sent to browser)
5. ❌ Don't use `any` type — prefer TypeScript inferred types or `z.infer`
6. ❌ Don't manually edit migration files
7. ❌ Don't use `setTimeout` in server actions (use `unstable_after()` if needed)
8. ❌ Don't nest client components inside server components that pass callbacks

### Dev Commands
```bash
pnpm dev              # Start dev server (Turbopack)
pnpm db:generate      # Generate SQL migration from schema changes
pnpm db:migrate       # Apply pending migrations
pnpm db:seed          # Run seed script (idempotent)
pnpm db:studio        # Open Drizzle Studio (GUI DB viewer)
pnpm test             # Run Vitest unit tests
pnpm test:e2e         # Run Playwright tests
pnpm lint             # ESLint + Tailwind class sorting
pnpm type-check       # tsc --noEmit (strict mode enabled)
```

### Deployment
- **Production DB**: Turso (libsql) — same Drizzle schema, different connection URL
- **CI Pipeline**: lint → type-check → test → build → db:migrate → deploy
- **Environment**: `DATABASE_URL` for production (file path for local, libsql:// for Turso)
- **Backup**: SQLite file automatically backed up to `.backups/` on deploy (via GitHub Action)

### Pull Request Checklist (for Claude Code)
- [ ] Did you run `pnpm type-check`? (no `any` types)
- [ ] Did you run `pnpm lint`? (no warnings)
- [ ] Did you run `pnpm test`? (all passing)
- [ ] Did you add DB indexes for new queries?
- [ ] Did you wrap new server actions in try/catch?
- [ ] Did you add Zod validation for all public inputs?
- [ ] Did you add loading state for async operations?

### Testing Rules
- **Unit tests** live next to the file they test: `actions/create-team.ts` → `actions/create-team.test.ts`
- **Mock DB** with `better-sqlite3` in-memory database (not `vitest-mock-extended`)
- **E2E tests** use Playwright with a fresh seeded SQLite database per test file
- **Snapshot tests** only for UI components that rarely change

## Why These Conventions

- **Server Actions over API routes**: Less boilerplate, built-in revalidation, no serialization
- **Drizzle over Prisma**: Better SQLite support, lighter bundle, raw SQL escape hatch
- **kebab-case files**: Case-insensitive file systems (Windows/macOS) won't cause import bugs
- **Snake_case DB**: SQL convention, works with raw queries, no quoting needed
- **Immutable migrations**: Historical accuracy — you can recreate any DB version from git
- **Try/catch in server actions**: Prevents unhandled rejections from crashing the Node.js process
