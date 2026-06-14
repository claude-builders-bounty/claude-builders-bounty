# CLAUDE.md

## Project Overview
Next.js 15 SaaS application with SQLite via Drizzle ORM.

## Tech Stack
- **Framework**: Next.js 15 App Router (React 19, RSC-first)
- **Database**: SQLite via better-sqlite3 (local) / Turso (prod)
- **ORM**: Drizzle ORM with drizzle-kit for migrations
- **Auth**: NextAuth.js v5 (Auth.js) with credentials + OAuth
- **Styling**: Tailwind CSS v4 + shadcn/ui components
- **Forms**: React Hook Form + Zod validation
- **Payments**: Stripe (subscription tier management)
- **Email**: Resend for transactional emails
- **Deployment**: Vercel
## Database Migration Rules
1. NEVER edit existing migration files - they are immutable history
2. Use `drizzle-kit push` during dev, then `drizzle-kit generate` for final
3. Migration workflow:
   ```bash
   npx drizzle-kit push     # During development
   npx drizzle-kit generate  # Before deployment
   npx drizzle-kit migrate   # Apply in production
   ```
4. Schema changes must be additive (no renames or drops)
5. Every table needs: id (PK), created_at, updated_at
6. Soft deletes prefer deleted_at column

## Dev Commands
```bash
npm run dev              # Start dev server
npm run build            # Production build
npx drizzle-kit push     # Push schema to DB
npx drizzle-kit generate # Generate migration
npx drizzle-kit migrate  # Apply migrations
npx tsx scripts/seed.ts  # Seed test data
```

## Patterns to Follow
- Server Components by default; useClient only when needed
- Data fetching in Server Components (async, direct DB queries)
- API routes for mutations; server actions for forms
- Every DB function returns {data, error} tuple
- Zod validation on every public API endpoint
- Auth check at top of every protected route
- Use next/image for all images
- Prepared statements via Drizzle, never raw SQL

## Anti-Patterns to Avoid
- Using fetch in client when Server Component could handle it
- Storing session in localStorage (use NextAuth cookies)
- Hardcoding URLs (use env vars or path aliases)
- Importing server code (DB, auth) into client components
- Multiple DB connections (use singleton pattern)
- Ignoring TS errors with as any or ts-ignore
- Business logic in page components (extract to lib/)
- Using useEffect for data fetching
- Multiple sequential DB queries in a loop (use joins)
- Committing .env.local without review

## Architecture Decisions
1. RSC over client components: reduces JS bundle, improves SEO
2. Drizzle over Prisma: lighter, better SQLite support
3. SQLite over PostgreSQL: simpler ops, Turso for scale
4. Server Actions for forms: no separate API routes needed
5. Stripe subscription-first: delegate payment complexity

## Testing
```bash
npm run test          # Unit tests (Vitest)
npm run test:e2e      # E2E tests (Playwright)
```
- Unit tests: src/**/*.test.ts
- Component tests: src/components/**/*.test.tsx
- E2E: e2e/ (critical flows: auth, checkout, settings)
- Test DB: in-memory SQLite seeded per test

## Environment Variables
DATABASE_URL=file:./data/dev.db
AUTH_SECRET=                              # NextAuth secret
AUTH_GITHUB_ID=                           # GitHub OAuth
AUTH_GITHUB_SECRET=                       # GitHub OAuth
STRIPE_SECRET_KEY=                        # Stripe
NEXT_PUBLIC_APP_URL=http://localhost:3000  # App URL

