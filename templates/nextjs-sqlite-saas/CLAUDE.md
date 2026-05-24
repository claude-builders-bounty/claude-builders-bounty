# Claude Code Instructions for Next.js 15 + SQLite SaaS

This project is a Next.js 15 SaaS boilerplate using the App Router, React 19, and `better-sqlite3`.

## Architecture & Conventions

### Stack Constraints
- Next.js 15 App Router (`app/` directory). DO NOT use `pages/`.
- React 19 Server Components by default.
- `better-sqlite3` for local synchronous DB queries. No heavy ORMs (no Prisma, no Drizzle). Raw SQL only.
- Tailwind CSS v4 for styling.

### Server vs. Client Components
- Everything is a Server Component unless it absolutely requires state, effects (`useEffect`), or browser APIs.
- Prefix Client Components with `"use client";` at the very top.
- Data fetching must happen on the Server. Pass primitive props down to Client Components.
- DO NOT pass entire database objects to the client. Pick only the fields needed.

### Database & Migrations
- The DB lives at `db/local.sqlite3`.
- Migrations live in `db/migrations/` as sequenced `.sql` files (e.g., `0001_initial.sql`).
- When modifying the schema:
  1. Create a new file in `db/migrations/` with the current timestamp prefix.
  2. Write explicit `CREATE TABLE` / `ALTER TABLE` raw SQL.
  3. Update `db/schema.sql` to reflect the final state.
- Keep queries simple. Use prepared statements via `better-sqlite3`'s `.prepare()`.
- Use the standard `db/index.ts` exported singleton for querying.

### Routing & API
- Use Next.js Server Actions (`"use server";`) inside `app/actions/` for data mutations instead of traditional API routes (`route.ts`).
- Only use API routes (`app/api/.../route.ts`) if providing a public REST API or webhooks.

## Development Commands
- `npm run dev` - Starts the Next.js development server.
- `npm run build` - Builds for production.
- `npm run db:migrate` - Applies pending SQL migrations from `db/migrations/`.
- `npm run db:seed` - Populates the database with initial dummy data.

## Anti-Patterns (NEVER DO THESE)
- Do not use `localStorage` for critical app state (use cookies or DB).
- Do not leak secrets to the client. Avoid defining `NEXT_PUBLIC_` unless necessary.
- Do not write massive "God Components". Keep components small and focused.
- Do not use nested callbacks for async tasks; use modern `async/await`.
