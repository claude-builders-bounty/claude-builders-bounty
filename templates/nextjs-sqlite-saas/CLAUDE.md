# CLAUDE.md

Project guidance for Claude Code. This is a **Next.js 15 (App Router) + SQLite
SaaS**. Read this fully before writing code — it encodes the decisions that are
already made so you don't re-litigate them in every task.

Every rule below has a reason. When a rule and a reason conflict with what you
were about to do, follow the rule and say why in your summary.

---

## Stack & versions

| Concern        | Choice                                   | Why this and not the alternative |
|----------------|------------------------------------------|----------------------------------|
| Framework      | **Next.js 15**, App Router only          | Server Components cut client JS and let data-fetching live next to the UI that needs it. We do **not** use the `pages/` router. |
| Language       | **TypeScript**, `strict: true`           | The DB layer and Server Actions cross trust boundaries; types are the cheapest guard. No `any` in committed code. |
| Runtime        | **Node.js 20 LTS**                       | `better-sqlite3` is a native module — it needs the Node runtime, not the Edge runtime. |
| Database       | **SQLite** via **better-sqlite3** (local/single-node) or **Turso/libSQL** (multi-region) | better-sqlite3 is synchronous and the fastest embedded option for a single server. Switch to Turso only when you actually need replicas — don't pre-optimize. |
| Query builder  | **Drizzle ORM** + **drizzle-kit**        | Typed schema, typed queries, SQL-first migrations you can read. No hidden N+1s, unlike a heavy ORM. |
| Auth           | **Auth.js (NextAuth v5)** with the Drizzle adapter | First-class App Router + Server Component support; sessions in our own SQLite, no third-party lock-in. |
| Styling        | **Tailwind CSS**                         | Co-located utility classes keep styles with markup; no separate CSS files to drift. |
| Validation     | **Zod**                                  | One schema validates the form, types the Server Action input, and documents the shape. |
| Package manager| **pnpm**                                 | Strict, fast, disk-efficient. If you see `package-lock.json`, that's a mistake — we use `pnpm-lock.yaml`. |
| Tests          | **Vitest** (unit) + **Playwright** (e2e) | Vitest shares Vite's transform with the app; Playwright tests the real auth + nav flows. |

Pin these. If a task needs a new dependency, add it with `pnpm add`, never by
hand-editing `package.json`, so the lockfile stays correct.

---

## Folder structure

```
.
├── app/                      # App Router — routes, layouts, Server Components
│   ├── (marketing)/          # public pages (route group, no auth)
│   ├── (app)/                # authenticated app (route group, guarded by layout)
│   │   ├── layout.tsx        # checks session; redirects to /login if absent
│   │   └── dashboard/
│   ├── api/                  # Route Handlers — ONLY for webhooks & 3rd-party callbacks
│   │   └── webhooks/stripe/route.ts
│   ├── layout.tsx            # root layout (html/body, providers)
│   └── globals.css
├── components/
│   ├── ui/                   # generic, app-agnostic primitives (Button, Input)
│   └── <feature>/            # feature-specific components (billing/, settings/)
├── lib/
│   ├── db/
│   │   ├── index.ts          # the single DB client (see "Data layer")
│   │   ├── schema.ts         # Drizzle table definitions — the source of truth
│   │   └── queries/          # reusable query functions, one file per entity
│   ├── auth.ts               # Auth.js config + helpers (auth(), signIn, signOut)
│   ├── actions/              # Server Actions, grouped by feature
│   └── validations/          # Zod schemas, one file per feature
├── drizzle/                  # GENERATED migrations — never hand-edit
├── drizzle.config.ts
├── middleware.ts             # lightweight redirects only (NOT auth logic)
└── tests/
```

**Rules that matter here:**

- **Route groups `(marketing)` and `(app)` are the security boundary.** The
  `(app)/layout.tsx` calls `auth()` and redirects unauthenticated users. Putting
  a page in `(app)/` is how it becomes protected — don't sprinkle auth checks per
  page, because the one you forget is the breach.
- **`app/api/` is for webhooks and OAuth callbacks ONLY.** Internal mutations are
  Server Actions, internal reads are Server Components. A Route Handler for
  internal data is a needless public HTTP surface to secure.
- **`components/ui/` knows nothing about your domain.** If a component imports
  from `lib/db` or `lib/actions`, it doesn't belong in `ui/`.
- **`lib/db/schema.ts` is the single source of truth for the data model.** Types
  flow from it via `$inferSelect` / `$inferInsert`; never redeclare row types by
  hand.

---

## Naming conventions

| Thing                      | Convention            | Example                          |
|----------------------------|-----------------------|----------------------------------|
| Route folders / segments   | `kebab-case`          | `app/(app)/team-settings/`       |
| React components           | `PascalCase`          | `BillingCard`                    |
| Component files            | match the export      | `BillingCard.tsx`                |
| Hooks                      | `useThing` camelCase  | `useCurrentUser`                 |
| Server Actions             | `verbNoun` camelCase  | `createInvite`, `cancelPlan`     |
| DB tables (Drizzle)        | `snake_case`, **plural** | `users`, `team_members`       |
| DB columns                 | `snake_case`          | `created_at`, `stripe_customer_id` |
| Booleans                   | `is_`/`has_` prefix   | `is_active`, `has_paid`          |
| Timestamps                 | `_at` suffix          | `created_at`, `deleted_at`       |
| Zod schemas                | `thingSchema`         | `createTeamSchema`               |
| Env vars                   | `SCREAMING_SNAKE`     | `DATABASE_URL`, `AUTH_SECRET`    |

Why plural snake_case tables: it's the SQL norm, reads naturally in raw queries
(`select * from team_members`), and Drizzle maps it to camelCase in TS for you,
so both sides stay idiomatic.

---

## Data layer

The DB client is created **once** and reused. Never `new Database()` inside a
request — that leaks file handles and breaks WAL.

```ts
// lib/db/index.ts
import { drizzle } from "drizzle-orm/better-sqlite3";
import Database from "better-sqlite3";
import * as schema from "./schema";

const sqlite = new Database(process.env.DATABASE_URL!.replace(/^file:/, ""));
sqlite.pragma("journal_mode = WAL");   // concurrent readers + one writer; the SQLite SaaS default
sqlite.pragma("foreign_keys = ON");    // SQLite is OFF by default — enforce FKs explicitly
sqlite.pragma("busy_timeout = 5000");  // wait, don't instantly throw, on a brief write lock

export const db = drizzle(sqlite, { schema });
```

**Rules:**

- **`db` is imported, never reconstructed.** One process, one connection.
- **Always set `journal_mode = WAL` and `foreign_keys = ON`.** SQLite ships with
  FK enforcement *off* — every orphaned row you find later is from forgetting
  this line.
- **All reads/writes go through Drizzle and live in `lib/db/queries/`.** A
  component or action calls `getTeamById(id)`, not inline SQL. This keeps the
  data shape in one place and makes the query testable.
- **Scope every multi-tenant query by the owning id.** `where(eq(rows.teamId, teamId))`
  is not optional — a missing tenant filter is a cross-tenant data leak, the
  worst class of SaaS bug.
- **Use `db.transaction()` for any multi-statement write.** better-sqlite3
  transactions are synchronous and atomic; a half-applied write corrupts state.
- **One writer.** SQLite serializes writes. Don't fan out concurrent write jobs;
  batch them in a transaction instead.

### Querying from Server Components

Server Components may call query functions directly — no API round-trip:

```tsx
// app/(app)/dashboard/page.tsx
import { auth } from "@/lib/auth";
import { getTeamsForUser } from "@/lib/db/queries/teams";

export default async function DashboardPage() {
  const session = await auth();              // guaranteed by (app)/layout, but re-read for the id
  const teams = await getTeamsForUser(session!.user.id);
  return <TeamList teams={teams} />;
}
```

---

## SQL / migration conventions

Migrations are **generated from `schema.ts`**, reviewed, then applied. The
workflow is non-negotiable because it's what keeps the schema and the migrations
honest.

1. Edit `lib/db/schema.ts` (add a column, table, index).
2. `pnpm db:generate` — drizzle-kit diffs the schema and writes a new SQL file
   into `drizzle/`.
3. **Read the generated SQL.** This is a code review step, not a formality.
4. `pnpm db:migrate` to apply.

**Rules:**

- **Never hand-edit a file in `drizzle/` after it's been applied anywhere.** A
  migration is an immutable record. To change a shipped migration, write a new
  one.
- **Never `db:push` against production.** `push` skips the migration history and
  silently diverges environments. It's fine for the very first local spike, then
  switch to generate+migrate.
- **Every table gets `id`, `created_at`, and `updated_at`.** Use `text` UUIDs
  (`crypto.randomUUID()`) for ids, not autoincrement — UUIDs don't leak row
  counts and don't collide if you ever shard to Turso.
- **Soft-delete with `deleted_at timestamp` where history matters; never hard-DELETE
  billing or audit rows.** A merchant dispute six months later needs the record.
- **Index every foreign key and every column you filter or sort on in a hot path.**
  SQLite won't warn you; an unindexed `where team_id = ?` is a full table scan.
- **Store money as integer cents (`integer`), never float.** Floating point and
  currency don't mix; `0.1 + 0.2 !== 0.3`.
- **Store timestamps as Unix epoch integers or ISO-8601 text, consistently.** Pick
  one (Drizzle's `integer({ mode: "timestamp" })` is the default here) and never
  mix.

Example schema row:

```ts
// lib/db/schema.ts
import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";
import { sql } from "drizzle-orm";

export const teams = sqliteTable("teams", {
  id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
  name: text("name").notNull(),
  ownerId: text("owner_id").notNull().references(() => users.id),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull().default(sql`(unixepoch())`),
  updatedAt: integer("updated_at", { mode: "timestamp" }).notNull().default(sql`(unixepoch())`),
});
```

---

## Component patterns

- **Server Components by default.** Add `"use client"` only when you need state,
  effects, or browser APIs. The directive is contagious — put it on the smallest
  leaf, not on a page that then ships the whole tree to the client.
- **Mutations are Server Actions, validated with Zod at the top.** Never trust the
  client; never accept an unparsed payload.

  ```ts
  // lib/actions/teams.ts
  "use server";
  import { auth } from "@/lib/auth";
  import { createTeamSchema } from "@/lib/validations/teams";
  import { insertTeam } from "@/lib/db/queries/teams";

  export async function createTeam(formData: FormData) {
    const session = await auth();
    if (!session?.user) throw new Error("Unauthorized");      // authz FIRST
    const data = createTeamSchema.parse(Object.fromEntries(formData));  // validate SECOND
    return insertTeam({ ...data, ownerId: session.user.id });
  }
  ```

- **Authorize before you validate, validate before you touch the DB.** Every
  Server Action follows that order. The check you skip is the one that's
  exploited.
- **Fetch data in the Server Component that renders it.** Don't lift fetching into
  a client component with `useEffect` — that reintroduces loading spinners and
  waterfalls Server Components exist to remove.
- **Use `loading.tsx` and `error.tsx` per route segment** for streaming and
  graceful failures, instead of manual `isLoading` flags.
- **Keep client state local.** Reach for `useState`/`useReducer` and URL search
  params before adding any global store. Most SaaS screens need neither.
- **`revalidatePath`/`revalidateTag` after a mutation** so the UI reflects the new
  state without a full reload.

---

## Auth

- **Auth.js (NextAuth v5) is the only auth.** Config in `lib/auth.ts`, sessions in
  our SQLite via the Drizzle adapter.
- **Protect routes with the `(app)` layout, not middleware.** `middleware.ts` is
  for cheap redirects; real session checks belong in the Server Component layout
  where you can read the full session and the DB.
- **Read the user via `await auth()` server-side.** Don't pass the user id from
  the client and trust it — derive it from the session every time.
- **Secrets live in env (`AUTH_SECRET`, provider keys), never in code or the
  repo.** Commit a `.env.example` with empty values; `.env*` is gitignored.

---

## Commands

```bash
pnpm dev              # start the dev server (Turbopack)
pnpm build            # production build
pnpm start            # serve the production build
pnpm lint             # eslint
pnpm typecheck        # tsc --noEmit  (run before every commit)
pnpm test             # vitest unit tests
pnpm test:e2e         # playwright

pnpm db:generate      # generate a migration from schema.ts changes
pnpm db:migrate       # apply pending migrations
pnpm db:studio        # drizzle-studio: browse the DB
# pnpm db:push        # local spike ONLY — never against shared/prod
```

Before committing, run `pnpm typecheck && pnpm lint && pnpm test`. CI runs the
same; failing locally first is faster.

---

## Testing

- **Unit-test query functions and Server Actions against an in-memory SQLite**
  (`new Database(":memory:")` + migrate). They run in milliseconds and exercise
  real SQL, not mocks.
- **Mock at the boundary, not the DB.** Stub Stripe and email; use a real
  (in-memory) database. A mocked DB tests your mock, not your schema.
- **E2e the auth flow and one full mutation path with Playwright** (sign in →
  create something → see it persist). Those are the flows that break on upgrades.
- **Every bug fix gets a regression test** that fails before the fix.

---

## What we don't do (and why)

- **No `pages/` router.** Mixing routers splits conventions and confuses
  data-fetching. App Router only.
- **No client-side data fetching for first paint** (`useEffect` + `fetch` in a
  component). It defeats Server Components, adds spinners, and creates waterfalls.
- **No internal REST API for our own UI.** Server Components read; Server Actions
  write. A `/api` route for internal data is an extra public surface to secure
  for no benefit.
- **No ORM other than Drizzle, no raw `sqlite.prepare()` scattered in components.**
  Centralizing queries in `lib/db/queries/` is what makes them testable and
  tenant-safe.
- **No `db:push` to shared environments.** It bypasses migration history and
  diverges schemas silently.
- **No floats for money, no client-trusted ids, no missing tenant filters.** These
  are the three quiet correctness/security bugs that bite SaaS apps; they're
  banned, not discouraged.
- **No secrets in the repo, no `.env` committed.** Use `.env.example`.
- **No `any`, no `// @ts-ignore` without a one-line reason comment.** `strict` is
  on for a reason; silencing it hides the bug it found.
- **No connection-per-request to SQLite.** One client, WAL mode, busy_timeout.
  Anything else fights SQLite's single-writer model.
- **No long-running work inside a Server Action/request** (sending bulk email,
  video processing). Enqueue it; the request should return fast.

---

When in doubt: read `lib/db/schema.ts` for the data model, `lib/auth.ts` for who
the user is, and the nearest `loading.tsx`/`error.tsx` for the UX contract. If a
task seems to require breaking a rule here, surface that in your summary rather
than breaking it silently.
