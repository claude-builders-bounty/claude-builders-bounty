# Next.js 15 App Router + SQLite Project Guidelines

## Core Stack
- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript (Strict Mode)
- **Database:** SQLite (better-sqlite3)
- **ORM:** Drizzle ORM
- **Styling:** Tailwind CSS + shadcn/ui

## Project Structure
```text
├── app/
│   ├── (auth)/        # Route group for authentication pages
│   ├── api/           # Next.js Route Handlers
│   ├── layout.tsx     # Root layout
│   └── page.tsx       # Landing page
├── components/
│   ├── ui/            # Generic/reusable shadcn UI components
│   └── feature/       # Domain-specific components
├── db/
│   ├── schema.ts      # Drizzle schema definitions
│   ├── index.ts       # Database client initialization
│   └── migrations/    # Generated SQL migration files
├── lib/
│   ├── utils.ts       # Helper functions
│   └── actions.ts     # React Server Actions
└── types/             # Shared TypeScript types
```

## Component Patterns
- **Server Components by Default:** Assume every component in `app/` is a React Server Component (RSC). Only add `"use client"` when state, context, or browser APIs (like `window`, `useEffect`) are strictly necessary.
- **Client Component Leaf Nodes:** Push `"use client"` as far down the component tree as possible to minimize the client-side JavaScript bundle.
- **Data Fetching:** Fetch data directly in Server Components using async/await. Avoid `useEffect` for data fetching.

## Database & SQLite Conventions
- **Client Configuration:** We use `better-sqlite3` for local performance or `libsql` if connecting to a Turso edge database.
- **Schema:** All schema definitions live in `db/schema.ts`. Use explicit types for timestamps (e.g., `integer('created_at', { mode: 'timestamp' })`).
- **Migrations:** Never modify the database schema directly. Always update `db/schema.ts` and generate a migration using `npx drizzle-kit generate:sqlite`. Apply them via `drizzle-kit push:sqlite`.
- **Query Patterns:** Prefer Drizzle's relational query API (`db.query...`) for deep relationships, and raw SQL builder (`eq()`, `and()`) for high-performance tight loops.

## State Management & Mutations
- **React Server Actions:** Use Server Actions in `lib/actions.ts` for form submissions and database mutations.
- **Validation:** Always validate incoming Action payloads using **Zod**. Never trust client input.
- **Revalidation:** After a successful Server Action mutation, call `revalidatePath()` or `revalidateTag()` to update the UI without full page reloads.

## What We Don't Do (Anti-Patterns)
- ❌ **No traditional API Routes (unless needed by webhooks):** Do not create `app/api/...` routes just for internal app data fetching. Use Server Actions or direct Server Component DB queries.
- ❌ **No Heavy Client State:** Avoid Redux or Zustand. Rely on URL query parameters for shareable state, and standard React hooks (`useState`) for local ephemeral UI state.
- ❌ **No Vercel Postgres / external DBs:** This project is explicitly designed for local SQLite or Edge SQLite (Turso) for minimal latency. Do not propose PostgreSQL or MySQL setups.

## Available Scripts
- `npm run dev`: Starts the Next.js development server.
- `npm run db:generate`: Generates SQL migrations from `schema.ts`.
- `npm run db:push`: Applies pending migrations to the local SQLite database.
- `npm run db:studio`: Opens Drizzle Studio to inspect the database.
