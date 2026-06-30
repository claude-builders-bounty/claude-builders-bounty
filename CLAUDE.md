# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated context file for Claude Code. Paste this into the repo root after `npx create-next-app` and SQLite setup.

## Stack & Versions

| Tool | Version | Why |
|------|---------|-----|
| Node.js | 20 LTS | Stability; Next.js 15 requires ≥18.17 |
| Next.js | 15.x (App Router) | Server Components, streaming |
| better-sqlite3 | ^11.0 | Sync API in Server Components / Route Handlers |
| TypeScript | 5.x | Strict mode enforced |

`bun` is allowed but `npm` is the canonical runner in this stack.

## Folder Structure

```
app/
  layout.tsx         # Root layout + global providers
  page.tsx           # Landing / marketing page
  (dashboard)/       # Route group — authenticated zone
    layout.tsx       # Dashboard shell
    page.tsx         # Dashboard home
components/
  ui/                # shadcn/ui primitives
  features/          # Domain components: UserForm, QueryTable …
lib/
  db/
    schema.ts        # better-sqlite3 connection + schema DDL
    migrations.ts    # Knex-style numbered migrations
  utils/
    cn.ts            # clsx + tailwind-merge
middleware.ts       # Auth edge middleware
```

## Naming Conventions

- **Files**: `kebab-case.tsx` for components, `PascalCase.tsx` only if it is a nested compound component.
- **Database tables**: `snake_case`.
- **Columns**: `snake_case`, `id` PRIMARY KEY, foreign keys as `{table}_id`.
- **Route segments**: `(group)` for parallel / auth-only layouts.

## DB Migration Rules

1. **One table per migration file.** Never alter an existing migration after merge.
2. Migrations run via `bun run db:migrate` (npm alias: `npm run db:migrate`).
3. Always add a **down** migration for reversible changes.
4. Never run raw SQL inside a Server Component — use a typed query helper in `lib/db/queries/`.

## Component Patterns

- **Server Components by default.** Add `"use client"` only for interactivity (onClick, useEffect, useState).
- **Data-fetching**: fetch inside Server Components; never on the client when the data is static or user-specific.
- **Forms**: use `react-hook-form` + Zod. Server Actions are preferred over API routes for mutations.
- **Loading / Error**: `loading.tsx` and `error.tsx` in the same segment as the page.

## Dev Commands

```bash
npm run dev         # localhost:3000
npm run build       # production build
npm run db:migrate  # apply + generate migrations
npm run lint        # next lint + eslint
```

## Anti-Patterns

| Don't | Why |
|-------|-----|
| Put business logic inside Route Handlers | Move it to `lib/db/queries/` for reuse |
| Use `any` in TypeScript | Use `unknown` + Zod schemas |
| Fetch data on the client when a Server Component can do it | Increases bundle + latency |
| Store secrets in `.env.local` without validation | Use `zod` schema to validate at startup |
| Mix SQLite types (sync better-sqlite3) with web Workers | SQLite runs on the server only |
