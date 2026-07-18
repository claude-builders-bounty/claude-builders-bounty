# CLAUDE.md - Next.js + SQLite SaaS Project

## Tech Stack
- **Framework**: Next.js 14+ (App Router)
- **Database**: SQLite via better-sqlite3 / Turso (libsql)
- **ORM**: Drizzle ORM
- **Auth**: NextAuth.js / Auth.js v5
- **UI**: Tailwind CSS + shadcn/ui
- **Language**: TypeScript (strict mode)

## Project Structure
/app            - Next.js App Router pages & API routes
/components     - Reusable React components (shadcn/ui)
/db             - Database schema, migrations, queries
/lib            - Shared utilities, helpers, config
/auth           - Authentication configuration
/actions        - Server actions
/types          - TypeScript types & interfaces
/public         - Static assets

## Conventions
- Use server components by default; add "use client" only when needed
- Server actions for mutations, API routes for external integrations
- All database queries through Drizzle ORM (no raw SQL)
- Environment variables via z-environment validation
- Error boundaries at every route segment

## Database Patterns
- Single SQLite file for development; Turso for production
- Migrations via Drizzle Kit: `npx drizzle-kit push`
- Use transactions for multi-step operations
- Soft deletes via `deletedAt` column

## Commands
pnpm dev         - Start dev server
pnpm build       - Build for production
pnpm db:push     - Push schema changes
pnpm db:studio   - Open Drizzle Studio
pnpm lint        - Run ESLint
pnpm test        - Run tests

## Environment
DATABASE_URL=file:./data/dev.db
AUTH_SECRET=...
AUTH_GITHUB_ID=...
RESEND_API_KEY=...
