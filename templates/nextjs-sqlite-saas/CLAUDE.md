# CLAUDE.md — Next.js 15 + SQLite SaaS

Operating manual for this codebase. Read it before the first edit; it overrides generic
Next.js advice. Every rule carries its reason so you can tell when it does not apply.

---

## Stack — exact versions, no drift

| Piece | Choice |
|---|---|
| Runtime | Node 22 LTS |
| Framework | Next.js 15, **App Router** |
| React | 19 (Server Components by default) |
| Language | TypeScript 5, `strict: true`, `noUncheckedIndexedAccess: true` |
| Styling | Tailwind CSS v4 |
| Database | **better-sqlite3** (synchronous, in-process) |
| Migrations | hand-rolled numbered `.sql` files + one runner |
| Validation | Zod |
| Auth | cookie session in `sessions` table, httpOnly, SameSite=Lax |
| Tests | `node --test` for logic, Playwright for the 3 critical flows |

**No ORM.** `better-sqlite3` already returns rows; an ORM adds a second language between the
code and the schema and hides the query plan. — because SQLite queries are cheap to read and
the ORM abstraction leaks the moment you need an index hint or a window function.

**No `better-sqlite3` alternative is needed.** Do not swap to Turso/libSQL unless the deployment
target has no persistent disk — because the synchronous API removes async waterfalls, and that is
the single biggest source of slow pages here.

---

## Folder structure

```
app/
  (marketing)/page.tsx           # public, no auth check
  (app)/layout.tsx               # authed pages; this layout enforces the session
  (app)/page.tsx
  api/stripe/webhook/route.ts
  layout.tsx
components/
  ui/button.tsx                  # dumb primitives: Button, Input, Dialog
  invoices/invoice-list.tsx      # feature components, colocated with their page
db/
  client.ts                      # the one and only database handle
  migrate.ts                     # the migration runner
  reset.mjs                      # dev-only: drop the db file
  new.mjs                        # scaffold the next numbered migration
  migrations/0001_init.sql       # never renamed, never edited
  queries/users.ts               # one file per entity
  queries/invoices.ts
lib/
  env.ts                         # env parsing + validation, the only place process.env is read
  auth.ts                        # session read/write, the only place cookies are touched
  result.ts                      # Result<T, E> helpers
tests/
  unit/result.test.ts            # node --test
  e2e/smoke.spec.ts              # playwright
data/app.db                      # created at runtime; gitignored
```

**Route groups `(marketing)` / `(app)`** — because the auth check belongs in one layout, not
repeated in forty pages, and a marketing page should not pay for a session lookup.

**`db/queries/<entity>.ts`** — because a query called from three route handlers should be
written once; scattering `db.prepare(...)` inline guarantees three subtly different versions.

---

## Dev commands

```bash
npm run dev                 # next dev
npm run build               # production build — the gate that must pass before any PR
npm run typecheck           # tsc --noEmit
npm run lint                # eslint
npm run test                # node --test tests/unit
npm run test:e2e            # playwright
npm run db:migrate          # apply pending migrations
npm run db:reset            # delete data/app.db, re-migrate, seed — dev only
npm run db:new -- add_x     # create db/migrations/NNNN_add_x.sql
```

**Always run `npm run typecheck` and `npm run build` after a change** — because `tsc` catches the
type break and `next build` catches the "server component imports a client hook" error that no
test will.

---

## Naming conventions

| Thing | Convention | Example |
|---|---|---|
| Files & folders | `kebab-case` | `invoice-list.tsx` |
| Components | `PascalCase`, named export | `export function InvoiceList()` |
| Hooks | `use-*.ts`, `useX` | `use-invoice-filter.ts` |
| Server actions | colocated `actions.ts`, `verbNoun` | `createInvoice` |
| DB tables | `snake_case`, plural | `invoices`, `invoice_items` |
| DB columns | `snake_case` | `created_at`, `account_id` |
| Booleans | `is_` / `has_` prefix | `is_active` |
| Route params | `[invoiceId]`, never `[id]` | `/invoices/[invoiceId]` |

**Tables plural, columns singular** — because `SELECT * FROM invoice` and `invoice.id` read
inconsistently, and consistency is what lets you guess correctly.

**`[invoiceId]` over `[id]`** — because a nested route has two ids and `params.id` forces you to
scroll up to learn which one you have.

**Named exports for components, default exports only for `page.tsx` / `layout.tsx`** — because
Next requires default exports for those files and nothing else; one rule per file type.

---

## Database rules

### One handle, opened once

```ts
// db/client.ts
import Database from "better-sqlite3";
import { env } from "@/lib/env";

const g = globalThis as { __db?: Database.Database };

export const db =
  g.__db ??
  (() => {
    const d = new Database(env.DATABASE_PATH);
    d.pragma("journal_mode = WAL");   // concurrent readers alongside one writer
    d.pragma("foreign_keys = ON");    // SQLite has FKs off by default
    d.pragma("busy_timeout = 5000");  // wait instead of throwing SQLITE_BUSY
    return d;
  })();

if (process.env.NODE_ENV !== "production") g.__db = db; // survive HMR
```

**Cache on `globalThis`** — because Next reloads modules in dev and every reload would otherwise
open another file handle until SQLite refuses.

**`WAL` + `busy_timeout`** — because SQLite allows one writer; without these, a concurrent request
gets `SQLITE_BUSY` instead of waiting its turn.

`foreign_keys = ON` is per-connection and off by default — because a schema that looks referential
and is not is worse than one that admits it.

**Scripts run through `tsx`, never bare `node`** — because `node` reads neither `tsconfig` path
aliases nor extensionless relative imports, so `@/lib/env` in a script fails only when you run it.

**Never run a script that opens the database without `--env-file-if-exists=.env`** — because
`lib/env.ts` refuses to start on a missing `SESSION_SECRET`, and the failure looks like a database
bug rather than a config one.

### Every statement is prepared, never interpolated

```ts
const byId = db.prepare("SELECT id, email, is_active FROM users WHERE id = ?");
export const getUser = (id: string) => byId.get(id) as User | undefined;
```

**`?` placeholders only** — because `WHERE email = '${email}'` breaks on an apostrophe in a name
and is an injection surface.

**List columns explicitly, never `SELECT *`** — because a migration that adds a `password_hash`
column silently ships it to the client if you used `*`.

### Migrations

- Filename `NNNN_snake_case.sql`, zero-padded and monotonic (`0001_init.sql`) — because the runner
  applies them in lexical order, so a name that sorts wrong runs wrong.
- **Never edit a shipped migration** — because a live database has already run it; add
  `0007_fix_x.sql` instead.
- One logical change per file — because it keeps the migration a reviewable unit and a failure
  traceable to one concept.
- **Every migration is idempotent where that is cheap** (`CREATE TABLE IF NOT EXISTS`,
  `CREATE INDEX IF NOT EXISTS`) — because a half-applied environment is the normal state after an
  incident, and re-running must be safe.
- **Destructive changes ship in two steps**: add the new column, backfill, then drop the old one in
  a later migration — because a single migration that drops a column has no rollback.
- SQLite's `ALTER TABLE` is limited: to change a column type, create `*_new`, `INSERT … SELECT`,
  drop, rename — in one transaction, because a half-renamed table is unreadable by either shape.
- Wrap multi-statement migrations in `BEGIN; … COMMIT;` — because SQLite stops at the first failing
  statement and would otherwise leave the rest unapplied.
- Add the index in the same migration as the column it covers — because that is the only moment
  the intent is unambiguous.
- **A migration file is plain SQL: no `BEGIN`, no `COMMIT`** — because the runner already opens a
  transaction around the file *and* its bookkeeping row, and a nested `BEGIN` throws
  `cannot start a transaction within a transaction`.

The runner (already in `db/migrate.ts`, extend rather than replace):

```ts
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { db } from "./client";

db.exec("CREATE TABLE IF NOT EXISTS _migrations (name TEXT PRIMARY KEY, applied_at TEXT NOT NULL)");

const applied = new Set(db.prepare("SELECT name FROM _migrations").all().map((r: any) => r.name));
const dir = join(process.cwd(), "db", "migrations");
const pending = readdirSync(dir).filter((f) => f.endsWith(".sql") && !applied.has(f)).sort();

for (const file of pending) {
  const sql = readFileSync(join(dir, file), "utf8");
  db.transaction(() => {
    db.exec(sql);
    db.prepare("INSERT INTO _migrations (name, applied_at) VALUES (?, ?)").run(file, new Date().toISOString());
  })();
  console.log(`applied ${file}`);
}
console.log(pending.length ? `${pending.length} applied` : "up to date");
```

**Each migration runs inside a transaction with its bookkeeping row** — because a migration that
half-applies is the one state with no automatic recovery.

### Queries live in `db/queries/`, typed at the boundary

```ts
export type User = { id: string; email: string; is_active: 0 | 1 };
```

**Booleans are `0 | 1`, not `boolean`** — because SQLite stores integers, and a cast that lies is
where `if (user.is_active)` starts passing for `"0"`.

**Multi-write operations use `db.transaction`** — because two sequential writes that must agree
become inconsistent the moment a request fails between them.

---

## Component patterns

- **Server Component by default. `"use client"` is opt-in and justified in a comment.** — because a
  client component ships its whole import graph to the browser, and the default should be cheap.
- **Data is read in the Server Component or the route handler, never in the client.** — because a
  client fetch adds a request waterfall and a loading state you did not need.
- **`useEffect` + `fetch` is a smell; `loading.tsx` and Server Components are the answer.** — because
  the browser round trip is the slowest hop available.
- **Mutations go through Server Actions in the nearest `actions.ts`.** — because they are typed
  end-to-end and avoid a hand-written API route plus a hand-written client fetch.
- **Validate every Action input with Zod at the top of the function.** — because `FormData` is
  `any`-typed at runtime no matter what TypeScript believes.
- **Every Action returns `Result<T, E>` or calls `redirect()`; never throws for a user-facing error.**
  — because a thrown error in production becomes a generic 500 page instead of a field message.
- **Route handlers (`route.ts`) only for webhooks, file downloads, and non-JSON responses.** —
  because anything a Server Component can call directly does not need a public URL.
- **Auth is checked in `app/(app)/layout.tsx`; `lib/auth.ts` is the only module that reads cookies.**
  — because per-page checks drift, and a forgotten one is an open page.
- **`"use cache"` / `revalidatePath` immediately after every successful write.** — because a
  mutation that leaves a stale cache looks like a bug in the code that reads it.
- **Props are explicit, not `{...rest}` spread.** — because a spread defeats the excess-property
  check that is the entire point of a typed prop.

---

## What we don't do, and why

| Never | Because |
|---|---|
| `any` outside a cast with a comment | it disables every check downstream, not just here |
| `as` casts on `fetch`/DB JSON | the shape is unverified; parse with Zod instead |
| Prisma / Drizzle / an ORM | a second schema language to keep in sync with the SQL that actually runs |
| `SELECT *` | columns change; the payload does not need to |
| String-interpolated SQL | one apostrophe in a name breaks it |
| `useEffect` data fetching | the waterfall that `loading.tsx` already removes |
| Client components importing `db/` | `better-sqlite3` is native and cannot bundle for the browser |
| Barrel `index.ts` re-exports | it defeats tree-shaking and creates import cycles |
| `process.env.X` outside `lib/env.ts` | an unset var fails at the use site, hours later, in prod |
| A new dependency for a 20-line helper | supply-chain surface and a lockfile diff for every reader |
| `export default` on a `lib/` function | renames stop being refactors |
| Editing a shipped migration | the database has already run it |
| `console.log` left in a commit | structured logs belong in one place; `console.log` is the diff noise |
| `!important` in Tailwind | specificity fights are a symptom of an unsorted class list |
| A `useState` mirror of server data | two sources of truth diverge on the first mutation |
| `npm install -g` | global and local versions drift per machine |

---

## Definition of done

A change is finished when **all** of these pass, run from the repo root:

```bash
npm run typecheck && npm run lint && npm run test && npm run build
```

Plus, according to what changed:

- schema → a new numbered migration and `npm run db:reset` succeeds from empty
- a user-facing flow → a Playwright test in `tests/e2e/`
- env var → it is added to `lib/env.ts` **and** `.env.example`

**Report the actual command output.** "Should work" is not done; a green `next build` is.

---

## Working with Claude in this repo

- **Read the file before editing it.** — because half the bugs here come from an assumed shape.
- **Match the surrounding style even where you would choose differently.** — because a diff that
  reformats is unreviewable.
- **Small, single-purpose diffs.** — because a mixed refactor + behaviour change cannot be reverted
  cleanly.
- **State the plan before touching more than three files.** — because a two-line course correction
  is cheaper than a wrong 500-line diff.
- **When the rules above conflict with a generic Next.js tutorial, this file wins.** — because it
  was written against this codebase.
