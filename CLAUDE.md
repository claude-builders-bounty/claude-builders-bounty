# CLAUDE.md — Project Context for Claude Code

> This file is the single source of truth for an AI agent working on this
> codebase. If a rule here conflicts with a local convention, this file
> wins. If it conflicts with the user's explicit instruction, the user wins.
> Keep it short, opinionated, and unambiguous.

## 1. Stack & Versions

- **Framework:** Next.js 15 App Router (NOT the Pages router).
- **Language:** TypeScript 5.x, strict mode on. `strict: true`,
  `noUncheckedIndexedAccess: true`, `exactOptionalPropertyTypes: false`.
- **Database:** SQLite via `better-sqlite3` (synchronous, single-file).
  If deployed to Turso, swap the driver but keep the same query API shape.
- **ORM / query layer:** raw SQL through a thin `db/` module. No Prisma,
  no Drizzle. Reason: a SaaS with SQLite doesn't need a sync engine; a
  single `prepare`d-statement cache is enough.
- **Migrations:** hand-written SQL files in `db/migrations/`, numbered
  `NNN_short_name.sql`. No migration tooling (no `umzug`, no `knex`).
- **Auth:** `iron-session` for cookie sessions, `bcrypt` for hashing.
- **Styling:** Tailwind CSS, no CSS-in-JS, no CSS modules.
- **Forms / data:** `react-hook-form` + `zod` for validation.
- **Node / runtime:** Node 20 LTS, `output: "standalone"` for deploys.

## 2. Folder Structure

```
app/                    # Next.js App Router
  (marketing)/          # Public marketing pages (no auth)
  (app)/                # Authenticated app routes
    (auth)/            # Login / signup layouts
    dashboard/         # Main app surface
    billing/
  api/                  # Route handlers (app/api/...)
components/             # React components, by feature folder
  ui/                   # Dumb presentational primitives
  <feature>/           # Feature-scoped components
db/
  index.ts              # Singleton connection + prepared-statement cache
  migrations/           # NNN_name.sql, forward-only
  seed.sql             # Dev seed data
lib/                    # Framework-agnostic utilities
  crypto.ts             # Password hashing, token helpers
  validators.ts         # zod schemas (shared by server + client)
  env.ts                # Runtime env validation (fail fast)
middleware.ts           # Next.js middleware (auth guard, rate limit)
scripts/                # One-shot node scripts (migrate, seed)
tests/                  # Vitest + @testing-library/react
types/                  # Shared TS types / .d.ts
```

**Rules**
- One route = one folder under `app/`. A folder is a route only if it has
  a `page.tsx` (or `layout.tsx` / `route.ts` for API).
- Feature components live under `components/<feature>/` and import only
  from `components/ui/` and `lib/` — never from sibling features directly.
  Cross-feature data flows through a `lib/` function, not a component
  import.
- Server Components by default; add `"use client"` only when you need
  interactivity (state, events, browser APIs).
- No barrel files (`index.ts` that re-exports everything). Import by
  path, so dead code is visible and tree-shakable.

## 3. Naming Conventions

| Thing | Pattern | Example |
|---|---|---|
| React component | `PascalCase.tsx` | `BillingPortal.tsx` |
| Server-only file | camelCase, suffix `.server.ts` | `invoices.server.ts` |
| API route handler | `route.ts` inside `app/api/...` | `app/api/invoices/route.ts` |
| Zod schema | `PascalCase` + `Schema` | `CreateInvoiceSchema` |
| DB table | snake_case, plural | `invoice_items` |
| SQL migration | `NNN_short_desc.sql` | `014_add_user_mfa.sql` |
| Test file | mirrors source name + `.test.ts(x)` | `BillingPortal.test.tsx` |
| Constant export | `SCREAMING_SNAKE_CASE` | `MAX_INVOICE_ITEMS` |
| Env var read | one import from `lib/env.ts` | `env.STRIPE_KEY` |

- Files: `camelCase` for `.ts`, `PascalCase` for `.tsx`.
- Route params: read with `useParams` / route context, typed via the
  `params` generic — never `as any`.
- A component that renders a list of items gets a named
  `<Item>Row` / `<Item>Card` child, not an inline map of divs.

## 4. DB & Migration Rules

- **All SQL is written as named, prepared statements** in `db/index.ts`.
  No string concatenation of user input. `better-sqlite3` is
  synchronous: do NOT wrap in `async`/`await`; the driver is sync on
  purpose.
- Every new table ships with:
  - `id TEXT PRIMARY KEY` (ULID, not autoincrement — sortable, no
    collision, 26 chars).
  - `created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))`.
  - `updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))`.
- **Migrations are forward-only and immutable.** Never edit a shipped
  migration. To change history, write `NNN+1_fix_prev.sql`.
- A migration must be idempotent-safe: re-running it on a fresh DB must
  succeed. Use `IF NOT EXISTS` where practical.
- Seed data is split into `db/seed.sql` (dev-only, not auto-run in prod).
- Transactions: one `db.transaction(() => { ... })` block per business
  operation that touches >1 table. Never mix `COMMIT` into individual
  statements.
- The app validates env (database path, WAL mode) on boot in
  `lib/env.ts`; a misconfigured prod boot must fail loud, not lazily.
- Enable WAL mode once at connection time. Do not toggle journal mode
  at runtime.

## 5. Component Patterns

- **Server-first:** render data in a Server Component; pass *serializable
  props* to a Client component. Do not pass a `better-sqlite3`
  statement or a live DB handle across the Server/Client boundary.
- **Co-locate styles** with Tailwind utility classes. No separate
  `.module.css`. A component that needs >3 utility lines gets extracted
  to a `components/ui/` primitive.
- **Forms:** every form has a zod schema in `lib/validators.ts`,
  `react-hook-form` resolver, and the schema is imported on both the
  client (for validation) and the API route (for re-validation). One
  schema, two uses.
- **API routes** return `Response.json(...)` with an envelope
  `{ data }` on success and `{ error: { code, message } }` on failure.
  Never leak a raw stack trace or a `SQLITE_*` error code to the client.
- **Errors:** throw typed errors from `lib/errors.ts`
  (`NotFoundError`, `ConflictError`, `UnauthorizedError`). API routes
  catch and map to a status code + the envelope. No `catch (e) {
  console.log }` that swallows.
- **No default exports** for components or route handlers; use named
  exports so refactors are findable. (Next.js route files do export
  named `GET`/`POST` functions.)

## 6. Dev Commands

```bash
pnpm dev            # dev server, hot reload
pnpm build          # production build
pnpm test           # vitest run (CI mode)
pnpm test:watch     # vitest watch
pnpm lint           # eslint + tsc --noEmit
pnpm db:migrate     # apply db/migrations/ in order
pnpm db:seed        # load db/seed.sql (dev only)
pnpm db:studio      # open better-sqlite3 inspector
```

- `pnpm db:migrate` is the ONLY way to advance the schema. No manual
  `ALTER TABLE` in a commit.
- Run `pnpm lint` and `pnpm test` locally before pushing. CI runs the
  same two plus a migration dry-run on a clean DB.

## 7. Anti-Patterns (what we don't do, and why)

- **No `any` / `@ts-ignore`.** If a type is wrong, fix the type.
  Reason: with SQLite the data model is small enough that a leak of `any`
  becomes a real bug at query time.
- **No client-side fetch of our own API.** Call a Server Action or a
  function in `lib/` directly. Reason: same origin, same process —
  JSON-encoding a request to ourselves is waste.
- **No global state libraries** (Redux / Zustand). React Context +
  Server Actions cover a SaaS at this scale. Reason: fewer moving parts,
  and state that touches the DB must be re-validated on the server anyway.
- **No ORM codegen.** Hand-written SQL + zod. Reason: codegen drifts
  from the schema; a hand-written prepared statement is honest about what
  it queries.
- **No `console.log` in shipped code.** Use a structured logger
  (`pino`) with request ids. Reason: log lines without correlation ids
  are unreadable at 3am.
- **No `useEffect` for data fetching.** Fetch in a Server Component or a
  Server Action. `useEffect`-fetch is a React anti-pattern and causes
  duplicate requests.
- **No `process.env` reads scattered through files.** All env access goes
  through `lib/env.ts`, which validates once at boot. Reason: a typo in
  an env name should crash at start, not return `undefined` at runtime.
- **No feature-flag without a migration.** A flag that changes DB shape
  needs a migration that adds the column; the flag only gates the
  *usage*, never the *existence*.

## 8. Testing Rules

- Unit: `lib/` and `db/` functions are tested with plain Vitest + a
  temp-file SQLite DB. No mocking of the DB itself.
- Component: `@testing-library/react`, render the real component, assert
  on behavior not implementation.
- API route: call the exported `GET`/`POST` handler directly with a
  constructed `Request`, assert on the JSON envelope. No supertest.
- A test that needs a specific DB shape gets a `beforeAll` that applies a
  subset of migrations into a `:memory:` DB. Never reuse the dev DB in
  tests.

## 9. For Claude Code Specifically

When you work in this repo:
- Read this file before proposing any change. If you're unsure, re-read
  §4 (DB rules) — they are the most common source of a bad patch.
- New feature = (1) zod schema in `lib/validators.ts`, (2) migration in
  `db/migrations/` if the data shape changes, (3) API route or Server
  Action, (4) client component, (5) test. In that order.
- Do not add dependencies without listing the reason in the PR
  description and updating this file's §1 if the stack changes.
- Keep this file under ~200 lines. If a rule grows long, split it into
  its own doc under `docs/` and link it here.
- After any DB migration, run `pnpm db:migrate` on a clean clone as the
  last verification step.
