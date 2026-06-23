# CLAUDE.md ? Next.js 15 + SQLite SaaS Project

## Project Structure
```
/
??? src/
?   ??? app/          # Next.js App Router pages
?   ??? components/   # React components (shadcn/ui)
?   ??? lib/          # Shared utilities, DB client
?   ??? db/           # Drizzle schema + migrations
?   ??? actions/      # Server Actions
??? public/           # Static assets
??? tests/            # Vitest tests
```

## Tech Stack
- **Framework**: Next.js 15 (App Router)
- **Database**: SQLite via Turso (libsql) or better-sqlite3
- **ORM**: Drizzle ORM
- **UI**: shadcn/ui + Tailwind CSS 4
- **Auth**: NextAuth.js / Auth.js v5
- **Forms**: React Hook Form + Zod validation
- **Testing**: Vitest + Playwright

## Naming Conventions
- **Files**: kebab-case for pages (`user-profile.tsx`), PascalCase for components (`UserCard.tsx`)
- **Variables**: camelCase for JS, snake_case for DB columns
- **DB tables**: plural snake_case (`user_sessions`)
- **Server Actions**: verb-noun (`createUser`, `updateProfile`)
- **API routes**: RESTful plural (`/api/users/[id]`)

## Commands
```bash
npm run dev          # Start dev server (localhost:3000)
npm run build        # Production build
npm run test         # Run Vitest
npm run test:e2e     # Playwright E2E tests
npm run db:push      # Push schema changes
npm run db:studio    # Open Drizzle Studio
npm run lint         # ESLint + Prettier check
```

## Code Patterns
- Use Server Components by default; add 'use client' only when needed
- Data fetching in Server Components or Server Actions, not useEffect
- Form validation with Zod + React Hook Form
- Error boundaries at route group level
- Loading states with React Suspense
- DB queries in `src/lib/db.ts`, never inline in components
- Migrations via Drizzle Kit, never raw SQL

## Anti-Patterns (Avoid)
- ? Client-side data fetching when Server Component suffices
- ? Direct DB access from client components
- ? `any` types ? use Zod inference or explicit types
- ? Magic strings for routes ? use constants
- ? Large `useEffect` blocks ? prefer Server Actions
- ? Mixing migration strategies ? use Drizzle only

## Testing
- Unit tests with Vitest (colocated: `*.test.ts`)
- E2E with Playwright (`tests/e2e/`)
- Test DB queries against a test SQLite database
- Mock external APIs in integration tests
