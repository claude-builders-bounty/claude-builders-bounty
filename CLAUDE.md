# CLAUDE.md

## Stack & Versions
- **Next.js 15** (App Router, React 19, Server Components by default)
- **TypeScript 5.7+** (strict mode, no `any` without explicit justification)
- **SQLite** via **better-sqlite3** (synchronous API)
- **Tailwind CSS 4** with `@tailwindcss/vite` plugin
- **Zod** for validation (API routes, form actions, env parsing)
- **Drizzle ORM** for type-safe SQL
- **Lucide React** for icons (single import per icon)

## Folder Structure
```
src/
  app/
    (auth)/
    (dashboard)/
    api/
  components/
    ui/
    features/
    layout/
  lib/
    db/
    auth/
    utils/
  hooks/
  types/
db/
  migrations/
  schema.ts
  index.ts
```

## Database & Migration Conventions
- Always use Drizzle migrations — never modify SQLite directly
- Migration workflow: `db/schema.ts` → `drizzle-kit generate` → `drizzle-kit migrate`
- Never ship a migration without a corresponding schema change in the same PR
- Column naming: `snake_case` in SQL, `camelCase` in TypeScript (Drizzle maps automatically)
- Timestamps: always `created_at` and `updated_at`, defaults to `CURRENT_TIMESTAMP`
- Enable WAL mode in production: `PRAGMA journal_mode=WAL;`

## Dev Commands
```bash
pnpm dev              # Next.js dev server
pnpm build            # Production build
pnpm lint             # ESLint
pnpm typecheck        # tsc --noEmit
pnpm db:generate      # Generate Drizzle migrations
pnpm db:migrate       # Apply pending migrations
pnpm db:studio        # Drizzle Studio
pnpm test             # Vitest (unit)
pnpm test:e2e         # Playwright (E2E)
```

## Component Patterns
- Server Components by default — only add `'use client'` when you need interactivity
- No barrel exports — import directly from file path
- Props destructuring in function signature
- One component per file — no exceptions
- Forms use Server Actions with Zod validation
- Error boundaries wrap feature sections, not individual components

## What We Don't Do (and Why)
- No ORMs other than Drizzle — Prisma adds bloat, Knex is too low-level
- No `any` types — use `unknown` and narrow with Zod
- No `useEffect` for data fetching — Server Components or React Query
- No API route wrappers (tRPC, GraphQL) until 20+ endpoints
- No CSS-in-JS — Tailwind is the single source of truth
- No `.env` committed — `.env.example` documents required vars
- No `// eslint-disable` without a comment explaining why
- No giant PRs — PRs over 15 files need justification
