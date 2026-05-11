# CLAUDE.md — Next.js 15 + SQLite SaaS

> Drop this file at the repo root. It tells Claude Code everything it needs to be productive on this codebase without asking clarifying questions.

---

## Stack

- **Runtime:** Node 20 LTS (use the version pinned in `.nvmrc`)
- **Framework:** Next.js 15 — **App Router only**. No `pages/` directory.
- **Language:** TypeScript, `strict: true`. No `any`. No `// @ts-ignore` without a comment explaining why.
- **DB:** SQLite via `better-sqlite3` (local) and Turso/libSQL (prod). Schema is identical; only the driver changes.
- **Migrations:** Plain `.sql` files in `db/migrations/`, applied in lexicographic order. No ORM-managed migrations.
- **Query layer:** Hand-written SQL wrapped in typed functions in `db/queries/`. No Prisma, no Drizzle. Reason: schemas are small, raw SQL is faster to debug, and we never need to swap DBs.
- **Auth:** Lucia or a hand-rolled session-cookie scheme. **No NextAuth.** Reason: NextAuth's data model fights SQLite-only stacks.
- **Styling:** Tailwind v4. No CSS-in-JS.
- **UI primitives:** shadcn/ui (copy-paste, not a dependency). Lives in `components/ui/`.
- **Forms:** React Hook Form + Zod. Server Actions for submission.
- **Payments:** Stripe via webhooks → `db/queries/billing.ts`. Never store card data.
- **Email:** Resend. Templates in `emails/` rendered with `react-email`.
- **Testing:** Vitest (unit), Playwright (e2e). No Jest.
- **Deploy:** Vercel for the app, Turso for the DB. Both regions co-located.

If a dependency is not listed here, ask before adding it.

---

## Folder Structure

```
app/                      # App Router routes only
  (marketing)/            # public site — landing, pricing, /blog
  (app)/                  # authed product — everything behind /dashboard
    dashboard/
      layout.tsx          # session guard lives here, NOT in middleware
      page.tsx
  api/
    webhooks/stripe/route.ts
    health/route.ts
  layout.tsx              # root layout — fonts + <body> only
  globals.css

components/
  ui/                     # shadcn primitives — do not edit by hand, re-run the CLI
  <feature>/              # one folder per product feature, colocated

lib/
  auth.ts                 # session read/write — server-only
  env.ts                  # zod-validated process.env, imported everywhere
  utils.ts                # tiny helpers only (cn, formatCurrency); no business logic
  stripe.ts               # Stripe client + typed event narrowing

db/
  client.ts               # exports `db` — better-sqlite3 in dev, libSQL in prod
  schema.sql              # the canonical, latest schema (for reference & fresh installs)
  migrations/             # 0001_init.sql, 0002_add_teams.sql, ...
  queries/                # one file per table/aggregate; pure functions
    users.ts
    subscriptions.ts

emails/                   # react-email templates
public/
scripts/                  # one-off ops scripts (seed, backfill); never imported by app code
tests/
  unit/
  e2e/
```

**Rules**
- Routes are folders. Components are files. Don't make a folder for a single component.
- Colocate: a feature's component, its server actions, and its query helpers live next to each other unless reused.
- `app/` files are Server Components by default. Add `"use client"` only when you need state, effects, or browser APIs.

---

## Naming

- Files: `kebab-case.ts`, `kebab-case.tsx`. Exception: React components export `PascalCase` from `kebab-case.tsx`.
- Server Actions: verbs — `create-invoice.ts` exports `createInvoice`.
- DB queries: nouns — `users.ts` exports `getUserById`, `insertUser`, `listUsersByTeam`.
- Booleans: `is*`, `has*`, `can*`. Never `*Flag`.
- Env vars: `SCREAMING_SNAKE_CASE`. Public ones MUST start with `NEXT_PUBLIC_`.
- Tables: plural snake_case (`users`, `team_members`). Columns: snake_case. PKs: `id` (text, ULID).
- IDs: ULIDs as TEXT, not autoincrement integers. Reason: safe to expose in URLs, sortable, no enumeration leaks.

---

## SQL & Migrations

- One migration = one file. Filename: `NNNN_short_description.sql`, zero-padded to 4 digits.
- Migrations are **append-only and immutable**. Once committed to `main`, never edit. Fix forward with a new migration.
- Every migration must be idempotent at the statement level (`CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`). Reason: turso branches occasionally re-run tail migrations.
- Run migrations with `pnpm db:migrate`. The script tracks applied filenames in a `_migrations` table.
- **No destructive changes without a two-step migration.** To drop a column: (1) ship code that stops reading it, (2) ship a migration that drops it. Never combine.
- Default to `NOT NULL` with a `DEFAULT`. Nullable columns must justify themselves in a comment.
- Foreign keys: always declared, always `ON DELETE` explicit (`CASCADE`, `SET NULL`, or `RESTRICT`).
- Enable `PRAGMA foreign_keys = ON;` in `db/client.ts`. Without it, SQLite silently ignores FK constraints.
- Money is stored as **integer cents**, never floats. Column type: `INTEGER NOT NULL`.
- Timestamps: `created_at INTEGER NOT NULL DEFAULT (unixepoch())`. Store unix seconds, format in the UI.
- Don't use SQLite's `DATETIME` or `BOOLEAN` types — they don't exist. Use `INTEGER` and convert in TS.

### Query patterns

- All DB access goes through `db/queries/*`. Routes and components never call `db.prepare(...)` directly.
- Each query function takes a `db` handle as its first arg in tests, defaults to the singleton in app code. Makes tests trivial without mocks.
- Reads return plain objects validated by a Zod schema in the same file. Writes take a Zod-parsed input.
- Use `prepare()` + statement caching. Don't re-prepare in a hot path.
- Transactions: `db.transaction(fn)`. Always wrap multi-statement writes.

---

## Auth Sessions

- Session cookies: `__session`, `HttpOnly`, `Secure`, `SameSite=Lax`, 30-day rolling.
- Session row in DB; cookie holds only the session id. No JWTs. Reason: JWT revocation is harder than a `DELETE`.
- The session guard lives in `app/(app)/layout.tsx`, not in `middleware.ts`. Middleware is for redirects only. Reason: middleware can't talk to better-sqlite3 (Edge runtime).
- Server Components/Actions read the session via `lib/auth.ts → getSession()`. Never pass session data through props from a Client Component.

---

## Server Actions

- One action per file in `app/<route>/_actions/<action>.ts`. Export a single named function.
- Every action: `"use server"` at the top, Zod-parse the input on line 1, return `{ ok: true, data }` or `{ ok: false, error }`. No throwing across the network boundary.
- Re-check authorization inside every action. Never trust that the caller "must be" authed because the route is gated — actions can be invoked from anywhere.
- Use `revalidatePath`/`revalidateTag` at the end of mutating actions. Don't manually refetch.

---

## Components

- Default to Server Components. A component becomes a Client Component only if it uses `useState`, `useEffect`, event handlers, or browser APIs.
- Push `"use client"` as far down the tree as possible. A 100-line client component that wraps the whole page is a code smell.
- Don't pass functions as props across the server/client boundary. Use Server Actions (`<form action={...}>`) instead.
- Suspense + streaming: wrap slow data fetches in `<Suspense>`. Don't block the shell on a slow query.
- Loading UI: prefer skeletons via `loading.tsx`, not spinners.

---

## Env Vars

- Every env var is declared and parsed in `lib/env.ts` with Zod. Importing `process.env.FOO` directly anywhere else is a lint error.
- Server-only secrets must NOT be prefixed `NEXT_PUBLIC_`. If you see `NEXT_PUBLIC_STRIPE_SECRET_KEY` in a PR, that's a security incident, not a typo.
- `.env.example` is committed and must list every key with a placeholder. `.env.local` is gitignored.

---

## Tests

- Unit tests sit next to the file: `users.ts` → `users.test.ts`.
- Test the DB layer against a real in-memory SQLite (`new Database(":memory:")` with the schema applied), not a mock. Reason: mocked SQL hides real bugs (FK violations, NOT NULL surprises).
- E2E tests in `tests/e2e/` hit a seeded SQLite file. Reset between runs.
- Don't test framework internals (Next router, Tailwind classes). Test behavior.
- A bug fix lands with a regression test in the same commit.

---

## Dev Commands

```bash
pnpm install
pnpm dev                  # next dev on :3000
pnpm db:migrate           # apply pending migrations to local SQLite
pnpm db:reset             # drop the local SQLite file and re-migrate (DEV ONLY)
pnpm db:seed              # insert demo data
pnpm typecheck            # tsc --noEmit
pnpm lint                 # eslint
pnpm test                 # vitest
pnpm test:e2e             # playwright
pnpm build                # next build — must pass before merging
```

Before committing: `pnpm typecheck && pnpm lint && pnpm test`. If you skipped any of these, say so in the PR.

---

## What We Don't Do (and Why)

- **No ORMs.** SQL is the API. Prisma's migration model and SQLite are a poor fit; Drizzle adds a layer we don't need at this scale.
- **No NextAuth.** Its assumptions about the data model conflict with hand-rolled SQLite schemas, and the cookie flow is harder to audit than 30 lines of our own code.
- **No `pages/` router.** Mixing routers fragments data fetching and middleware. Pick one; we picked App Router.
- **No CSS-in-JS.** Runtime cost, RSC friction, no upside over Tailwind for our component scope.
- **No `useEffect` for data fetching.** That's what Server Components and Server Actions are for. `useEffect` is for subscribing to non-React systems.
- **No global stores (Zustand/Redux) by default.** URL state, Server Components, and React Context cover 95% of cases. Add a store only when you've justified it in a PR description.
- **No barrel files (`index.ts` re-exports).** They break tree-shaking and slow `tsc`. Import from the source file.
- **No "utility" dumping ground.** `lib/utils.ts` is for genuinely generic helpers. Feature logic lives with the feature.
- **No `any`, no `as` casts** except at parse boundaries (Zod, `JSON.parse`, third-party SDK responses) — and even then, prefer `z.parse`.
- **No commented-out code.** Delete it; git remembers.
- **No `console.log` in committed code.** Use `lib/logger.ts` (pino in prod, console in dev).
- **No SQLite in serverless write paths.** `better-sqlite3` is for local dev and ops scripts. Prod writes go through libSQL/Turso. Reason: serverless functions can't share a file-backed DB.
- **No long-running work in route handlers.** Offload to a queue (we use a SQLite-backed `jobs` table polled by a cron worker) or to a webhook handler with idempotency.
- **No webhook handler without idempotency.** Every webhook has a `provider_event_id` UNIQUE column. Replays are no-ops.

---

## When in Doubt

1. Mirror the closest existing example in the codebase.
2. Prefer fewer files and less indirection.
3. If a rule above blocks you, the rule is probably right — but if you're sure it's wrong, propose the change in the PR description rather than silently breaking it.
