# CLAUDE.md

> Read this first, every session. Skim §1–§3 before touching code; jump to §4
> when you need to ship a feature.

This file describes a Next.js 15 (App Router) SaaS with SQLite for persistence.
Every rule below has a reason — when the reason is no longer true, change the
rule, do not bend it.

---

## §1. Stack & versions

We pin to these versions and only these versions:

| Layer | Choice | Why this and not the alternative |
|---|---|---|
| Framework | **Next.js 15 (App Router)** | Server Components for SSR-by-default; RSC streaming keeps TTFB short. Pages Router would force SPA hydration for everything. |
| React | **19.0.0+** | Required by Next 15; `use()` + `useFormState` removes a class of `useEffect` hacks. |
| Runtime | **Node 22 LTS** | Built-in `--watch` removes nodemon; V8 `cause` chains surface real errors. |
| Database | **SQLite via better-sqlite3 (libsql/turso for prod)** | Synchronous reads → no connection-pool footgun. WAL mode gives us concurrent readers + one writer. Remote sync (Turso) is a swap-in. |
| ORM | **Drizzle ORM** | SQL-shaped, no codegen step, single-file migrations. Prisma generates a 70MB client and locks you out of raw SQL. |
| Auth | **Auth.js v5 (next-auth@beta)** | Session in edge middleware, DB adapter is one import. |
| Styling | **Tailwind v4 + shadcn/ui (Radix primitives)** | No CSS-in-JS runtime cost; RSC serialises Radix cleanly. |
| Type-check | **TypeScript 5.4+ with `strict: true` + `noUncheckedIndexedAccess`** | The two flags that actually catch bugs. Others are noise. |
| Package manager | **pnpm 9** | Hard links save 60% disk; workspace support for free. |
| Testing | **Vitest 1.x + Playwright** | Vitest's ESM first; Playwright is the only honest e2e today. |

If a tool isn't on this list, add a row explaining why before adopting it.

---

## §2. Folder structure

```
.
├── app/                      # Next.js App Router
│   ├── (marketing)/          # unauthenticated routes (no layout auth check)
│   ├── (app)/                # authenticated SaaS shell
│   │   └── layout.tsx        # session guard + nav
│   ├── api/                  # Route Handlers (POST /api/webhooks/…)
│   └── _actions/             # Server Actions only — never imported by client components
├── src/
│   ├── server/               # code that runs in Node, never in the browser
│   │   ├── db/
│   │   │   ├── schema/       # one Drizzle table per file
│   │   │   ├── migrations/   # drizzle-kit generated SQL
│   │   │   └── client.ts     # single better-sqlite3 instance, hot reuse
│   │   ├── auth/             # Auth.js config + helpers
│   │   └── jobs/             # background work (cron, queues)
│   ├── lib/                  # isomorphic helpers (date, format, env)
│   └── ui/                   # shadcn/ui components + design tokens
├── tests/
│   ├── unit/                 # Vitest specs mirroring src/ tree
│   └── e2e/                  # Playwright specs mirroring user flows
├── drizzle.config.ts
├── next.config.ts
└── tsconfig.json
```

### Rules

- **Place server-only code under `src/server/`** and import only from Server Components, Route Handlers, or Server Actions. Importing it into a Client Component throws at build time.
- **`app/_actions/`** holds named Server Actions only. No React components, no API routes — those don't belong.
- **One Drizzle table per file.** `users.ts`, `subscriptions.ts`, `events.ts`. Avoid `db/schema.ts` 1000-line god files.
- **Tests mirror source.** If a file is `src/server/jobs/invoice.ts`, its spec is `tests/unit/server/jobs/invoice.test.ts`. Path → test path. Always.
- **Never `src/`, never `components/` at root** — the App Router owns `app/`. Mixing them breaks the routing convention.

---

## §3. SQL & migration conventions

We use Drizzle ORM with a hand-curated migration log. Treat schema the same way you'd treat production infra: every change is a PR.

### Migrations

```bash
# Local dev cycle:
pnpm db:generate      # drizzle-kit scans schema/, writes SQL to src/server/db/migrations/
pnpm db:migrate       # applies pending migrations to ./local.db
pnpm db:studio        # inspect data in the browser

# CI / prod:
pnpm db:check         # verify generated migrations are committed
```

**Never edit a committed migration.** If you need to fix something, add a new
migration. SQLite does not support down-migrations without pain; we use
`drizzle-kit push` only on local dev.

### SQL patterns we DO

- **Prepared statements everywhere.** Drizzle handles this by default; if you write raw SQL, it goes through `client.prepare()`.
- **WAL mode, `synchronous=NORMAL`, `busy_timeout=5000`** set once at startup. Without these, multi-tab dev shows `SQLITE_BUSY` at 80% concurrent reads.
- **`COUNT(*)` capped at 10k rows** by default. Anything bigger is a paginated query, not a counter.
- **Soft delete via `deleted_at INTEGER NULL`**, not `is_deleted BOOLEAN`. Integer indices are smaller and the timeline is auditable.
- **UUIDv7 primary keys.** Sortable, distributed-safe, no information leak.

### SQL patterns we DON'T

- ❌ **No `JSON1` user-facing queries without limits.** They get slow, then they get embedded in reports. Use typed columns + a versioned JSON blob for unknown shape.
- ❌ **No dynamic schema introspection at runtime.** Drizzle's metadata is build-time only — it's not a runtime feature.
- ❌ **No `SELECT *`.** Always project columns. SQLite allows it; production also has to migrate columns.
- ❌ **No `IN (subquery)` from user input.** Use Drizzle's `inArray()` with a parameterised list.

---

## §4. Component patterns

### Server Components (default)

Every component is a Server Component unless it needs:

- `onClick`, `onChange`, etc. — use `'use client'`
- `useState`, `useReducer`, browser-only APIs

```tsx
// app/(app)/dashboard/page.tsx — Server Component by default
import { db } from '@/src/server/db/client';
import { invoices } from '@/src/server/db/schema/invoices';
import { eq } from 'drizzle-orm';
import { redirect } from 'next/navigation';

export default async function DashboardPage() {
  const rows = await db.select().from(invoices).where(eq(invoices.user_id, user.id));
  return <InvoiceList rows={rows} />;
}
```

### Server Actions

Server Actions replace all `POST /api/*` mutations **except** webhooks, OAuth
callbacks, and anything called from outside the app.

```tsx
// app/_actions/create-invoice.ts
'use server';

export async function createInvoice(input: CreateInvoiceInput) {
  const session = await auth();
  if (!session) throw new Error('UNAUTHORIZED');

  const validated = schema.parse(input);
  const id = await db.insert(invoices).values(validated).returning({ id: invoices.id });
  revalidatePath('/dashboard');
  return id;
}
```

### Client Components (sparingly)

A client component is an island. Keep islands small; never wrap the layout in `'use client'`.

```tsx
'use client';
import { useFormState } from 'react-dom';
import { createInvoice } from '@/app/_actions/create-invoice';

export function InvoiceForm() {
  const [state, formAction] = useFormState(createInvoice, { ok: false });
  return <form action={formAction}>...</form>;
}
```

### shadcn/ui

Components live in `src/ui/` and are owned by us. Run `pnpm ui add button`
to copy a component from shadcn — never install it as a dep.

---

## §5. What we don't do (and why)

| Anti-pattern | Why we forbid it |
|---|---|
| **Pages Router** | Two routers, double the docs, double the bugs. App Router is the default and the only default we support. |
| **Prisma** | Too big, too slow, codegen breaks continuously in CI. Drizzle is 200kb and emits SQL you can read. |
| **CSS-in-JS (styled-components, emotion)** | Runtime cost on RSC. Tailwind v4 + shadcn covers 100% of the cases. |
| **`useEffect` for data fetching** | Use Server Components or `useSWR` in the rare Client island. Effects double-render and lose SSR. |
| **Custom Webpack config** | Use Turbopack (`next dev --turbo`). If you hit a real edge case, file an issue, don't band-aid. |
| **Yarn / npm / bun** | pnpm only. Hoisting differs across managers; lockfile drift is the #1 cause of prod bugs. |
| **`any` types** | `unknown` + a type guard, or a typed import. If you can't type it, the API is bad. |
| **`@ts-ignore`** | `@ts-expect-error` with a TODO + Linear ticket number. We do not let exceptions silent-multiply. |
| **Time libraries other than `Temporal` polyfill or `date-fns`** | Moment is dead, Luxon is dead, `Date` is wrong. Pick from the two approved options only. |
| **Manual column types in `schema/`** | Use Drizzle's `text()`, `integer()`, etc. — never `customType` without a column-level comment explaining the SQL. |

---

## §6. Dev commands

| Command | Purpose |
|---|---|
| `pnpm dev` | Next 15 + Turbopack + HMR |
| `pnpm build` | Production build |
| `pnpm typecheck` | `tsc --noEmit` with the strict flags |
| `pnpm lint` | ESLint flat config + Tailwind plugin |
| `pnpm test` | Vitest in watch mode |
| `pnpm test:run` | Vitest single-run, used in CI |
| `pnpm e2e` | Playwright, headed in dev / headless in CI |
| `pnpm db:generate` | Drizzle migration SQL generation |
| `pnpm db:migrate` | Apply migrations |
| `pnpm db:studio` | Visual DB inspector |
| `pnpm ui add <name>` | Copy a shadcn component into `src/ui/` |

---

## §7. Quick greenfield check

Before committing any new project setup, run:

```bash
pnpm install
pnpm db:generate && pnpm db:migrate
pnpm typecheck && pnpm lint
pnpm test
```

If the four commands above pass, the project is shippable.
