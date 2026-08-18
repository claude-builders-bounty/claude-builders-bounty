# CLAUDE.md

Opinionated working agreement for a **Next.js 15 App Router + SQLite** SaaS. Paste this at the repo root. Do not ask whether to use the App Router, Prisma, or Postgres — those decisions are already made.

## Stack & versions

- Next.js **15** App Router only. No `pages/`.
- React Server Components by default. `"use client"` is a last resort, not a default.
- SQLite via **`better-sqlite3`** in local/dev. Same SQL files work on **Turso** in production (`@libsql/client`). Do not introduce Prisma, Drizzle, or an ORM unless the user explicitly asks — the query surface stays small and reviewable.
- Auth: session cookie + `users` table. No NextAuth adapters until there is a second provider.
- Node 22. `npm` scripts only in `package.json`; do not add Makefile wrappers.

## Folder structure

```
app/                 # routes, layouts, server actions
  (auth)/            # login/register — no app chrome
  (app)/             # authenticated product chrome
  api/               # Route Handlers only for webhooks / non-form clients
lib/
  db.ts              # single getDb() — never import better-sqlite3 elsewhere
  sql/               # numbered migrations: 001_init.sql
  auth.ts
components/          # presentational only; no SQL
```

Route groups exist so marketing and product do not share a layout by accident. Do not flatten them.

## Naming

- Files: `kebab-case.ts`. React components: `PascalCase.tsx`.
- SQL tables: `snake_case`, plural (`invoices`). Primary key `id` integer. Foreign keys `*_id`.
- Server Actions: `verbNoun` (`createInvoice`). They live next to the route that uses them, not in a global `actions.ts` dump.

## SQL / migrations

- Schema changes are **append-only SQL files** in `lib/sql/`. Never edit a migration that already ran on anyone's machine.
- `getDb()` applies pending files in order and records them in `schema_migrations`.
- SQLite has limited `ALTER`. Prefer new table + copy over in-place column rewrites.
- Every user-owned row has `user_id`. Queries filter by it. No "admin sees all" unless the route is behind an explicit `role = 'admin'` check.
- Bind parameters only. String-concatenated SQL is a bug.

## Component patterns

- Fetch in Server Components. Mutate through Server Actions with `revalidatePath`.
- Forms: native `<form action={...}>`. Do not add a client store for a single form.
- Client components are for: input that must feel instant (combobox, drag), or browser APIs. They receive serializable props. They do not import `lib/db.ts`.
- Tailwind in the component file. No CSS modules unless the design cannot be expressed in utilities.

## Dev commands

```
npm run dev          # next dev
npm run build        # next build
npm run db:migrate   # apply lib/sql
npm run db:reset     # delete local sqlite file + migrate (dev only)
```

SQLite file path: `data/app.db` (gitignored). Do not put the database under `app/` — Next will try to bundle it.

## What we don't do (and why)

- **No Prisma / Drizzle** — a 6-table SaaS does not need a schema DSL and a generate step. SQL in files is the source of truth.
- **No `pages/` directory** — mixed routers split caching rules and confuse App Router layouts.
- **No client-side data fetching for first paint** — the HTML should already have the rows. SWR is for optional refresh, not the primary load.
- **No shared "service layer" until the third copy-paste** — `lib/db.ts` + a function next to the route is enough. Premature services hide SQL from the reviewer.
- **No environment-specific schema** — one migration stream. Feature flags are data, not extra tables per env.
- **Do not store secrets in SQLite.** Sessions can live there; API keys cannot.

If a request conflicts with this file, follow this file and mention the conflict in the PR, do not silently switch stacks.
