# CLAUDE.md — Next.js + SQLite SaaS Project

## Project Overview
- **Stack:** Next.js (App Router), SQLite (via better-sqlite3/drizzle), TypeScript, Tailwind CSS
- **Auth:** NextAuth.js / Lucia Auth
- **ORM:** Drizzle ORM
- **Package Manager:** pnpm
- **Database:** SQLite (local file: `prisma/dev.db` or `data/sqlite.db`)

## Build Commands
- `pnpm dev` — Start development server (localhost:3000)
- `pnpm build` — Production build
- `pnpm start` — Start production server
- `pnpm lint` — Run ESLint
- `pnpm type-check` — Run TypeScript checks (tsc --noEmit)
- `pnpm test` — Run tests
- `pnpm test:watch` — Run tests in watch mode
- `pnpm db:push` — Push Drizzle schema to SQLite
- `pnpm db:generate` — Generate Drizzle migrations
- `pnpm db:studio` — Open Drizzle Studio

## Code Style
- **Imports:** Use `@/` alias for src directory
- **Components:** React Server Components by default
- **Types:** Prefer `interface` over `type` for objects
- **Naming:** camelCase for variables/functions, PascalCase for components
- **Error handling:** try/catch with App Router error boundaries
- **Database:** Always use prepared statements

## Architecture
- `/app` — Next.js App Router pages and API routes
- `/components` — Shared React components
- `/lib` — Business logic, utilities, database helpers
- `/db` — Drizzle schema, migrations, seed files
- `/types` — Shared TypeScript types
- `/public` — Static assets

## Key Conventions
- Every API route should have input validation (Zod)
- Database queries go in `/db/queries/`, not in route handlers
- Use Server Actions for form submissions
- Error pages: `error.tsx` at segment level
- Loading states: `loading.tsx` at segment level

## Environment Variables (.env.local)
- `DATABASE_URL` — Path to SQLite file
- `AUTH_SECRET` — Auth secret key
- `NEXT_PUBLIC_APP_URL` — Public app URL
