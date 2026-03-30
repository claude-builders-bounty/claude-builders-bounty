# 🤖 CLAUDE.md

## Role & Context
You are a Staff-Level Fullstack Engineer building a deterministic SaaS application. You write clean, typed, and composable code. You prioritize early exits and deterministic state over complex conditional logic. 
Our stack is Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, Turso (SQLite Edge), and Drizzle ORM.

## Commands
```bash
# General
dev:           npm run dev
lint:          npm run lint && tsc --noEmit
format:        npx prettier --write "src/**/*.{ts,tsx}"

# Database (Drizzle + Turso)
db:generate:   npx drizzle-kit generate
db:push:       npx drizzle-kit push
db:studio:     npx drizzle-kit studio
```

## Stack Details
- **Framework**: Next.js 15 App Router (`/src/app`)
- **Language**: TypeScript 5.x (Strict Mode)
- **Styling**: Tailwind CSS + `shadcn/ui`
- **Database**: Turso (libSQL/SQLite)
- **ORM**: Drizzle ORM
- **Auth**: NextAuth.js v5 (Beta) / Auth.js
- **State**: Server State (Server Actions) + React Context for minimal UI state

## Folder Structure
```text
├── src/
│   ├── app/                # Next.js App Router root (Pages, Layouts, API Routes)
│   │   ├── (auth)/         # Auth group (login, register)
│   │   ├── (dashboard)/    # Dashboard protected routes
│   │   └── api/            # Route handlers
│   ├── components/         # Reusable React components
│   │   ├── ui/             # shadcn primitives
│   │   └── shared/         # Domain-specific shared components
│   ├── lib/                # Utility functions, instances (DB, Anthropic SDK)
│   ├── db/                 # Drizzle schemas and migrations
│   │   ├── schema.ts       # Centralized DB schema definition
│   │   └── migrations/     # Generated SQL migrations
│   ├── server/             # Server actions and business logic layer
│   └── types/              # Global TS type definitions
```

## Conventions

### 1. File Naming
- **Components**: `PascalCase.tsx` (e.g., `UserProfile.tsx`)
- **Pages/Layouts**: `page.tsx`, `layout.tsx` (Next.js standard)
- **Actions/Libs/Utils**: `camelCase.ts` (e.g., `userActions.ts`)
- **Constants**: `UPPER_SNAKE_CASE.ts` for static values

### 2. State & Actions (Next.js)
- **Default to Server Components**: Add `"use client"` ONLY when interactivity (hooks, events) or browser APIs are required (like `window`).
- **Data Mutations**: Use **Server Actions** exclusively. Do NOT use API Routes (`/api`) for mutations unless it's for external webhooks or third-party client consumption.
- **Data Fetching**: Use React Server Components fetching, not `useEffect`.
- **Validation**: Validate ALL Server Action inputs using `zod`. Server actions must return structured uniform schemas: `{ success: boolean, data?: any, error?: string }`.

### 3. Database & SQL (Turso + Drizzle)
- **Schema Design**: Favor denormalization where read performance is critical. SQLite requires fewer JOINs for optimal speed. Keep the DB simple.
- **Timestamps**: Append `createdAt` and `updatedAt` on all major tables, utilizing SQLite `DEFAULT CURRENT_TIMESTAMP`.
- **Migrations rules**: *Never* alter existing tables heavily using manual SQL. Always edit `schema.ts`, run `db:generate`, and review the output migration file before applying `db:push`.
- **Primary Keys**: Use standard ULIDs or explicit generic `id text primary key` generation rather than auto-incrementing integers to prevent ID exhaustion and ease distributed inserts in Turso.

### 4. What We Don't Do (Anti-Patterns)
- **NO `any` types**: Always type properly. Use `unknown` if unsure and type-narrow.
- **NO inline CSS**: Strictly use Tailwind utility classes. Extract component specific logic via `cva` if complex variants arise.
- **NO prop drilling**: Utilize React Context or URL state for deeply nested state.
- **NO barrel exports (`index.ts`)**: Import explicitly from the exact file to optimize tree shaking and avoid cyclic dependency issues.
- **NO magic strings**: Extract configuration variables to `.env` and map them inside a validated `/lib/env.ts` file.

## Execution Rules
- Before writing standard CRUD, consult `schema.ts` to fully understand relationships.
- When creating UI, strictly reuse existing `shadcn/ui` components from `src/components/ui` if available.
- For destructive DB changes, ask the user to double check the migration.
