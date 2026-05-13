# CLAUDE.md — Next.js + SQLite SaaS Project

## Stack & Versions

- **Framework**: Next.js 15 (App Router)
- **Database**: SQLite via better-sqlite3 (local/dev) or Turso (production)
- **ORM**: Drizzle ORM
- **Auth**: NextAuth.js v5 (Auth.js) with credentials + OAuth providers
- **UI**: Tailwind CSS v4 + shadcn/ui
- **Language**: TypeScript strict mode
- **Package Manager**: pnpm
- **Node**: >=20

## Folder Structure

```
src/
├── app/              # Next.js App Router pages & API routes
│   ├── (auth)/       # Auth-required layouts
│   ├── (public)/     # Public pages (landing, marketing)
│   ├── api/          # API route handlers
│   └── layout.tsx    # Root layout
├── components/       # React components
│   ├── ui/           # shadcn/ui primitives
│   └── features/     # Feature-specific components
├── db/               # Database
│   ├── schema/       # Drizzle schema files
│   ├── migrations/   # Auto-generated migrations
│   └── index.ts      # DB client & connection
├── lib/              # Utilities, helpers, config
│   ├── auth.ts       # Auth.js config
│   └── utils.ts      # Shared utilities
└── types/            # Shared TypeScript types
```

## Dev Commands

```bash
pnpm dev              # Start dev server (localhost:3000)
pnpm build            # Production build
pnpm lint             # ESLint + TypeScript check
pnpm test             # Run tests (Vitest)
pnpm db:generate      # Generate migration from schema changes
pnpm db:push          # Push schema to local DB (dev only)
pnpm db:studio        # Drizzle Studio GUI
pnpm type-check       # tsc --noEmit
```

## SQL / Migration Conventions

- **One schema file per domain**: `schema/users.ts`, `schema/projects.ts`, `schema/subscriptions.ts`
- **Every migration must be reviewed** before pushing to production
- **Never edit migration files** after creation — generate new ones
- **Use `db:push` only in dev** — production uses `db:migrate`
- **Soft deletes preferred** over DELETE — add `deletedAt` column
- **Foreign keys**: define them explicitly in Drizzle schema

### Schema Example

```typescript
// src/db/schema/users.ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

export const users = sqliteTable("users", {
  id: text("id").primaryKey(),
  email: text("email").notNull().unique(),
  name: text("name"),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
  updatedAt: integer("updated_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date())
    .$onUpdateFn(() => new Date()),
  deletedAt: integer("deleted_at", { mode: "timestamp" }),
});
```

## Component Patterns

- **Server Components by default** — only add "use client" for interactivity
- **Page Components** fetch data directly — no getServerSideProps/getStaticProps
- **Forms**: use Server Actions, not client-side form handlers
- **Loading states**: use loading.tsx and Suspense boundaries
- **Error boundaries**: use error.tsx per route segment

## API Route Patterns

- **Route Handlers** in app/api/ — no more pages/api/
- **Validation**: use Zod schemas for request validation
- **Response format**: always return { data, error } shape
- **Auth**: check session in every protected route handler

## What We Don't Do (And Why)

| Don't | Why |
|-------|-----|
| Redux / Zustand / Jotai | Server Components + URL state + React Context cover 95% of needs |
| Prisma | Drizzle is lighter, faster, and SQL-first for SQLite |
| CSS Modules / styled-components | Tailwind + shadcn/ui covers everything |
| MongoDB / external DB in dev | SQLite in dev = zero setup, same schema as Turso production |
| Monorepo tools | Not needed until 3+ apps |
| Custom auth from scratch | NextAuth.js v5 handles OAuth, JWT, database sessions |
