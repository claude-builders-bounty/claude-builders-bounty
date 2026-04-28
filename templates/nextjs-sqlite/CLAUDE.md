# Next.js + SQLite SaaS Project Guidelines 💡

This project uses Next.js 15 (App Router), TypeScript, and SQLite (via `better-sqlite3`).

## Stack & Versions
- **Next.js**: 15.x (App Router only)
- **Database**: SQLite with `better-sqlite3`
- **ORM/Migrations**: Prisma or Drizzle (standardize on Drizzle for speed)
- **Styling**: Tailwind CSS
- **Auth**: NextAuth.js v5 or Clerk

## Folder Structure
- `src/app/`: File-based routing (App Router).
- `src/components/`: Reusable UI components. Use `src/components/ui/` for Shadcn components.
- `src/lib/`: Shared utilities and database client.
- `src/db/`: Schema definitions and migration files.
- `src/hooks/`: Custom React hooks.
- `public/`: Static assets.

## SQL & Migration Conventions
- Use `drizzle-kit` for migrations.
- **Naming**: Use `snake_case` for database tables and columns.
- **Rules**: 
    - Every table MUST have a `created_at` and `updated_at` timestamp.
    - Use UUIDs or CUIDs for primary keys (prevent ID enumeration).
    - Always define foreign key constraints explicitly.

## Dev Commands
- `npm run dev`: Start development server.
- `npm run build`: Build for production.
- `npm run db:push`: Push schema changes to SQLite (local dev).
- `npm run db:generate`: Generate migration files.

## Component Patterns
- Use **Server Components** by default. Only use `'use client'` when necessary (interactivity, hooks).
- **Data Fetching**: Fetch data directly in Server Components using `await db.select()...`.
- **Server Actions**: Use for all mutations (POST/PATCH/DELETE).

## What We Don't Do (and why)
- **No `any`**: TypeScript strict mode is enabled. Use proper interfaces.
- **No barrels**: Avoid `index.ts` files in folders (leads to circular dependencies).
- **No client-side state for DB**: Don't use `useState` to mirror database state; use `useOptimistic` or revalidate paths.
- **No fat components**: Keep components under 200 lines. Extract logic to hooks or smaller components.
