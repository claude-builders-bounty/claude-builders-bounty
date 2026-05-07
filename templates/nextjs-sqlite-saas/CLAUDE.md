# CLAUDE.md — Next.js 15 + SQLite SaaS

> Drop this file at the repo root. Claude Code reads it on every session and uses it as the operating manual for this codebase.

## Stack & versions

- **Runtime:** Node 20 LTS (lockfile pinned). No 22.x — better-sqlite3 prebuilds lag on bleeding-edge.
- **Framework:** Next.js 15 App Router. **Server Components are the default**; only mark `'use client'` when you actually need React state, refs, or browser APIs.
- **DB:** SQLite via `better-sqlite3` (synchronous, in-process). Use Turso/libSQL only if multi-region read replicas are an explicit product requirement — most SaaS apps don't need it.
- **ORM:** Drizzle. Reason: SQL-first, generates real migrations, zero runtime overhead. Avoid Prisma here — its codegen + better-sqlite3 native binding combo causes Vercel build flakiness.
- **Auth:** Lucia v3 with the `oslo` crypto helpers. Avoid Clerk/Auth0 unless the user's plan is paid — third-party auth becomes a recurring cost line item that's hard to reverse later.
- **Validation:** Zod everywhere — for env, request bodies, DB inputs, and form state. One schema, three call-sites.
- **Styling:** Tailwind v4 + a small `lib/cn.ts` (clsx + tailwind-merge). No CSS-in-JS — server components and CSS-in-JS fight each other.
- **State:** RSC + Server Actions for mutations. Reach for Zustand (small) or React Query (server-state caching) only when a real client-side need appears.
- **Tests:** Vitest. Hit DB via an in-memory SQLite (`:memory:`); run migrations in `beforeEach`.

## Folder structure (all paths are relative to repo root)

```
app/                         # Next.js App Router routes
  (marketing)/               # public routes (landing, pricing) — no auth
  (app)/                     # authed app shell
    layout.tsx               # session-required guard lives here, NOT in middleware
    [slug]/page.tsx          # dynamic routes use server components by default
  api/
    webhooks/                # external (Stripe, Clerk-if-used) — verify signatures
    trpc/[trpc]/route.ts     # only if tRPC is in use
components/
  ui/                        # primitives (shadcn-style); no business logic
  features/                  # feature-scoped composites (one folder per feature)
db/
  schema.ts                  # Drizzle table definitions
  migrations/                # generated; checked in; immutable once shipped
  client.ts                  # exports `db` (singleton); no top-level `await`
lib/
  auth.ts                    # session helpers (createSession, validateRequest)
  env.ts                     # `process.env` parsed via Zod, exports typed `env`
  rate-limit.ts              # simple sliding-window using SQLite
emails/                      # react-email templates (.tsx)
scripts/
  migrate.ts                 # `tsx scripts/migrate.ts` runs all pending migrations
  seed.ts                    # idempotent seed for local dev
tests/
  unit/
  integration/               # spin up :memory: DB + run a real handler
```

## SQL / migration conventions

- **Migrations are append-only.** Once a migration ships to prod, never edit it. New change = new migration.
- **One concern per migration.** A "make column NOT NULL" migration is separate from a "backfill column" migration. Lets you roll forward incrementally.
- **`drizzle-kit generate` first, hand-edit second.** Generated SQL is the baseline; hand-edits add comments, indexes, and `ON DELETE CASCADE` clauses the generator misses.
- **No `DROP COLUMN` in a single migration.** Three-step: (1) deploy code that doesn't read the column, (2) drop the column, (3) clean up the generator's warnings. SQLite DROP COLUMN is also slow on large tables.
- **Foreign keys are always declared with `ON DELETE CASCADE` or `ON DELETE RESTRICT`.** If you can't decide, `RESTRICT` and let the bug surface in tests.
- **Timestamps are stored as `INTEGER` (unix seconds), never as `TEXT`.** SQLite doesn't have a native datetime; storing as integer is faster, simpler, and avoids timezone headaches.
- **Indexes are part of the migration that introduces the access pattern**, not added later as an afterthought.

## Component patterns

- **Default to server.** A component that fetches data is a server component. Reach for `'use client'` only for interactive widgets — and put the boundary as deep in the tree as possible.
- **Forms:** `<form action={serverAction}>`. The server action reads the FormData with the same Zod schema the DB uses. No double validation logic.
- **Loading states:** lean on `loading.tsx` and `Suspense`. Don't sprinkle `isLoading` flags through client components — that's an anti-pattern in App Router.
- **Streams:** for any list >100 items, use `<Suspense>` boundaries to stream below-the-fold content.
- **Error UI:** every route has an `error.tsx`; every async server component is wrapped by a parent `error.tsx`. Render a stable, recoverable UI.
- **Cache hints:** call `unstable_cache` (or future `cacheTag`) at the data-access function level, not in the component. Keep components dumb about caching.

## Dev commands

```bash
pnpm dev                     # next dev with turbopack
pnpm test                    # vitest run
pnpm test:watch              # vitest --watch
pnpm db:generate             # drizzle-kit generate (after schema change)
pnpm db:migrate              # apply pending migrations
pnpm db:studio               # drizzle-kit studio (browse local DB)
pnpm typecheck               # tsc --noEmit
pnpm lint                    # eslint --max-warnings 0
pnpm build                   # next build (verifies prod compile)
```

Use **pnpm** (not npm or yarn). The workspace is single-package; switching package managers mid-project breaks lockfile reproducibility.

## What we DON'T do (and why)

- **No `getServerSideProps` / pages-dir patterns.** App Router only. Mixing the two creates duplicate auth/data-fetching paths.
- **No `useEffect` for data fetching.** Server Components fetch. If you reach for `useEffect`, you have either a real subscription (websocket) or a misplaced server-side concern.
- **No global mutable state in client code.** State lives in the URL, in cookies, or in the DB. Zustand only for ephemeral UI state (e.g. modals, multi-step wizards).
- **No string-concat SQL.** Every query goes through Drizzle's tagged template or its query builder. Even one-off scripts.
- **No `any` in app code.** `unknown` + Zod parse, every time. Reserve `any` for genuinely unknown JSON from third parties — and even then, parse it before it leaves the boundary function.
- **No top-level `await` in module init.** It blocks Next.js's optimizer and breaks Vercel's edge build.
- **No `console.log` in shipped code.** Use `lib/log.ts` (a tiny pino wrapper) so prod logs are structured and dev logs are pretty.
- **No `dotenv` import.** Next.js loads `.env.local` automatically; double-loading shadows values and confuses CI.
- **No npm scripts that wrap multi-command shell pipelines.** If a script needs more than one command, it goes in `scripts/*.ts` (typed, debuggable) — not in `package.json`.
- **No README.md duplicates of this file.** README is for humans browsing GitHub; this is for Claude. They diverge on purpose.

## Patterns to follow

- **One Drizzle query per data-access function.** If a component needs three queries, write one DAL function that joins or aggregates them. Components never call `db` directly.
- **Server Actions live next to the route that uses them**, not in a global `actions/` folder. Co-locate cohesion.
- **Validation runs at the boundary.** API route → Zod parse `req.body`. Server action → Zod parse FormData. DAL → trust the input (already validated).
- **Database client is a singleton.** `db/client.ts` exports a single `better-sqlite3` instance with WAL mode enabled. Never `new Database(...)` elsewhere.
- **Error responses are uniform.** Routes return `Response.json({ error: { code, message } }, { status })`. The frontend expects that shape — don't surprise it.
- **Route handlers stay <50 lines.** Anything bigger means business logic crept into the HTTP layer; refactor into `lib/` or a feature module.

## Anti-patterns the agent has seen recently — don't repeat

- Adding `"use client"` to the page itself to fix a single client-only child. Move the boundary to that child instead.
- Wrapping every async function with `try/catch` that just `console.error`s and re-throws. If you can't recover, don't catch.
- Reaching for `react-query` to fetch data that a Server Component could fetch on the server.
- Importing `better-sqlite3` in code paths that may run on the edge runtime — it's Node-only. Mark routes `export const runtime = 'nodejs'` when in doubt.
- "Just one any here, I'll fix it later." There is no later.

## When the agent is stuck

1. **Read `db/schema.ts` first.** Most data shape questions are answered there.
2. **Check `lib/env.ts`** before assuming an env var exists.
3. **Run `pnpm typecheck`** before claiming the change is complete. The compiler catches 80% of regressions for free.
4. **Run `pnpm test`** — the integration tests in `tests/integration/` exercise real DB handlers and surface migration drift instantly.
5. If still stuck after 5 attempts, stop and summarize what's blocking. Don't guess.
