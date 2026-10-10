# CLAUDE.md

Guidance for Claude Code when working in this repository. **Read this file in full
before making changes.** The rules below are opinionated on purpose — every one of
them exists because the opposite caused a real bug, outage, or a slow PR. When a
rule looks arbitrary, the *Why* line explains it. Follow the rules; don't "improve"
them in a drive-by.

---

## 1. Stack & versions

Pin these. Don't upgrade a major version as part of unrelated work.

| Concern        | Choice                                             | Why |
|----------------|----------------------------------------------------|-----|
| Framework      | Next.js 15 (App Router) + React 19                 | Server Components remove most client data-fetching code. |
| Language       | TypeScript 5.x, `"strict": true`                   | `strict` catches the null/undefined bugs that dominate SaaS incidents. |
| Runtime        | **Node.js 20 LTS** (never Edge for the app runtime) | `better-sqlite3` is a native module — it cannot run on Vercel/Edge. |
| Database       | SQLite via **better-sqlite3** (dev + single-node prod) or **Turso/libSQL** (multi-region) | One dialect, zero-server local dev. |
| ORM / query    | **Drizzle ORM** + `drizzle-kit`                    | Typed SQL, real migrations, no hidden N+1 like ActiveRecord-style ORMs. |
| Validation     | **Zod** at every boundary                          | One schema drives form + server + DB-shape checks. |
| Forms          | React Hook Form + `@hookform/resolvers/zod`        | Client UX; the server action re-validates with the same schema. |
| UI             | Tailwind CSS + **shadcn/ui** primitives            | Own the component source; no locked-in component library. |
| Auth           | **Auth.js (NextAuth v5)** credentials provider      | Session in a signed cookie; no custom JWT code to get wrong. |
| Payments       | Stripe (Checkout + webhooks)                       | Never touch card data ourselves. |
| Package manager| **pnpm** (version pinned in `packageManager`)      | Strict node_modules prevents phantom deps. |
| Tests          | **Vitest** (unit/integration) + Playwright (e2e)   | Fast, native ESM, in-memory SQLite for integration. |

> **Why Node runtime, not Edge:** `better-sqlite3` is synchronous and native. If you
> need Edge, switch the whole DB layer to Turso's HTTP client — don't mix.

---

## 2. Dev commands

```bash
pnpm install            # install (never npm/yarn — lockfile is pnpm)

pnpm dev                # next dev on :3000
pnpm build              # production build
pnpm start              # run the production build
pnpm lint               # eslint
pnpm typecheck          # tsc --noEmit
pnpm test               # vitest run
pnpm test:watch         # vitest

pnpm db:generate        # drizzle-kit generate  -> new SQL migration
pnpm db:migrate         # apply pending migrations
pnpm db:seed            # seed local data
pnpm db:studio          # drizzle-kit studio
pnpm db:reset           # drop local db, migrate, seed
```

**Before you say a task is done, all of these must pass:** `pnpm typecheck`,
`pnpm lint`, `pnpm test`, `pnpm build`.

**Required environment (`.env.local`, git-ignored; `.env.example` is committed):**

```
DATABASE_URL=file:./local.db      # or libsql://... for Turso
AUTH_SECRET=<openssl rand -base64 32>
AUTH_URL=http://localhost:3000
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

Only `NEXT_PUBLIC_*` may appear in client code. `lib/env.ts` validates the rest at
boot with Zod, so a missing var fails fast at startup instead of at 2am.

---

## 3. Folder structure

```
app/
  (marketing)/            # public, static-first routes
    page.tsx
  (app)/                  # authenticated product
    layout.tsx            # session guard lives here
    dashboard/page.tsx
  api/
    webhooks/stripe/route.ts   # ONLY HTTP endpoints that must exist (webhooks, OAuth callbacks)
  layout.tsx
  globals.css
components/
  ui/                     # shadcn primitives — generated, do not hand-edit
  <feature>/              # feature-scoped components (components/invoices/…)
lib/
  env.ts                  # Zod-validated process.env
  db/
    index.ts              # singleton better-sqlite3/Turso client
    schema.ts             # Drizzle schema — SINGLE SOURCE OF TRUTH
    queries/              # typed query functions, one file per aggregate
  auth/                   # session helpers
  stripe/                 # client + webhook helpers
  utils.ts                # cn(), formatters
server/
  actions/                # "use server" actions, grouped by feature
drizzle/                  # generated migrations — COMMITTED, append-only
tests/
  setup.ts
  *.test.ts
```

**Rules**

- Route groups `(name)` organize without changing the URL. Use them to split
  marketing vs. authed surfaces.
- One component per file; export the component as a named export.
- Server-only code lives under `server/` or `lib/` and imports `server-only` at the
  top so it can never be bundled into a client component.

### Naming conventions

| Thing | Convention | Example |
|---|---|---|
| Files & folders | `kebab-case` | `invoice-list.tsx`, `server/actions/invoices.ts` |
| React components | `PascalCase` export | `export function InvoiceList()` |
| Hooks | `useThing` | `useInvoiceFilters` |
| Server actions | `verbNoun` | `createInvoice`, `cancelSubscription` |
| DB tables / columns | `snake_case` | `invoice_items.unit_amount_cents` |
| TS variables/functions | `camelCase` | `invoiceItems` |
| Env vars | `UPPER_SNAKE` | `STRIPE_WEBHOOK_SECRET` |
| Types/interfaces | `PascalCase`, no `I` prefix | `Invoice`, not `IInvoice` |
| Boolean vars | `is`/`has`/`can` prefix | `isActive`, `hasAccess` |

---

## 4. SQL / migration conventions

This is the section that breaks production when ignored.

- **`lib/db/schema.ts` is the single source of truth.** Never write a table by hand
  in SQL first. Change the schema, then `pnpm db:generate`.
- **Migrations are append-only.** Never edit a committed file in `drizzle/`. Need a
  change? Generate a new migration. Editing an applied migration means every
  environment diverges silently.
- **Never `db:push` against production.** `push` is a dev-only convenience; prod uses
  `db:migrate`. Automate migrations in deploy, not from a laptop.

**Schema rules**

- Primary keys: `text` IDs generated in the app with `cuid2` (sortable-ish, no
  enumeration like autoincrement, no UUID fragmentation). Example id column:
  `id: text('id').primaryKey().$defaultFn(() => createId())`.
- Timestamps: store as `integer` Unix **milliseconds**. Every table gets
  `created_at` and `updated_at`, both `notNull`. Set `updated_at` in code on every
  write — SQLite has no `ON UPDATE`.
- **Money is an integer number of cents** (`*_amount_cents`). Never `REAL`/`FLOAT`.
  `0.1 + 0.2 !== 0.3` is a real billing bug.
- Every foreign key is declared `.references(() => other.id)` **and** indexed.
- SQLite does not enforce foreign keys unless you turn them on **per connection** —
  the client in `lib/db/index.ts` must run `PRAGMA foreign_keys = ON;`.
- Set `PRAGMA journal_mode = WAL;` and `PRAGMA busy_timeout = 5000;` on connection.
  SQLite allows a **single writer**; WAL lets readers proceed during writes and
  `busy_timeout` avoids `SQLITE_BUSY` thrown at users.
- Add an index for every column used in `WHERE`, `JOIN`, or `ORDER BY` on a hot path.
- Soft-delete only when you need an audit trail: add a nullable `deleted_at` and
  scope queries with `isNull(table.deletedAt)`. Otherwise hard-delete.
- Multi-write operations go in `db.transaction((tx) => { ... })`. A partial write is
  worse than a failed one.

```ts
// lib/db/schema.ts
import { sqliteTable, text, integer, index } from 'drizzle-orm/sqlite-core';
import { createId } from '@paralleldrive/cuid2';

export const invoices = sqliteTable('invoices', {
  id: text('id').primaryKey().$defaultFn(() => createId()),
  orgId: text('org_id').notNull().references(() => orgs.id),
  amountCents: integer('amount_cents').notNull(),
  status: text('status', { enum: ['draft', 'open', 'paid', 'void'] }).notNull().default('draft'),
  createdAt: integer('created_at').notNull().$defaultFn(() => Date.now()),
  updatedAt: integer('updated_at').notNull().$defaultFn(() => Date.now()),
}, (t) => ({
  orgIdx: index('invoices_org_idx').on(t.orgId),
}));
```

---

## 5. Component patterns

- **Server Components are the default.** Add `"use client"` only to the smallest
  interactive leaf (a form, a dropdown). Client components do not fetch data with
  `useEffect` — data comes from the server.
- **Data fetching lives in Server Components and server actions.** A page reads via
  `lib/db/queries/*`; there is no `fetch('/api/...')` from the client for our own data.
- You rarely need `app/api/*`. Route handlers are for things that *must* be HTTP:
  Stripe webhooks, OAuth callbacks, health checks. Everything else is a Server
  Component or a Server Action.
- **Server actions validate with Zod at the top**, then authorize, then mutate:

```ts
'use server';
export async function createInvoice(input: unknown) {
  const session = await requireSession();
  const data = createInvoiceSchema.parse(input);          // 1. validate
  await assertOrgAccess(session.user.id, data.orgId);     // 2. authorize
  const invoice = await db.transaction((tx) => { /* … */ }); // 3. mutate
  revalidatePath('/dashboard/invoices');
  return { ok: true as const, id: invoice.id };
}
```

- Actions return a **discriminated result** `{ ok: true, ... } | { ok: false, error }`.
  Don't throw for expected failures; the UI renders the error inline.
- Use `loading.tsx` and `error.tsx` per route instead of a global spinner. Wrap slow
  sections in `<Suspense>` so the shell streams immediately.
- Forms: React Hook Form + `zodResolver` on the client for instant feedback, and the
  **same** Zod schema re-validated in the action. Client validation is UX; server
  validation is security.
- Styling is Tailwind classes only — no inline `style`, no CSS modules. Merge
  conditional classes with `cn()`.
- shadcn/ui primitives live in `components/ui/` and are treated as vendored: extend by
  composing a wrapper in `components/<feature>/`, don't fork the primitive.

---

## 6. Security & auth

- **Authorize in the action / query, not in middleware.** Middleware is fine for
  redirecting logged-out users; it is not a security boundary.
- **Multi-tenant data is always scoped by `org_id`.** Every query filters on the
  caller's org. A missing `where eq(table.orgId, orgId)` is a cross-tenant leak and a
  blocking review comment.
- Sessions come from Auth.js. Never roll your own JWT or store tokens in
  `localStorage`.
- Validate `process.env` once, in `lib/env.ts`, and import the typed object — never
  read `process.env.X` scattered across the codebase.
- Strip/validate all input at the boundary with Zod; treat everything from the client
  (including hidden form fields and IDs) as untrusted.
- Webhooks: verify the Stripe signature against the **raw** body before parsing.
- Never log secrets or full session objects. Redact in error reporting.

---

## 7. Testing

- Unit + integration: **Vitest**. Integration tests run against an in-memory SQLite
  (`:memory:`), applying the **real** `drizzle/` migrations, then seeding — so tests
  exercise the same schema users get.

```ts
// tests/setup.ts
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import { migrate } from 'drizzle-orm/better-sqlite3/migrator';

export function makeTestDb() {
  const sqlite = new Database(':memory:');
  sqlite.pragma('foreign_keys = ON');
  const db = drizzle(sqlite);
  migrate(db, { migrationsFolder: './drizzle' });
  return db;
}
```

- Every bug fix ships with a test that fails before the fix.
- E2E: Playwright for the critical money/auth flows only (signup, checkout, pay).
- Don't test implementation details; test behavior through the public surface.

---

## 8. Git, PRs & CI

- Trunk-based: short-lived branches off `main`, PR required (no direct pushes).
- **Conventional commits** (`feat:`, `fix:`, `chore:`, `docs:`). One logical change
  per PR; keep diffs small.
- CI must be green before merge: `pnpm typecheck && pnpm lint && pnpm test && pnpm build`.
- Migrations and the schema change ship in the **same PR** — never merge a schema
  change without its generated migration.

---

## 9. What we don't do — and why

- **No `any`.** Use `unknown` + Zod parse at boundaries. `any` disables the only
  safety net a JS codebase has.
- **No non-null assertions (`!`) outside tests.** They're a lie the compiler can't
  check; handle the null.
- **No float money.** Integer cents only. (See §4.)
- **No raw string interpolation in SQL.** Use Drizzle's query builder / bound params
  — string-built SQL is how injections happen.
- **No editing applied migrations.** Append a new one. (See §4.)
- **No `useEffect` data fetching.** Fetch on the server; the client receives props.
- **No `app/api/*` for internal data.** Server Components/Actions replace it.
- **No secrets in client bundles.** Only `NEXT_PUBLIC_*` is safe; everything else
  stays server-side.
- **No cross-tenant queries.** Every tenant table query is org-scoped. (See §6.)
- **No synchronous native DB calls in Edge runtime.** Use Node runtime, or switch the
  DB client entirely to Turso.
- **No global mutable singletons** except the DB client, and that one **must** be
  cached on `globalThis` so `next dev` HMR doesn't open a new connection on every
  reload:

```ts
// lib/db/index.ts
import 'server-only';
const globalForDb = globalThis as unknown as { db?: AppDb };
export const db = globalForDb.db ?? makeDb();
if (process.env.NODE_ENV !== 'production') globalForDb.db = db;
```

- **No unvalidated env access.** Import the typed `env` object from `lib/env.ts`.
- **No large PRs mixing refactors with features.** Reviewers can't reason about both.

---

## 10. Recipes

**Add a table**
1. Add the `sqliteTable` to `lib/db/schema.ts` (ids, timestamps, FKs + indexes).
2. `pnpm db:generate` → review the SQL in `drizzle/`.
3. `pnpm db:migrate`.
4. Add typed queries under `lib/db/queries/<aggregate>.ts`.

**Add a page**
1. Create the route under `app/(app)/<segment>/page.tsx` (Server Component).
2. Read data via `lib/db/queries/*`; render Server Components.
3. Add `loading.tsx` / `error.tsx` if the route can be slow or fail.

**Add a mutation**
1. Write a `"use server"` action in `server/actions/<feature>.ts`.
2. `requireSession()` → `schema.parse(input)` → authorize → `db.transaction`.
3. `revalidatePath(...)` and return `{ ok: true } | { ok: false, error }`.
4. Call it from a small `"use client"` form.

**Ship a migration to prod**
1. `pnpm db:generate` and commit the SQL.
2. Back up first: `sqlite3 prod.db "VACUUM INTO 'backup.db'"` (or snapshot the Turso branch).
3. Run `pnpm db:migrate` during deploy, before the new code serves traffic.
