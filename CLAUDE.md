# Claude Code Guide: Next.js 15 + SQLite SaaS

This is an opinionated guide for building our SaaS product. We use **Next.js 15 (App Router)** and **SQLite (better-sqlite3 / Turso)**. Follow these conventions strictly to maintain a clean, scalable, and maintainable codebase.

## 🛠 Stack & Versions

- **Framework:** Next.js 15 (App Router only)
- **Database:** SQLite (Turso for edge/production, `better-sqlite3` for local dev)
- **ORM:** Drizzle ORM (Type-safe, fast, and aligns well with SQLite)
- **Styling:** Tailwind CSS + Shadcn UI
- **Authentication:** NextAuth.js (v5 / Auth.js)
- **Language:** TypeScript (Strict mode enabled)

## 📁 Folder Structure

We follow a feature-driven folder structure inside the `src/` directory.

```text
src/
├── app/                  # Next.js App Router (Pages, Layouts, API Routes)
│   ├── (auth)/           # Route groups for auth pages
│   ├── (dashboard)/      # Route groups for app dashboard
│   ├── api/              # Route handlers (RESTful endpoints if needed)
│   └── layout.tsx        # Global layout
├── components/           # Shared UI components
│   ├── ui/               # Shadcn components (dumb components)
│   └── forms/            # Complex client-side form components
├── db/                   # Database configuration and schemas
│   ├── schema/           # Drizzle schema files (split by domain, e.g., users.ts)
│   ├── migrations/       # Generated SQL migrations
│   └── index.ts          # DB connection instance
├── features/             # Domain-specific logic (Feature sliced)
│   ├── billing/          # Billing domain (actions, queries, types)
│   └── projects/         # Projects domain
├── lib/                  # Generic utilities and helpers (e.g., utils.ts)
└── types/                # Global TypeScript definitions
```

*Reasoning:* Splitting logic into `features/` prevents the `app/` directory from becoming a tangled mess of UI and business logic. The `app/` directory should only handle routing and composing features.

## 💾 SQL / Migration Conventions

We use **Drizzle ORM** for schema definition and migrations.

### Schema Definition
- **File splitting:** Define schemas per domain in `src/db/schema/` (e.g., `users.ts`, `workspaces.ts`). Do not put everything in one massive `schema.ts`.
- **Naming conventions:** 
  - Table names must be **plural, snake_case** (e.g., `users`, `workspace_members`).
  - Column names must be **snake_case** (e.g., `created_at`, `stripe_customer_id`).
- **Timestamps:** Every table must have `created_at` (default to `sql\`CURRENT_TIMESTAMP\``) and `updated_at`.

### Migrations
- **Generation:** Always generate migrations via Drizzle Kit: `npm run db:generate`.
- **Execution:** Do not run migrations automatically in the Next.js runtime. Use a separate script (`npm run db:migrate`) as part of the deployment pipeline.
- **Rules:** Never edit generated migration files manually. If a mistake is made and the migration hasn't been pushed, delete the file and regenerate. If it has been pushed, create a new migration to fix it.

## 🧩 Component Patterns

### Server vs Client Components
- **Default to Server Components (RSC).** Only add `'use client'` when absolutely necessary (e.g., `useState`, `useEffect`, event listeners like `onClick`).
- **Data Fetching:** Fetch data directly in Server Components using Drizzle queries. Pass data as props to Client Components.
- **Server Actions:** Use Server Actions for all mutations. Define them in a separate file (e.g., `actions.ts`) next to the feature, and annotate the file or function with `'use server'`.

### Component Props
- Export the Props interface for every component.
- Name it `[ComponentName]Props` (e.g., `interface ButtonProps`).

### State Management
- Prefer URL Search Parameters (`?query=foo`) for state that needs to be shareable or survives page reloads (e.g., pagination, filtering, tabs). Use `nuqs` if complex parsing is needed.
- Use React Context only for global UI state (e.g., Theme, Sidebar toggle).

## 🚫 What We Don't Do (Anti-Patterns)

1. **No Pages Router (`src/pages`).**
   - *Why:* We are fully committed to the App Router paradigm. Mixing them creates confusion and bloats the bundle.
2. **No direct database queries in Client Components or Route Handlers (unless acting as a public API).**
   - *Why:* Use Server Components for reading data and Server Actions for mutating data. Route handlers (`app/api/...`) should be reserved for webhooks or external API consumers.
3. **No `any` types.**
   - *Why:* Type safety is non-negotiable. Use `unknown` if the type is truly dynamic, and narrow it down using type guards.
4. **No large Client Components.**
   - *Why:* Pushing too much JS to the client hurts performance. Push logic down the tree and keep Client Components at the leaves. Pass Server Components as `children` to Client Components if they need to wrap server-rendered content.
5. **No raw SQL queries (unless strictly necessary).**
   - *Why:* Drizzle provides a powerful query builder. Raw SQL bypasses type safety. If you must use raw SQL, document clearly why Drizzle couldn't handle it.

## 🚀 Dev Commands

- `npm run dev`: Start local development server.
- `npm run db:generate`: Generate SQL migrations based on schema changes.
- `npm run db:migrate`: Apply pending migrations to the SQLite database.
- `npm run db:studio`: Open Drizzle Studio to inspect the local database.
- `npm run build`: Create a production build (runs TS typecheck automatically).