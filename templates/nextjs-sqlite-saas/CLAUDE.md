# CLAUDE.md — Next.js 15 + SQLite SaaS

## Tech Stack
- **Framework**: Next.js 15 (App Router), React 19, TypeScript strict
- **Database**: SQLite via better-sqlite3 (local dev) / Turso (production)
- **ORM**: Drizzle ORM (schema-first, no migrations drift)
- **Auth**: NextAuth.js v5 with credentials + OAuth providers
- **Styling**: Tailwind CSS v4 + shadcn/ui components
- **Validation**: Zod schemas shared between client and server
- **Payments**: Stripe (webhook-driven subscription state)

## Project Structure
```
src/
  app/          # App Router pages
  components/   # Shared UI components (shadcn + custom)
  db/           # Drizzle schema, queries, migrations
  lib/          # Utilities, config, middleware
  actions/      # Server Actions (mutation only)
  api/          # Route handlers (external-facing)
```

## Conventions
- Server Components by default; 'use client' only when needed
- Server Actions in src/actions/, one file per domain
- DB queries in src/db/queries/, never inline in components
- Shared Zod schemas in src/lib/schemas/, validated on both sides
- Env vars via src/lib/env.ts using @t3-oss/env-nextjs
- No barrel exports — explicit imports only

## Naming
- Files: kebab-case.ts
- Components: PascalCase.tsx
- Functions/variables: camelCase
- DB tables: snake_case
- Types: PascalCase with Type suffix

## Database Rules
- All queries use Drizzle prepared statements
- Migrations are generated, never hand-written
- Foreign keys enforced via foreignKey() in schema
- Soft deletes via deletedAt column
- Cursor-based pagination

## Dev Workflow
npm run dev, npm run db:generate, npm run db:push, npm run lint, npm run typecheck, npm run test

## Anti-patterns
- No useEffect for data fetching
- No direct DB access from components
- No barrel exports
- No large client bundles without dynamic imports
- No raw SQL

## Security
- All input validated via Zod
- CSRF via Server Actions (built-in)
- Rate limiting on auth routes
- SQLite WAL mode
- Stripe webhook signature verification
