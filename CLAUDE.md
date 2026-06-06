# Next.js 15 + SQLite SaaS — Claude Code Operating Manual

You are working on a **multi-tenant SaaS** built with **Next.js 15 App Router**, **React 19**, **TypeScript (strict)**, and **SQLite**. The database runs either **locally via `better-sqlite3`** or **remotely via Turso (`@libsql/client`)**. This file is the source of truth for architecture, naming, and workflow. Follow it by default; only deviate when the user explicitly overrides a rule.

---

## Stack & Versions

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15.x, App Router only | Pages Router is out of scope; App Router gives RSC + server actions |
| UI | React 19, Tailwind CSS 4 | Utility-first styling; no CSS-in-JS runtime cost |
| Language | TypeScript 5.x, `strict: true` | Catch schema/type drift at compile time |
| Validation | Zod 3.x | Shared schemas for forms, server actions, and API routes |
| Local DB | `better-sqlite3` 11.x | Sync driver; fast for dev and single-node deploys |
| Remote DB | `@libsql/client` (Turso) | Same SQL dialect, edge-friendly replication |
| Migrations | Plain SQL files in git | No ORM magic; diffs are reviewable |
| Package manager | `pnpm` | Faster installs, strict dependency graph |
| Testing | Vitest + React Testing Library | Same config as Vite ecosystem; fast unit tests |

**Default assumption:** greenfield project, single SQLite file at `./data/app.db` in development, Turso in production. Auth uses **session cookies + server-side session table** unless the user says otherwise.

---

## Dev Commands

Run these from the repo root. If a script is missing, add it to `package.json` instead of inventing one-off shell invocations.

```bash
pnpm install          # install dependencies
pnpm dev              # Next.js dev server (http://localhost:3000)
pnpm build            # production build
pnpm start            # serve production build
pnpm typecheck        # tsc --noEmit
pnpm lint             # eslint
pnpm test             # vitest run
pnpm test:watch       # vitest
pnpm db:migrate       # apply pending SQL migrations
pnpm db:migrate:status # list applied vs pending migrations
pnpm db:seed          # seed dev data (never runs in production)
```

**Migration runner contract:** `pnpm db:migrate` reads `src/db/migrations/*.sql` in filename order, records each applied migration in a `_migrations` table, and skips already-applied files. Migrations are **not** run automatically on `pnpm dev`.

---

## Folder Structure

```
.
├── CLAUDE.md                 # this file
├── data/                     # local SQLite file (gitignored)
├── public/                   # static assets only
├── src/
│   ├── app/                  # routes, layouts, loading/error UI
│   │   ├── (auth)/           # login, signup — no app chrome
│   │   ├── (app)/            # authenticated shell (sidebar, nav)
│   │   │   └── [orgSlug]/    # tenant-scoped routes
│   │   ├── api/              # webhooks & third-party callbacks only
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/               # dumb primitives (Button, Input, Dialog)
│   │   └── features/         # domain components (InvoiceTable, ProjectCard)
│   ├── db/
│   │   ├── migrations/       # append-only SQL (see below)
│   │   ├── queries/          # one file per aggregate (users.ts, invoices.ts)
│   │   └── schema.sql        # full schema snapshot for reference / fresh installs
│   ├── lib/
│   │   ├── db.ts             # singleton connection (ONLY db entrypoint)
│   │   ├── auth.ts           # session helpers
│   │   ├── env.ts            # typed, validated env vars (zod)
│   │   └── utils.ts          # pure helpers (cn, formatCurrency)
│   ├── server/
│   │   ├── actions/          # server actions ('use server')
│   │   └── jobs/             # cron / background tasks (idempotent)
│   └── types/                # shared TS types (no runtime imports from db/)
├── scripts/
│   ├── migrate.ts            # migration runner
│   └── seed.ts               # dev seed data
└── tests/
    ├── db/                   # query + migration tests
    └── components/           # component tests
```

**Rules:**
- `src/app/` owns routing and page composition only — no SQL here.
- `src/db/queries/` owns all reads/writes. One module per domain entity.
- `src/lib/db.ts` is the **only** place that imports `better-sqlite3` or `@libsql/client`.
- `src/server/` is server-only; never import it from `"use client"` files.
- Do not add new top-level `src/` folders without strong justification.

---

## Naming Conventions

| Artifact | Convention | Example |
|----------|------------|---------|
| Route folders | `kebab-case` | `src/app/(app)/[orgSlug]/billing/page.tsx` |
| React components | `PascalCase` file + export | `InvoiceRow.tsx` → `export function InvoiceRow` |
| UI primitives | `kebab-case` in `components/ui/` | `button.tsx`, `dialog.tsx` |
| Query modules | `kebab-case`, entity name | `src/db/queries/invoices.ts` |
| Query functions | `verbNoun`, camelCase | `listInvoices`, `getInvoiceById`, `createInvoice` |
| Server actions | file `kebab-case`, fn `actionVerbNoun` | `actionCreateInvoice` in `create-invoice.ts` |
| Migration files | `YYYYMMDDHHMMSS_snake_slug.sql` (UTC) | `20260315120000_create_invoices.sql` |
| SQL identifiers | `snake_case` | `created_at`, `org_id`, `deleted_at` |
| TS types | `PascalCase` | `Invoice`, `CreateInvoiceInput` |
| Env vars | `SCREAMING_SNAKE` | `DATABASE_URL`, `SESSION_SECRET` |

**Table naming:** plural nouns (`users`, `organizations`, `invoices`). Join tables: `{a}_{b}` alphabetically (`org_members`, not `members_orgs`).

**Primary keys:** `id TEXT PRIMARY KEY` with UUID v7 (or ULID) generated in application code — not SQLite `INTEGER AUTOINCREMENT`. Reason: safe distributed ID generation and consistent shape across Turso replicas.

---

## SQL & Migration Conventions

### Principles

1. **Migrations are append-only.** Never edit a migration that has been merged to `main`. Fix forward with a new file.
2. **One concern per migration.** Don't combine unrelated table changes.
3. **Prefer additive changes.** Add columns with defaults; backfill in the same migration; drop old columns in a later migration after code no longer reads them.
4. **Every migration must be safe to re-run in dev** where practical (`CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`).

### Migration file template

```sql
-- 20260315120000_create_invoices.sql
-- Creates invoices table for org-scoped billing.

CREATE TABLE IF NOT EXISTS invoices (
  id          TEXT PRIMARY KEY NOT NULL,
  org_id      TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
  status      TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'paid', 'void')),
  created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  deleted_at  TEXT
);

CREATE INDEX IF NOT EXISTS idx_invoices_org_created
  ON invoices (org_id, created_at DESC)
  WHERE deleted_at IS NULL;
```

### Query rules

- **No `SELECT *`.** List columns explicitly so schema changes surface as type errors, not silent bugs.
- **Always filter soft-deleted rows:** `WHERE deleted_at IS NULL` unless querying archives.
- **Paginate with deterministic ordering:** `ORDER BY created_at DESC, id DESC` plus `LIMIT`/`OFFSET` or keyset pagination.
- **Updates/deletes require a scoped `WHERE`:** never `UPDATE invoices SET status = 'paid'` without a predicate. Deletes on user data are **soft** (`SET deleted_at = ...`) unless the row is ephemeral (sessions, tokens).
- **Use transactions** for multi-table writes: wrap in `db.transaction(() => { ... })` (better-sqlite3) or batch calls (libsql).
- **Parameterize everything.** No string interpolation of user input into SQL.

### Timestamps

Store as **ISO 8601 UTC strings** (`TEXT`) using `strftime('%Y-%m-%dT%H:%M:%fZ', 'now')`. Convert to `Date` only at UI boundaries. Reason: SQLite date functions work on ISO strings; mixing integer epochs and strings causes subtle bugs.

### Money

Store as **integer cents** (`amount_cents INTEGER`). Never use `REAL` for currency. Format for display in the UI layer only.

---

## Component Patterns

### Server Components (default)

Every file in `src/app/` and most of `src/components/features/` are **Server Components** unless they need browser interactivity.

```tsx
// src/app/(app)/[orgSlug]/invoices/page.tsx
import { listInvoices } from '@/db/queries/invoices';
import { InvoiceTable } from '@/components/features/invoice-table';

export default async function InvoicesPage({
  params,
}: {
  params: Promise<{ orgSlug: string }>;
}) {
  const { orgSlug } = await params;
  const invoices = await listInvoices(orgSlug);
  return <InvoiceTable invoices={invoices} />;
}
```

Fetch data in Server Components by calling query functions directly — **no `fetch()` to your own API routes** for internal data.

### Client Components (islands)

Add `"use client"` only when you need: React state, effects, event handlers, or browser APIs.

```tsx
'use client';

import { useTransition } from 'react';
import { actionVoidInvoice } from '@/server/actions/void-invoice';

export function VoidInvoiceButton({ invoiceId }: { invoiceId: string }) {
  const [pending, startTransition] = useTransition();
  return (
    <button
      disabled={pending}
      onClick={() => startTransition(() => actionVoidInvoice(invoiceId))}
    >
      Void
    </button>
  );
}
```

Keep client components **small and leaf-level**. Pass serializable props from server parents; never pass functions that close over secrets.

### Server Actions

```tsx
// src/server/actions/create-invoice.ts
'use server';

import { z } from 'zod';
import { requireOrgMember } from '@/lib/auth';
import { createInvoice } from '@/db/queries/invoices';
import { revalidatePath } from 'next/cache';

const schema = z.object({
  orgSlug: z.string().min(1),
  amountCents: z.number().int().positive(),
});

export async function actionCreateInvoice(input: z.infer<typeof schema>) {
  const data = schema.parse(input);
  const { orgId, userId } = await requireOrgMember(data.orgSlug);
  const invoice = await createInvoice({ orgId, amountCents: data.amountCents, createdBy: userId });
  revalidatePath(`/${data.orgSlug}/invoices`);
  return { ok: true as const, invoice };
}
```

**Server action checklist:** validate input → authorize → mutate → revalidate affected paths → return structured result (never throw raw strings to the client).

### Loading, error, and not-found

Co-locate `loading.tsx`, `error.tsx`, and `not-found.tsx` in route segments that fetch data. Reason: streaming and error boundaries are route-level concerns, not component hacks.

### Forms

Prefer **Server Actions + `useFormState`/`useActionState`** over client-side `fetch` to API routes. Reason: progressive enhancement, less client JS, auth stays on server.

---

## Patterns to Follow

1. **Tenant scoping in every query.** All org-owned rows include `org_id`; every query function accepts `orgId` or resolves it from the session — never trust client-supplied IDs alone.
2. **Map at the query boundary.** Query functions return typed domain objects (`Invoice`), not raw `Row` types. UI never imports from `better-sqlite3`.
3. **Env validation at boot.** `src/lib/env.ts` parses `process.env` with Zod and exports `env`. Fail fast on missing secrets.
4. **Colocate feature code.** Invoice UI lives under `components/features/`, invoice queries under `db/queries/invoices.ts`, invoice actions under `server/actions/`.
5. **API routes for webhooks only.** Internal CRUD goes through server actions or direct query calls in RSC. `/api/*` is for Stripe webhooks, OAuth callbacks, and external integrations.
6. **Idempotent background jobs.** Jobs in `src/server/jobs/` must tolerate retries (use unique constraints + upsert or status checks).
7. **Feature flags via env or DB**, not compile-time `#ifdef`-style branching.

---

## What We Don't Do (And Why)

| Don't | Why |
|-------|-----|
| Use Pages Router (`pages/`) | Out of scope; mixing routers breaks conventions and caching |
| Use Prisma, Drizzle, or Kysely | Raw SQL + typed query modules keeps migrations visible and dependency-light |
| Put SQL in React components or route files | Untestable, breaks server/client boundaries, causes connection leaks |
| Import `src/lib/db.ts` from client components | Bundles native modules / leaks credentials; build will fail or worse, succeed insecurely |
| Run migrations on every dev server start | Race conditions and non-deterministic schema state across branches |
| Use `SELECT *` | Silent breakage when columns are added or removed |
| Store money as floats | Rounding errors; use integer cents |
| Store enums as unconstrained TEXT | Typo values slip into production; use `CHECK` constraints or lookup tables |
| Create `utils/` catch-all files | Becomes a junk drawer; put helpers in `lib/` with clear names |
| Add `"use client"` to layout files | Forces entire subtrees client-side; kills RSC benefits |
| Fetch internal data via `/api/...` from the same app | Extra latency, duplicate auth, harder caching |
| Commit `data/*.db` or `.env` files | Local state and secrets belong in gitignore |
| Mix `better-sqlite3` and `@libsql/client` in the same module | Different sync/async semantics; pick one per environment behind `lib/db.ts` |
| Hard-delete user content by default | Recovery and audit requirements; use `deleted_at` |
| Add npm dependencies without checking bundle impact | Client bundle size is a product concern; prefer server-side or lightweight libs |
| Use `any` or `@ts-ignore` | Defeats strict mode; fix the type or add a narrow assertion with a comment |

---

## Environment Variables

```bash
# .env.local (never committed)
DATABASE_URL="file:./data/app.db"          # or libsql://... for Turso
SESSION_SECRET="..."                       # 32+ random bytes
NEXT_PUBLIC_APP_URL="http://localhost:3000" # only NEXT_PUBLIC_* var allowed
```

All server secrets are read in `src/lib/env.ts`. **`NEXT_PUBLIC_*` is only for non-sensitive, client-safe values** (app URL, analytics IDs). Never expose database URLs or session secrets.

---

## When to Ask Clarifying Questions

Ask before implementing if the request touches:

- **Auth provider change** (Clerk, Auth.js, custom magic links) — affects session schema and middleware
- **Multi-tenant model change** (org vs workspace vs team hierarchy) — affects every query
- **Deployment target** (Vercel serverless vs long-running Node vs edge) — affects SQLite driver choice and connection pooling
- **Billing integration** (Stripe Billing vs one-off Checkout) — affects webhook routes and idempotency
- **Data retention / GDPR deletion policy** — affects soft-delete vs hard-delete strategy

For routine feature work within the conventions above, **proceed without asking**.
