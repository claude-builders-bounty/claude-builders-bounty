# CLAUDE.md — Next.js 15 App Router + SQLite SaaS Starter

> Opinionated production template for Next.js 15 (App Router) + SQLite (better-sqlite3 / Turso) — structure, naming, DB, and workflow for agents and humans.

## Stack

- **Framework:** Next.js 15 App Router (TS, `app/` only, no `pages/`)
- **DB:** SQLite via `better-sqlite3` locally, `turso` (`@libsql/client`) in prod — same SQL, swap via `DATABASE_URL`
- **ORM:** `drizzle-orm` + `drizzle-kit` (typed migrations, no hidden magic)
- **Auth:** Auth.js (NextAuth) — SQLite adapter
- **Styling:** Tailwind CSS

## Project Structure

```
app/
  (marketing)/page.tsx
  (app)/dashboard/page.tsx
  api/
    webhooks/stripe/route.ts
  layout.tsx
components/ui/      # shadcn/ui
lib/
  db/
    index.ts        # drizzle instance
    schema.ts       # tables
    migrate.ts
  auth.ts
drizzle/
  0000_init.sql
  meta/
scripts/
  seed.ts
```

**Rule:** `app/` = routes only. Logic lives in `lib/`. No business logic in `components/`.

## Naming

- Files: `kebab-case` (`user-settings.ts`), components: `PascalCase`
- Tables: `snake_case` plural (`users`, `subscriptions`), columns `snake_case`, TS types `camelCase`
- Env: `DATABASE_URL=file:./data.db` (local) or `libsql://...` (Turso)

## Database & Migrations

```bash
npm run db:generate   # drizzle-kit generate from schema.ts
npm run db:migrate    # drizzle-kit migrate
npm run db:seed       # tsx scripts/seed.ts
```

- Never hand-edit SQL in `drizzle/`. Edit `lib/db/schema.ts` → `generate`.
- Example `lib/db/schema.ts`:

```ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";
export const users = sqliteTable("users", {
  id: text("id").primaryKey(),
  email: text("email").notNull().unique(),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull(),
});
```

- Prod: set `DATABASE_URL=libsql://...` + `TURSO_AUTH_TOKEN`

## Dev Commands

```bash
npm run dev          # Next.js dev
npm run build        # next build (runs db:migrate in postbuild)
npm run lint && npm run typecheck
npm run test         # vitest
```

## Patterns

- Use Server Components by default; `"use client"` only for state/effects
- All DB access through `lib/db` — never raw `better-sqlite3` in routes
- Validate at boundary: `zod` in `app/api/*/route.ts`

## Anti-Patterns

- Don't put `pages/` alongside `app/`
- Don't use Prisma with SQLite here — drizzle is lighter, typed, zero hidden SQL
- Don't commit `data.db` — it is gitignored, seed it

## Why this template

SQLite keeps costs $0 (no Postgres host), deploys anywhere (VPS `myn8n-automation.org`), and Turso makes it edge-ready without rewrite. Drizzle gives typed SQL without ORM surprises.
