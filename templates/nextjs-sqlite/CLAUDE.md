# Next.js 15 + SQLite SaaS Project - Claude Guidelines

You are an expert AI assistant working on a Next.js 15 (App Router) SaaS project using SQLite (via Turso or better-sqlite3) and Drizzle ORM. Follow these opinionated guidelines to ensure a production-ready, maintainable, and secure codebase.

## 1. Stack & Versions
- **Framework:** Next.js 15 (App Router exclusively). Never use the `pages` directory.
- **Language:** TypeScript (Strict mode enabled).
- **Database:** SQLite (Turso for edge-ready production, better-sqlite3 for local dev).
- **ORM:** Drizzle ORM.
- **Styling:** Tailwind CSS with Shadcn UI.
- **Authentication:** NextAuth.js (v5) or Lucia Auth (v3).

## 2. Folder Structure & Architecture
We use a feature-sliced architecture inside the `src` directory to keep domains isolated.

```text
src/
├── app/               # Next.js App Router (routing, pages, layouts only)
│   ├── (auth)/        # Route groups for logical separation
│   ├── api/           # Route handlers (REST/Webhooks)
│   └── globals.css    # Global Tailwind styles
├── components/        # Shared UI components
│   ├── ui/            # Shadcn UI primitives (buttons, inputs, etc.)
│   └── layouts/       # Reusable layout wrappers
├── db/                # Database layer
│   ├── schema.ts      # Drizzle schema definitions
│   ├── index.ts       # Database client initialization
│   └── migrations/    # Generated SQL migrations
├── features/          # Domain-driven feature modules (e.g., users, billing, workspaces)
│   └── [domain]/
│       ├── actions.ts # Next.js Server Actions
│       ├── queries.ts # Database read operations (Drizzle queries)
│       ├── components/# Domain-specific React components
│       └── types.ts   # Zod schemas and TypeScript interfaces
└── lib/               # Shared utilities (formatters, constants, external API clients)
```

**Reasoning:** Keeping Server Actions and DB queries inside `src/features/[domain]` prevents the `app` directory from becoming a bloated mess of business logic.

## 3. Component Patterns
- **Server Components by Default:** All components in `app/` and `features/` must be Server Components unless they require interactivity (`useState`, `useEffect`, `onClick`).
- **Use `"use client"` at the Leaves:** Push client boundaries as far down the component tree as possible.
- **Data Fetching:** Fetch data directly in Server Components using async/await. Do NOT use `useEffect` or `useQuery` for initial data fetching.
- **Suspense & Streaming:** Wrap slow data-fetching components in `<Suspense fallback={<Skeleton />}>` to unblock the initial render.

## 4. SQL / Database Migration Conventions
- **Single Source of Truth:** `src/db/schema.ts` is the single source of truth for the database schema.
- **Naming Conventions:**
  - Table names: Plural, snake_case (e.g., `users`, `stripe_customers`).
  - Column names: snake_case (e.g., `created_at`, `stripe_customer_id`).
  - Boolean columns: Prefix with `is_` or `has_` (e.g., `is_active`, `has_pro_plan`).
- **Timestamps:** Every table must have `created_at` (default `sql\`CURRENT_TIMESTAMP\``) and `updated_at` columns.
- **Migrations:**
  - Never write raw `ALTER TABLE` scripts manually.
  - Run `npm run db:generate` to generate Drizzle migrations.
  - Run `npm run db:push` to apply them to the local SQLite database.

## 5. Server Actions & Mutations
- **Location:** Place Server Actions in `src/features/[domain]/actions.ts`.
- **"use server" directive:** Always place `"use server"` at the very top of the `actions.ts` file, not inside individual functions.
- **Validation:** Always validate input using Zod before interacting with the database.
- **Error Handling:** Return a standardized object from Server Actions: `{ success: boolean; data?: any; error?: string }`. Never throw raw errors to the client.
- **Revalidation:** Use `revalidatePath` or `revalidateTag` after a successful mutation to update the UI.

## 6. What We Don't Do (Anti-Patterns)
- **NO `pages/` directory:** This is a Next.js 15 App Router project. Do not mix paradigms.
- **NO Prisma:** We use Drizzle ORM. Prisma's Rust engine overhead is unnecessary for a lightweight SQLite/Turso stack.
- **NO Client-Side DB Calls:** Never import `src/db/index.ts` in a file marked with `"use client"`.
- **NO Raw SQL Queries:** Always use Drizzle's query builder or relational queries. Raw SQL is only acceptable for complex aggregations where Drizzle falls short.
- **NO Default Exports:** Use named exports for everything except Next.js special files (`page.tsx`, `layout.tsx`, `route.ts`). This ensures better refactoring and intellisense.

## 7. Common Dev Commands
When I ask you to run commands, use these:
- `npm run dev` - Start the local dev server.
- `npm run db:generate` - Generate Drizzle migrations after schema changes.
- `npm run db:push` - Apply schema changes to the local SQLite database.
- `npm run db:studio` - Open Drizzle Studio to inspect the database.
- `npm run build` - Build the Next.js app for production.

---
**Claude:** Acknowledge you have read and understood these rules by strictly adhering to them in all subsequent code generation and refactoring tasks. Do not ask for clarification on the stack; assume Next.js 15 App Router + SQLite + Drizzle.
