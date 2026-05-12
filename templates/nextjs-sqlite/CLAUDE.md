# Project Guidelines (Next.js 15 + SQLite SaaS)

Opinionated instructions for building high-performance, maintainable SaaS products with Next.js 15 and SQLite.

## Tech Stack
- **Framework**: Next.js 15 (App Router)
- **Runtime**: Node.js 20+
- **Database**: SQLite (via `better-sqlite3` for local or `libsql` for Turso)
- **ORM**: Drizzle ORM
- **Styling**: Tailwind CSS
- **Auth**: NextAuth.js / Auth.js v5

## Project Structure
- `/app`: App Router pages and layouts.
- `/components/ui`: Reusable UI primitives (shadcn style).
- `/components/features`: Feature-specific components.
- `/lib/db`: Database schema and client initialization.
- `/lib/utils`: Shared helper functions.
- `/styles`: Global CSS.

## Naming Conventions
- **Files**: Use kebab-case for all files (e.g., `user-profile.tsx`).
- **Components**: PascalCase for React components (e.g., `Button`).
- **DB Schema**: camelCase for column names, snake_case for table names.

## SQL / Migration Rules
- **No Manual SQL**: Use Drizzle Kit for all schema changes and migrations.
- **Migration Command**: `npm run db:push` for development, `npm run db:migrate` for production.
- **SQLite Specifics**: Always use `PRAGMA journal_mode = WAL` and `PRAGMA synchronous = NORMAL` for high concurrency.

## Component Patterns
- **Server Components by Default**: Only use `'use client'` at the smallest possible leaf level.
- **Zustand for State**: Avoid complex Prop Drilling; use Zustand for global UI state.
- **React Server Actions**: Use Server Actions for all data mutations. No API routes for internal mutations.

## Anti-Patterns (What we don't do)
- **No Barrel Files**: Export components individually to prevent bundle bloating and circular dependencies.
- **No `any`**: TypeScript must be strict. Use `unknown` or interfaces for all data.
- **No Inline Styles**: Use Tailwind classes for all styling to maintain consistency.
- **No Client Fetching**: Use Server Components and `fetch` with caching; avoid `useEffect` for data fetching.
