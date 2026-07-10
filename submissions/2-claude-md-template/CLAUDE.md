# CLAUDE.md — Next.js 15 + SQLite (Turso) SaaS Project

## Project Overview
- **Framework:** Next.js 15 (App Router)
- **Database:** SQLite via Turso (LibSQL)
- **ORM:** Drizzle ORM
- **Auth:** Lucia Auth / NextAuth v5
- **Deployment:** Vercel (serverless)
- **Language:** TypeScript (strict mode)

## Project Structure
```
src/
├── app/
│   ├── (auth)/          # Auth routes (login, register)
│   ├── (dashboard)/     # Authenticated routes
│   ├── api/             # API route handlers
│   └── layout.tsx       # Root layout with providers
├── components/
│   ├── ui/              # shadcn/ui components
│   └── forms/           # React Hook Form + Zod
├── db/
│   ├── schema/          # Drizzle schema definitions
│   ├── migrations/      # SQL migration files
│   └── index.ts         # DB client (Turso/libsql)
├── lib/
│   ├── auth.ts          # Auth configuration
│   ├── utils.ts         # Utility functions
│   └── validations.ts   # Zod schemas
└── actions/             # Server Actions
```

## Conventions

### Naming
- **Files:** kebab-case (`user-profile.tsx`)
- **Components:** PascalCase (`UserProfile`)
- **Functions:** camelCase (`fetchUserData`)
- **DB Tables:** snake_case (`user_sessions`)
- **DB Columns:** snake_case (`created_at`)
- **API Routes:** kebab-case with params (`/api/users/[id]`)

### Coding Standards
- Use `async/await` over raw promises
- Prefer Server Components by default; add `"use client"` only when needed
- Use `Server Actions` for form submissions (not API routes for simple mutations)
- Never import server code into client components
- Always validate inputs with Zod before DB operations
- Use `satisfies` operator for type-safe object literals

### Database Patterns
- All migrations are SQL files in `db/migrations/`
- Run migrations: `npm run db:migrate`
- Generate migrations: `npm run db:generate`
- Every table must have: `id`, `created_at`, `updated_at`
- Soft deletes preferred: add `deleted_at` column
- Use prepared statements for frequent queries

### Auth Patterns
- Session-based auth (Lucia) / JWT (NextAuth)
- Store only `userId` and `role` in session/JWT
- Always check auth in Server Actions and API routes
- Use middleware for protected route redirects

### Commands
```bash
npm run dev          # Start dev server
npm run build        # Production build
npm run lint         # ESLint + Prettier
npm run type-check   # tsc --noEmit
npm run test         # Vitest
npm run db:generate  # Generate Drizzle migrations
npm run db:migrate   # Run pending migrations
npm run db:seed      # Seed database
```

### Anti-Patterns (Avoid)
- ❌ `useEffect` for data fetching (use Server Components or React Query)
- ❌ Direct DB access from Client Components
- ❌ Storing raw passwords — use `bcrypt` or `Argon2`
- ❌ `any` type — use `unknown` and narrow
- ❌ Large client bundles — use `next/dynamic` for heavy components
- ❌ SQL injection — always use parameterized queries via Drizzle
- ❌ Over-fetching — use `select` to limit columns
- ❌ Missing error boundaries — wrap each route segment

## Environment Variables
```
# Required
DATABASE_URL=          # Turso database URL
DATABASE_AUTH_TOKEN=   # Turso auth token
AUTH_SECRET=           # Auth encryption key

# Optional
RESEND_API_KEY=        # Email service
NEXT_PUBLIC_URL=       # Production URL
STRIPE_SECRET_KEY=     # Stripe integration
```

## Git Workflow
- `main` — production-ready, auto-deploys to Vercel
- `develop` — staging branch
- Feature branches: `feat/description`
- Bug fixes: `fix/description`
- Commit messages: [Conventional Commits](https://www.conventionalcommits.org/)
  - `feat:` new feature
  - `fix:` bug fix
  - `refactor:` code change (no feature/fix)
  - `docs:` documentation
  - `chore:` maintenance

## Testing
- Unit tests: Vitest + Testing Library
- E2E tests: Playwright (separate config)
- Test files co-located with components: `Component.test.tsx`
- Minimum 80% coverage on new code
