# Claude Code Guidelines: Next.js 15 App Router + SQLite SaaS

This document defines the strict architectural constraints, conventions, and rules for this project. 
As an AI coding assistant, you **must** adhere to these guidelines to ensure consistency, performance, and security across the codebase.

## 🏗 Stack & Versions
- **Framework**: Next.js 15 (App Router **only** - no `pages/` directory).
- **Database**: SQLite (via `better-sqlite3` for local/Docker, or Turso/libsql for edge deployment).
- **ORM**: Drizzle ORM (Prisma is banned due to cold start overhead and binary size).
- **Styling**: Tailwind CSS + Shadcn UI (Radix primitives).
- **Language**: TypeScript (Strict mode enabled).

## 📁 Folder Structure (Strict)
Do not deviate from this directory structure. It separates domain logic from UI routing.

```
src/
├── app/                  # Next.js App Router (Routing, Layouts, Server Actions)
│   ├── (auth)/           # Grouped routes (e.g., login, register)
│   ├── api/              # Route handlers (keep to a minimum, prefer Server Actions)
│   └── globals.css       # Tailwind base
├── components/           # UI Components
│   ├── ui/               # Generic Shadcn/dumb components (Buttons, Inputs)
│   └── shared/           # Domain-aware shared components (e.g., UserAvatar)
├── db/                   # Database Layer
│   ├── schema.ts         # Drizzle Schema (Source of truth)
│   └── index.ts          # DB Connection initialization
├── lib/                  # Utilities and pure functions
│   └── utils.ts          # Tailwind merge utilities etc.
└── actions/              # Server Actions (Business logic mutations)
```

## 📜 Coding Conventions & Patterns

### 1. Component Patterns
- **React Server Components (RSC) by default**: All components are server components unless they require state (`useState`), effects (`useEffect`), or event listeners (`onClick`).
- **Targeted `'use client'`**: When interactivity is needed, push the `'use client'` directive as far down the component tree as possible. Never put `'use client'` on a page layout or top-level wrapper if it can be avoided.
- **Data Fetching**: Fetch data directly in Server Components using async/await. Do NOT use `useEffect` for data fetching.

### 2. State & Mutations (Server Actions)
- **Use Server Actions for all mutations**. Do not create `/api` route handlers for forms or internal app mutations.
- **Action Pattern**: Place Server Actions in `src/actions/`. Every action must:
  1. Validate input using `zod`.
  2. Check authentication/authorization before proceeding.
  3. Return a standard response object: `{ success: boolean; data?: any; error?: string }`.
  4. Call `revalidatePath()` or `revalidateTag()` before returning if cache needs invalidation.

### 3. Database & Drizzle Schema
- **File**: `src/db/schema.ts` is the single source of truth.
- **Naming Constraints**:
  - Tables: snake_case and plural (e.g., `users`, `subscriptions`).
  - Columns: snake_case (e.g., `stripe_customer_id`).
  - Boolean columns: prefix with `is_` or `has_` (e.g., `is_active`).
- **Timestamps**: All tables must include `created_at` (default `now()`) and `updated_at`.

## 🚫 Anti-Patterns (Do NOT do these)

1. **Do not use Prisma**: We are explicitly using Drizzle ORM for better edge compatibility and performance with SQLite/Turso.
2. **Do not mix Server and Client logic**: Never pass sensitive data (like password hashes or internal IDs) to Client Components.
3. **Do not use `useEffect` for data loading**: React Query or standard fetch inside `useEffect` is banned for initial data. Use RSCs.
4. **Do not use `console.log` for business logic errors**: Use a structured logging approach or return explicit `{ error: string }` from actions.
5. **Do not write inline raw SQL**: Always use the Drizzle query builder. Raw SQL (`sql\`...\``) should only be used for complex aggregations or specific SQLite functions that Drizzle doesn't cover natively.

## 🛠 Commands

When asked to run tasks, use these standard commands:

- **Run dev server**: `npm run dev`
- **Build**: `npm run build`
- **Database Migrations**: 
  - Generate: `npx drizzle-kit generate`
  - Apply (Push): `npx drizzle-kit push`
  - Studio UI: `npx drizzle-kit studio`
- **Add a Shadcn UI component**: `npx shadcn@latest add <component-name>`

Always verify TypeScript compilation (`npx tsc --noEmit`) before declaring a refactoring complete.
