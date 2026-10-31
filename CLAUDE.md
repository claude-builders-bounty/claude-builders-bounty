# CLAUDE.md — Next.js 15 + SQLite SaaS Project

## Stack & Versions

- **Framework**: Next.js 15 (App Router), React 19, TypeScript 5
- **Styling**: Tailwind CSS v4, Lucide React icons
- **Database**: SQLite via `better-sqlite3` (local) / Turso (production), Drizzle ORM
- **Auth**: Auth.js v5 (optional, server-side sessions only)
- **Runtime**: Node.js 20+ (required for native `better-sqlite3` bindings)

## Project Structure

```
src/
├── app/                  # Routes, layouts, pages, loading/error boundaries
│   ├── (auth)/           # Auth route group
│   ├── (dashboard)/      # Protected route group
│   ├── api/              # Route Handlers (POST/PATCH/DELETE only)
│   └── layout.tsx        # Root layout
├── components/
│   └── ui/               # Shared UI primitives (Button, Card, Input…)
├── db/
│   ├── index.ts          # Single connection module (server-only)
│   ├── schema.ts         # Drizzle table definitions
│   └── migrations/       # Versioned .sql migration files
├── lib/
│   ├── actions/          # Server Actions (typed, colocated by feature)
│   └── utils.ts          # Pure helper functions
└── types/                # Shared TypeScript types & Zod schemas
```

## Commands

| Command              | Purpose                                    |
| :------------------- | :----------------------------------------- |
| `npm run dev`        | Start dev server (Turbopack)               |
| `npm run build`      | Production build                           |
| `npm run lint`       | ESLint + type check                        |
| `npm run db:generate`| Generate Drizzle migration from schema     |
| `npm run db:migrate` | Apply pending migrations                   |
| `npm run db:studio`  | Open Drizzle Studio for visual inspection  |

## Architecture Rules

1. **Server Components by default.** Add `"use client"` only on leaf interactive widgets (modals, forms, dropdowns). Never on layout or page components.
2. **Data fetching lives on the server.** Fetch in Server Components, Server Actions, or Route Handlers. Never fetch via `useEffect` when a Server Component can do it directly.
3. **Database access is server-only.** Import `db` from `@/db` which is marked `"server-only"`. Importing it in a Client Component is a build-time error.
4. **Parameterized queries only.** Use Drizzle's query builder or `sql` template tag. Zero raw string concatenation.
5. **Server Actions handle mutations.** Define with `"use server"` in `src/lib/actions/`. Validate all inputs with Zod before touching the database.
6. **No default exports except routes.** Pages, layouts, and route handlers use default export. Everything else uses named exports.

## SQLite & Migration Rules

1. **Connection pragmas** — every connection must run on open:
   ```sql
   PRAGMA journal_mode = WAL;
   PRAGMA foreign_keys = ON;
   PRAGMA busy_timeout = 5000;
   ```
2. **Migrations are strictly additive.** Never modify or delete an applied migration file. To change a table, create a new migration.
3. **Timestamps** — store as ISO-8601 UTC strings (`TEXT`) or Unix epoch milliseconds (`INTEGER`). Never use SQLite date functions for storage.
4. **IDs** — use `nanoid` or `cuid2` (TEXT primary key). Avoid auto-increment integers for distributed-safe ID generation.
5. **No `.db` files in git.** Add `*.db`, `*.db-wal`, `*.db-shm` to `.gitignore`.

## What We Do NOT Do

| Anti-Pattern | Why |
| :--- | :--- |
| Use Pages Router (`pages/`) patterns | App Router is the standard. No mixed routing. |
| `useEffect` + `fetch` for initial data | Server Components fetch directly — faster, no waterfall, no loading spinner. |
| `DROP TABLE` or `.sync({ force: true })` in staging/prod | Destructive. Use additive migrations only. |
| Raw SQL string concatenation | SQL injection risk. Always parameterize. |
| Import `db` in Client Components | Leaks Node-only modules to the browser bundle. `server-only` guard enforces this. |
| Edit or delete applied migration files | Breaks migration history. Create a new migration instead. |
| Default export non-route files | Breaks tree-shaking and makes imports ambiguous. |
| Commit `.env` files with secrets | Use `.env.local` (gitignored) for secrets. Validate with `@t3-oss/env-nextjs`. |
