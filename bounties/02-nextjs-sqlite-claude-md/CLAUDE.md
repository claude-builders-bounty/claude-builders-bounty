# CLAUDE.md — Next.js 15 + SQLite SaaS

Opinionated agent guide for a greenfield **Next.js 15 App Router** product with **SQLite** (`better-sqlite3` locally, Turso-compatible SQL).

If a request conflicts with this file, **follow this file** unless the user explicitly overrides.

---

## Stack & versions

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js **15** App Router only | RSC + server actions; no Pages Router dual stack |
| Language | TypeScript **strict** | Catch null/undefined at compile time |
| DB | SQLite via `better-sqlite3` (dev) / **libSQL/Turso** (prod-compatible SQL) | Single-file local, SQL that ports to Turso |
| Migrations | Numbered SQL files in `db/migrations/` | Reviewable diffs; no magic ORM auto-migrate in prod |
| Auth | Server-side session cookie + hashed password (or Auth.js if already chosen) | Keep auth out of client bundles |
| Styling | Tailwind CSS + `cn()` helper | Fast UI without CSS modules sprawl |
| Validation | Zod at every boundary | Forms, server actions, webhooks |
| Package manager | `pnpm` | Fast, strict lockfile |

**Do not introduce:** Pages Router, Prisma Migrate without discussion, MongoDB, Redux, CSS-in-JS runtime.

---

## Folder structure

```text
app/                    # App Router only
  (marketing)/          # Public marketing routes
  (app)/                # Authenticated product shell
  api/                  # Route handlers (webhooks, rare public APIs)
  layout.tsx
  globals.css
components/
  ui/                   # Dumb presentational pieces
  forms/                # Form UIs bound to server actions
lib/
  db.ts                 # Single DB client export
  auth.ts               # Session helpers
  validators/           # Zod schemas
  utils.ts              # cn(), formatting
db/
  migrations/           # 001_init.sql, 002_....sql
  migrate.ts            # Applies migrations in order
scripts/                # One-off CLI (seed, backfill)
```

**Rules**
- Feature code lives under `app/(app)/<feature>/` with colocated `_components` if private.
- Never import server-only modules (`better-sqlite3`, secrets) into client components.
- Mark server-only files with `import "server-only"`.

---

## Naming conventions

| Thing | Convention | Example |
|-------|------------|---------|
| React components | PascalCase file | `InvoiceList.tsx` |
| Server actions file | `actions.ts` next to the route | `app/(app)/invoices/actions.ts` |
| Zod schemas | `camelCase` + `Schema` suffix | `createInvoiceSchema` |
| SQL tables | `snake_case` plural | `invoices`, `invoice_items` |
| SQL columns | `snake_case` | `created_at`, `user_id` |
| Env vars | `SCREAMING_SNAKE` | `DATABASE_URL`, `SESSION_SECRET` |

Route segments: **kebab-case** (`/billing-settings`).

---

## Database & migrations

1. Schema changes = **new** `db/migrations/NNN_description.sql` (never edit applied migrations).
2. Migrations are **pure SQL**, idempotent only when safe (`CREATE TABLE IF NOT EXISTS` for bootstrap only).
3. Every table gets: `id` (text UUID or integer PK — pick one per project and stick to it), `created_at`, `updated_at`.
4. Foreign keys **ON**; enable `PRAGMA foreign_keys = ON` on every connection.
5. Money: store as **integer cents** (`amount_cents`), never float.
6. Soft delete: `deleted_at` nullable timestamp; default queries filter `deleted_at IS NULL`.

`lib/db.ts` responsibilities:
- open connection once (singleton in dev)
- set pragmas
- export typed query helpers, not a second ORM

**Anti-pattern:** string-building SQL from user input. Use bound parameters only.

---

## Component & server patterns

### Prefer

- **Server Components** for data fetch.
- **Server Actions** for mutations (`"use server"`), validate with Zod first.
- `revalidatePath` / `revalidateTag` after mutations.
- Thin client components only for interactivity (forms with pending state, dialogs).

### Avoid

- `useEffect` data fetching for first paint.
- Passing whole DB rows to the client when a DTO would do.
- Catch-all `try/catch` that swallows errors without logging.
- `any` types to “just make it build”.

### Example mutation shape

```ts
"use server";
export async function createInvoice(input: unknown) {
  const data = createInvoiceSchema.parse(input);
  const user = await requireUser();
  // insert with bound params
  revalidatePath("/invoices");
}
```

---

## Dev commands

```bash
pnpm install
pnpm dev                 # next dev
pnpm build && pnpm start
pnpm db:migrate          # node db/migrate.ts
pnpm db:seed             # optional
pnpm lint
pnpm test                # if present
```

Document exact scripts in root `package.json`; if a script is missing, **add it** rather than inventing ad-hoc node one-liners in chat.

---

## What we don’t do (and why)

| Don’t | Why |
|-------|-----|
| Dual Pages + App Router | Double mental model, broken layouts |
| Client-side secret env | Leak risk |
| Auto-migrate on every request | Race conditions + surprise schema drift |
| Float money | Rounding bugs |
| Giant `utils.ts` god file | Split by domain (`lib/invoices.ts`) |
| Skip Zod “because TypeScript” | Runtime is untyped HTTP/forms |
| Add a new state library early | Server components + URL state first |

---

## Agent workflow

When implementing a feature:

1. Read this file + existing `db/migrations` and matching feature folder.
2. Add/adjust Zod schema → migration (if schema change) → server action → UI.
3. Run migrate + lint before claiming done.
4. Prefer smallest diff that satisfies the request.

When unclear: choose the option that keeps **one database**, **server-first data**, and **strict types**.
