# CLAUDE.md — Next.js 15 + SQLite SaaS

You are working in a SaaS app built on Next.js 15 (App Router) with SQLite through
`better-sqlite3`. This file is the house style. Follow it without asking; if a rule
here conflicts with what the user asks for, say so in one sentence and do what they ask.

## Stack & versions

| Thing | Version | Why pinned |
| --- | --- | --- |
| Next.js | 15.x, App Router only | Pages Router is gone in new code; mixing routers breaks route groups and layouts |
| React | 19 | Required by Next 15 |
| TypeScript | 5.x, `strict: true` | `strict` off means runtime `undefined` bugs that SQLite will happily store as NULL |
| SQLite driver | `better-sqlite3` | Synchronous API: no connection pool to leak, and every query is one call |
| Validation | `zod` | One schema for forms, server actions and route handlers — no third copy of the rules |
| Styling | Tailwind + `cn()` | No CSS-in-JS: RSC cannot ship runtime style injection |
| Tests | `vitest` + `node:test` for scripts | Vitest for components, plain node for scripts so `npm test` works with no browser |

Never introduce an ORM (Prisma, Drizzle) or a second DB driver into this repo. The
query layer is hand-written SQL in `src/db/` — that is a decision, not an oversight.

## Folder structure

```
app/
  (marketing)/          # public pages, no auth
  (app)/                # authenticated shell: sidebar + layouts
    dashboard/page.tsx
    settings/page.tsx
  api/
    webhooks/stripe/route.ts   # route handlers only for webhooks + file streams
  layout.tsx            # fonts, <html>, providers
src/
  db/
    client.ts           # the one better-sqlite3 instance (module singleton)
    schema.sql          # current full schema, generated from migrations
    migrations/         # 0001_init.sql, 0002_add_orgs.sql, ...
    migrate.mjs         # runner; also used by CI
  queries/              # one file per domain: users.ts, orgs.ts, invoices.ts
  actions/              # server actions ("use server"), one file per domain
  components/
    ui/                 # dumb primitives (Button, Input) — no data fetching
    features/           # feature components that may read from hooks/props
  lib/                  # pure helpers: money.ts, dates.ts, env.ts
tests/
```

Rules with reasons:

- **`src/queries/` holds every SQL string.** Components and actions never build SQL.
  Reason: one place to audit for missing `WHERE`, and one place to add indexes later.
- **`src/actions/` holds every mutation.** Route handlers are for things that are not
  a form submit (webhooks, streaming downloads). Reason: actions get the request
  context, CSRF handling and revalidation for free; route handlers do not.
- **`components/ui` may not import from `src/queries`.** Reason: primitives get reused
  inside client components, and a SQL import there drags `better-sqlite3` into the
  browser bundle — the build fails with a cryptic native-module error.
- **No `utils.ts`.** Name the file after the domain (`money.ts`, `dates.ts`). Reason:
  `utils.ts` becomes the junk drawer everyone imports and nobody owns.

## Naming conventions

- DB tables: `snake_case`, **plural** (`users`, `org_invites`). Columns: `snake_case`.
- TS types mirror rows with a `Row` suffix: `UserRow`, `OrgInviteRow`. API-shaped types
  drop it: `User`, `OrgInvite`. Reason: you can tell at a glance whether a value came
  straight from SQLite.
- Booleans in SQLite are `INTEGER` 0/1. Name them `is_*` / `has_*` and convert at the
  query boundary (`Boolean(row.is_active)`), never in components.
- Timestamps: `created_at`, `updated_at`, `deleted_at`, all `TEXT` ISO-8601 UTC
  (`strftime('%Y-%m-%dT%H:%M:%fZ','now')`). Reason: SQLite has no date type; ISO strings
  sort correctly and survive JSON round-trips.
- Server actions: `verbNoun` (`createInvoice`, `updateOrgName`). Never `handleX` — that
  hides whether it mutates.
- Files: `kebab-case.ts`; components `PascalCase.tsx`.

## SQL & migration conventions

**One migration = one file, append-only. Never edit a migration that has run anywhere.**

```
src/db/migrations/0007_add_invoice_status.sql
```

- Filename is `NNNN_snake_case.sql`, zero-padded to 4 digits. The runner applies files
  in lexicographic order and records them in `_migrations(name, applied_at)`.
- Every migration must be runnable twice without error (`CREATE TABLE IF NOT EXISTS`,
  `CREATE INDEX IF NOT EXISTS`). Reason: a crashed run must be resumable, and CI replays
  the whole chain.
- Destructive changes (drop column, rename) go through the three-step dance:
  add new → backfill → drop old in a *later* release. Reason: SQLite's `ALTER TABLE`
  is limited and a rolled-back deploy must still read the old shape.
- Enable WAL and foreign keys in `client.ts`, once, at startup:

```ts
// src/db/client.ts
import Database from "better-sqlite3";
export const db = new Database(process.env.DATABASE_PATH ?? "./data/app.db");
db.pragma("journal_mode = WAL");   // readers don't block the writer
db.pragma("foreign_keys = ON");    // SQLite ignores FKs unless you ask
db.pragma("busy_timeout = 5000");  // avoid SQLITE_BUSY under concurrent writes
```

- Parameter binding only. Template literals around user input are a bug, not a shortcut:

```ts
// yes
db.prepare("SELECT * FROM users WHERE email = ?").get(email);
// no — SQL injection, and better-sqlite3 will not warn you
db.prepare(`SELECT * FROM users WHERE email = '${email}'`).get();
```

- Every list query has an explicit `ORDER BY` and a `LIMIT`. Reason: SQLite row order is
  not guaranteed, and an unbounded list is a memory leak that only shows up in prod.
- Wrap multi-statement writes in `db.transaction(fn)`. Reason: better-sqlite3 is
  synchronous, so a partial write leaves the DB half-updated with no error surfaced.
- Add an index in the same migration as the column you will filter on. Reason: SQLite
  will not tell you it is doing a full scan.

## Component patterns

- Server Components by default. Add `"use client"` only when you need state, effects,
  or a browser API — and put the directive on the smallest leaf that needs it.
- Data fetching happens in the page/layout (async Server Component) or in a server
  action. Never in a `ui/` primitive.
- Forms use server actions with `useActionState` (React 19). Do not hand-roll
  `fetch("/api/...")` for mutations — you lose revalidation and progressive enhancement.
- Validate on the server, then again on the client only for UX. Zod schema lives in
  `src/actions/<domain>.ts` and is exported for the form to reuse.
- Loading states: `loading.tsx` per route segment; `<Suspense>` for a slow widget inside
  an otherwise fast page. Reason: a top-level spinner on a fast page feels slower than
  no spinner at all.

```ts
// src/actions/invoices.ts
"use server";
import { z } from "zod";
import { revalidatePath } from "next/cache";
import { db } from "@/db/client";

export const createInvoiceSchema = z.object({
  orgId: z.string().uuid(),
  amountCents: z.number().int().positive(),
});

export async function createInvoice(_prev: unknown, formData: FormData) {
  const parsed = createInvoiceSchema.safeParse({
    orgId: formData.get("orgId"),
    amountCents: Number(formData.get("amountCents")),
  });
  if (!parsed.success) return { ok: false, errors: parsed.error.flatten() };

  db.prepare(
    "INSERT INTO invoices (id, org_id, amount_cents, created_at) VALUES (?, ?, ?, ?)"
  ).run(crypto.randomUUID(), parsed.data.orgId, parsed.data.amountCents,
        new Date().toISOString());

  revalidatePath("/dashboard/invoices");
  return { ok: true };
}
```

## Dev commands

```bash
npm run dev            # next dev --turbopack
npm run build          # must pass before any PR
npm run db:migrate     # node src/db/migrate.mjs
npm run db:reset       # rm data/app.db && npm run db:migrate  (local only)
npm run test           # vitest run
npm run lint           # eslint + tsc --noEmit
```

`npm run build` is the gate. If it fails on a native module, the cause is almost always
a server-only import pulled into a client component — check `"use client"` boundaries
before touching bundler config.

## What we don't do (and why)

- **No ORM.** Hand-written SQL, because this app's hot paths are 3 joins and an
  aggregate; an ORM adds a compile step and hides the query plan.
- **No `SELECT *`.** Columns get reordered or added; explicit lists keep RSC payloads
  from silently growing.
- **No client-side secrets or `process.env` in components.** Only `NEXT_PUBLIC_*`
  reaches the browser; everything else is a server-only import that will throw.
- **No `any`.** Use `unknown` + a zod parse at the boundary. `any` in a row type is how
  NULLs become `undefined` three files later.
- **No barrel files (`index.ts` re-exports).** They defeat tree-shaking and create import
  cycles in RSC.
- **No `useEffect` for data fetching.** Server Components or actions; effects cause
  double-fetch in dev and waterfalls in prod.
- **No date math in components.** All date logic in `src/lib/dates.ts`, UTC in, UTC out.
- **No silent catches.** `catch {}` is banned; log with context or rethrow.

## Definition of done

A change is done when: `npm run lint` and `npm run build` pass, the migration runs on a
fresh DB (`npm run db:reset`), and any new table has an index on its foreign keys.
