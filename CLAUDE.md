# CLAUDE.md - Next.js 15 + SQLite SaaS Standard

## 🛠 Stack & Versions
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript 5+
- **Database**: SQLite via `better-sqlite3` (Local) or `libsql` (Turso)
- **Styling**: Tailwind CSS 4.0
- **State/Data**: Server Components (Primary), Server Actions (Mutations)
- **Validation**: Zod

## 📁 Project Structure
- `app/`: Route handlers, pages, and layouts.
- `components/`: UI components.
    - `ui/`: Low-level atomic components (shadcn style).
    - `features/`: Domain-specific components (e.g., `billing/`, `auth/`).
- `lib/`: Shared utilities and core logic.
    - `db/`: SQLite connection and schema definitions.
    - `utils/`: Generic helper functions.
- `hooks/`: Custom React hooks.
- `types/`: Global TypeScript definitions.
- `prisma/` or `drizzle/`: DB migrations (if using an ORM).

## 🗄 SQL & Migration Conventions
- **Migration Tool**: Drizzle ORM (recommended) or direct SQL scripts in `/migrations`.
- **Naming**: `snake_case` for table and column names.
- **Primary Keys**: Always use `id INTEGER PRIMARY KEY AUTOINCREMENT` or `id TEXT PRIMARY KEY` (UUID).
- **Timestamps**: Always include `created_at` and `updated_at` (default current timestamp).
- **Indices**: Add indices to foreign keys and frequently queried columns to prevent full table scans.
- **Transactions**: Use transactions for multi-step mutations to ensure atomicity.

## 🧩 Component Patterns
- **Server-First**: Use Server Components by default. Add `'use client'` only for interactivity.
- **Composition**: Pass data from Page $\rightarrow$ Server Component $\rightarrow$ Client Component.
- **Loading States**: Use `loading.tsx` and `Suspense` for granular loading UI.
- **Error Handling**: Use `error.tsx` for route-level error boundaries.
- **Form Submission**: Always use Server Actions for mutations. Validate input with Zod before processing.

## 🚫 Anti-Patterns (What we DON'T do)
- **No Client-Side Fetching**: Do not use `useEffect` or `SWR/React Query` for initial data loading; use Server Components.
- **No Direct DB Access in Client**: Never import `db` or SQL queries in `'use client'` files.
- **No Inline Styles**: Use Tailwind classes exclusively.
- **No `any` Types**: Use strict TypeScript. Define interfaces for all DB entities.
- **No Large Components**: Split components into smaller, reusable pieces if they exceed 150 lines.

## ⌨️ Dev Commands
- `npm run dev`: Start development server.
- `npm run build`: Build for production.
- `npm run db:migrate`: Run pending SQL migrations.
- `npm run db:seed`: Populate database with initial test data.
- `npm run lint`: Run ESLint and Prettier checks.
