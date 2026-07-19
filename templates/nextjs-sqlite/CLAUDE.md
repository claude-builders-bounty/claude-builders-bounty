# Claude Code Guidelines: Next.js 15 App Router + SQLite

## Purpose
This document defines the strict, opinionated standards for developing this greenfield Next.js 15 + SQLite SaaS project. You must implicitly follow these rules without asking for clarification.

## Stack
- **Framework**: Next.js 15 (App Router strictly)
- **Database**: SQLite (via better-sqlite3 locally, Turso for prod) using Drizzle ORM
- **UI/Styling**: Tailwind CSS v4, shadcn/ui, Radix Primitives
- **Language**: TypeScript (Strict)
- **Package Manager**: pnpm

## Development Commands
- `pnpm install` - Install dependencies
- `pnpm dev` - Start development server
- `pnpm db:generate` - Generate Drizzle migrations
- `pnpm db:push` - Apply schema changes
- `pnpm db:studio` - Open Drizzle database explorer
- `pnpm typecheck` - Run tsc validation
- `pnpm lint` - Run ESLint

## Folder Structure
- `app/` - Routing (layouts, pages, loading, error, route handlers). **No business logic here.**
- `components/` - React components.
  - `components/ui/` - Pure UI (shadcn) components.
  - `components/features/` - Domain-specific components.
- `lib/` - Utilities, shared configs, and Zod schemas.
- `db/` - Database connection and definitions.
  - `db/schema.ts` - Drizzle schemas.
- `actions/` - Next.js Server Actions (all mutations).
- `types/` - Shared TypeScript interfaces.

## Architectural Patterns
### Component Strategy
- **Default to Server Components**: Everything in `app/` and `components/` is a Server Component unless interactive.
- **Isolate Client Components**: Push `'use client'` as far down the component tree as possible. Only use it when hooks (`useState`, `useEffect`) or browser events (`onClick`) are required.

### Data Fetching
- **Server Fetching**: Fetch data directly in Server Components using `async/await`.
- **NO `useEffect` Fetching**: Never fetch data inside Client Components unless implementing a real-time subscription or infinite scroll.

### Mutations
- **Server Actions Only**: Use `'use server'` inside the `actions/` directory. Do not use API routes (`app/api/`) for internal app logic. API routes are strictly for external webhooks.
- **Forms**: Use `react-hook-form` with `@hookform/resolvers/zod` in Client Components. Pass data to Server Actions upon validation.

## Database & Migrations
- **Schema is Truth**: `db/schema.ts` is the source of truth. Modify it first, then run `pnpm db:generate`.
- **Naming**: Use `snake_case` and plural names for tables (e.g., `user_profiles`).
- **Transactions**: For writes involving multiple tables, wrap them in `db.transaction()`. SQLite executes transactions sequentially, preventing race conditions.
- **Type Inference**: Avoid manual types for database models. Always use `typeof schema.users.$inferSelect` and `$inferInsert`.

## Naming Conventions
- **Files/Folders**: `kebab-case` (e.g., `auth-layout.tsx`, `date-utils.ts`).
- **React Components**: `PascalCase` (e.g., `SubscriptionCard`).
- **Functions/Variables**: `camelCase` (e.g., `fetchUserProfile`).
- **Server Actions**: Suffix with `Action` (e.g., `updateBillingAction`).

## Anti-Patterns (CRITICAL)
- ❌ **NEVER** write raw SQL. Always use the Drizzle query builder.
- ❌ **NEVER** use `any`. If a type is unknown, use `unknown` and validate it via Zod.
- ❌ **NEVER** export default components except in `app/` routing files (`page.tsx`, `layout.tsx`). Use named exports for standard components.
- ❌ **NEVER** skip error handling. All Server Actions must return a structured response indicating success or error (e.g., `{ success: false, error: string }`).