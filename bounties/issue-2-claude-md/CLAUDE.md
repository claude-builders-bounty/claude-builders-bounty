# CLAUDE.md — Next.js 15 + SQLite SaaS

You are working on a multi-tenant SaaS built with Next.js 15 (App Router) and SQLite.
Read this file before writing any code. **Every rule below has a reason** — stated
inline. If a rule seems arbitrary, the reason tells you when it is safe to break it.

## 0. Stack (pinned — do not swap without discussion)

| Layer | Choice | Pinned | Why this one |
|---|---|---|---|
| Runtime | Node.js 20+, Next.js 15 App Router | `next@15.x`, `react@19.x` | Pages Router is legacy; App Router is the only supported pattern |
| Language | TypeScript, `strict: true` | `typescript@^5.6.x` | Strict catches the null/undefined bugs that dominate SaaS support tickets |
| Database | SQLite | system SQLite ≥ 3.35 (no npm pin) | Single file, zero ops. Correct for SaaS up to ~100 GB / moderate write concurrency. Backups: `cp` when idle, `VACUUM INTO 'backup.db'` for live atomic snapshots (WAL-safe) |
| DB client (local) | `better-sqlite3` (synchronous) | latest stable (native binding — pin in lockfile, not here) | Fastest local SQLite, zero config. Sync API is fine because it runs in the Node server process |
| DB client (prod) | Turso (`@libsql/client`) | latest stable | Same SQLite dialect at the edge / serverless, where `better-sqlite3` (native binding, sync) cannot run. One dialect, two clients — SQL stays portable |
| ORM | Drizzle ORM + `drizzle-kit` | `drizzle-orm@^0.35.x` | No binary engine to download, migrations are plain readable SQL, no cold-start penalty. Prisma's engine model fights SQLite |
| Auth | Auth.js v5 (`next-auth`) | `next-auth@5.x` | **Only this one.** Lucia was deprecated by its author — do not introduce it into new code |
| Validation | Zod, schemas in `lib/validators/` | `zod@^3.24.x` | Single source of truth: the same schema validates Server Action input and drives form errors |
| Styling | Tailwind CSS | `tailwindcss@^4.0.x` | Utility classes keep styling colocated and themeable; no runtime CSS-in-JS cost |
| IDs | `createId()` from `@paralleldrive/cuid2` as `TEXT PRIMARY KEY` | latest stable | Not sequential → no ID enumeration attacks; TEXT because SQLite INTEGER PKs alias the rowid |

Pins are the minimum known-good versions — bump them deliberately with a reason, never blindly on `latest`.

**What we deliberately do NOT use:** tRPC (Server Components + Server Actions cover it; one less codegen step), Prisma, Redux/Zustand for server data (the server is the source of truth).

## 1. Folder structure

```
src/
├── app/
│   ├── (auth)/login/page.tsx        # Route groups: URL unaffected, layouts separated
│   ├── (dashboard)/
│   │   ├── layout.tsx               # Auth guard + org switcher (server)
│   │   └── projects/page.tsx        # Thin: fetch + render, no business logic
│   ├── api/webhooks/stripe/route.ts # ONLY webhooks + third-party callbacks go in api/
│   ├── layout.tsx
│   └── globals.css
├── components/ui/                   # shadcn-style primitives only (button, input…)
├── db/
│   ├── schema.ts                    # THE schema. Everything derives from here
│   ├── migrations/                  # Generated SQL. NEVER hand-edit (see §3)
│   ├── client.ts                    # getDb(): better-sqlite3 locally, libsql in prod
│   └── seed.ts
├── lib/
│   ├── auth.ts                      # Auth.js config (one place)
│   ├── validators/                  # Zod schemas, one file per domain (project.ts)
│   ├── utils.ts                     # cn(), formatDate() — truly shared only
│   └── constants.ts
├── actions/                         # Server Actions, one file per domain
│   └── projects.ts
├── hooks/                           # Client-only reusable hooks (useDebouncedValue…)
├── types/                           # Shared TS types (DTOs between server/client)
└── middleware.ts                    # Auth redirect ONLY. No DB calls here (edge runtime)
```

Why this shape:
- `actions/` is separate from `app/` because Server Actions are **callable units**,
  not pages — colocating them in route folders scatters them across the URL tree.
- Only webhooks live in `app/api/`: everything else is a Server Component or Server
  Action. API routes for CRUD are a Pages-Router habit; each one is an HTTP round-trip
  you did not need.
- `middleware.ts` does redirects only: it runs on the edge runtime where
  `better-sqlite3` cannot load. Any DB touch here crashes production while working locally.

## 2. Naming conventions

| Element | Convention | Example | Why |
|---|---|---|---|
| Component files | PascalCase | `ProjectCard.tsx` | Matches the exported component name; grep-friendly |
| Util/lib files | camelCase | `formatDate.ts` | Distinguishes non-components at a glance |
| Directories | kebab-case | `user-settings/` | URLs are kebab-case; keeps dir ↔ route mapping 1:1 |
| DB tables | snake_case, plural | `projects` | SQL convention; plural reads naturally (`FROM projects`) |
| DB columns | snake_case | `created_at` | Matches SQL, avoids quoting |
| Timestamps | `INTEGER` unix-ms, `created_at`/`updated_at` | `1735689600000` | SQLite has no real datetime type; TEXT dates sort unreliably across formats |
| Env vars | UPPER_SNAKE | `DATABASE_URL` | 12-factor, works everywhere |
| Zod schemas | PascalCase + `Schema` | `CreateProjectSchema` | Verb in the name: schemas validate *actions*, not entities |
| Server Actions | camelCase verb phrase | `createProject` | They are functions; no `Action` suffix noise |
| Tenant FK | `org_id TEXT NOT NULL` on every tenant table | — | See §7; missing it is a data-leak bug, not a style issue |

## 3. Database & migration rules (SQLite-specific — read carefully)

SQLite is not Postgres. These rules exist because the defaults will bite you.

1. **WAL mode + busy_timeout are mandatory.** On boot, `db/client.ts` runs
   `PRAGMA journal_mode = WAL` and `PRAGMA busy_timeout = 5000`.
   Why: the default rollback journal takes a database-wide write lock; WAL lets
   readers proceed during writes, and `busy_timeout` turns "database is locked"
   crashes into 5-second waits. Without these, two concurrent form submits = 500s.
2. **Never hand-edit `db/migrations/`.** Change `db/schema.ts`, run
   `npm run db:generate`, review the generated SQL, then `npm run db:migrate`.
   Why: the migration journal (`_journal.json`) tracks what has applied; a hand edit
   desyncs history and every environment diverges silently.
3. **Destructive schema changes go through explicit table-rebuild migrations**
   (create new → copy → drop → rename), reviewed by a human. Generated
   `DROP COLUMN` only works on SQLite ≥ 3.35 — the rebuild is the safe default
   regardless of version.
   Why: a migration that works on your laptop's SQLite and fails in prod is a 3 AM page.
4. **Every table gets** `id TEXT PRIMARY KEY` (cuid2), `created_at INTEGER`,
   `updated_at INTEGER` (unix ms). No exceptions — auditability and cache keys
   depend on them.
5. **Foreign keys are `ON DELETE CASCADE` for owned children**
   (e.g. `tasks.project_id → projects.id`), `ON DELETE RESTRICT` for shared
   references (e.g. `projects.org_id → orgs.id`).
   Why: deleting a project must not orphan tasks; deleting an org with projects
   must fail loudly instead of vaporizing customer data.
6. **Index every FK and every column in a WHERE clause.** SQLite does not
   auto-index foreign keys — unindexed joins on growing tables are the #1
   "it was fast in dev" production slowdown.
7. **Raw SQL only via Drizzle's `sql` template tag** (parameterized).
   String-concatenated SQL is a security bug, not a shortcut.
8. **Seeds live in `db/seed.ts`**, runnable via `npm run db:seed`, idempotent
   (upsert on natural key). Why: onboarding a new dev must be one command,
   and CI reseeds from scratch.

## 4. Data fetching

- **Server Components fetch directly.** `const projects = await db.select()…` in
  `page.tsx`. No `useEffect` for data, no client `fetch` for your own data.
  Why: `useEffect` fetching causes waterfalls, spinners, and race conditions the
  framework already solved.
- **Client components receive data as props.** Mark `"use client"` only for
  interactivity (state, event handlers). Keep them small; the parent stays server.
- **Cache with `cacheLife()` / `cacheTag()`** (Next 15, requires
  `experimental.dynamicIO: true` in `next.config.ts`), not ad-hoc memoization.
  Invalidate with `revalidateTag()` after mutations.
  Why: framework-managed cache composes with ISR; hand-rolled caches leak and stale.
- **Never `SELECT *`.** List columns explicitly.
  Why: new columns must be an explicit decision. `SELECT *` silently widens every
  API response the moment the schema changes — including sensitive columns.

## 5. Server Actions & forms

- Forms submit to Server Actions (`actions/projects.ts`), not API routes.
- Validate input with the Zod schema **first line** of the action; return
  `{ ok: false, error: "…" }` for *expected* failures (validation, permission denied).
- **Throw for *unexpected* failures** (DB down, invariant violated) — `error.tsx`
  boundaries are designed to catch thrown errors; swallowing them hides outages.
- Revalidate: `revalidateTag("projects")` (or `revalidatePath`) after every mutation.
  Why: forgetting this is the #1 "my data didn't update" bug report.
- Actions are async functions, never React components; they take plain objects,
  not `FormData`, at the boundary where you control both sides (Zod parses it anyway).
- Every file in `actions/` starts with `"use server"`. Without it the function
  silently becomes a client-callable stub that fails at runtime — the most common
  greenfield mistake with this layout.

## 6. Auth (one way)

- Auth.js v5, session in SQLite via the Drizzle adapter, config in `lib/auth.ts`.
- `middleware.ts`: redirect unauthenticated users to `/login`. Nothing else.
- Data access: `const session = await auth()` in Server Components/Actions, then
  **scope every query by `session.user.orgId`** (see §7).
- Never trust client-side auth state for authorization; it is UX hinting only.
- Secrets (`AUTH_SECRET`, OAuth client secrets) come from env, never committed.
  Why: client state is attacker-controlled; the session cookie is the only truth,
  and it is verified server-side.

## 7. Multi-tenancy

Single database, `org_id TEXT NOT NULL` on every tenant-owned table, composite
index `(org_id, id)`. Every query includes `.where(eq(table.orgId, orgId))` —
consider it part of the table name.

Why not one database per tenant: at this scale it multiplies backups, migrations,
and connection handling for isolation you do not need yet. When a tenant
outgrows the shared DB, *then* split — the `org_id` column makes the export trivial.

Why not row-level security in SQLite: SQLite has no RLS. The application layer
*is* the enforcement point, which is why the convention is absolute, not advisory.

Reference sketch (the `orgs` side of the example in §3):

```ts
// db/schema.ts
export const orgs = sqliteTable("orgs", {
  id: text("id").primaryKey().$defaultFn(() => createId()),
  name: text("name").notNull(),
  createdAt: integer("created_at").notNull().$defaultFn(() => Date.now()),
  updatedAt: integer("updated_at").notNull().$defaultFn(() => Date.now()).$onUpdateFn(() => Date.now()),
});
export const projects = sqliteTable("projects", {
  id: text("id").primaryKey().$defaultFn(() => createId()),
  orgId: text("org_id").notNull().references(() => orgs.id, { onDelete: "restrict" }),
  name: text("name").notNull(),
  createdAt: integer("created_at").notNull().$defaultFn(() => Date.now()),
  updatedAt: integer("updated_at").notNull().$defaultFn(() => Date.now()).$onUpdateFn(() => Date.now()),
}, (t) => [index("projects_org_id_idx").on(t.orgId, t.id)]);
// NOTE: $defaultFn fires on INSERT only; $onUpdateFn keeps updated_at honest.
// createId() is from @paralleldrive/cuid2 (the "cuid2()" in §0).
```

## 8. Dev commands

```bash
npm run dev            # Dev server, http://localhost:3000 (Turbopack)
npm run build          # Production build — must pass before every PR
npm run lint           # ESLint + tsc --noEmit; CI runs this, keep it green locally
npm run test           # Vitest unit tests
npm run test:e2e        # Playwright (needs `npm run build` first — it tests prod build)
npm run db:generate    # Drizzle: schema.ts → new migration SQL (review it!)
npm run db:migrate     # Apply pending migrations to DATABASE_URL
npm run db:seed        # Idempotent seed (safe to re-run)
npm run db:studio      # Drizzle Studio GUI on :4983
```

## 9. What we don't do (and why)

| Anti-pattern | Why not |
|---|---|
| Prisma | Engine binary, slow cold starts, fights SQLite. Drizzle migrations are SQL you can read |
| Lucia | Deprecated by its author. Auth.js v5 is the maintained path |
| tRPC | Server Components + Server Actions already give end-to-end types with zero codegen |
| `pages/` router | Legacy since Next 13; mixing routers doubles the mental model |
| `useEffect` for data fetching | Waterfalls, spinners, races — solved by Server Components |
| Client `fetch` to our own API for CRUD | An HTTP round-trip you did not need; use a Server Action |
| Barrel exports (`index.ts` re-exporting everything) | Slows builds, invites circular imports, complicates refactors; import from the source file |
| `any` | Use `unknown` + Zod narrowing; `any` is how runtime bugs ship |
| `SELECT *` | Schema changes break responses silently |
| DB calls in `middleware.ts` | Edge runtime: `better-sqlite3` cannot load there; crashes prod, works locally |
| Hand-edited migrations | Desyncs the journal; environments diverge silently |
| One database per tenant (now) | Operational cost without need; `org_id` keeps the split option open |
| Business logic in `page.tsx` | Pages are thin: fetch, render, delegate. Logic lives in `actions/`/`lib/` |
| Redux/Zustand for server data | The server is the source of truth; Server Components + URL state already cover it. Client stores duplicate and stale it |
| `console.log` debugging in committed code | Use the debugger or structured logging; stray logs leak into prod |

## 10. Error handling

- Route-level: `error.tsx` (catches thrown errors), `not-found.tsx`, `loading.tsx`
  (Suspense — no spinner components in page code).
- Server Actions: return `{ ok: false, error }` for expected failures;
  **throw** for unexpected ones so `error.tsx` and monitoring see them.
- Never leak internals: user-facing errors are generic ("Something went wrong"),
  details go to the error tracker with a correlation ID.
- Validate at the boundary (Zod), assert invariants inside (`if (!org) throw`).
  Why: validation handles the hostile outside; assertions catch your own bugs early.
