# Next.js 15 App Router + SQLite SaaS Context

## Stack & Versions
- Framework: Next.js 15 (App Router only)
- Database: SQLite (via `better-sqlite3` or Turso)
- ORM: Drizzle ORM
- Styling: Tailwind CSS
- Language: TypeScript 5.x

## Folder Structure
- `app/`: Next.js App Router. Pages (`page.tsx`), Layouts (`layout.tsx`), and API routes (`route.ts`).
- `components/`: UI Components. Categorized into `ui/` (primitives, e.g., shadcn/ui) and `feature/` (domain-specific).
- `db/`: Database configuration, schemas (`schema.ts`), and migrations (`migrations/`).
- `lib/`: Utility functions, helpers, and third-party integrations.
- `actions/`: Next.js Server Actions. Do not place business logic in API routes; use Server Actions whenever possible.

## Naming Conventions
- React Components: PascalCase (e.g., `Button.tsx`, `UserProfile.tsx`).
- Utility Files, Actions, and Hooks: camelCase (e.g., `useUser.ts`, `authActions.ts`).
- Database Tables: snake_case, plural (e.g., `users`, `user_subscriptions`).
- Folders in `app/`: kebab-case (e.g., `dashboard/user-settings`).

## SQL / Migration Conventions
- All schema definitions live in `db/schema.ts`.
- Run migrations using `drizzle-kit generate` and `drizzle-kit push`.
- Never manually edit migration files.
- Foreign keys must use `CASCADE` on delete where logical (e.g., deleting a user deletes their sessions).
- Prefer timestamps: `created_at` and `updated_at` (default to `sql\`CURRENT_TIMESTAMP\``) on all tables.

## Component Patterns
- Use Server Components by default.
- Add `'use client'` only at the top of components that require state (`useState`, `useReducer`), effects (`useEffect`), or browser APIs.
- Keep Client Components as leaf nodes in the component tree to minimize JavaScript shipped to the browser.
- Pass data to Client Components as props rather than fetching data inside them.

## Anti-Patterns: What we don't do (and why)
- **NO Pages Router (`pages/`)**: This is a pure App Router project. Do not mix paradigms.
- **NO Client-side data fetching for initial load**: Use React Server Components to fetch data directly from SQLite. It's faster and reduces client complexity.
- **NO API Routes for forms**: Use Server Actions (`use server`) with progressive enhancement for form submissions.
- **NO generic DB queries scattered**: Encapsulate complex database operations in dedicated repository functions in `db/queries.ts` to promote reusability and maintainability.

## Dev Commands
- Start dev server: `npm run dev`
- Generate migrations: `npm run db:generate`
- Push migrations: `npm run db:push`
- Build for production: `npm run build`
