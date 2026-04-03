# CLAUDE.md — Next.js + SQLite SaaS Template

## Project Overview
This is a Next.js SaaS application using SQLite for persistence.

## Tech Stack
- **Framework:** Next.js 14+ (App Router)
- **Database:** SQLite via better-sqlite3
- **ORM:** Drizzle ORM
- **Auth:** NextAuth.js v5
- **Styling:** Tailwind CSS + shadcn/ui
- **Testing:** Vitest + React Testing Library
- **Language:** TypeScript (strict mode)

## Project Structure
```
app/
  (auth)/          # Auth pages (login, register)
  (dashboard)/     # Protected dashboard pages
  api/             # API route handlers
    auth/[...nextauth]/route.ts
    [...route]/    # REST endpoints
  layout.tsx       # Root layout
  page.tsx         # Landing page
components/
  ui/              # shadcn/ui components
  forms/           # Reusable form components
  charts/          # Data visualization
lib/
  db/
    schema.ts      # Drizzle schema definitions
    migrate.ts     # Migration runner
    index.ts       # Database connection singleton
  auth.ts          # NextAuth configuration
  validations.ts   # Zod schemas
  utils.ts         # Shared utilities
drizzle/           # Generated migrations
public/            # Static assets
tests/             # Test files
```

## Code Conventions

### API Routes
- Use Route Handlers: `app/api/[resource]/route.ts`
- Always validate input with Zod (`lib/validations.ts`)
- Return `{ data, error }` pattern
- Handle errors with `NextResponse.json({ error }, { status })`

### Database
- Schema in `lib/db/schema.ts` — use Drizzle's `pgTable` equivalent (`sqliteTable`)
- Migrations: `npm run db:generate` then `npm run db:migrate`
- Always use parameterized queries (Drizzle handles this)
- Connection singleton pattern in `lib/db/index.ts`

### Auth
- Protect routes with `auth()` from `lib/auth.ts`
- Server components: `const session = await auth()`
- Middleware in `middleware.ts` for route protection

### Components
- Use shadcn/ui components from `components/ui/`
- Client components: add `"use client"` directive
- Props interfaces defined inline, not exported unless reused

## Testing
```bash
npm test              # Run all tests
npm run test:watch    # Watch mode
npm run test:coverage # Coverage report
```

### Test Patterns
- Co-locate tests: `__tests__/` next to the module
- Use `describe/it` blocks
- Mock external APIs, use real SQLite for integration tests
- Factory functions for test data

## Common Commands
```bash
npm run dev           # Dev server on :3000
npm run build         # Production build
npm run start         # Start production server
npm run lint          # ESLint
npm run db:studio     # Drizzle Studio (DB browser)
```

## Architecture Decisions
- **SQLite over Postgres:** Simpler deployment, single-file DB, sufficient for SaaS scale (<10k users)
- **App Router over Pages:** Server components reduce client bundle, streaming support
- **Drizzle over Prisma:** Lighter, SQL-like API, better SQLite support
- **better-sqlite3 over sql.js:** Synchronous, faster, native bindings

## Deployment
- Single Dockerfile (Node.js + SQLite file on volume)
- Vercel-compatible (use `@vercel/postgres` if scaling beyond SQLite)
- Environment variables: `DATABASE_URL`, `NEXTAUTH_SECRET`, `NEXTAUTH_URL`

## Security Checklist
- [ ] Input validation on all API routes (Zod)
- [ ] CSRF protection (NextAuth default)
- [ ] Rate limiting on auth endpoints
- [ ] SQL injection prevented by Drizzle parameterization
- [ ] XSS prevented by React auto-escaping
- [ ] Environment secrets not in client bundle
