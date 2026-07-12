# Claude AI Instructions

This file provides system context and rules for AI assistants (like Claude) working in this repository.

## Stack & Versions
- **Framework:** Next.js 15 (App Router only)
- **Language:** TypeScript
- **Database:** SQLite (using `better-sqlite3` or Turso)
- **ORM / Query Builder:** Drizzle ORM (preferred for type safety)
- **Styling:** Tailwind CSS + Shadcn UI
- **Auth:** NextAuth.js (v5 / Auth.js)

## Dev Commands
- `npm run dev`: Start local development server
- `npm run build`: Build production application
- `npm run db:push`: Push schema changes to the database
- `npm run db:studio`: Open Drizzle studio / DB viewer
- `npm run lint`: Run ESLint and TypeScript checks

## Folder Structure
- `app/`: Next.js App Router routes. Keep files collocated (e.g., `app/dashboard/page.tsx`, `app/dashboard/loading.tsx`).
- `components/ui/`: Reusable, generic UI components (e.g., Shadcn buttons, inputs).
- `components/features/`: Domain-specific components (e.g., `SubscriptionCard.tsx`).
- `lib/db/`: Database configuration, connection pooling, and schema definitions.
- `lib/actions/`: Next.js Server Actions. Do not put server actions inside components.
- `lib/utils/`: Pure utility functions without side effects.

## Component Patterns
- **Server Components by Default:** All components are Server Components unless they need state or browser APIs. Only use `'use client'` when strictly necessary.
- **Colocation:** Keep styles, tests, and types close to the component if they aren't globally reused.
- **Server Actions for Mutations:** Always use Server Actions for database mutations. Define them in `lib/actions/` and ensure they validate inputs using Zod.
- **Prop Drilling:** Avoid deep prop drilling. If components share state heavily, use React Context or URL search parameters as the source of truth.

## SQL / Migration Conventions
- **Schema Source of Truth:** `lib/db/schema.ts` (or separated into `lib/db/schema/` for large apps) is the single source of truth.
- **Migration Rules:** Do not manually edit the SQLite database. Always use Drizzle migrations (or your respective ORM's migration tool).
- **Foreign Keys:** Always enable foreign key constraints (`PRAGMA foreign_keys = ON;`) on every connection instance.
- **Timestamps:** Every table must have `created_at` (default to current timestamp) and `updated_at` (updated via triggers or ORM lifecycle hooks) columns.

## What we don't do (and why)
- **NO Pages Router:** Next.js 15 App Router is the standard here. Do not create a `pages/` directory. Reason: Mixing routing paradigms causes confusing bugs and splits caching logic.
- **NO Client-Side DB Calls:** Never connect to SQLite from client components. Reason: Security risk and SQLite requires Node.js/server environments.
- **NO Inline Server Actions:** Avoid defining `async function myAction()` directly inside a component's render function. Reason: It clutters the UI logic and makes the action harder to test or reuse. Put them in `lib/actions/`.
- **NO Default Exports (except pages/layouts):** Use named exports for components and utility functions. Reason: Named exports ensure consistent naming during refactoring and better IDE auto-imports.
- **NO `any` types:** Never use `any` in TypeScript. If the type is unknown, use `unknown` and narrow it down with Zod or type guards. Reason: `any` defeats the purpose of TypeScript.

## Naming Conventions
- **Files/Folders:** `kebab-case` for routes (`app/user-profile`), `PascalCase` for React components (`Button.tsx`), `camelCase` for utilities (`formatDate.ts`).
- **Database Tables:** `snake_case` and pluralized (e.g., `users`, `subscription_plans`).
- **Environment Variables:** `UPPER_SNAKE_CASE`. Prefix client-exposed variables with `NEXT_PUBLIC_`.
