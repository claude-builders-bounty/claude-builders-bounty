# CLAUDE.md - Next.js 15 App Router + SQLite (Turso/Better-SQLite3)

## Commands

### Development
- `npm run dev` - Start dev server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run typecheck` - Run TypeScript check

### Testing
- `npm test` - Run all tests
- `npm run test:watch` - Run tests in watch mode
- `npm run test:e2e` - Run Playwright e2e tests

### Database
- `npm run db:push` - Push schema to database
- `npm run db:generate` - Generate Drizzle migrations
- `npm run db:migrate` - Run pending migrations
- `npm run db:studio` - Open Drizzle Studio

### Commands (single)
- `npm run test -- -t "test name"` - Run single test
- `npm run lint -- --fix` - Auto-fix lint issues

## Code Style

- TypeScript strict mode enabled
- Use `import type` for type-only imports
- Path aliases: `@/` maps to `src/`
- React Server Components by default; add `'use client'` only when needed
- Server Actions use `'use server'` in separate files
- Async components are the default; avoid useEffect for data fetching
- Use `next/navigation` (not `next/router`)
- `generateMetadata` for all route segments

## Data Access

- Drizzle ORM with SQLite (Turso for production, better-sqlite3 for dev)
- Schema in `src/db/schema/`
- Queries in `src/db/queries/`
- All DB access via Server Components or Server Actions
- Use `revalidatePath` / `revalidateTag` for cache invalidation

## Architecture

- `src/app/` - App Router pages and API routes
- `src/components/` - Shared React components
- `src/db/` - Database schema, queries, migrations
- `src/lib/` - Utility functions and shared logic
- `src/actions/` - Server Actions
- `public/` - Static assets

## Auth

- NextAuth.js v5 (Auth.js) with credentials + OAuth providers
- Session in `src/lib/auth.ts`
- Middleware in `src/middleware.ts`
- Route protection via middleware matcher

## Environment Variables

Required vars in `.env.local`:
- `DATABASE_URL` - SQLite connection string
- `AUTH_SECRET` - Auth.js secret
- `AUTH_GITHUB_ID` / `AUTH_GITHUB_SECRET` - GitHub OAuth (optional)
