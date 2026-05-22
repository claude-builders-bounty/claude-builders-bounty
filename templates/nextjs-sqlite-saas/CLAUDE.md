# Next.js + SQLite SaaS Project Guide

## Stack & Versions
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript 5+
- **Database**: SQLite (via `better-sqlite3` or Turso)
- **ORM/Query Builder**: Drizzle ORM (recommended for type safety and speed)
- **Styling**: Tailwind CSS
- **Auth**: NextAuth.js or Clerk

## Folder Structure
- `src/app/`: Routes and Layouts
- `src/components/`: Reusable UI components (Atomic design: atoms, molecules, organisms)
- `src/db/`: Database schema and client initialization
- `src/lib/`: Shared utility functions and constants
- `src/hooks/`: Custom React hooks
- `src/server/`: Server actions and server-only logic
- `drizzle/`: Database migrations

## SQL & Migration Conventions
- **Migrations**: Always use `drizzle-kit` for migrations. Never edit migrations manually.
- **Naming**: Use `snake_case` for table and column names in SQL. Use `camelCase` for TypeScript counterparts.
- **SQLite Limits**: Be mindful of SQLite's lack of native `enum` types (use `text` with `check` constraints or application-level validation).

## Component Patterns
- **Server Components**: Default to Server Components for data fetching.
- **Client Components**: Use `"use client"` only when interactive (hooks, event listeners).
- **Server Actions**: All mutations must go through Server Actions (`src/server/actions.ts`).

## Dev Commands
- `npm run dev`: Start development server
- `npm run db:generate`: Generate migrations from schema
- `npm run db:push`: Push changes directly to DB (local dev only)
- `npm run db:studio`: Visual explorer for SQLite

## Anti-Patterns (What we don't do)
- **No `useEffect` for Data Fetching**: Use Server Components or RSC for initial load.
- **No Inline Styles**: Use Tailwind classes for consistency and performance.
- **No Barrel Exports (`index.ts`)**: Avoid them in `src/components` to prevent circular dependencies and slow tree-shaking.
- **No Large Client Components**: Keep the client-side bundle small by splitting interactive parts into smaller components.

## SQLite Performance Tip
- Always enable WAL (Write-Ahead Logging) mode for `better-sqlite3`:
  ```js
  const db = new Database('sqlite.db');
  db.pragma('journal_mode = WAL');
  ```
