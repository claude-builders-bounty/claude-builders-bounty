# CLAUDE.md — Next.js + SQLite SaaS Project

## Project Overview
A SaaS application built with Next.js 14 (App Router), SQLite (via Drizzle ORM), and Tailwind CSS.

## Tech Stack
- **Framework:** Next.js 14 (App Router)
- **Database:** SQLite via better-sqlite3 + Drizzle ORM
- **Auth:** NextAuth.js with GitHub/Google providers
- **Styling:** Tailwind CSS + shadcn/ui
- **Testing:** Vitest + Playwright

## Project Structure
```
src/
  app/           # Next.js App Router pages
    api/         # API routes
    (auth)/      # Auth pages (login, register)
    (dashboard)/ # Protected dashboard pages
  components/    # React components
  lib/           # Shared utilities
  db/            # Database schema + migrations
  hooks/         # Custom React hooks
public/          # Static assets
drizzle.config.ts
```

## Development Commands
```bash
npm run dev        # Start dev server
npm run build      # Production build
npm run db:push    # Push schema to SQLite
npm run db:studio  # Open Drizzle Studio
npm run test       # Run tests
npm run lint       # ESLint
```

## Database
- SQLite file: `./data/app.db` (gitignored)
- Schema: `src/db/schema.ts`
- Migrations: `drizzle/migrations/`

## API Conventions
- Use `app/api/` route handlers
- Auth check: `const session = await getServerSession(authOptions)`
- Validation: Zod schemas in `src/lib/validations.ts`

## Code Style
- TypeScript strict mode
- Prefer `const` over `let`
- Components in PascalCase
- Functions in camelCase
- Database tables in snake_case

## Testing
- Unit: Vitest (`*.test.ts`)
- E2E: Playwright (`*.spec.ts`)
- Run all: `npm run test:all`

## Common Patterns
- Server components by default, `"use client"` only when needed
- Form handling: react-hook-form + zod
- State: React Context + useReducer for complex state
- Error boundaries: `app/error.tsx`
