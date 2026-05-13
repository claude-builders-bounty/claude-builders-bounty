# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Build & Test Commands
- `npm run dev` — Start development server
- `npm run build` — Type-check and build
- `npm run lint` — Run ESLint
- `npm run typecheck` — Run TypeScript checks
- `npx prisma generate` — Regenerate Prisma client after schema changes
- `npx prisma db push` — Push schema to SQLite without migrations
- `npx prisma migrate dev` — Create and apply a new migration
- `npm run test` — Run Jest tests
- `npm run test:watch` — Run tests in watch mode
- `npm run test:coverage` — Run tests with coverage report
- `npm run e2e` — Run Playwright E2E tests

## Code Style & Structure
- **Route pattern**: `app/(routes)/(group)/page.tsx` — Group routes by feature domain
- **Data layer**: lib/db.ts exports Prisma client singleton; lib/queries/ per entity
- **Components**: app/_components/ for shared UI; each route has its own component dir
- **Server actions**: lib/actions/ with one file per domain (auth, billing, projects)
- **Middleware**: src/middleware.ts handles auth checks and route protection
- **Types**: types/ directory mirrors database schema; Zod schemas in lib/validations/

## Architecture Rules
1. **Server-first**: Fetch data in Server Components; client components only for interactivity
2. **No direct DB from client**: All mutations go through Server Actions or API routes
3. **SQLite considerations**: No concurrent writes; use Prisma transactions for atomicity
4. **Auth**: NextAuth v5 with credentials + OAuth; session in JWT cookie
5. **Billing**: Stripe webhooks handled in app/api/webhooks/stripe/route.ts

## Naming Conventions
- **Files**: kebab-case for routes (`user-settings/page.tsx`), PascalCase for components (`UserSettings.tsx`)
- **Exports**: Named exports for components, default exports for pages
- **Variables**: camelCase; constants in UPPER_SNAKE_CASE
- **Database models**: PascalCase (User, Project, Subscription)

## Error Handling
- Use `neverthrow` Result pattern for business logic
- Server Actions return `{ success: boolean; error?: string; data?: T }`
- API routes use try/catch with structured error response
- Display errors via toast for actions, inline validation for forms

## State Management
- URL search params for filter/sort/pagination state
- React Server Components for data fetching
- Zustand for complex client state (multi-step forms, real-time)
- React Query for client-side data fetching with caching
