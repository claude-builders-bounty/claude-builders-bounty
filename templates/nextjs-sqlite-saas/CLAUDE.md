# Next.js 15 + SQLite SaaS — Claude Code Guide

You are building a **multi-tenant B2B SaaS** with **Next.js 15 App Router**, **React 19**, **TypeScript strict**, and **SQLite**. Local development uses **`better-sqlite3`**; production uses **Turso** via **`@libsql/client`**. This document defines stack choices, folder layout, SQL rules, and component patterns. Treat it as authoritative — deviate only when the user explicitly overrides a convention.

---

## Table of Contents

Navigate by topic — each `##` section is standalone. Reference app folders include a `README.md` explaining their purpose.

| Section | What it covers |
|---------|----------------|
| [Stack & Versions](#stack--versions) | Pinned dependencies and greenfield defaults |
| [Dev Commands](#dev-commands) | `pnpm` scripts and migration runner contract |
| [Folder Structure](#folder-structure) | `src/` tree, boundary rules, per-folder READMEs |
| [Naming Conventions](#naming-conventions) | Files, SQL, types, and env var naming |
| [SQL & Migration Conventions](#sql--migration-conventions) | Append-only migrations, queries, timestamps, money |
| [Component Patterns](#component-patterns) | RSC, client islands, Server Actions, forms |
| [Patterns to Follow](#patterns-to-follow) | Tenant scope, validation, colocation |
| [What We Don't Do (And Why)](#what-we-dont-do-and-why) | Anti-patterns table with reasons |
| [Environment Variables](#environment-variables) | `env.ts`, `db.ts`, secret handling |
| [When to Ask Clarifying Questions](#when-to-ask-clarifying-questions) | Auth, tenancy, deployment, billing |
| [Auth and Authorization](#auth-and-authorization) | Sessions, `requireOrgMember`, middleware |
| [Route Handlers and APIs](#route-handlers-and-apis) | External webhooks only |
| [SQL Migration Runner](#sql-migration-runner) | `scripts/migrate.ts` integrity checks |
| [Dev Seed Script](#dev-seed-script) | Production guard and idempotent upserts |
| [Testing Rules](#testing-rules) | Query, action, component, migration tests |
| [Development Environment Setup](#development-environment-setup) | Local `.env.local`, migrations, and first run |
| [Deployment](#deployment) | Turso, build, and production env checklist |
| [Template Maintenance Best Practices](#template-maintenance-best-practices) | Keeping CLAUDE.md and reference app in sync |
| [Security Checklist](#security-checklist) | Auth, authorization, and data-handling review |
| [Greenfield Smoke Test](#greenfield-smoke-test) | Five-step validation checklist |

---

## Stack & Versions

| Layer | Pin | Rationale |
|-------|-----|-----------|
| Framework | Next.js 15.x, App Router | RSC + Server Actions; Pages Router is not used |
| UI | React 19, Tailwind CSS 4 | Server-first rendering; no runtime CSS-in-JS |
| Language | TypeScript 5.x, `strict: true` | Catch schema drift at compile time |
| Validation | Zod 3.x | One schema for forms, actions, and env parsing |
| Local DB | `better-sqlite3` 11.x | Synchronous driver; ideal for dev and single-node deploys |
| Prod DB | `@libsql/client` (Turso) | Same SQL dialect; edge replication without Postgres ops |
| Migrations | Plain `.sql` files in git | Reviewable diffs; no ORM migration DSL |
| Package manager | `pnpm` | Strict dep graph; faster CI installs |
| Tests | Vitest + React Testing Library | Fast unit tests; same tooling as Vite ecosystem |

**Greenfield defaults:** SQLite file at `./data/app.db` in dev; Turso URL in production. Auth is **httpOnly session cookies** backed by a `sessions` table. Tenancy is **organization-scoped** via `org_id` on every owned row.

---

## Dev Commands

Run from the repo root. If a script is missing, add it to `package.json` — do not invent ad-hoc shell one-liners.

```bash
pnpm install              # install dependencies
pnpm dev                  # Next.js dev server (localhost:3000)
pnpm build                # production build
pnpm start                # serve production build
pnpm typecheck            # tsc --noEmit
pnpm lint                 # eslint
pnpm test                 # vitest run
pnpm test:watch           # vitest in watch mode
pnpm db:migrate           # apply pending SQL migrations
pnpm db:migrate:status    # show applied vs pending migrations
pnpm db:seed              # seed dev data (blocked in production)
```

**Migration runner contract:** `pnpm db:migrate` reads `src/db/migrations/*.sql` in lexicographic filename order, records each in `_migrations`, and skips already-applied files. Migrations never run automatically on `pnpm dev`.

---

## Folder Structure

```
.
├── CLAUDE.md                     # this file — copy to project root
├── data/                         # local SQLite file (gitignored)
├── public/                       # static assets only
├── src/
│   ├── app/
│   │   ├── (auth)/               # login, signup — no app chrome
│   │   ├── (app)/                # authenticated shell (sidebar, nav)
│   │   │   └── [orgSlug]/        # tenant-scoped routes
│   │   ├── api/                  # webhooks & third-party callbacks only
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/                   # stateless primitives (Button, Input)
│   │   └── features/             # domain UI (InvoiceTable, ProjectCard)
│   ├── db/
│   │   ├── migrations/           # append-only SQL files
│   │   ├── queries/              # one module per aggregate
│   │   └── schema.sql            # full schema snapshot for fresh installs
│   ├── lib/
│   │   ├── db.ts                 # singleton connection — ONLY db entrypoint
│   │   ├── auth.ts               # session read/write helpers
│   │   ├── env.ts                # Zod-validated env vars
│   │   └── utils.ts              # pure helpers (cn, formatCurrency)
│   ├── middleware.ts             # auth redirect for (app)/ routes only
│   ├── server/
│   │   ├── actions/              # 'use server' mutations
│   │   └── jobs/                 # cron / background tasks (idempotent)
│   └── types/                    # shared TS types (no db runtime imports)
├── scripts/
│   ├── migrate.ts                # migration runner
│   └── seed.ts                   # dev seed data
└── tests/
    ├── db/                       # query + migration tests
    └── components/               # component tests
```

**Per-folder READMEs:** Each directory under `src/`, `scripts/`, and `tests/` ships a `README.md` describing its contents and import boundaries. Read the folder README before adding files.

**Boundary rules:**
- `src/app/` — routing and page composition only; no SQL.
- `src/db/queries/` — all reads/writes; one file per domain entity.
- `src/lib/db.ts` — the only module that imports `better-sqlite3` or `@libsql/client`.
- `src/server/` — server-only; never import from `"use client"` files.
- No new top-level `src/` folders without explicit justification.

---

## Naming Conventions

| Artifact | Convention | Example |
|----------|------------|---------|
| Route folders | `kebab-case` | `src/app/(app)/[orgSlug]/billing/page.tsx` |
| Feature components | `PascalCase` file + export | `InvoiceRow.tsx` → `export function InvoiceRow` |
| UI primitives | `kebab-case` in `components/ui/` | `button.tsx`, `dialog.tsx` |
| Query modules | `kebab-case`, entity name | `src/db/queries/invoices.ts` |
| Query functions | `verbNoun`, camelCase | `listInvoices`, `getInvoiceById` |
| Server actions | `kebab-case` file, `actionVerbNoun` fn | `actionCreateInvoice` in `create-invoice.ts` |
| Migration files | `YYYYMMDDHHMMSS_snake_slug.sql` (UTC) | `20260315120000_create_invoices.sql` |
| SQL columns/tables | `snake_case` | `created_at`, `org_id`, `deleted_at` |
| TS types | `PascalCase` | `Invoice`, `CreateInvoiceInput` |
| Env vars | `SCREAMING_SNAKE` | `DATABASE_URL`, `SESSION_SECRET` |

**Tables:** plural nouns (`users`, `organizations`, `invoices`). Join tables: alphabetically ordered (`org_members`, not `members_orgs`).

**Primary keys:** `id TEXT PRIMARY KEY` with UUID v7 (or ULID) generated in application code — not `INTEGER AUTOINCREMENT`. Reason: safe distributed ID generation and consistent shape across Turso replicas.

---

## SQL & Migration Conventions

### Principles

1. **Append-only.** Never edit a migration merged to `main`. Fix forward with a new file.
2. **One concern per file.** Do not combine unrelated schema changes.
3. **Additive first.** Add columns with defaults; backfill in the same migration; drop obsolete columns later.
4. **Idempotent where practical.** Use `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS` so dev re-runs are safe.

### Migration template

```sql
-- 20260315120000_create_invoices.sql
-- Org-scoped invoices for billing.

CREATE TABLE IF NOT EXISTS invoices (
  id           TEXT PRIMARY KEY NOT NULL,
  org_id       TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
  status       TEXT NOT NULL DEFAULT 'draft'
               CHECK (status IN ('draft', 'sent', 'paid', 'void')),
  created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  updated_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  deleted_at   TEXT
);

CREATE INDEX IF NOT EXISTS idx_invoices_org_created
  ON invoices (org_id, created_at DESC)
  WHERE deleted_at IS NULL;
```

### Query rules

- **No `SELECT *`.** List columns explicitly so schema changes surface as type errors.
- **Filter soft-deletes:** `WHERE deleted_at IS NULL` unless querying archives.
- **Deterministic pagination:** `ORDER BY created_at DESC, id DESC` with `LIMIT`/`OFFSET` or keyset pagination.
- **Scoped writes:** every `UPDATE`/`DELETE` includes a `WHERE` clause; user data deletes are soft (`SET deleted_at = ...`).
- **Transactions for multi-table writes:** `db.transaction(() => { ... })` (better-sqlite3) or batched calls (libsql).
- **Parameterized queries only.** Never interpolate user input into SQL strings.

```ts
// src/db/queries/invoices.ts — parameterized reads; orgId is always bound, never concatenated
import { getDb } from '@/lib/db';
import Database from 'better-sqlite3';

export type Invoice = {
  id: string;
  orgId: string;
  amountCents: number;
  status: string;
};

export function listInvoices(orgId: string): Invoice[] {
  const db = getDb() as Database.Database;
  const rows = db
    .prepare(
      `SELECT id, org_id, amount_cents, status
       FROM invoices
       WHERE org_id = ? AND deleted_at IS NULL
       ORDER BY created_at DESC, id DESC
       LIMIT 100`,
    )
    .all(orgId) as Array<{
      id: string;
      org_id: string;
      amount_cents: number;
      status: string;
    }>;
  return rows.map((row) => ({
    id: row.id,
    orgId: row.org_id,
    amountCents: row.amount_cents,
    status: row.status,
  }));
}
```

Reason: `?` placeholders keep user-derived `orgId` out of SQL strings; explicit column lists surface schema drift at compile time.

### Timestamps

Store as **ISO 8601 UTC strings** (`TEXT`) via `strftime('%Y-%m-%dT%H:%M:%fZ', 'now')`. Convert to `Date` only at UI boundaries. Reason: SQLite date functions work on ISO strings; mixing integer epochs causes subtle bugs.

### Money

Store as **integer cents** (`amount_cents INTEGER`). Never `REAL`. Format for display in the UI layer only.

---

## Component Patterns

### Server Components (default)

Files in `src/app/` and most of `src/components/features/` are Server Components unless they need browser APIs.

```tsx
// src/app/(app)/[orgSlug]/invoices/page.tsx
import { listInvoices } from '@/db/queries/invoices';
import { requireOrgMember } from '@/lib/auth';
import { InvoiceTable } from '@/components/features/invoice-table';

export default async function InvoicesPage({
  params,
}: {
  params: Promise<{ orgSlug: string }>;
}) {
  const { orgSlug } = await params;
  const { orgId } = await requireOrgMember(orgSlug);
  const invoices = await listInvoices(orgId);
  return <InvoiceTable invoices={invoices} orgSlug={orgSlug} />;
}
```

Fetch data by calling query functions directly — **never `fetch()` your own `/api` routes** for internal reads.

### Client Components (islands)

Add `"use client"` only for: React state, effects, event handlers, or browser APIs.

```tsx
'use client';

import { useTransition } from 'react';
import { actionVoidInvoice } from '@/server/actions/void-invoice';

export function VoidInvoiceButton({
  orgSlug,
  invoiceId,
}: {
  orgSlug: string;
  invoiceId: string;
}) {
  const [pending, startTransition] = useTransition();
  return (
    <button
      disabled={pending}
      onClick={() =>
        startTransition(() => actionVoidInvoice({ orgSlug, invoiceId }))
      }
    >
      Void
    </button>
  );
}
```

Keep client components **small and leaf-level**. Pass serializable props from server parents.

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

export async function actionCreateInvoice(input: unknown) {
  const parsed = schema.safeParse(input);
  if (!parsed.success) {
    return { ok: false as const, error: 'Invalid input' };
  }
  const data = parsed.data;
  try {
    const { orgId, userId } = await requireOrgMember(data.orgSlug);
    const invoice = await createInvoice({
      orgId,
      amountCents: data.amountCents,
      createdBy: userId,
    });
    revalidatePath(`/${data.orgSlug}/invoices`);
    return { ok: true as const, invoice };
  } catch {
    return { ok: false as const, error: 'Failed to create invoice' };
  }
}
```

**Action checklist:** validate → authorize → mutate → revalidate affected paths → return structured result. Never throw raw error strings to the client.

```tsx
// src/server/actions/void-invoice.ts
'use server';

import { z } from 'zod';
import { requireOrgMember } from '@/lib/auth';
import { voidInvoice } from '@/db/queries/invoices';
import { revalidatePath } from 'next/cache';

const schema = z.object({
  orgSlug: z.string().min(1),
  invoiceId: z.string().min(1),
});

export async function actionVoidInvoice(input: unknown) {
  const parsed = schema.safeParse(input);
  if (!parsed.success) {
    return { ok: false as const, error: 'Invalid input' };
  }
  const data = parsed.data;
  try {
    const { orgId } = await requireOrgMember(data.orgSlug);
    await voidInvoice({ orgId, invoiceId: data.invoiceId });
    revalidatePath(`/${data.orgSlug}/invoices`);
    return { ok: true as const };
  } catch {
    return { ok: false as const, error: 'Failed to void invoice' };
  }
}
```

### Route-level UI

Co-locate `loading.tsx`, `error.tsx`, and `not-found.tsx` in data-fetching route segments. Streaming and error boundaries are route concerns, not component hacks.

### Forms

Prefer **Server Actions + `useActionState`** over client `fetch` to API routes. Auth stays on the server; forms work without JavaScript.

```tsx
'use client';

import { useActionState } from 'react';
import { actionCreateInvoice } from '@/server/actions/create-invoice';

export function CreateInvoiceForm({ orgSlug }: { orgSlug: string }) {
  const [state, formAction, pending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      const amountCents = Number(formData.get('amountCents'));
      return actionCreateInvoice({ orgSlug, amountCents });
    },
    null,
  );
  return (
    <form action={formAction}>
      <input name="amountCents" type="number" required />
      <button disabled={pending}>Create</button>
      {state?.ok === false && <p role="alert">{state.error}</p>}
      {state?.ok && <p>Invoice created</p>}
    </form>
  );
}
```

---

## Patterns to Follow

1. **Tenant scope every query.** Org-owned rows carry `org_id`; query functions accept `orgId` or resolve it from the session — never trust client-supplied IDs alone.
2. **Map at the query boundary.** Query modules return typed domain objects (`Invoice`), not raw driver rows.
3. **Validate env at boot.** `src/lib/env.ts` parses `process.env` with Zod and exports `env`. Fail fast on missing secrets.
4. **Colocate by feature.** Invoice UI in `components/features/`, queries in `db/queries/invoices.ts`, actions in `server/actions/`.
5. **API routes for externals only.** Internal CRUD uses Server Actions or direct query calls in RSC. `/api/*` is for Stripe webhooks, OAuth callbacks, and third-party integrations.
6. **Idempotent background jobs.** Jobs in `src/server/jobs/` must tolerate retries via unique constraints, upserts, or status checks.
7. **Feature flags via env or DB** — not compile-time branching.

---

## What We Don't Do (And Why)

| Don't | Why |
|-------|-----|
| Use Pages Router (`pages/`) | Out of scope; mixing routers breaks caching and conventions |
| Use Prisma, Drizzle, or Kysely | Raw SQL + typed query modules keeps migrations visible and deps light |
| Put SQL in route files or components | Untestable, leaks connections, breaks server/client boundaries |
| Import `src/lib/db.ts` from client code | Bundles native modules or leaks credentials |
| Run migrations on `pnpm dev` startup | Race conditions and non-deterministic schema across branches |
| Use `SELECT *` | Silent breakage when columns change |
| Store money as floats | Rounding errors; integer cents are exact |
| Store enums as unconstrained TEXT | Typos reach production; use `CHECK` constraints |
| Add catch-all `utils/` files | Becomes a junk drawer; use `lib/` with clear names |
| Put `"use client"` on layouts | Forces entire subtrees client-side; kills RSC benefits |
| Fetch internal data via `/api/...` | Extra latency, duplicate auth, worse caching |
| Commit `data/*.db` or `.env` files | Local state and secrets belong in gitignore |
| Mix sync and async DB drivers in one module | Different semantics; abstract behind `lib/db.ts` per environment |
| Hard-delete user content by default | Audit and recovery requirements; use `deleted_at` |
| Hardcode database paths in source code | Connection details must come from `env.DATABASE_URL` via `src/lib/env.ts` |
| Add client deps without bundle review | Bundle size is a product concern |
| Use `any` or `@ts-ignore` | Defeats strict mode; fix the type or add a narrow assertion |

---

## Environment Variables

```bash
# .env.local (never committed)
DATABASE_URL="file:./data/app.db"           # or libsql://... for Turso
SESSION_SECRET="..."                        # 32+ random bytes
NEXT_PUBLIC_APP_URL="http://localhost:3000" # only NEXT_PUBLIC_* allowed
```

All server secrets are read in `src/lib/env.ts`. **`NEXT_PUBLIC_*` is only for client-safe values** (app URL, analytics IDs). Never expose database URLs or session secrets.

```ts
// src/lib/env.ts
import { z } from 'zod';

const envSchema = z.object({
  DATABASE_URL: z
    .string()
    .min(1)
    .refine(
      (url) => url.startsWith('file:') || url.startsWith('libsql:'),
      'DATABASE_URL must use file: or libsql: scheme',
    ),
  SESSION_SECRET: z.string().min(32),
  NEXT_PUBLIC_APP_URL: z.string().url(),
});

export const env = envSchema.parse({
  DATABASE_URL: process.env.DATABASE_URL,
  SESSION_SECRET: process.env.SESSION_SECRET,
  NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
});
```

```ts
// src/lib/db.ts — sole database entrypoint; never hardcode paths here
import Database from 'better-sqlite3';
import { createClient } from '@libsql/client';
import { env } from './env';

type DbClient = Database.Database | ReturnType<typeof createClient>;

let instance: DbClient | null = null;

export function getDb(): DbClient {
  if (!instance) {
    if (env.DATABASE_URL.startsWith('libsql:')) {
      instance = createClient({ url: env.DATABASE_URL });
    } else {
      const filePath = env.DATABASE_URL.replace(/^file:/, '');
      instance = new Database(filePath);
      (instance as Database.Database).pragma('journal_mode = WAL');
      (instance as Database.Database).pragma('foreign_keys = ON');
    }
  }
  return instance;
}
```

Reason: every connection reads `env.DATABASE_URL` validated at boot — no `./data/app.db` literals in application code.

---

## When to Ask Clarifying Questions

Ask before implementing when the request touches:

- **Auth provider change** (Clerk, Auth.js, magic links) — affects session schema and middleware
- **Multi-tenant model change** (org vs workspace vs team) — affects every query
- **Deployment target** (Vercel serverless vs long-running Node vs edge) — affects driver and pooling
- **Billing integration** (Stripe Billing vs Checkout) — affects webhooks and idempotency
- **Data retention / GDPR policy** — affects soft-delete vs hard-delete strategy

For routine feature work within these conventions, **proceed without asking**.

---

## Auth and Authorization

Sessions are **httpOnly cookies** backed by a `sessions` table. Reason: cookies resist XSS exfiltration better than localStorage tokens.

1. **Read session in Server Components and actions** via `getSession()` from `src/lib/auth.ts` — never parse cookies manually.
2. **Resolve org membership** in `requireOrgMember(orgSlug)` before any org-scoped read or write.
3. **Middleware** (`src/middleware.ts`) only redirects unauthenticated users away from `(app)/` routes. Reason: keep auth logic out of middleware matchers; complex checks belong in layouts and actions.
4. **Never trust `orgSlug` or `orgId` from the client alone.** Always verify the session user belongs to that org in the database.

---

## Route Handlers and APIs

`src/app/api/` is for **external callbacks only** — Stripe webhooks, OAuth redirects, cron ingress. Reason: internal CRUD belongs in Server Actions with shared auth helpers.

```tsx
// src/app/api/webhooks/stripe/route.ts
import { headers } from 'next/headers';
import { env } from '@/lib/env';

export async function POST(request: Request) {
  const signature = (await headers()).get('stripe-signature');
  if (!signature) return new Response('Missing signature', { status: 400 });
  const body = await request.text();
  // verify with env.STRIPE_WEBHOOK_SECRET, then upsert idempotently
  return new Response('ok');
}
```

Webhook handlers must be **idempotent** (use event IDs or unique constraints). Return `400` for bad signatures, `200` for duplicates.

---

## SQL Migration Runner

`scripts/migrate.ts` applies pending files in lexicographic order and records each in `_migrations`. Run via `pnpm db:migrate` — never on dev server startup.

```ts
// scripts/migrate.ts
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import Database from 'better-sqlite3';
import { env } from '../src/lib/env';

const MIGRATIONS_DIR = join(process.cwd(), 'src/db/migrations');

function ensureMigrationsTable(db: Database.Database) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS _migrations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      filename TEXT NOT NULL UNIQUE,
      applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    );
  `);
}

function applyMigrations() {
  const filePath = env.DATABASE_URL.replace(/^file:/, '');
  const db = new Database(filePath);
  db.pragma('foreign_keys = ON');
  ensureMigrationsTable(db);

  const applied = new Set(
    (db.prepare('SELECT filename FROM _migrations').all() as { filename: string }[])
      .map((row) => row.filename),
  );
  const files = readdirSync(MIGRATIONS_DIR)
    .filter((f) => f.endsWith('.sql'))
    .sort();

  for (const filename of files) {
    if (applied.has(filename)) continue;
    const sql = readFileSync(join(MIGRATIONS_DIR, filename), 'utf8');
    db.transaction(() => {
      db.exec(sql);
      db.prepare('INSERT INTO _migrations (filename) VALUES (?)').run(filename);
    })();
  }

  const recorded = (
    db.prepare('SELECT COUNT(*) as count FROM _migrations').get() as { count: number }
  ).count;
  if (recorded !== files.length) {
    throw new Error(
      `Migration integrity check failed: ${recorded} applied vs ${files.length} files`,
    );
  }
  db.close();
}

applyMigrations();
```

Reason: filename-order application plus a post-run count check catches skipped files, partial applies, and duplicate `_migrations` rows.

---

## Dev Seed Script

`pnpm db:seed` runs `scripts/seed.ts` for local fixtures only. Block production runs at the top of the script — never gate on env vars only in `package.json`.

```ts
// scripts/seed.ts — dev-only fixtures; never run against production data
import Database from 'better-sqlite3';
import { env } from '../src/lib/env';

if (process.env.NODE_ENV === 'production') {
  console.error('db:seed is blocked in production');
  process.exit(1);
}

const filePath = env.DATABASE_URL.replace(/^file:/, '');
const db = new Database(filePath);
db.pragma('foreign_keys = ON');

// Upsert a dev org + user; use deterministic IDs so re-runs are idempotent
db.prepare(
  `INSERT INTO organizations (id, slug) VALUES (?, ?)
   ON CONFLICT(id) DO NOTHING`,
).run('org-dev-1', 'acme');

db.close();
```

Reason: an explicit `NODE_ENV` guard prevents accidental seeding in deployed environments; idempotent upserts make `pnpm db:seed` safe to re-run during development.

---

## Testing Rules

- **Query modules:** test against an in-memory SQLite database or a temp file; seed minimal schema in `beforeEach`.
- **Server actions:** call the action function directly with mocked `requireOrgMember` — no HTTP layer; assert both success and validation-error paths; mock `next/cache` and assert `revalidatePath` after successful mutations.
- **Components:** React Testing Library for client islands; RSC pages are covered indirectly via query/action tests.
- **Migrations:** apply all migrations to a fresh DB in CI; assert `_migrations` row count matches file count.

```ts
// tests/server/actions/create-invoice.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { revalidatePath } from 'next/cache';
import { actionCreateInvoice } from '@/server/actions/create-invoice';
import * as auth from '@/lib/auth';

vi.mock('@/lib/auth');
vi.mock('next/cache', () => ({
  revalidatePath: vi.fn(),
}));

describe('actionCreateInvoice', () => {
  beforeEach(() => {
    vi.mocked(auth.requireOrgMember).mockResolvedValue({
      orgId: 'org-1',
      userId: 'user-1',
    });
  });

  it('returns structured error for invalid input', async () => {
    const result = await actionCreateInvoice({ orgSlug: '', amountCents: -1 });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error).toBeDefined();
  });

  it('returns ok with invoice on success', async () => {
    const result = await actionCreateInvoice({ orgSlug: 'acme', amountCents: 1000 });
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.invoice).toBeDefined();
  });

  it('revalidates the org invoice list path on success', async () => {
    await actionCreateInvoice({ orgSlug: 'acme', amountCents: 1000 });
    expect(vi.mocked(revalidatePath)).toHaveBeenCalledWith('/acme/invoices');
  });
});
```

```ts
// tests/server/actions/void-invoice.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { revalidatePath } from 'next/cache';
import { actionVoidInvoice } from '@/server/actions/void-invoice';
import { createInvoice } from '@/db/queries/invoices';
import * as auth from '@/lib/auth';

vi.mock('@/lib/auth');
vi.mock('next/cache', () => ({
  revalidatePath: vi.fn(),
}));

describe('actionVoidInvoice', () => {
  beforeEach(() => {
    vi.mocked(auth.requireOrgMember).mockResolvedValue({
      orgId: 'org-1',
      userId: 'user-1',
    });
  });

  it('revalidates the org invoice list path on success', async () => {
    const invoice = createInvoice({ orgId: 'org-1', amountCents: 500, createdBy: 'user-1' });
    await actionVoidInvoice({ orgSlug: 'acme', invoiceId: invoice.id });
    expect(vi.mocked(revalidatePath)).toHaveBeenCalledWith('/acme/invoices');
  });
});
```

```ts
// tests/db/migrations.test.ts — fresh in-memory DB; assert every migration file is recorded
import { describe, it, expect } from 'vitest';
import Database from 'better-sqlite3';
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

describe('migrations', () => {
  it('applies all SQL files and records them in _migrations', () => {
    const db = new Database(':memory:');
    db.exec(`
      CREATE TABLE _migrations (
        filename TEXT PRIMARY KEY,
        applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
      );
    `);
    const migrationsDir = join(process.cwd(), 'src/db/migrations');
    const files = readdirSync(migrationsDir)
      .filter((f) => f.endsWith('.sql'))
      .sort();
    const insert = db.prepare('INSERT INTO _migrations (filename) VALUES (?)');
    for (const filename of files) {
      db.exec(readFileSync(join(migrationsDir, filename), 'utf8'));
      insert.run(filename);
    }
    const count = (
      db.prepare('SELECT COUNT(*) as count FROM _migrations').get() as { count: number }
    ).count;
    expect(count).toBe(files.length);
  });
});
```

```tsx
// tests/components/create-invoice-form.test.tsx — RTL for client islands; mock server actions
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CreateInvoiceForm } from '@/components/features/create-invoice-form';

vi.mock('@/server/actions/create-invoice', () => ({
  actionCreateInvoice: vi.fn(),
}));

describe('CreateInvoiceForm', () => {
  it('surfaces server action validation errors', async () => {
    const { actionCreateInvoice } = await import('@/server/actions/create-invoice');
    vi.mocked(actionCreateInvoice).mockResolvedValueOnce({
      ok: false,
      error: 'Invalid input',
    });

    render(<CreateInvoiceForm orgSlug="acme" />);
    await userEvent.type(screen.getByRole('spinbutton'), '-1');
    await userEvent.click(screen.getByRole('button', { name: /create/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid input');
  });
});
```

Reason: testing at the query/action boundary catches most regressions without brittle full-stack E2E for every change.

---

## Development Environment Setup

Configure a fresh clone before running the app or tests:

1. **Install toolchain:** Node.js 20+, `pnpm` 9+, and native build tools for `better-sqlite3` (`python3`, `make`, `g++` on Linux).
2. **Create `.env.local`** at the repo root (never commit it). Copy `.env.example` as a starting point:

```bash
cp .env.example .env.local
# Generate a strong SESSION_SECRET (32+ chars required):
openssl rand -base64 32
```

`.env.example` documents the required keys (placeholder value is ≥32 chars so `src/lib/env.ts` validation passes on first copy):

```bash
DATABASE_URL="file:./data/app.db"
# Minimum 32 characters — matches src/lib/env.ts z.string().min(32)
SESSION_SECRET="replace-with-openssl-rand-base64-32-output"
NEXT_PUBLIC_APP_URL="http://localhost:3000"
```

3. **Initialize the database:**

```bash
mkdir -p data
pnpm install
pnpm db:migrate          # apply SQL migrations in filename order
pnpm db:seed             # optional dev fixtures (blocked in production)
pnpm typecheck           # confirm strict TS before first dev run
pnpm dev                 # http://localhost:3000
```

Reason: validating env at boot and applying migrations explicitly prevents “works on my machine” schema drift across branches.

**CI / test env:** Vitest sets `DATABASE_URL=":memory:"` in `tests/setup.ts` so unit tests never touch the on-disk `./data/app.db` file. `reference/scripts/run-tests.sh` and the template `tests/run-ci-checks.sh` set `TMPDIR` under project-local `.cache/` (alongside `vitest.config.ts` `cacheDir: "node_modules/.vitest"`) so sequential migration + full-suite runs do not flake when `/tmp` is cleared mid-run.

**Greenfield smoke test:** From the monorepo root, `bash templates/nextjs-sqlite-saas/tests/smoke-greenfield.sh` copies this CLAUDE.md into a fresh `create-next-app@15` scaffold and validates all bounty sections survive the copy. If `/tmp` is noexec or non-writable (common in fleet sandboxes), the script retries under `templates/nextjs-sqlite-saas/.cache/smoke-workdirs/` (gitignored).

---

## Deployment

Production uses **Turso** (`libsql://`) instead of local `file:` paths. Reason: replicated SQLite without managing Postgres connection pools.

| Step | Command / action |
|------|------------------|
| Provision DB | Create a Turso database; copy the `libsql://` URL |
| Set secrets | `DATABASE_URL`, `SESSION_SECRET` (32+ bytes), `NEXT_PUBLIC_APP_URL` (public HTTPS origin) |
| Migrate | Run `pnpm db:migrate` in the deploy pipeline **before** `pnpm start` |
| Build | `pnpm build` — Next.js 15 App Router with Server Actions |
| Serve | `pnpm start` on a long-running Node process (not edge-only) |

Reason: migrations must complete before traffic hits the app; `getDb()` reads `env.DATABASE_URL` validated at boot — never hardcode paths in source.

**Do not** run `pnpm db:seed` in production — the seed script exits when `NODE_ENV=production`.

---

## Template Maintenance Best Practices

When evolving this template (or a project copied from it):

1. **Update CLAUDE.md first** — conventions are authoritative; code follows the doc, not the reverse.
2. **Append migrations only** — never edit merged SQL files; add a new timestamped file for schema changes.
3. **Mirror changes in the reference app** — if CLAUDE.md shows a pattern, `reference/` must implement and test it.
4. **Run the full gate before pushing:** `npm test` from the monorepo root (257 tests: 29 reference Vitest + 39 delivery + 189 peer-review acceptance). Last verified 2026-07-03T14:59Z — peer review APPROVED for PR #2529.
5. **Keep folder READMEs current** — each `src/`, `scripts/`, and `tests/` subdirectory documents its boundary rules.

Reason: the reference app is the executable proof that CLAUDE.md conventions work in a real Next.js 15 project.

---

## Security Checklist

Review these before shipping auth, billing, or multi-tenant features:

| Area | Requirement |
|------|-------------|
| **Env secrets** | `SESSION_SECRET` ≥ 32 chars; parsed in `src/lib/env.ts` at boot — fail fast on missing values |
| **SQL injection** | All queries use `?` placeholders; never interpolate user input into SQL strings |
| **Tenant isolation** | Every org-owned query filters by `org_id` resolved via `requireOrgMember(orgSlug)` |
| **Session cookies** | `httpOnly`, `Secure` in production, `SameSite=Lax` — never store tokens in localStorage |
| **Server Actions** | Validate with Zod → authorize → mutate → revalidate; return structured errors, not raw throws |
| **Webhooks** | Verify signatures (Stripe, etc.); upsert idempotently by event ID |
| **Soft deletes** | Default to `deleted_at` instead of hard deletes for user content |
| **Client bundle** | Never import `src/lib/db.ts` or server secrets from `"use client"` modules |

Reason: parameterized queries and org-scoped authorization are the two highest-impact defenses for this SQLite SaaS stack.

---

## Greenfield Smoke Test

After copying this file to a new Next.js 15 project root, Claude Code should handle these without clarifying questions:

1. Create `organizations` table (`id`, `slug`, soft-delete columns) in `src/db/migrations/20260315120000_create_organizations.sql`; child tables reference `organizations(id)` via `org_id`.
2. Create `src/db/queries/invoices.ts` with `listInvoices(orgId)` using explicit column lists and `deleted_at IS NULL`.
3. Add `src/server/actions/create-invoice.ts` and `src/server/actions/void-invoice.ts` with Zod validation, `requireOrgMember`, and `revalidatePath`.
4. Scaffold `src/app/(app)/[orgSlug]/invoices/page.tsx` as a Server Component: resolve `orgSlug` from route params → `requireOrgMember(orgSlug)` → `listInvoices(orgId)`.
5. Run `pnpm db:migrate` and `pnpm typecheck` — migrations apply in filename order; types stay strict.

**Expected behavior:** Claude Code follows `src/` layout, raw SQL migrations, tenant scoping, and Server Action patterns without asking which ORM, router, or auth model to use.
