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
- Server Components by default; 'use client' only when needed (interactivity, context, hooks)
- Server Actions in `src/actions/`, one file per domain
- Database queries in `src/db/queries/`, never inline in components
- Shared Zod schemas in `src/lib/schemas/`, validated on both client and server
- All environment variables via `src/lib/env.ts` using `@t3-oss/env-nextjs`
- No barrel exports (`index.ts`) — explicit imports only

## Naming
- Files: `kebab-case.ts`
- Components: `PascalCase.tsx`
- Functions/variables: `camelCase`
- Database tables: `snake_case`
- Types/interfaces: `PascalCase` with `Type` suffix for complex types
- Server action files: `domain.actions.ts`

## Database Rules
- All queries use Drizzle prepared statements (never raw SQL)
- Migrations are generated, never hand-written
- Foreign keys enforced via `foreignKey()` in schema
- Soft deletes via `deletedAt` column where applicable
- Pagination via cursor-based (not offset) for performance

## Dev Workflow
```bash
npm run dev          # Start dev server
npm run db:generate  # Generate Drizzle migrations
npm run db:push      # Push schema to local SQLite
npm run db:studio    # Drizzle Studio GUI
npm run lint         # ESLint + Prettier check
npm run typecheck    # tsc --noEmit
npm run test         # Vitest
```

## Anti-patterns to Avoid
- ❌ `useEffect` for data fetching — use Server Components or Server Actions
- ❌ Wrapping everything in try/catch in Server Actions — use `ActionState` return type
- ❌ Storing sessions in SQLite — use NextAuth's built-in JWT strategy
- ❌ Direct database access from components — always go through queries layer
- ❌ Large client bundles — use dynamic imports with `next/dynamic`

## Security
- All user input validated via Zod before reaching database
- CSRF protection via Next.js Server Actions (built-in)
- Rate limiting on auth routes via `upstash-rate-limiter`
- SQLite WAL mode for concurrent reads
- Stripe webhook signatures verified on every event
