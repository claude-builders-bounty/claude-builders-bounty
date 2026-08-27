# Next.js 15 + SQLite SaaS Template - CLAUDE.md

## Stack & Versions
- Next.js 15 (App Router only, React 19)
- Tailwind CSS 4 (via `@tailwindcss/postcss`)
- SQLite via `better-sqlite3` (local/production) or Turso (edge)
- Drizzle ORM (schema definitions, typed queries, migrations)
- NextAuth.js v5 (Authentication)

## Build, Test, and Run Commands
- `npm run dev` - Start the local development server (with turbopack).
- `npm run build` - Build for production. Never run without first generating DB migrations.
- `npm run db:push` - Rapidly prototype database schema without tracking migration history.
- `npm run db:generate` - Generate SQL migration files in `drizzle/` based on schema changes.
- `npm run db:migrate` - Apply generated migrations to the SQLite database.
- `npm run lint` - Run ESLint and Next.js strict linting.

## Folder Structure
- `/app` - Next.js App Router files. Strict colocation (components, hooks, tests live alongside the page/layout they belong to).
- `/app/(auth)` - Grouping for auth routes (sign-in, sign-up), keeping URL paths clean.
- `/app/api` - Only for webhooks or external API routes. Do not use for internal fetching (use Server Actions instead).
- `/lib/db` - Database instantiation, schema definitions (`schema.ts`), and Drizzle configuration.
- `/components/ui` - Generic, reusable UI components (e.g., shadcn/ui).
- `/drizzle` - Generated SQL migration files (tracked in git).

## SQL / Migration Conventions
- Use Drizzle ORM for all queries. Avoid raw SQL strings to maintain type safety and prevent SQL injection.
- Schema definitions must live in `lib/db/schema.ts` (or split into `lib/db/schema/*.ts` if it exceeds 300 lines).
- Database timestamps must use integer unix epochs or ISO strings, as SQLite does not have a native Date type. Drizzle handles this conversion if configured correctly.
- Always run `npm run db:generate` before committing changes to the schema.
- SQLite does not support dropping columns easily. Be prepared to create a new table, copy data, and rename it in migrations if necessary (though Drizzle handles most of this).

## Component Patterns
- Default to React Server Components (RSC). Only add `'use client'` at the absolute lowest level in the tree when state (`useState`), effects (`useEffect`), or browser APIs (like `window`) are strictly necessary.
- Fetch data directly in the Server Component. Pass data down as props.
- Use Next.js 15 Server Actions for all mutations (creating/updating/deleting data). Never build an API route for a form submission.
- Extract complex Server Actions into `lib/actions/` to keep Server Components clean.
- Type all components. Use standard `React.FC` or just typed functional components.

## What we don't do (and why)
- **Do not use `pages/` directory**: Next.js 15 App Router is the standard. Avoid mixing paradigms.
- **Do not use internal API routes for data fetching**: Fetch directly in Server Components or use Server Actions. Fetching your own API routes from Server Components creates unnecessary network overhead.
- **Do not use heavy client-side state management (Redux/Zustand)**: RSCs reduce the need for global client state. Rely on URL search params and server state instead.
- **Do not store secrets in the codebase**: Use `.env.local` for local secrets. Never prefix a secret with `NEXT_PUBLIC_` unless it strictly must be exposed to the browser.
- **Do not use raw `better-sqlite3` queries**: Always route through Drizzle to leverage TypeScript guarantees.
