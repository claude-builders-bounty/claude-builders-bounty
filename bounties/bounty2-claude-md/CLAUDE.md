# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> Opinionated conventions for a production SaaS project built with Next.js 15 (App Router) and SQLite (better-sqlite3 via Prisma).

## Stack & Versions

- **Framework**: Next.js 15 (App Router, Turbopack dev)
- **Database**: SQLite via Prisma ORM + better-sqlite3
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS 4
- **Auth**: NextAuth.js v5 (Auth.js) with credentials + OAuth providers
- **Validation**: Zod (server + client)
- **Testing**: Vitest + Playwright
- **Package Manager**: pnpm

## Folder Structure

```
src/
├── app/              # Next.js App Router pages
│   ├── (auth)/       # Auth group (login, register, reset-password)
│   ├── (dashboard)/  # Dashboard group (authenticated routes)
│   ├── api/          # Route handlers (API endpoints)
│   └── layout.tsx    # Root layout
├── components/
│   ├── ui/           # Primitives (button, input, card, modal)
│   ├── forms/        # Form components wrapped with react-hook-form
│   └── layout/       # Sidebar, header, nav components
├── lib/
│   ├── db.ts         # Prisma client singleton
│   ├── auth.ts       # NextAuth.js config
│   └── utils.ts      # Shared utilities (cn, format, etc.)
├── actions/          # Server Actions
│   └── *.ts          # One file per domain (users, billing, projects)
├── schemas/          # Zod schemas
│   └── *.ts          # One file per domain
├── types/            # Shared TypeScript types
└── styles/           # Global CSS, Tailwind layers
```

**Rules:**
- `app/` only contains route files (`page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`, `route.ts`).
- Business logic goes in `lib/` or `actions/`.
- One file per exported function—no god files over 200 lines.

## SQL / Migration Conventions

- All schema changes go through Prisma migrations: `pnpm prisma migrate dev --name <description>`.
- Migrations are reviewed in PRs. Never edit migration files after they're created.
- Every table gets: `id TEXT PRIMARY KEY`, `createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP`, `updatedAt DATETIME NOT NULL`.
- Soft deletes: add `deletedAt DATETIME?` instead of `DELETE FROM`.
- Index columns used in WHERE, ORDER BY, or JOIN. Measure with `EXPLAIN QUERY PLAN`.
- Never use `SELECT *`. Always select specific columns.
- Use transactions for operations that update multiple rows: `prisma.$transaction([...])`.

## Component Patterns

- **Server components by default**. Only add `'use client'` when you need:
  - `useState`, `useEffect`, `useContext`
  - Browser-only APIs (localStorage, navigator)
  - Event handlers (onClick, onSubmit)
- **Composition over props drilling**. Use `children` or layout components.
- **Loading states**: Every `page.tsx` that fetches data should have a matching `loading.tsx`.
- **Error states**: Every route group should have an `error.tsx`.
- **Not found**: Custom `not-found.tsx` per route group.
- No `any` types. No `eslint-disable`. No `// @ts-ignore`.

## Naming Conventions

| Artifact         | Convention                | Example                      |
|-----------------|---------------------------|------------------------------|
| Pages           | `kebab-case/page.tsx`     | `user-settings/page.tsx`     |
| Components      | PascalCase.tsx            | `UserAvatar.tsx`             |
| Server Actions  | camelCase.ts              | `createProject.ts`           |
| Schemas         | camelCase.ts              | `projectSchema.ts`           |
| API routes      | `[param]/route.ts`        | `[projectId]/route.ts`       |
| Types           | PascalCase.ts             | `ProjectTypes.ts`            |
| CSS classes     | kebab-case                | `flex items-center gap-2`    |

## Dev Commands

```bash
pnpm dev          # Start dev server (Turbopack)
pnpm build        # Production build
pnpm lint         # ESLint + Prettier check
pnpm test         # Run Vitest
pnpm test:e2e     # Run Playwright
pnpm prisma:gen   # Generate Prisma client after schema change
pnpm prisma:push  # Push schema to local DB (dev only)
pnpm prisma:seed  # Seed database
pnpm db:studio    # Open Prisma Studio
```

## What We Don't Do (and Why)

1. **❌ Redux / Zustand / any global state library** — Next.js 15 Server Components + URL state cover 95% of use cases. For the remaining 5%, use React Context with careful memoization.
2. **❌ Raw SQL (except in migrations)** — Prisma gives type safety and prevents injection. If a query is slow, add an index, don't reach for raw SQL.
3. **❌ `useEffect` for data fetching** — Use Server Components or `server-only` functions. Client-side fetching is an anti-pattern here.
4. **❌ Monorepo — for now** — Start as a single package. Extract packages only when there's a proven need and a clear boundary.
5. **❌ CSS-in-JS** — Tailwind CSS + `cn()` utility covers styling. No Emotion, Styled Components, or CSS Modules.
6. **❌ `any` types for quick fixes** — If you can't type something, pause and figure it out. `unknown` + type narrowing is acceptable; `any` is not.
7. **❌ Direct Prisma access in components** — Always use Server Actions (`src/actions/`) as the data access layer. Components should never import `prisma` directly.

## Security Rules

- Validate ALL inputs with Zod before processing in Server Actions.
- Rate-limit auth endpoints (login, register, password reset).
- Never log tokens, passwords, or PII.
- Use `next/headers` and `next/cookies` — never access `req` objects directly.
- SQLite WAL mode is enabled by default in Prisma. Ensure backups run before migrations in production.
