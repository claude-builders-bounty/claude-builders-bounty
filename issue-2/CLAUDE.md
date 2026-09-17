# CLAUDE.md

## Stack & Versions
- **Framework:** Next.js 15 (App Router only)
- **Database:** SQLite (via Turso or `better-sqlite3`) with Drizzle ORM
- **Styling:** Tailwind CSS + Shadcn UI
- **Package Manager:** `pnpm` (strictly enforced)

## Folder Structure
- `app/`: Next.js 15 App Router pages, layouts, and API routes (`route.ts`).
  - Colocate components tightly: if a component is only used in `/app/dashboard`, it belongs in `/app/dashboard/_components/`.
- `components/ui/`: Generic, reusable Shadcn UI components (do not modify these directly unless global styling changes are needed).
- `lib/db/`: Database configuration, Drizzle schema (`schema.ts`), and queries.
- `lib/utils/`: Pure helper functions.
- `types/`: Global TypeScript interfaces and types.

## Development Commands
- **Run dev server:** `pnpm dev`
- **Generate migrations:** `pnpm db:generate`
- **Push schema to DB:** `pnpm db:push`
- **Lint code:** `pnpm lint`

## SQL & Migration Conventions
- Use **Drizzle ORM** for all database interactions.
- Never write raw SQL strings unless absolutely necessary for complex SQLite aggregations.
- Store schema definitions in `lib/db/schema.ts`. Use table names in plural and snake_case (e.g., `user_profiles`).
- For boolean flags in SQLite, use integer columns mapping to `0` and `1`.

## Component Patterns
- **Server Components by Default:** Keep components as React Server Components (RSC). Only add `"use client"` when state (`useState`), effects (`useEffect`), or browser APIs are required.
- **Data Fetching:** Fetch data directly in Server Components using async/await. Do NOT use `useEffect` or `SWR`/`React Query` unless doing complex client-side polling.
- **Server Actions:** Place server actions inside a `_actions.ts` file next to the feature. Always wrap database mutations in a `try/catch`.

## What We DON'T Do (Anti-patterns)
- **NO `pages/` directory:** We use App Router exclusively. Do not generate `pages/api` routes.
- **NO Client-side Data Fetching by default:** Avoid fetching from `/api` routes on the client when it can be done in RSC or Server Actions.
- **NO generic `components/` dumping:** Do not place feature-specific components in the root `components/` folder. Use colocated `_components` folders within the relevant route.
- **NO `npm` or `yarn`:** Always use `pnpm` to avoid lockfile conflicts.
