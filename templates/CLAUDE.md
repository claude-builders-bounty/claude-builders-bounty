# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Stack & Versions
- **Framework**: Next.js 15 (App Router)
- **Runtime**: Node.js 20+
- **Database**: SQLite (via `better-sqlite3` for local, `Turso` for production)
- **ORM**: Drizzle ORM (strongly recommended for SQLite)
- **Styling**: Tailwind CSS
- **Auth**: NextAuth.js or Clerk

## Build & Dev Commands
- `npm run dev`: Start development server
- `npm run build`: Build production application
- `npm run lint`: Run ESLint checks
- `npm run db:push`: Push schema changes to SQLite (Drizzle)
- `npm run db:studio`: Open Drizzle Studio for DB exploration

## Project Structure
- `app/`: Next.js App Router (Routes, Layouts, Server Actions)
- `components/`:
  - `ui/`: Base components (shadcn/ui pattern)
  - `features/`: Complex, domain-specific components
- `lib/`:
  - `db/`: Database client and schema definitions
  - `utils.ts`: General helper functions
- `public/`: Static assets
- `styles/`: Global CSS

## Coding Standards
- **Naming**: 
  - Components: `PascalCase.tsx`
  - Logic/Hooks: `camelCase.ts`
  - DB Tables: `snake_case`
- **TypeScript**: Strict mode enabled. No `any`. Use `zod` for runtime validation.
- **Server Components**: Default to Server Components. Use `'use client'` sparingly for interactivity only.
- **Data Fetching**: Use Server Components and direct DB calls. No `useEffect` for initial data.
- **State Management**: Prefer URL state (searchParams) or Server Actions + `useOptimistic`.

## SQL & Migration Conventions
- **Schema**: Define in `lib/db/schema.ts`.
- **Migrations**: Use Drizzle Kit for automated migration generation.
- **Local DB**: File stored at `db.sqlite` (gitignored).
- **Safety**: Always use parameterized queries (Drizzle handles this by default).

## Anti-Patterns (What we don't do)
- **No manual SQL strings**: Use the ORM's query builder to ensure type safety and prevent injection.
- **No client-side DB access**: All database logic must reside in Server Components or Server Actions.
- **No barrels (index.ts)**: Prefer direct imports to improve tree-shaking and avoid circular dependencies.
- **No `any`**: If a type is unknown, use `unknown` and a type guard.

## Component Patterns
- Use **Server Actions** for all mutations.
- **Form Handling**: Use `react-hook-form` with `@hookform/resolvers/zod` and `zod` for validation.
- **Icons**: Use `lucide-react` exclusively.
- **UI Components**: Use shadcn/ui (Radix UI primitives).
- Wrap complex components in `ErrorBoundary` and `Suspense` for better UX.
- Prefer **Tailwind** utility classes over CSS Modules or CSS-in-JS.
