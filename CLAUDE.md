# CLAUDE.md

## Project Overview
Next.js 15 App Router SaaS application with SQLite (better-sqlite3 or Turso).

## Stack
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript (strict mode)
- **Database**: SQLite via better-sqlite3 (local) or @libsql/client (Turso/cloud)
- **Auth**: NextAuth.js v5 with credentials + OAuth providers
- **Styling**: Tailwind CSS v4
- **ORM**: Drizzle ORM
- **Validation**: Zod
- **Testing**: Vitest + Playwright
- **Package Manager**: pnpm

## Project Structure
```
src/
├── app/                    # Next.js App Router pages
│   ├── (auth)/            # Auth group (login, register)
│   ├── (dashboard)/       # Authenticated dashboard group
│   ├── api/               # API route handlers
│   └── layout.tsx         # Root layout
├── components/
│   ├── ui/                # shadcn/ui components
│   ├── forms/             # Form components (react-hook-form + zod)
│   └── layouts/           # Layout components
├── lib/
│   ├── db/                # Database schema + migrations
│   │   ├── schema.ts      # Drizzle schema
│   │   ├── index.ts       # DB client singleton
│   │   └── migrations/    # Drizzle migrations
│   ├── auth.ts            # NextAuth config
│   ├── auth-client.ts     # Client-side auth helpers
│   └── utils.ts           # Shared utilities
├── server/
│   ├── actions.ts         # Server actions
│   ├── queries.ts         # Database query functions
│   └── mutations.ts       # Database mutation functions
└── types/
    └── index.ts           # Shared TypeScript types
```

## Naming Conventions
- **Files**: kebab-case (`user-profile.tsx`, `auth-helpers.ts`)
- **Components**: PascalCase (`UserProfile`, `SignInForm`)
- **Functions**: camelCase (`getUserById`, `createSession`)
- **Types/Interfaces**: PascalCase (`User`, `SessionData`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_LOGIN_ATTEMPTS`)
- **Database tables**: snake_case plural (`user_sessions`, `api_keys`)

## Database
- Use Drizzle ORM for all DB operations
- Migrations are in `src/lib/db/migrations/`
- Run `pnpm db:generate` after schema changes
- Run `pnpm db:migrate` to apply migrations
- Seed data in `src/lib/db/seed.ts`
- Never use raw SQL unless absolutely necessary

## Auth Flow
1. NextAuth.js v5 handles sessions via JWT
2. Protected routes use `middleware.ts` with route matchers
3. Server components: `import { auth } from '@/lib/auth'` then `const session = await auth()`
4. Client components: `import { useSession } from '@/lib/auth-client'`
5. API routes: validate with `auth()` in each handler

## API Routes
- ALL routes return `{ data, error }` shape
- Use Zod for request validation
- Handle errors with try/catch, return appropriate status codes
- Rate limiting via `@upstash/ratelimit` (optional)

## Testing
- Unit tests: Vitest (`*.test.ts`)
- E2E tests: Playwright (`e2e/*.spec.ts`)
- Run: `pnpm test` (unit), `pnpm test:e2e` (e2e)
- Test DB: in-memory SQLite per test file

## Commands
```bash
pnpm dev           # Next.js dev server (port 3000)
pnpm build         # Production build
pnpm start         # Production server
pnpm db:generate   # Generate Drizzle migrations
pnpm db:migrate    # Apply migrations
pnpm db:studio     # Drizzle Studio (port 4983)
pnpm test          # Run unit tests
pnpm test:e2e      # Run Playwright tests
pnpm lint          # ESLint
pnpm format        # Prettier
```

## Code Style
- Prefer server components over client components
- Use server actions for mutations (not API routes)
- Avoid `useEffect` for data fetching -- use server components
- Keep components under 200 lines; extract sub-components
- Use `cn()` utility for conditional Tailwind classes
- No default exports in `lib/` or `server/` -- use named exports
