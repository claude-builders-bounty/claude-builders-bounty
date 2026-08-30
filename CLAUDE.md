# CLAUDE.md — Convention Contract for This Project

> This file is the **single source of truth** for how Claude Code should work
> in this repo. Every rule below exists because it prevents a real failure
> we hit or saw in the wild. If a rule feels arbitrary, read its "why".

## Stack & versions (pin these)

- **Framework:** Next.js **15** (App Router), React 19, TypeScript 5
- **Database:** SQLite via **better-sqlite3** (sync, simplest for SaaS CRUD)
- **ORM:** Drizzle ORM (typed schema, easy migrations) — **do not** add Prisma
- **Auth:** Better Auth (or Auth.js) — session cookie + DB session table
- **Styling:** Tailwind CSS v4
- **Package manager:** pnpm (lockfile is the contract — never commit with npm)

**Why pinned?** Next 15 + React 19 change APIs; better-sqlite3 gives us sync
writes which remove a whole class of race conditions in a single-process server.

## Folder structure (follow it)

```
app/                     # App Router routes (colocate UI + data where possible)
  (marketing)/           # public pages, SEO landing
  (app)/                 # authenticated app area
    dashboard/
  api/                   # route handlers (server actions preferred when possible)
  layout.tsx
  page.tsx
components/              # shared React components (client unless stated)
  ui/                    # primitives (Button, Input...)
  features/              # feature-specific composites
db/
  schema.ts              # Drizzle schema (single source of truth)
  migrations/            # auto-generated, committed
  client.ts              # better-sqlite3 + drizzle instance (module singleton)
  seed.ts                # dev seed script
lib/                     # non-React logic: email, billing, auth helpers
services/                # domain services (thin, no JSX)
tests/
hooks/
middleware.ts            # auth/route protection
```

**Why?** Splitting `components/ui` from `features` keeps primitives pure and
reusable; colocating data loading in route files avoids prop-drilling; a single
`db/` folder means one place to reason about persistence.

## SQL / migration conventions

- **Schema is Drizzle-first.** Edit `db/schema.ts`, then generate a migration:
  ```bash
  pnpm db:generate   # writes db/migrations/<ts>_<name>.sql
  pnpm db:migrate     # applies pending migrations to dev db
  ```
- **Every schema change is a new migration file.** Never edit an applied
  migration in place — migrations are append-only history.
- **Primitive foreign keys:** use signed `id` (SQLite) with `REFERENCES`, or the
  `integer pk` pattern — and set `onDelete` explicitly (cascade vs restrict).
- **Always add an index for every FK** and for every column in a `WHERE` that
  appears in a hot path.
- **Transactions** for multi-row writes (better-sqlite3: `.transaction()`).
- **Destructive changes** (dropping a column/table) require a soft-release step:
  deploy code that tolerates the old schema first, then migrate.

**Why?** SQLite is a single file; a bad migration is expensive to recover from.
Append-only migrations + explicit FKs + indexes keep it fast and safe.

## Component patterns

- **Server components by default.** Only add `"use client"` when you need
  state, effects, or browser APIs.
- **Forms:** use Next.js **Server Actions** for mutations; client-side just
  calls the action. Return `{ success } | { error }` and render error states.
- **Data fetching:** read in the server component (or Server Action), pass
  primitives down. Use `cache()`/`unstable_cache` only for repeated reads.
- **Never** put `fetch` in a client component for server-owned data — use
  Server Actions or route handlers behind the same auth.
- **Loading/error UI:** always ship `loading.tsx` + `error.tsx` per route
  segment that loads async data.
- **Keys:** `key` props must be stable (db id, not array index).

**Why?** Server components remove bundle weight and are the default the
framework wants; Server Actions are typed and beat hand-written fetch chains.

## What we don't do (and why)

| Don't | Why |
|---|---|
| Don't commit `.env*` or `.db` files | secrets + deployment, db file is generated |
| Don't use `any` | removes type safety that prevents the bugs we automate against |
| Don't call the db from a client component | breaks the single-connection model & auth boundary |
| Don't import from `next/headers` in non-RSC | breaks static rendering silently |
| Don't bypass migrations with raw SQL in app code | diverges the real schema from `db/schema.ts` |
| Don't add a global `crypto.randomUUID()` PK on SQLite | integer autoincrement is faster & index-friendly |
| Don't nest route handlers just because it feels organized | flat `app/api` with clear names is easier to audit |
| Don't use `useEffect` for derived state | use computed values / memoization so render is deterministic |

## Dev commands (canonical)

```bash
pnpm install                # install (never npm install / yarn)
pnpm dev                    # local dev server @ localhost:3000
pnpm build                  # production build (must pass before merge)
pnpm start                  # serve the production build
pnpm db:generate            # write migration from schema change
pnpm db:migrate             # apply migrations
pnpm db:seed                # seed dev data
pnpm test                   # run vitest suite
pnpm lint && pnpm typecheck # gate CI
```

## PR / review expectations (when acting as a reviewer)

- Inspect `db/migrations/` for **unexpected schema drift** on every PR that
  touches `db/`.
- Flag any `any`, unhandled `await`, or db call in a client component.
- Verify a form mutation returns a typed result and has an error boundary.
- Confirm no `console.log` leaks credentials or PII.

*This file is the contract. When in doubt, follow it over habit.*
