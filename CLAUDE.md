# CLAUDE.md - Next.js 15 + SQLite SaaS Template

## Tech Stack
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Database**: SQLite (via Drizzle ORM & `better-sqlite3` or Turso)
- **Styling**: Tailwind CSS + Shadcn UI
- **Validation**: Zod
- **Icons**: Lucide React

## Project Structure
```text
├── app/                # App Router (routes, layouts, loading, error)
├── actions/            # Server Actions (mutations)
├── components/         # React components
│   ├── ui/             # Shadcn UI components (atomic)
│   └── shared/         # Reusable business components
├── db/                 # Database layer
│   ├── schema/         # Drizzle schema definitions
│   └── migrations/     # SQL migration files
├── hooks/              # Custom React hooks
├── lib/                # Shared utilities (db client, utils, etc.)
├── services/           # Business logic (reusable across actions/API)
├── types/              # Global TypeScript types
└── public/             # Static assets
```

## Development Commands
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
- `npm run db:generate` - Generate Drizzle migrations from schema
- `npm run db:migrate` - Apply migrations to local SQLite
- `npm run db:studio` - Open Drizzle Studio (DB GUI)

## Database & Migrations
- **ORM**: Drizzle ORM is the source of truth.
- **Schema**: Define all tables in `db/schema/*.ts`.
- **Migrations**:
  1. Modify schema files.
  2. Run `npm run db:generate`.
  3. Run `npm run db:migrate`.
- **Rule**: Never modify the `.sqlite` file directly. Always use migrations to ensure environment parity.
- **Transactions**: Use Drizzle transactions for multi-step writes to ensure atomicity.

## Coding Patterns

### 1. Server Components vs Client Components
- **Default**: Use Server Components for data fetching and SEO.
- **Client**: Use `'use client'` only for interactivity (onClick, useState, useEffect) or browser APIs.
- **Pattern**: Keep Client Components at the leaves of the component tree to minimize JS bundle size.

### 2. Data Fetching & Mutations
- **Fetching**: Fetch data directly in Server Components using `await db.select()...`.
- **Mutations**: Use **Server Actions** in the `actions/` directory.
- **Validation**: Always validate input in Server Actions using **Zod**.
- **Revalidation**: Use `revalidatePath` or `revalidateTag` after successful mutations.

### 3. Component Architecture
- **Shadcn UI**: Use components in `components/ui/`. Do not modify them directly; wrap them if customization is needed.
- **Logic Separation**: Keep business logic in `services/`. Server Actions should call services. This makes logic testable and reusable.

### 4. Naming Conventions
- **Files**: `kebab-case` for all files (e.g., `user-profile.tsx`).
- **Components**: `PascalCase` (e.g., `UserProfile.tsx`).
- **Functions/Variables**: `camelCase`.
- **Types/Interfaces**: `PascalCase`.

## Anti-Patterns (What NOT to do)
- ❌ **No `useEffect` for data fetching**: Use Server Components or SWR/TanStack Query if client-side fetching is strictly required.
- ❌ **No direct DB calls in Client Components**: This will fail or leak secrets. Always use Server Actions or API routes.
- ❌ **No `any` type**: Use Zod for runtime validation and strict TypeScript types.
- ❌ **No massive components**: If a component exceeds 150 lines, split it into smaller sub-components.
- ❌ **No business logic in `app/` routes**: Keep routes thin; move logic to `services/`.