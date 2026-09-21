# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

Opinionated project rules for Claude Code. Paste into the repo root of a greenfield
Next.js 15 (App Router) + SQLite SaaS. Prefer Turso (`@libsql/client`) in production
and `better-sqlite3` only for local/scripts.

## Stack & versions (pin these)

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js **15** App Router (`app/`) | RSC + Route Handlers are the default path; Pages Router is legacy here. |
| Language | TypeScript **strict** | Catch null/undefined at edit time, not in prod. |
| UI | React 19 + Tailwind CSS 4 (or 3 if locked) | Utility-first keeps design tokens in one place. |
| DB | SQLite via **Turso/libSQL** in prod; `better-sqlite3` for local CLI/migrations | One SQL dialect; edge-friendly replicas later without rewriting queries. |
| Migrations | SQL files in `db/migrations/` applied by a tiny Node script | No magic ORM migrations; reviewable diffs. |
| Auth | Session cookies (iron-session / Lucia / Auth.js DB sessions) | JWT-in-localStorage is out of scope for this template. |
| Validation | Zod at every boundary | Forms, Route Handlers, and webhooks share the same schemas. |
| Package manager | `pnpm` | Fast, strict peer deps; lockfile is source of truth. |

Do **not** add Prisma/Drizzle unless the human explicitly asks — keep SQL visible.

## Folder structure

```
app/
  (marketing)/          # public pages, no auth
  (app)/                # authenticated product shell
    layout.tsx
    dashboard/
  api/                  # Route Handlers only (no Pages API)
components/
  ui/                   # primitives (Button, Input) — no business logic
  features/             # domain widgets (BillingCard, OrgSwitcher)
db/
  migrations/           # 0001_init.sql, 0002_*.sql (ordered)
  schema.sql            # optional dumped view of current schema
  client.ts             # single getDb() factory
lib/
  auth.ts
  env.ts                # Zod-parsed env
  money.ts              # integer cents helpers
scripts/
  migrate.ts
  seed.ts
tests/
  unit/
  integration/
```

Naming:
- Files: `kebab-case.ts` for modules; `PascalCase.tsx` for components.
- DB tables: `snake_case` plural (`org_members`).
- Columns: `snake_case` (`created_at`, `user_id`).
- Route segments: `kebab-case` (`/settings/billing`).

## Dev commands

```bash
pnpm install
pnpm dev                 # next dev --turbopack if available
pnpm build && pnpm start
pnpm db:migrate          # node --import tsx scripts/migrate.ts
pnpm db:seed
pnpm test                # vitest
pnpm lint && pnpm typecheck
```

Env (via `lib/env.ts`):
- `DATABASE_URL` — required (file: or libsql:)
- `SESSION_SECRET` — >=32 chars
- `APP_URL` — canonical origin

## SQL / migration rules

1. **Every schema change is a new numbered SQL file.** Never edit an already-applied migration.
2. Migrations are **forward-only** in this template. Prefer additive changes; destructive changes require a written rollback note in the PR.
3. Use **integer cents** for money (`price_cents INTEGER NOT NULL`). Never `REAL` for currency.
4. Timestamps: `created_at TEXT NOT NULL DEFAULT (datetime('now'))` (ISO UTC) unless you standardize on unix integers — pick one and stick to it.
5. Foreign keys: `PRAGMA foreign_keys = ON` on every connection.
6. Soft deletes only when product needs undo; otherwise hard delete + audit table.
7. Access the DB **only** through `getDb()` in `db/client.ts`. No ad-hoc `new Database()` in components.

Example migration header:

```sql
-- 0003_add_org_billing.sql
-- why: per-org Stripe customer id for SaaS billing
ALTER TABLE orgs ADD COLUMN stripe_customer_id TEXT;
CREATE UNIQUE INDEX orgs_stripe_customer_id_uq ON orgs(stripe_customer_id)
  WHERE stripe_customer_id IS NOT NULL;
```

## Component & data patterns

**Do**
- Server Components by default; add `"use client"` only for interactivity.
- Fetch in Server Components / Route Handlers; pass serializable props down.
- Co-locate Zod schemas with the feature (`lib/schemas/org.ts`).
- Return typed `Result` / throw `HttpError` mapped to status codes in Route Handlers.
- Keep server secrets out of Client Components (no `process.env.SECRET` in client bundles).

**Route Handler sketch**

```ts
import { z } from "zod";
import { getDb } from "@/db/client";
import { requireSession } from "@/lib/auth";

const Body = z.object({ name: z.string().min(1).max(80) });

export async function POST(req: Request) {
  const session = await requireSession();
  const body = Body.parse(await req.json());
  const db = getDb();
  // ...parameterized SQL only
  return Response.json({ ok: true }, { status: 201 });
}
```

**Server Actions (forms / mutations from RSC)**

Prefer Server Actions for cookie-auth form posts; keep Route Handlers for webhooks and external clients.

```ts
"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import { getDb } from "@/db/client";
import { requireSession } from "@/lib/auth";

const Input = z.object({ name: z.string().min(1).max(80) });

export async function createOrg(raw: unknown) {
  const session = await requireSession();
  const input = Input.parse(raw);
  const db = getDb();
  // parameterized INSERT … RETURNING id
  revalidatePath("/dashboard");
  return { ok: true as const };
}
```

Rules:
- Mark the module `"use server"` (or the export) — never import server-only DB code into a Client Component.
- Validate with Zod at the action boundary; treat `FormData` as untrusted.
- Return serializable results; throw typed errors the UI can map.
- Call `revalidatePath` / `revalidateTag` after mutations so RSC trees refresh.
- Do not put Stripe secret keys or `SESSION_SECRET` in action files that are also imported by client trees.

## What we don't do (and why)

| Anti-pattern | Why not |
|--------------|---------|
| Pages Router | Splits mental model; App Router is the product surface. |
| ORM-first schema | Hides SQL; SQLite is simple enough to own. |
| `any` / disabling strict | Undoes TypeScript's value for a SaaS codebase. |
| Client-side DB access | Secrets + CORS nightmare; keep SQLite server-side. |
| Float money | Rounding bugs in billing. |
| Global mutable singletons beyond `getDb()` | Hard to test; prefer request-scoped helpers. |
| Giant `utils.ts` | Prefer `lib/<domain>.ts`. |
| Feature flags in random JSON files | Use env + DB table if needed; document defaults. |
| Committing `.env` | Use `.env.example` only. |

## Claude Code working agreements

1. Before large refactors, list files you will touch and wait for a short plan approval if the change spans >5 files.
2. Prefer editing existing patterns over introducing new libraries.
3. After DB changes: add migration + update any seed/scripts + run `pnpm db:migrate` in instructions.
4. Never invent Stripe/Turso API shapes — read installed SDK types.
5. Tests: add at least one integration test for new Route Handlers that mutate data.

## Quick checklist for a new feature

- [ ] Zod schema at the boundary (action, Route Handler, or form)
- [ ] Migration if schema changes
- [ ] Server Component, Server Action, or Route Handler owns data access
- [ ] Money in cents
- [ ] No secrets in client bundles
- [ ] `pnpm typecheck` clean
- [ ] Mutating path has at least one integration or action test
