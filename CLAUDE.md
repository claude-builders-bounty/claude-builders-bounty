# Next.js 15 App Router + SQLite SaaS Template

## Tech Stack
- **Framework**: Next.js 15 (App Router, Server Actions)
- **Database**: SQLite (via `better-sqlite3` or Turso/libSQL)
- **ORM**: Prisma (or Drizzle, depending on setup)
- **Styling**: Tailwind CSS + Shadcn UI
- **Language**: TypeScript (Strict Mode)

## Project Structure
- `app/`: Next.js App Router routes and layouts only.
- `app/api/`: Edge functions and route handlers.
- `components/ui/`: Dumb, reusable visual components (e.g., Shadcn).
- `components/features/`: Smart, domain-specific components.
- `lib/db/`: Database connection singletons and query wrappers.
- `lib/actions/`: Next.js Server Actions (all server-side mutations go here).
- `prisma/`: Prisma schema and migrations (if using Prisma).

## Naming Conventions
- **Files**: `kebab-case` (e.g., `user-profile.tsx`, `auth-utils.ts`).
- **Components**: `PascalCase` (e.g., `<UserProfile />`).
- **Variables/Functions**: `camelCase`.
- **Server Actions**: Must end with `Action` (e.g., `updateProfileSettingsAction`).
- **DB Tables**: `snake_case`, plural (e.g., `users`, `user_subscriptions`).

## DB Migration Rules (SQLite specific)
- **Rule**: Do not use `ALTER COLUMN` (SQLite has limited support).
- **Rule**: Create a new table, copy data, drop the old table, and rename if structural changes are needed.
- **Prisma**: Run `npx prisma migrate dev` sequentially. Do not alter raw SQL dumps manually unless resolving conflicts.
- **WAL Mode**: Ensure Write-Ahead Logging (WAL) is enabled on connect for concurrent read/writes. `PRAGMA journal_mode=WAL;`

## Component Patterns
- **Server by Default**: All components in `app/` are Server Components.
- **Client Boundary**: Use `'use client'` strictly at the leaf nodes (e.g., buttons, form inputs, interactive charts) to minimize client bundle size.
- **Data Fetching**: Fetch data in Server Components and pass it down as props. Do not use `useEffect` or SWR/React Query unless fetching highly dynamic polling data.
- **Mutations**: Use Server Actions (`'use server'`) invoked via `<form action={...}>` or `useTransition`.

## Anti-Patterns (What we don't do)
- **No `useEffect` for data fetching**: Leads to waterfalls and poor UX. Use Server Components.
- **No inline raw SQL strings**: Vulnerable to injection. Always use the ORM or parameterized queries (e.g., `db.prepare('...').run()`).
- **No storing secrets in the codebase**: Always use `.env.local` for `DATABASE_URL`, API keys, etc.
- **No large Client Components**: Do not put `'use client'` at the top of a page layout. It breaks SSR benefits.

## Development Commands
- `npm run dev` - Start the local dev server.
- `npx prisma studio` - Open database UI (if using Prisma).
- `npm run build` - Create a production build.
- `npm run lint` - Run ESLint and Prettier.
