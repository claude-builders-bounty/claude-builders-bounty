# Next.js 15 + SQLite SaaS Project Guide (CLAUDE.md)

Opinionated developer conventions and rules for the codebase.

## 🛠 Tech Stack & Versions
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Database**: SQLite (via `better-sqlite3` or `libsql`/Turso)
- **Styling**: Tailwind CSS
- **ORM**: Drizzle ORM (recommended for type-safe SQLite access)

## 📁 Folder Structure
```text
├── src/
│   ├── app/                # Next.js App Router (pages, layouts, route handlers)
│   │   ├── api/            # API Route Handlers
│   │   └── (dashboard)/    # Dashboard layout and group
│   ├── components/         # Shared React components (UI components)
│   ├── db/                 # Database schema, client config, and migrations
│   │   ├── schema.ts       # Drizzle schema definitions
│   │   └── index.ts        # Database client initialization
│   ├── lib/                # Shared utilities, hooks, API wrappers
│   └── actions/            # Next.js Server Actions
```

## 🗄 SQL & Migration Conventions
- **Migrations**: Always generate migrations via `drizzle-kit generate` instead of writing raw SQL files manually.
- **Client Instance**: Export a single, cached database client instance. SQLite only supports a single writer; ensure database connections are reused to prevent "database is locked" errors.
- **WAL Mode**: Always run SQLite in Write-Ahead Logging (WAL) mode (`PRAGMA journal_mode = WAL;`) for concurrent read/write scaling.
- **Indexes**: Define explicit foreign key constraints and indexes on querying columns (e.g. `user_id` or `workspace_id`) in `schema.ts`.

## 🧩 Component Patterns
- **Server Components**: By default, all components are Server Components. Fetch data directly in Server Components using async functions.
- **Client Components**: Mark with `'use client'` ONLY when using browser APIs, React hooks (`useState`, `useEffect`), or interactive events.
- **Server Actions**: Group mutation functions under `src/actions/` and mark with `'use server'` at the top of the file. Use them for form submissions or interactive mutations.
- **Loading UI**: Use `loading.tsx` at the router level for page skeleton loads, and Suspense boundaries for granular component skeleton streams.

## 🚫 What We Don't Do (And Why)
- **No Client Fetching for Initial Data**: Do not use `useEffect` or client-side libraries (like `axios`) to fetch initial page state. This delays rendering and hurts SEO. Fetch in Server Components instead.
- **No Global State for UI**: Avoid global state managers (like Redux or Zustand) for UI toggle states. Use URL search params or React Context instead to keep components shareable and lightweight.
- **No Raw Database Queries in Client Components**: Never import the db client or call schema methods inside `'use client'` files. It will crash the compiler and leak credentials. Wrap queries in Server Actions or API Route Handlers.
- **No Parallel SQLite Writes**: Do not trigger multiple asynchronous writes in parallel without sequencing, to avoid SQLite lock contention.

## ⌨️ Common Dev Commands
- **Start Dev Server**: `npm run dev`
- **Build App**: `npm run build`
- **DB Push Schema**: `npx drizzle-kit push`
- **DB Generate Migration**: `npx drizzle-kit generate`
- **DB Run Migrations**: `npx drizzle-kit migrate`
- **Open DB Studio**: `npx drizzle-kit studio`

## ⚠️ Anti-patterns to Avoid
- **Unbounded Queries**: Never perform `db.select().from(table)` without a `.limit()` or pagination filter. Unbounded queries will degrade database and memory performance as tables grow.
- **Prop Drilling**: Do not drill props down more than 3 levels. Use React Context or composition patterns.
- **Mixing Concerns**: Do not place business/database logic inside UI rendering files. Keep queries in helper libraries or server actions.
