# CLAUDE.md

Guidance for Claude Code (and any engineer) working in this repository: a
Next.js 15 App Router SaaS product backed by SQLite (better-sqlite3 locally,
Turso in production). Every rule below exists because of a specific failure
mode it prevents — read the "why" before you deviate.

## Stack

- **Framework:** Next.js 15, App Router only (no `pages/`).
- **Language:** TypeScript, strict mode. No `.js`/`.jsx` files in `src/`.
- **Database:** SQLite via `better-sqlite3` in development, [Turso](https://turso.tech)
  (libSQL) in production, both behind the same `db` client so query code never
  branches on environment.
- **Migrations:** hand-written, numbered SQL files — no ORM migration engine.
- **Styling:** Tailwind CSS.
- **Package manager:** pnpm. Never mix in npm/yarn lockfiles — a second
  lockfile silently pins different transitive versions per machine.

## Project Structure

```
src/
  app/                    # App Router routes only — no business logic here
    (marketing)/          # Route group: public pages, own layout
    (app)/                # Route group: authenticated app, own layout
    api/                  # Route handlers (webhooks, third-party callbacks only)
  server/
    db/
      client.ts           # Single DB client instance, imported everywhere
      migrations/          # 0001_*.sql, 0002_*.sql ... never edited after merge
      queries/             # One file per table/aggregate, hand-written SQL
    actions/               # Server Actions — the primary way the app writes data
    auth/
  components/
    ui/                    # Dumb, reusable, no data fetching
    <feature>/             # Feature components, may fetch/mutate via server/
  lib/                     # Framework-agnostic helpers (formatting, validation)
scripts/
  migrate.ts               # Applies pending migrations, dev and prod
  seed.ts                  # Dev-only fixture data
```

**Why this shape:** route handlers under `app/api` are reserved for things
that *must* be a plain HTTP endpoint (Stripe/webhook callbacks, OAuth
redirects). Everything else goes through Server Actions in `server/actions`.
Mixing "read data in a Server Component" and "write data in an API route"
across the same feature makes it impossible to trace a mutation from click to
row — one write path keeps the trace linear.

## Naming Conventions

- **Files:** kebab-case (`invoice-list.tsx`, `create-invoice.ts`). Next.js's
  own special files (`page.tsx`, `layout.tsx`, `route.ts`) keep their required
  names.
- **React components:** PascalCase, one component per file, file name matches
  the component (`InvoiceList` → `invoice-list.tsx`).
- **Server Actions:** verb-first (`createInvoice`, `revokeApiKey`), always
  `async function`, always exported with `"use server"` at the top of the
  file — not inline in a component. Inline actions can't be unit tested and
  silently re-bundle on every render.
- **DB tables:** snake_case, plural (`invoices`, `api_keys`).
- **DB columns:** snake_case (`created_at`, `stripe_customer_id`). The JS/TS
  layer maps these to camelCase at the query boundary (see below) — never let
  snake_case leak into component props.
- **Migration files:** `NNNN_short_description.sql`, zero-padded, strictly
  incrementing (`0007_add_invoices_due_date.sql`). The number is the sort key
  and the audit trail; never reuse or renumber one that has shipped.

## Database Rules

1. **All queries go through `server/db/queries/*`.** No `db.prepare(...)`
   calls inside components, actions, or route handlers. This is the only way
   to keep every query greppable and to swap the underlying driver
   (better-sqlite3 ↔ libSQL) without touching call sites.

2. **Every write happens inside a transaction, including single-statement
   writes that "obviously" don't need one.** SQLite's default is
   autocommit-per-statement; a Server Action that does two writes without an
   explicit transaction can leave a row half-updated if the second write
   throws. Wrap multi-step writes with the client's `transaction()` helper.

3. **Migrations are append-only.** Once a migration file is merged to `main`,
   it is immutable — fixing a mistake means writing a new migration, never
   editing the old one. Anyone who already ran the old migration has a
   different DB state than a fresh clone if you rewrite history.

4. **Every migration must have a working rollback path in practice, not code.**
   SQLite's `ALTER TABLE` can't drop columns or change constraints in place.
   To change a column, write the "create new table, copy data, drop old,
   rename" migration explicitly — never assume `ALTER TABLE ... DROP COLUMN`
   works across both better-sqlite3 and libSQL without testing it on both.

5. **`PRAGMA foreign_keys = ON` is set once, in the client, not per-query.**
   SQLite defaults foreign keys to *off*; forgetting this means orphaned rows
   pass silently in dev and only surface as a data-integrity bug in
   production.

6. **No `SELECT *` in checked-in query code.** Turso/libSQL and
   better-sqlite3 serialize rows slightly differently for some types
   (booleans, timestamps); naming columns explicitly is what makes the
   camelCase mapping layer safe to trust.

7. **IDs are generated in application code (`crypto.randomUUID()` or a
   ULID lib), not `AUTOINCREMENT`.** Turso is a distributed edge DB —
   autoincrement counters are a single point of write contention and don't
   survive branching/replica setups. Primary keys are `TEXT`, not `INTEGER`.

## Dev Commands

```bash
pnpm dev              # next dev, local better-sqlite3 file at ./local.db
pnpm db:migrate       # scripts/migrate.ts — applies pending migrations
pnpm db:seed          # scripts/seed.ts — dev fixtures, never run in prod
pnpm db:studio        # opens a local SQLite browser against ./local.db
pnpm typecheck        # tsc --noEmit — run before every commit
pnpm lint             # eslint, includes import-order and unused-exports rules
pnpm test             # vitest, unit + query-layer tests against a temp SQLite file
pnpm build            # next build — also runs typecheck as a build step
```

New migrations are picked up automatically by `pnpm db:migrate`; there is no
separate "generate migration" command because migrations are hand-written SQL,
not diffed from a schema file.

## Patterns to Follow

- **Server Components fetch data directly** by calling functions in
  `server/db/queries`, no client-side `fetch('/api/...')` for data the page
  already needs on first paint. This avoids a network round-trip the server
  didn't need to make.
- **Server Actions for all mutations**, called directly from forms
  (`<form action={createInvoice}>`) or from client components via a thin
  wrapper. This gets progressive enhancement and CSRF handling for free from
  Next.js instead of hand-rolling both in a `route.ts`.
- **Validate at the Server Action boundary with `zod`**, not in the
  component and not in the query function. One validation point per
  mutation keeps error messages consistent and keeps query functions trusting
  their inputs.
- **Optimistic UI via `useOptimistic`**, reverting on the Server Action's
  thrown error — don't hand-roll pending/error state with `useState` per
  form.
- **Environment access only through `lib/env.ts`**, a single `zod`-validated
  export. A missing `TURSO_AUTH_TOKEN` should fail at boot, not three
  requests into production traffic.
- **Feature flags / plan gating read from the DB row, not from env vars.**
  Env vars are per-deployment; SaaS entitlements are per-tenant.

## Anti-Patterns to Avoid

- **Don't fetch in a `useEffect` for data available at render time.** If a
  Server Component can read it, read it there — client-side fetching here
  only adds a loading spinner nobody asked for.
- **Don't put raw SQL in `app/api/*/route.ts`.** If you're reaching for a
  route handler to do a DB write, it should almost always be a Server Action
  instead; route handlers are for webhooks and OAuth callbacks only (see
  Project Structure above).
- **Don't use `better-sqlite3` APIs (synchronous calls) in code that also
  needs to run against Turso.** `better-sqlite3` is sync, libSQL is async —
  write every query as `async`/`await` even in the sync driver so the same
  code path runs unmodified in production.
- **Don't store money as `REAL`/float.** SQLite's floating point will produce
  rounding errors in aggregates. Store integer cents (`amount_cents INTEGER`).
- **Don't add a new npm dependency for something SQLite already does.** No
  separate cache layer, no separate queue library, for a single-region
  low-traffic SaaS app — SQLite handles it via a `jobs` table + polling, and
  it's one less moving part to operate.
