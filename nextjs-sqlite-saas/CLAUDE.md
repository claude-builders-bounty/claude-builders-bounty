# CLAUDE.md — Next.js 15 + SQLite SaaS

This file is the single source of truth for how code is written in this repo.
Read it fully before writing code. When something here conflicts with your
defaults, this file wins.

## 1. Stack & versions

| Layer | Choice | Why |
|---|---|---|
| Framework | Next.js 15 (`app/` router), React 19 | Server Components + Server Actions remove most client-side data plumbing |
| Language | TypeScript 5.6, `strict: true`, `noUncheckedIndexedAccess: true` | Bugs are cheaper to catch at compile time than in production |
| DB driver | `@libsql/client` (SQLite) | One driver works against a local file (`file:./data/app.db`) **and** Turso, so dev/prod never diverge |
| Query layer | Raw SQL in typed functions (`lib/db/queries/*`) | No ORM: the SQL you read is the SQL that runs. SQLite's feature set is the product |
| Validation | `zod` at every boundary (actions, route handlers, env) | Untrusted input is parsed once, then typed everywhere |
| Styling | Tailwind CSS v4 + `cn()` helper | No CSS-in-JS runtime, no naming debates |
| Auth | Session cookie (httpOnly, SameSite=Lax) + `lib/auth/session.ts` | No third-party dependency for the core security boundary |
| Tests | Vitest (unit/queries), Playwright (flows) | |
| Deploy | Vercel (app) + Turso (DB) | SQLite file does not survive serverless filesystem |

Do not add a dependency without writing the reason in the PR description.
A 40-line local helper beats a 400 KB package for anything used in one place.

## 2. Commands

```bash
npm run dev        # next dev, Turbopack
npm run build      # must pass before any PR
npm run typecheck  # tsc --noEmit
npm run lint       # eslint
npm run test       # vitest run
npm run db:generate -- add_users_table   # create db/migrations/0007_add_users_table.sql
npm run db:migrate                        # apply pending migrations
npm run db:seed                           # dev only, refuses to run when NODE_ENV=production
npm run db:reset                          # drop local file, migrate, seed (dev only)
```

Scripts live in `scripts/db/*.ts` and are run with `tsx`. Never run migration
logic inside `next build` — builds must be side-effect free.

## 3. Folder structure

```
app/
  (marketing)/page.tsx              # public pages, no auth
  (app)/dashboard/page.tsx          # authenticated shell, layout checks session
  (app)/dashboard/billing/page.tsx
  api/webhooks/stripe/route.ts      # only place raw HTTP handlers live
  api/health/route.ts
  layout.tsx  globals.css  error.tsx  not-found.tsx
components/
  ui/                               # dumb, reusable, no data access (Button, Input, Dialog)
  features/<feature>/               # feature-specific composition (InvoiceTable, InviteForm)
lib/
  db/client.ts                      # one client instance, WAL + pragmas
  db/schema.ts                      # generated types mirroring migrations
  db/queries/<entity>.ts            # ALL SQL lives here, nowhere else
  db/migrate.ts                     # migration runner
  auth/session.ts  auth/password.ts
  validation/<feature>.ts           # zod schemas shared by actions and forms
  env.ts                            # zod-parsed process.env
  utils.ts                          # cn(), formatCurrency(), formatDate()
db/
  migrations/0001_init.sql ...      # append-only, never edited after merge
  seed.ts
scripts/db/                         # migrate / seed / reset entrypoints
tests/
  unit/*.test.ts  e2e/*.spec.ts
```

Rules:

- A file that touches SQL lives under `lib/db/`. Components never import the client.
- `app/**/actions.ts` may only orchestrate: validate → call query → revalidate → return.
- Feature code that is used by one route stays next to that route; promote to
  `components/features/` only when a second consumer appears.

## 4. Naming conventions

- Files and folders: `kebab-case` (`invoice-table.tsx`, `reset-password/`).
- React components: `PascalCase`, one exported component per file, default export.
- Hooks: `useSomething` in `lib/hooks/use-something.ts`.
- Server Actions: verb-first camelCase (`createInvoice`, `inviteMember`), live in
  `actions.ts`, always `"use server"` at the top of the file.
- DB: tables `snake_case` **plural** (`invoices`), columns `snake_case` singular
  (`created_at`), indexes `idx_<table>_<columns>`, FKs `fk_<table>_<ref>`.
- Query functions: `getInvoiceById`, `listInvoicesByOrg`, `insertInvoice`,
  `updateInvoiceStatus` — the name states the shape of the result.
- Env vars: `SCREAMING_SNAKE_CASE`; anything readable by the browser is prefixed
  `NEXT_PUBLIC_` and is assumed public forever.

## 5. SQL & schema conventions

**Types** (SQLite has no real types; we enforce them by convention):

| Concept | Column type | Stored as |
|---|---|---|
| Primary key | `TEXT PRIMARY KEY` | `crypto.randomUUID()` — never autoincrement, IDs must not be enumerable |
| Timestamps | `TEXT NOT NULL` | ISO-8601 UTC (`2026-01-31T10:00:00.000Z`) |
| Booleans | `INTEGER NOT NULL DEFAULT 0` | `0` / `1` only |
| Money | `INTEGER NOT NULL` | minor units (cents); never `REAL` |
| Enums | `TEXT NOT NULL CHECK (status IN (...))` | explicit `CHECK`, not a lookup table |
| JSON blobs | `TEXT` | only for data the app never queries into |

**Every table** gets:
`id TEXT PRIMARY KEY`, `created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))`,
`updated_at TEXT NOT NULL` (written by the app on update), and `org_id TEXT NOT NULL REFERENCES organizations(id)` for multi-tenant data.

**Migrations**

1. One file per change: `db/migrations/NNNN_snake_case_description.sql`, zero-padded,
   sequential. Never reuse or renumber.
2. Migrations are append-only. A merged migration is immutable — fix it with a new one.
3. Never mix DDL and data backfill in the same file; backfills get their own migration.
4. SQLite cannot drop or alter most columns in place. The supported path is:
   create `<table>_new` → copy → drop old → rename. Write it out explicitly in the
   migration; do not hand-roll it at runtime.
5. Destructive changes (`DROP`, `DELETE` without `WHERE`) need `-- destructive`
   in the first line and a reviewer's approval.
6. New columns on tables with data must be nullable or have a `DEFAULT`.
7. Every foreign key needs an index. Every query pattern used by a list page needs
   a composite index covering its `WHERE` + `ORDER BY`.
8. `PRAGMA foreign_keys = ON`, `journal_mode = WAL`, `busy_timeout = 5000` are set in
   `lib/db/client.ts` for every connection. Never re-declare pragmas in migrations after `0001`.

Migration runner contract (`lib/db/migrate.ts`): reads `db/migrations/*.sql` sorted
by filename, keeps a `_migrations(name TEXT PRIMARY KEY, applied_at TEXT, checksum TEXT)`
table, applies each pending file atomically, and fails loudly if the checksum of an
already-applied file changed.

```ts
// Atomic + idempotent. Do NOT wrap migrations in execute("BEGIN")/execute("COMMIT"):
// @libsql/client does not give you a reliable session transaction that way.
await client.batch(
  [...splitStatements(sql).map((s) => ({ sql: s })),
   { sql: "INSERT INTO _migrations (name, checksum) VALUES (?, ?)", args: [file, checksum] }],
  "write", // one transaction
);
```

`splitStatements` strips `--` comments and splits on `;` at end of line. Migrations
therefore must not contain procedural blocks or semicolons inside string literals —
if you need one, put it in TypeScript, not in SQL.

**Queries**

- Parameterised only: `client.execute({ sql, args })`. String interpolation into SQL
  is a bug, including for `ORDER BY` — map user input to an allow-listed column name.
- `SELECT` explicit columns; no `SELECT *` outside `EXPLAIN` and ad-hoc debugging.
- Multi-tenant reads always filter by `org_id` **inside the query**, not after it.
- Writes that must be atomic go through `client.batch([...], "write")`.

## 6. Component & data patterns

- **Server Components are the default.** `"use client"` is a deliberate downgrade:
  add it to the smallest leaf that needs state, effects or browser APIs, and say why
  in the PR.
- **No data fetching in `useEffect`.** Read in a Server Component, mutate through a
  Server Action. There is no internal `fetch('/api/...')` from the client.
- **Route handlers** exist only for webhooks, third-party callbacks, files, and
  health checks. Everything else is an action.
- **Actions validate, then act.** Shape:

  ```ts
  "use server";
  export async function createInvoice(_prev: ActionState, formData: FormData): Promise<ActionState> {
    const session = await requireSession();               // authn
    const parsed = createInvoiceSchema.safeParse(Object.fromEntries(formData));
    if (!parsed.success) return { ok: false, fieldErrors: parsed.error.flatten().fieldErrors };
    const invoice = await insertInvoice({ ...parsed.data, orgId: session.orgId }); // authz inside query
    revalidatePath("/dashboard/invoices");
    return { ok: true, data: invoice };
  }
  ```

  `ActionState = { ok: true; data?: unknown } | { ok: false; error?: string; fieldErrors?: Record<string, string[]> }`.
  Actions never throw for expected failures and never return raw DB errors to the client.
- **Forms** use `useActionState` + progressive enhancement; the submit button reads
  `pending` from the action state, never from local `useState`.
- **Authz is checked in the data layer.** `middleware.ts` only redirects anonymous
  users away from `/(app)`; it is not a security boundary. Every query that writes
  scopes by `org_id` and every page re-checks membership.
- **Errors**: `error.tsx` per route segment for recoverable failures, `not-found.tsx`
  for missing records. Log with the request id, never with PII.
- **Loading** is expressed with `loading.tsx` / `<Suspense>` around the slow part,
  not with a page-level spinner that replaces the whole layout.
- **Server → client props must be serialisable.** No functions, no `Date` instances
  from the DB (they are strings), no class instances.

## 7. Security baseline (non-negotiable)

- Secrets only in `lib/env.ts`, parsed with zod at boot; the build fails on a missing var.
- `NEXT_PUBLIC_*` values are public. No tokens, no keys, no internal URLs.
- Session cookie: `httpOnly`, `secure` in production, `sameSite: "lax"`, 30-day sliding expiry, rotated on privilege change.
- Passwords: `argon2id` (or `bcrypt` cost ≥ 12). Never store or log plaintext.
- Every mutation re-checks the session; never trust a hidden `orgId` form field.
- Rate-limit auth endpoints and any action that sends email or costs money.
- No `dangerouslySetInnerHTML` with user content. Markdown is rendered with a
  sanitising renderer or not at all.

## 8. What we don't do (and why)

| Not allowed | Reason |
|---|---|
| Prisma / Drizzle / any ORM | The SQL is the contract; ORMs hide N+1s and make SQLite migrations a second language |
| `any`, `as unknown as`, `@ts-ignore` | They convert compile errors into production incidents. Fix the type or narrow it |
| `useEffect` for data loading | Double-fetch in StrictMode, waterfalls, no SSR. Use Server Components |
| Client-side auth checks as security | The client is attacker-controlled; authz lives in the query |
| Global state library (Redux/Zustand) | Server state belongs to the server; UI state is local or in the URL |
| `SELECT *` in app queries | A new column silently changes payload shape and leaks fields |
| Autoincrement integer PKs | Enumerable IDs leak volume and invite IDOR probing |
| `REAL` for money | Binary floats lose cents |
| Business logic in components | Untestable without a DOM, unreusable from actions |
| `console.log` in committed code | Use the logger; logs are queryable, console is not |
| Deleting or editing an applied migration | Other environments already ran it; the schema diverges forever |
| Running migrations during `next build` | Builds are cached and parallel; they would race |
| `npm install <pkg>` without a stated reason | Dependency debt is permanent, helpers are cheap |
| Long `await` chains that could be `Promise.all` | Latency multiplies |
| Mutations in `GET` route handlers | Crawlers and prefetchers will trigger them |

## 9. Recipes

**Add a table**
1. `npm run db:generate -- add_invoices` → edit the SQL (columns, `CHECK`s, FKs, indexes).
2. `npm run db:migrate` locally.
3. Add the row type to `lib/db/schema.ts` and query functions to `lib/db/queries/invoices.ts`.
4. Add a Vitest test that inserts and reads a row against an in-memory DB.

**Add a page**
1. Create `app/(app)/<segment>/page.tsx` as an async Server Component.
2. `const session = await requireSession()` at the top; pass only serialisable props down.
3. Add `loading.tsx` if the data call is slow; add `error.tsx` if it can fail.

**Add a mutation**
1. zod schema in `lib/validation/<feature>.ts`.
2. Query function in `lib/db/queries/` (transaction if it touches >1 table).
3. Action in `app/(app)/<segment>/actions.ts`: `requireSession` → parse → query → `revalidatePath`.
4. Form with `useActionState`; render `fieldErrors` next to inputs.

**Add an index**
Only with the query that needs it in the PR description. Confirm with
`EXPLAIN QUERY PLAN` that it is used; unused indexes slow down writes.

## 10. Definition of done

- `npm run typecheck && npm run lint && npm run test && npm run build` all pass.
- New behaviour has a test at the lowest level that can prove it (query test > action test > e2e).
- No new `any`, no new `console.log`, no new client component without a stated reason.
- Migration is additive, named correctly, and applied locally against a copy of prod-shaped data.
- The PR description states what changed, why, and how it was verified.
