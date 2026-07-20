# Next.js + SQLite SaaS Architecture

You are building a production-grade SaaS application using Next.js 15 App Router and SQLite (better-sqlite3 / Turso). 

## 🏗 Stack & Versions
- **Framework:** Next.js 15 (App Router only, no `pages/` directory)
- **Database:** SQLite (local via `better-sqlite3`, prod via Turso if applicable)
- **ORM/Query Builder:** Drizzle ORM (preferred) or Kysely. NEVER use Prisma due to edge/serverless cold start overhead.
- **Styling:** Tailwind CSS + Shadcn UI (Zinc dark mode default)
- **Auth:** NextAuth (Auth.js v5) or Supabase Auth

## 📁 Folder Structure
```text
├── src/
│   ├── app/              # Next.js App Router pages, layouts, and API routes
│   │   ├── (auth)/       # Auth-related routes (login, register)
│   │   ├── (dashboard)/  # Authenticated dashboard routes
│   │   └── api/          # Route handlers (REST endpoints)
│   ├── components/       # UI components
│   │   ├── ui/           # Shadcn UI primitives (dumb components)
│   │   └── shared/       # Shared composite components
│   ├── lib/              # Utility functions, helpers
│   ├── db/               # Database config, schemas, and migrations
│   │   ├── schema.ts     # Main database schema definition
│   │   └── index.ts      # DB connection client
│   └── actions/          # Next.js Server Actions (all mutations go here)
├── .env                  # Environment variables
└── package.json
```

## 💾 SQL / Database Conventions
- **Migrations:** Always generate and run migrations manually via `npm run db:generate` and `npm run db:push`. Do NOT auto-migrate on start.
- **Naming:** 
  - Tables: Plural, lowercase, snake_case (e.g., `users`, `subscriptions`).
  - Columns: snake_case (e.g., `created_at`, `stripe_customer_id`).
- **Dates/Times:** Always store timestamps as integers (Unix epoch) or ISO 8601 strings. SQLite lacks a native DATETIME type. 
- **Booleans:** Store as integers (0 or 1). Drizzle handles the mapping, but be aware at the raw SQL level.

## 🧱 Component Patterns
- **Server vs Client Components:** 
  - Default to Server Components (`async function MyComponent`).
  - Use Client Components (`"use client"`) ONLY for interactivity (hooks, state, event listeners).
  - Push the `"use client"` directive as far down the tree as possible to keep the tree mostly server-rendered.
- **Data Fetching:** Fetch data directly in Server Components using async/await. Do NOT use `useEffect` for data fetching unless absolutely necessary for client-side pagination.
- **Mutations:** Use Next.js Server Actions for forms and data mutations. Wrap server actions in a `try/catch` and return `{ error?: string, success?: boolean, data?: any }`.

## 🚫 What We Don't Do (And Why)
- **NO Client-side Secret Access:** Never prefix environment variables with `NEXT_PUBLIC_` unless they are explicitly meant for the browser (like an analytics key).
- **NO Prop Drilling:** If you are passing props more than 2 levels deep, use React Context or URL search parameters instead. URL state is preferred for things like search queries or active tabs.
- **NO Default Exports for Components:** Use named exports for everything except Next.js special files (`page.tsx`, `layout.tsx`, etc.). This makes refactoring easier.
- **NO `any` types:** Always define interfaces or types for your data.

## 🚀 Common Commands
- **Dev Server:** `npm run dev`
- **DB Generate:** `npm run db:generate`
- **DB Push:** `npm run db:push`
- **DB Studio:** `npm run db:studio` (Drizzle Studio)
