# CLAUDE.md

## Project Overview
Next.js 15 App Router SaaS application with SQLite (better-sqlite3 or Turso).

## Project Structure
```
src/
  app/           # App Router pages and layouts
    (auth)/      # Auth-required routes
    api/         # API routes (Route Handlers)
  components/    # Shared React components
    ui/          # Primitive UI components (Button, Input, etc.)
  lib/           # Shared utilities and business logic
    db/          # Database client, migrations, queries
    auth/        # Auth configuration and helpers
  types/         # Shared TypeScript types
prisma/          # Prisma schema (if using Prisma + SQLite)
  migrations/    # Database migrations
public/          # Static assets
```

## Naming Conventions
- **Files**: kebab-case (`user-profile.tsx`, `use-auth.ts`)
- **Components**: PascalCase (`UserProfile`, `SignInForm`)
- **Functions**: camelCase (`getUserById`, `formatCurrency`)
- **Database tables**: snake_case, plural (`user_sessions`, `order_items`)
- **Route handlers**: Named exports (`export async function GET()`) — never default exports
- **Type files**: Suffix with `.types.ts` or put in `types/` directory

## Database Rules
- **Migrations are append-only.** Never edit an existing migration — create a new one.
- **Always write down migrations.** Never use `db.push()` or `db.sync()` in production.
- **Use transactions** for any operation that touches multiple tables or modifies data.
- **Query in server components or route handlers only.** Client components fetch via API routes — never import db directly.
- **Index columns used in WHERE, JOIN, and ORDER BY clauses.**
- **Foreign keys are mandatory** — define them explicitly in migrations.

## Development Commands
```bash
npm run dev          # Start dev server (Turbo mode)
npm run build        # Production build
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript compiler check
npm run db:migrate   # Apply pending migrations
npm run db:seed      # Seed database with test data
npm run db:studio    # Open Prisma Studio (if using Prisma)
npm run test         # Run test suite
npm run test:watch   # Run tests in watch mode
```

## Patterns to Follow
- **Server-first data fetching**: Fetch data in Server Components using `async/await`. Pass data down to Client Components as props.
- **Route Handlers for mutations**: POST, PUT, DELETE go through API routes. GET can stay in server components.
- **Optimistic updates**: For mutations that affect UI, update the client state immediately and rollback on error.
- **Zod for validation**: Use Zod schemas for all user input, API params, and environment variables.
- **Server Actions for forms**: Use Next.js Server Actions with `useActionState` for form submissions.
- **Error boundaries**: Wrap client components that may throw in ErrorBoundary. Use `error.tsx` for route-level errors.
- **Loading states**: Use `loading.tsx` for route-level loading, `Suspense` for component-level.
- **Environment variables**: Use `NEXT_PUBLIC_` prefix only for client-safe values. Everything else stays server-only.

## Anti-Patterns to Avoid
- **No database calls in Client Components.** This includes importing db utilities directly. Use API routes or Server Actions.
- **No raw SQL in components.** Abstract all database logic into `lib/db/` functions.
- **No `any` types.** Always derive types from database schemas, Zod validation, or explicit interfaces.
- **No `useEffect` for data fetching.** Use Server Components, SWR, or React Query instead.
- **No inline styles.** Use CSS Modules, Tailwind CSS (if configured), or a design system.
- **No hardcoded URLs.** Use `process.env.NEXT_PUBLIC_URL` or relative paths.
- **No `dangerouslySetInnerHTML` without sanitization.** Use DOMPurify or similar.
- **No file upload processing in route handlers.** Offload to a background job or use server actions with size limits.

## Testing
- Unit tests for `lib/` utilities with Vitest
- Integration tests for API routes using `@testing-library/react` or supertest
- E2E tests with Playwright for critical user flows
- Test database is separate from dev — use `:memory:` SQLite for speed

## Deployment
- Platform: Vercel (recommended) or Docker
- Database: Turso (edge SQLite) for production, SQLite file for local dev
- CI: GitHub Actions for lint, type-check, test, build
