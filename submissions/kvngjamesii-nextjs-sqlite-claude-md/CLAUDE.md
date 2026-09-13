# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

Opinionated rules for Claude Code on a greenfield SaaS using **Next.js 15 (App Router)** and **SQLite** (`better-sqlite3` locally, Turso/`@libsql/client` in prod). Paste this file at the repo root. Do not ask whether to use the App Router, Pages Router, Prisma, or Postgres — this file already decided.

Every rule below exists because the alternative burned us on a real SaaS.

---

## Stack & versions (pinned choices)

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js **15.x**, App Router only | RSC + Server Actions replace most Route Handlers |
| Language | TypeScript **5.5+**, `strict: true`, `noUncheckedIndexedAccess` | Indexed access bugs are silent in SaaS billing code |
| Runtime | Node **20 LTS** | `better-sqlite3` native bindings; Edge is opt-in per route |
| Package manager | **pnpm** | Hoisting lies; we want deterministic `node_modules` |
| UI | React **19**, Tailwind **v4**, shadcn/ui (Radix) | Copy components; never invent a second design system |
| DB local | `better-sqlite3` + file `./data/app.db` | Zero-ops local; same SQL dialect as Turso |
| DB prod | Turso (`@libsql/client`) | Hosted SQLite + branching for previews |
| ORM | **Drizzle ORM** + `drizzle-kit` | SQL-shaped, tiny runtime, migrations we can read |
| Validation | **Zod** at every trust boundary | Forms, Server Actions, webhooks, env |
| Auth | Session cookie + Lucia-style pattern (or Auth.js DB sessions) | JWTs in localStorage are banned |
| Payments | Stripe Checkout + Customer Portal | No custom card forms |

Do not propose Prisma, Redux, Pages Router, MongoDB, or CSS-in-JS.

---

## Dev commands

Always use `pnpm`. Prefer these names so Claude never invents scripts:

```bash
pnpm dev              # next dev --turbopack
pnpm build            # next build (typecheck included via CI)
pnpm start            # next start
pnpm lint             # eslint .
pnpm typecheck        # tsc --noEmit
pnpm test             # vitest run
pnpm test:e2e         # playwright test

pnpm db:generate      # drizzle-kit generate
pnpm db:migrate       # apply migrations (never db:push in shared envs)
pnpm db:studio        # drizzle-kit studio
pnpm db:seed          # idempotent seed for plans + demo tenant
```

Environment: copy `.env.example` → `.env.local`. Required keys: `DATABASE_URL`, `SESSION_SECRET` (≥32 chars), `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `NEXT_PUBLIC_APP_URL`.

---

## Folder structure

Feature-ish layout under `src/`. Route groups separate marketing, auth, and the product shell.

```
.
├── CLAUDE.md
├── drizzle.config.ts
├── next.config.ts
├── package.json
├── public/
├── data/                      # local SQLite file only (gitignored)
│   └── app.db
├── drizzle/
│   └── migrations/            # generated SQL only — review before apply
└── src/
    ├── app/
    │   ├── (marketing)/       # public pages; no session required
    │   ├── (auth)/            # login / signup / reset
    │   ├── (app)/             # authenticated product shell
    │   │   ├── layout.tsx     # sidebar + tenant switcher
    │   │   ├── page.tsx       # dashboard
    │   │   ├── settings/
    │   │   └── billing/
    │   ├── api/
    │   │   └── webhooks/
    │   │       └── stripe/route.ts
    │   ├── layout.tsx
    │   └── page.tsx           # marketing home OR redirect
    ├── actions/               # Server Actions only (`"use server"`)
    │   ├── auth.ts
    │   ├── billing.ts
    │   └── *.ts               # one domain per file
    ├── components/
    │   ├── ui/                # shadcn primitives
    │   └── <feature>/         # feature composites (server by default)
    ├── db/
    │   ├── client.ts          # singleton connection + PRAGMAs
    │   ├── schema.ts          # single source of truth for tables
    │   └── seed.ts
    ├── lib/
    │   ├── auth.ts
    │   ├── env.ts             # Zod-parsed process.env
    │   ├── stripe.ts
    │   └── utils.ts
    └── types/                 # shared DTOs only when Zod infer is awkward
```

### Naming conventions

- Files: `kebab-case.ts` for modules; `PascalCase.tsx` only for components that export a component as default/named matching the file.
- Server Actions: `verbNounAction` (`createProjectAction`, `cancelSubscriptionAction`).
- DB tables: plural `snake_case` (`users`, `org_members`, `subscription_items`).
- Columns: `snake_case`. IDs are `text` (ULID / UUID v7), never autoincrement integers for public IDs.
- Route folders: lowercase, match URL segments. Prefer route groups `(name)` over deep nesting.
- Env vars: `SCREAMING_SNAKE`. Public browser vars must start with `NEXT_PUBLIC_`.

---

## SQL / migration conventions

### Connection (`src/db/client.ts`)

On every process start:

1. `PRAGMA foreign_keys = ON;` — SQLite defaults to OFF; without this, `ON DELETE CASCADE` is theater.
2. `PRAGMA journal_mode = WAL;` — readers don't block writers (local `better-sqlite3`).
3. `PRAGMA busy_timeout = 5000;` — absorb short write bursts instead of failing the request.
4. Singleton via `globalThis` in dev so Hot Reload does not open N file handles.

Turso/libSQL: use the HTTP/WS client; skip local PRAGMAs that Turso manages, but keep the same Drizzle schema.

### Schema rules

- Every table has `id text PRIMARY KEY`, `created_at integer NOT NULL` (unix seconds), `updated_at integer NOT NULL`.
- Prefer `integer` unix timestamps over ISO text — smaller indexes, easy range queries.
- Soft-delete only when compliance/audit requires it (`deleted_at`); otherwise hard delete + cascade.
- Multi-tenant: every tenant-owned row has `org_id text NOT NULL REFERENCES orgs(id)`. Queries always filter by `org_id` from the session — never from the client body alone.
- Money: store Stripe amounts as **integer cents**. Never `real`/`float` for currency.

### Migrations (non-negotiable)

1. Edit `src/db/schema.ts` only.
2. `pnpm db:generate` → read the SQL in `drizzle/migrations/`.
3. `pnpm db:migrate` locally; CI applies the same files.
4. **Never** `drizzle-kit push` against shared/staging/prod.
5. **Never** hand-edit an already-applied migration. Add a new one.
6. Destructive changes (drop column/table): expand → migrate app → contract. Two PRs minimum.
7. Seed is idempotent (`INSERT … ON CONFLICT DO NOTHING` for plans).

---

## Component & data patterns

### Default to Server Components

- `page.tsx` / layouts fetch with Drizzle directly. No `useEffect` data loading.
- Add `"use client"` only for interactivity (forms with local state, charts, drag-drop).
- Pass serializable props across the RSC → client boundary. Do not pass DB clients or functions.

### Mutations = Server Actions + Zod

```ts
"use server";
import { z } from "zod";
import { db } from "@/db/client";
import { requireSession } from "@/lib/auth";

const inputSchema = z.object({
  name: z.string().trim().min(1).max(80),
});

export async function createProjectAction(raw: unknown) {
  const session = await requireSession();
  const input = inputSchema.parse(raw);
  // always scope by session.orgId
  await db.insert(projects).values({
    id: ulid(),
    org_id: session.orgId,
    name: input.name,
    created_at: Math.floor(Date.now() / 1000),
    updated_at: Math.floor(Date.now() / 1000),
  });
}
```

- Validate with Zod **inside** the action, not only in the client form.
- Return `{ ok: true, data }` / `{ ok: false, error }` — throw only for unexpected failures.
- After mutation: `revalidatePath` / `revalidateTag` for the affected UI.

### Route Handlers

Use `app/api/**/route.ts` only for:

- Stripe (or other) webhooks
- OAuth callbacks
- External machine clients

Do not build a parallel REST API for the first-party UI — that is what Server Actions are for.

### AuthZ checklist (every mutation)

1. Authenticated session?
2. Membership in `org_id`?
3. Role allows the verb (`owner`/`admin`/`member`)?
4. Resource belongs to that org?

Skip any step and you have an IDOR.

---

## Patterns to follow

- **Thin pages, fat `lib/` + `actions/`** — pages compose; business rules live in modules you can unit-test.
- **One Zod schema shared** between form and action when possible (`z.infer`).
- **Suspense boundaries** per dashboard widget; avoid one giant loading spinner.
- **Stripe webhooks are the source of truth** for subscription state; the Checkout success URL is UX only.
- **Feature flags** as DB rows or env booleans — not commented-out JSX.
- **Errors**: map known domain errors to user-safe messages; log the rest with a request id.

---

## What we don't do (and why)

| Anti-pattern | Why not |
|--------------|---------|
| Pages Router | Split mental model; no RSC story we want |
| Prisma | Heavier client; migrations less reviewable as raw SQL |
| `db:push` in CI/prod | Silent drift; no audit trail |
| Autoincrement public IDs | Leaks growth; merge-hostile across branches |
| `SELECT *` in app code | Breaks when columns are added; prefer explicit selects |
| Client-side Supabase/Firebase-style direct DB | Bypasses authZ; we own the server |
| Storing secrets in `NEXT_PUBLIC_*` | They ship to the browser |
| Floats for money | Rounding bugs become chargebacks |
| Giant `components/ui` rewrites | Stick to shadcn; customize tokens, not primitives |
| `any` to "just make it compile" | Fix the type; SaaS bugs hide in `any` |
| Catch-all `app/api/[...]/` for the product UI | Duplicates Server Actions and auth checks |
| Asking the user "Postgres or SQLite?" | This template is SQLite-only by design |

---

## Definition of done (for Claude Code)

Before finishing a task:

1. `pnpm typecheck` and `pnpm lint` are clean for touched files.
2. New tables/columns have a generated migration, not only schema edits.
3. Mutations enforce org scoping.
4. No new `"use client"` without a reason in the file header comment.
5. `.env.example` updated if a new env var was introduced.

When unsure, prefer the narrower, server-side, Zod-validated path.
