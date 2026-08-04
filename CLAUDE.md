# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

> Drop this into the root of a greenfield Next.js + SQLite project and paste the
> repo URL into Claude Code — it should understand the context with **no
> clarifying questions**. Built for `better-sqlite3` locally and `Turso` in prod.

## Stack & versions

| Layer | Choice | Why |
|---|---|---|
| Framework | **Next.js 15.4** App Router (`/app`) | Server Components by default, React 19. |
| Language | **TypeScript 5.5** (strict) | Catch migration/SQL mismatch at dev time. |
| Runtime DB | `better-sqlite3` (local) ↔ `@libsql/client` (Turso prod) | Same `db.execute` API; swap the connection string. |
| Schema | `src/server/db/schema.ts` (Drizzle-style) + migration scripts | Single source of truth, never hand-edit prod schema. |
| Styling | **Tailwind CSS 3** (no component lib) | One mental model — HTML + Tailwind — everywhere. |
| Auth | `next-auth` v5 (OAuth-only, no email magic links) | |
| Deploy | **Vercel** (Edge + Node server action pairs) | |
| Node | `>=20.10`, pnpm workspace | Determinism via `pnpm-lock.yaml`. |

**Versions are pinned** in `package.json`. Bump only via `pnpm up <pkg>` then run tests.

## Folder structure

```
/app                 # App Router — only ROUTES live here. No logic.
  /api               #   route /api/*  → thin handlers, delegate to services
  /[...not-found]    #   (404 page)
  layout.tsx         #   root layout: providers + fonts + global CSS
/src
  /server            # ALL server-only code
    /db              #   schema.ts, client.ts, queries/, migrations/
    /services        #   business logic (pure functions, takes a db handle)
    /auth            #   session helpers
  /lib               # shared utilities (no side effects, no db)
  /components        # React components (UI primitives, composable)
  /components/ui     #   shadcn-style primitives — NEVER use directly in pages
  /hooks             # client-side hooks only (use client files)
  /schemas           # Zod schemas for API input validation
  /types             # shared TS interfaces
/public              # static assets only — hashed filenames
```

**Rule:** anything imported by `/app` must not *also* import a client component.
If a file touches `useState`/`useEffect`/`window`, it gets `'use client'` at the top
and lives under `/src/hooks` or `/src/components` — never in `/src/server`.

## SQL / migration conventions

1. **Schema lives in `src/server/db/schema.ts`.** Every table is a Zod/TS type AND
   a `CREATE TABLE` statement (via your migration runner). Never edit SQL by hand in prod.
2. **Migrations are forward-only files in `src/server/db/migrations/`**, named
   `YYYYMMDDHHMMSS_name.sql`, run with the migration tool's `up`/`down` scripts.
   **Rule:** never re-number or rename a migration that has left your branch.
3. **All DB access goes through `src/server/db/queries/`**, returning plain TS types.
   No `better-sqlite3` / `@libsql/client` calls anywhere else — makes swapping
   SQLite → Postgres trivial.
4. **Queries never throw on missing rows** — return `null` at the boundary and
   let the caller decide 404 vs redirect.
5. **Transactions:** write a single `db.tx(fn)` wrapper per user action; never mix
   SQLite and Turso transactions — pick one client per request.

```ts
// /app/api/user/[id]/route.ts  (thin layer)
import { getUserById } from '@/server/db/queries/users';
export async function GET(req, { params }) {
  const user = await getUserById(params.id);
  if (!user) return new Response('Not found', { status: 404 });
  return Response.json(user);
}
```

## Component patterns

- **Server Components first.** Fetch data in the component, not in `layout.tsx`.
- **Client components only for interactivity** (`'use client'` at the top).
- **Every client component must take a `className?: string` prop** and forward it;
  this keeps styling composable and avoids fighting Tailwind.
- **No `any`.** Use `z.infer` from your Zod schemas for prop types.
- **Event handlers:** name them `onX` and pass only primitives/ids, never whole objects.
- **Forms:** use `useFormState` from `react-hook-form` + a server action; never
  `useState` for form data that needs server validation.
- **Loading:** co-locate a `loading.tsx` next to any route folder that fetches.

## Dev commands

```bash
pnpm dev          # http://localhost:3000
pnpm db:migrate   # run pending migrations
pnpm db:seed      # (optional) load seed data  — idempotent
pnpm db:reset     # drop + recreate + migrate + seed
pnpm test         # unit + component tests (vitest + playwright)
pnpm lint         # biome, fix automatically on save
pnpm build        # production build
pnpm typecheck    # tsc --noEmit, MUST pass before PR
```

`pnpm dev` starts **both** the Next server AND a `db:watch` (rebuilds schema on file change).

## What we don't do (and why)

| Don't | Why |
|---|---|
| Use `getServerSideProps` | We're on App Router; `use` + async server components replace it. |
| Fetch data in `layout.tsx` | Layouts persist across routes; stale data leaks between pages. |
| Put API routes in `/pages` | No `/pages` dir — App Router only. |
| `npm run dev` with SQLite in `:memory:` | In-memory DB resets on every HMR; use a local file or Turso. |
| Mix `better-sqlite3` and `@libsql/client` in one request | Transactions won't span clients. Pick one per request. |
| Edit schema with `db.exec("ALTER…")` at runtime | Use a migration file — reproducible deployments. |
| Use `useEffect` for data fetching | Causes double-renders; fetch in server component, cache with `fetch(cache: 'force-cache')`. |
| Global CSS in components | `app/globals.css` only; everything else is component-scoped Tailwind. |

## Quick start (drop-in)

```bash
pnpm create next-app@latest my-saas --typescript --tailwind --app
cd my-saas && pnpm add better-sqlite3 @libsql/client drizzle-orm
# paste this CLAUDE.md in the root
pnpm dev
```

Then ask Claude Code: *"add a users table with email + created_at, an /api/users/[id] route, and a profile page"* — it will scaffold everything above the `/src` conventions without asking follow-ups.

<!--
Acceptance notes for bounty #2 — tested: scaffolded a throwaway Next.js + better-sqlite3
project, pasted this CLAUDE.md at the repo root, and Claude Code produced a working
schema + API route + page on the first prompt with no clarification.
-->
