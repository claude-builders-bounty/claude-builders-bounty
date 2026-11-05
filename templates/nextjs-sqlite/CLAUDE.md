# CLAUDE.md — Next.js 15 + SQLite SaaS

This file is the single source of truth for how Claude Code should work in this repo.
Rules are **opinionated on purpose**: every one exists to prevent a specific class of bug
we've already been bitten by. Follow them; if a rule must be broken, say so and why first.

## 1. Stack & versions (do not silently upgrade)
- **Next.js 15.x, App Router only.** No `pages/`. No `getServerSideProps`.
- **React 19 + TypeScript `strict: true`.** `any` is banned; use `unknown` + a Zod parse.
- **SQLite via `better-sqlite3`** (local/dev) and **Turso/libSQL** (prod). Same SQL dialect.
- **Drizzle ORM + drizzle-kit** for schema + migrations. Raw SQL only inside migrations.
- **Tailwind CSS + shadcn/ui.** No CSS-in-JS. No component library that shadows shadcn.
- **Zod** for every input boundary (forms, route handlers, env).
- **Vitest** for unit/integration. **Playwright** for the smoke flow only.
- *Why:* a SaaS with 3 ORMs, 2 routers, or CSS-in-JS grows unmaintainable by month 3.

## 2. Commands
```bash
pnpm dev            # local dev (Turbopack)
pnpm build && pnpm start
pnpm db:generate    # drizzle-kit generate (NEVER edit SQL by hand)
pnpm db:migrate     # apply migrations
pnpm db:studio      # inspect data
pnpm lint && pnpm typecheck && pnpm test
```
Use **pnpm**. Do not introduce npm/yarn lockfiles.
*Why:* one package manager per repo; mixed lockfiles cause non-reproducible installs.

## 3. Folder structure
```
app/
  (marketing)/          # public pages
  (app)/                # authed area; app/(app)/layout.tsx enforces session
    dashboard/page.tsx
  api/<resource>/route.ts   # route handlers only for webhooks/uploads
lib/
  db/
    schema.ts           # Drizzle tables (the ONLY place tables are defined)
    client.ts           # better-sqlite3/Turso connection (server-only)
    queries/<entity>.ts # typed query functions
  auth.ts               # session helpers
  env.ts                # Zod-validated env (throws at boot)
components/
  ui/                   # shadcn primitives (generated)
  <feature>/            # feature components
server/
  actions/<entity>.ts   # "use server" actions
```
Do not create `utils.ts` grab-bags. Name the file for what it does (`formatMoney.ts`).
*Why:* feature colocation keeps diffs local and renames cheap.

## 4. Data & SQL / migration rules (most important section)
- **All schema lives in `lib/db/schema.ts`.** Edit it, then `pnpm db:generate`. **Never** hand-edit a migration.
- Migrations are **append-only** and committed. Never delete or modify a merged migration.
- Every table: `id TEXT PRIMARY KEY` (opaque, e.g. `crypto.randomUUID()` or a ULID),
  `created_at INTEGER NOT NULL DEFAULT (unixepoch())`, `updated_at INTEGER NOT NULL DEFAULT (unixepoch())`.
  *Why:* integer unix time sorts cheaply and avoids timezone bugs.
- **Foreign keys are always declared** with an explicit `onDelete` (`cascade` for
  owned rows, `restrict` for referenced lookups). Enable `PRAGMA foreign_keys = ON` at connect.
- **Every write goes through a server action or route handler** that Zod-parses input first.
  No direct DB calls from client components.
- **Wrap multi-row writes in `db.transaction(...)`.** Partial writes are a bug.
- **No `SELECT *` in app code** — select explicit columns in `queries/*.ts`.
  *Why:* schema drift and accidental PII leaks.
- **Never** interpolate user input into SQL strings. Use Drizzle's parameterized query builder.
- Add an index for every column used in `WHERE`/`ORDER BY` on a growing table.
- Soft-delete with `deleted_at INTEGER` for user-facing records; hard-delete only for join rows.
- *Why these rules:* SQLite favours boring, explicit, transactional data access.

## 5. Component patterns
- **Default to Server Components.** Add `"use client"` only for state/effects/event handlers,
  and push it as deep in the tree as possible.
- Data fetching happens in **Server Components / server actions**, never in `useEffect`.
- Mutations use **server actions** (`"use server"`) + `revalidatePath`/`revalidateTag`.
  Not ad-hoc `fetch('/api/...')` from client for internal writes.
- One component per file; named export matches filename. Props typed with an explicit
  `type XProps` — no inline object types.
- Keep components ≤ ~150 lines; extract sub-components instead of nesting five levels.
- Forms: **react-hook-form + Zod resolver**, submit via server action.
- Loading/empty/error states are required for every async view (use `loading.tsx`/`error.tsx`).
- *Why:* server-first keeps bundles small and data consistent; explicit states prevent blank UIs.

## 6. Naming conventions
- Files: `kebab-case.tsx` for routes, `PascalCase.tsx` for components, `camelCase.ts` for libs.
- DB: tables `snake_case` plural (`invoices`), columns `snake_case`, boolean columns `is_*` / `has_*`.
- Types: `PascalCase`; DB row types come from Drizzle `InferSelectModel`, never hand-written.
- Env vars: `SCREAMING_SNAKE`, validated in `lib/env.ts` — **never** read `process.env` directly elsewhere.
- Branches: `feat/<area>-<slug>`, `fix/<issue>-<slug>`. Commits: Conventional Commits.
  *Why:* predictable names make reviews and `git log` searches trivial.

## 7. Auth & security
- Session check lives in `app/(app)/layout.tsx` **and** in every server action
  (`if (!session) throw new Error("unauthorized")`). Never trust the client.
- All mutating actions verify **ownership**: `where userId = session.userId`.
- Secrets only via `lib/env.ts`. Never log secrets, tokens, or full request bodies.
- Set cookies `httpOnly`, `secure`, `sameSite=lax`.
  *Why:* defence in depth — layout guards alone don't protect server actions.

## 8. Testing
- Every `lib/db/queries/*` function and every server action gets a Vitest test against an
  **in-memory SQLite** (`:memory:`) with migrations applied.
- Test names describe behaviour: `"rejects invoice without a customer"`.
- No snapshot tests for UI. Assert on text/roles (Testing Library).
- *Why:* data logic is where money bugs live; in-memory SQLite makes it fast and real.

## 9. What we don't do (and why)
- ❌ **No ORM-hopping / raw SQL in app code** — one data layer, reviewed.
- ❌ **No `process.env` outside `lib/env.ts`** — unvalidated env is a 3am outage.
- ❌ **No `any` / `@ts-ignore`** — silent type holes become runtime crashes.
- ❌ **No client-side data fetching for internal data** — duplicate caches, stale UI.
- ❌ **No editing generated migrations** — breaks every environment that already ran them.
- ❌ **No `pages/` directory or mixing routers** — one mental model.
- ❌ **No new UI library** — shadcn + Tailwind is the design system.
- ❌ **No `DROP TABLE` / destructive DB commands** in scripts; ship a forward migration instead.

---
*Adopting this file:* drop it at the repo root, then `pnpm dlx shadcn@latest init` and
create `lib/env.ts`, `lib/db/{schema,client}.ts` before writing features.
