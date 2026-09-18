# Project Context & Coding Guidelines

You are assisting with a SaaS project built on Next.js 15 (App Router) and SQLite (Turso / better-sqlite3).
This document enforces opinionated standards to maintain a highly cohesive, secure, and performant codebase.

## Stack & Versions
- **Framework**: Next.js 15 (App Router exclusively)
- **Database**: SQLite (via Turso or `better-sqlite3` locally)
- **ORM / Query Builder**: Drizzle ORM
- **Styling**: Tailwind CSS v3
- **Language**: TypeScript (Strict mode enabled)
- **Package Manager**: pnpm

## Folder Structure
We follow a feature-driven colocation strategy within the `src/` directory.

```text
src/
├── app/                  # Next.js 15 App Router (Routes, Layouts, Pages only)
│   ├── (auth)/           # Route groups for logical separation
│   ├── api/              # Route handlers (REST endpoints, Webhooks)
│   └── globals.css       # Global styles (Tailwind imports)
├── components/           # Shared generic UI components (Buttons, Inputs, Modals)
├── features/             # Feature-based colocation (The core of the app)
│   └── [feature-name]/   # E.g., `workspaces/`, `billing/`
│       ├── components/   # Feature-specific components
│       ├── actions.ts    # Next.js Server Actions for this feature
│       ├── queries.ts    # Database read operations (Drizzle)
│       └── schema.ts     # Drizzle schema definitions for this feature
├── lib/                  # Utility functions, clients (db client, auth client)
└── db/                   # Global database config
    ├── migrations/       # SQL migration files
    └── index.ts          # DB connection initialization
```

## SQL & Migration Conventions (Drizzle + SQLite)
1. **Schema Definition**: Schemas are defined in `src/features/[feature]/schema.ts`. We DO NOT use a single massive `schema.ts` file. 
2. **Migrations**: 
   - Never write raw SQL migrations manually.
   - Run `pnpm db:generate` to generate Drizzle migrations.
   - Run `pnpm db:push` for local development to sync the schema directly.
3. **Data Fetching**:
   - Always colocate database read queries in `queries.ts` and mutations in `actions.ts`.
   - Prefer Drizzle's relational query API (`db.query.table.findMany`) for deep nested fetching to prevent N+1 issues.
4. **Primary Keys**: Use string-based CUIDs or UUIDv7 for all primary keys, NOT auto-incrementing integers. (Reason: prevents enumeration attacks and makes data merging easier).

## Component Patterns
1. **Server vs Client Components**:
   - Default to Server Components (`React Server Components`).
   - Use `"use client"` ONLY when absolutely necessary (e.g., hooks like `useState`, `useEffect`, or browser APIs).
   - Push client components down the tree as far as possible to maximize SSR/SSG caching.
2. **Data Fetching in Components**:
   - Fetch data directly in Server Components using async/await. 
   - Never use `useEffect` for data fetching. (Reason: Waterfall requests, layout shift).
3. **Forms & Mutations**:
   - Use Next.js 15 Server Actions (`"use server"`) exclusively for data mutations.
   - Always use `useActionState` (React 19) for managing form states and loading UI.

## What We Don't Do (Anti-Patterns)
- **No Pages Router**: Do not use the legacy `src/pages/` directory. Everything must be in `src/app/`.
- **No API Routes for internal mutations**: Do not build `/api/xxx` endpoints for your own forms. Use Server Actions instead. (API routes are only for external webhooks/public APIs).
- **No generic `types.ts`**: Do not create generic type files. Keep types co-located with the feature they belong to, or export them directly from the `schema.ts`.
- **No massive global state**: Avoid Redux or Zustand unless absolutely necessary. Rely on URL state (search params) and React Server Components for data passing.

## Dev Commands
- `pnpm dev`: Start the local Next.js development server.
- `pnpm db:generate`: Generate SQL migration files based on schema changes.
- `pnpm db:push`: Push schema changes directly to the local SQLite database.
- `pnpm db:studio`: Open Drizzle Studio to view the local database.
- `pnpm lint`: Run ESLint and Prettier checks.
