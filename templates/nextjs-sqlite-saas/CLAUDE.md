# Claude Code Instructions for Next.js 15 + SQLite SaaS

This project is a Next.js 15 SaaS boilerplate using the App Router, React 19, and `better-sqlite3`.

## Stack & Versions
- **Next.js 15** (App Router only)
- **React 19** (Server Components by default)
- **better-sqlite3** (Local synchronous DB queries)
- **Tailwind CSS v4** (Styling)
- **TypeScript** (Strict mode)

## Folder Structure
- `app/`: Next.js App Router routes and pages. No `pages/` directory.
- `app/api/`: REST endpoints and webhooks.
- `app/actions/`: Server Actions (`"use server"`) for all data mutations.
- `components/`: Reusable React components.
  - `components/ui/`: Dumb/presentational components (e.g., buttons, inputs).
  - `components/shared/`: Complex components used across multiple pages.
- `db/`: Database configuration, schemas, and migrations.
  - `db/migrations/`: Sequenced SQL migration files.
  - `db/schema.sql`: The complete, current schema definition.
- `lib/`: Utility functions and shared logic (e.g., `lib/utils.ts`).
- `types/`: Global TypeScript type definitions.

## Naming Conventions
- **Files/Folders**: Use `kebab-case` for all file and folder names (e.g., `user-profile.tsx`, `app/auth-callback/`). Reason: Prevents casing conflicts across case-insensitive file systems.
- **Components**: Use `PascalCase` for component names and exports (e.g., `export function UserProfile()`).
- **Server Actions**: Prefix with a verb and use `camelCase` (e.g., `updateUserAction()`, `createSubscription()`).
- **SQL Tables**: Use `snake_case`, pluralized (e.g., `users`, `subscriptions`, `audit_logs`).

## SQL / Migration Conventions
- **Tooling**: We use raw SQL with `better-sqlite3`. No Prisma, no Drizzle. Reason: Raw SQL prevents ORM bloat, forces us to understand our queries, and `better-sqlite3` is highly optimized for synchronous access.
- **Migrations**: 
  - Live in `db/migrations/`. 
  - File format: `YYYYMMDD_HHMMSS_description.sql` (e.g., `20240524_103000_create_users_table.sql`). Reason: Sequential timestamps prevent merge conflicts.
- **Safety**: 
  - Always write idempotent migrations if possible (`CREATE TABLE IF NOT EXISTS`).
  - Update `db/schema.sql` to reflect the final database state alongside any migration.
- **Queries**: Use prepared statements via `.prepare()` for EVERYTHING to prevent SQL injection.

## Component Patterns
- **Server Components (RSC)**: Everything is a Server Component by default. Reason: Reduces client bundle size, improves SEO, allows direct DB queries without exposing endpoints.
- **Client Components**: 
  - Prefix with `"use client";` at the top.
  - Only use when state (`useState`), effects (`useEffect`), or browser APIs (like `window`) are strictly necessary.
  - Push Client Components down the tree as far as possible (leaf nodes). Reason: Minimizes the amount of JS sent to the browser.
- **Data Passing**: Pass plain objects/primitives to Client Components. DO NOT pass entire database rows if only a single field is needed. Reason: Security (preventing leak of hashes/PII) and payload size.

## What We Don't Do (And Why)
- **Do not use traditional API routes (`app/api/route.ts`) for internal UI actions.** Use Server Actions (`"use server"`) instead. Reason: Server actions provide end-to-end type safety and reduce network request boilerplate.
- **Do not use `localStorage` for authentication state.** Use secure, HTTP-only cookies. Reason: XSS attacks can easily steal `localStorage` tokens.
- **Do not leak server secrets to the client.** Never prefix env vars with `NEXT_PUBLIC_` unless absolutely required for the browser.
- **Do not build "God Components."** Keep components under 150-200 lines. Break them down. Reason: Maintainability and easier debugging.
- **Do not nest asynchronous callbacks.** Use modern `async/await` syntax. Reason: Readability and structured error handling (`try/catch`).

## Development Commands
- `npm run dev`: Starts the Next.js development server.
- `npm run build`: Builds the application for production.
- `npm run db:migrate`: Applies any pending SQL migrations from `db/migrations/` to the local SQLite DB.
- `npm run db:seed`: Populates the database with initial dummy/test data.
