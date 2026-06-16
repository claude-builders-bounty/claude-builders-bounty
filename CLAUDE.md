# CLAUDE.md

Guidance for Claude Code when working in this repository. This is a **Next.js 15
(App Router) + SQLite (better-sqlite3)** SaaS application. Follow these rules
exactly. When a rule has a reason, the reason is binding too — don't "improve"
something in a way that breaks the reason.

---

## Stack & versions

| Layer       | Choice                          | Why this and not the alternative |
|-------------|---------------------------------|----------------------------------|
| Runtime     | Node.js 20 LTS                  | better-sqlite3 is a native addon; it cannot run on the Edge runtime or in the browser. Everything that touches the DB stays on Node. |
| Framework   | Next.js 15, App Router only     | Server Components let us query SQLite directly in the render path with zero client JS. The Pages Router can't, so we never use it. |
| Language    | TypeScript 5, `strict: true`    | A nullable column that the types claim is non-null is a production bug waiting to happen. Strict mode catches it at build. |
| Database    | SQLite via `better-sqlite3`     | Synchronous API → no connection pool, no `await` on every query, no race conditions from interleaved async I/O. One file, one writer, fully ACID. |
| Migrations  | Plain `.sql` files + tiny runner| The schema is the source of truth, readable in a diff, and replayable on any machine. No ORM migration magic to debug. |
| Validation  | Zod                             | One schema validates the HTTP boundary AND infers the TypeScript type. Never define a shape twice. |
| Auth        | Lucia-style session cookies     | Sessions live in our own SQLite `session` table — no external auth service, no JWT-revocation problem. |
| IDs         | `nanoid`                        | Short, URL-safe, collision-resistant. Generated in app code (`lib/id.ts`) so the ID is known before insert. |
| Styling     | Tailwind CSS                    | Co-located with markup; no separate CSS files to drift out of sync with components. |
| Package mgr | pnpm                            | Strict, content-addressed `node_modules` stops "works on my machine" phantom-dependency bugs. Commit `pnpm-lock.yaml`. |

> **The single most important fact about this stack:** `better-sqlite3` is
> **synchronous and Node-only**. Any file that imports `@/lib/db` must run on the
> Node runtime. Never add `export const runtime = 'edge'` to a route that reads
> the database. Never import the db module into a Client Component.

---

## Dev commands

```bash
pnpm install            # install deps (uses pnpm-lock.yaml)
pnpm dev                # next dev — http://localhost:3000
pnpm build              # next build (also runs `tsc --noEmit` via the build)
pnpm start              # serve the production build
pnpm typecheck          # tsc --noEmit, run this before claiming a task is done
pnpm lint               # eslint
pnpm db:migrate         # apply pending migrations in db/migrations/
pnpm db:migrate:new     # scaffold a new timestamped migration file
pnpm db:reset           # delete the .sqlite file and re-run all migrations (DEV ONLY)
pnpm test               # vitest
```

**Definition of done for any change:** `pnpm typecheck && pnpm lint && pnpm test`
all pass. Run them — do not assume.

---

## Folder structure

```
app/                      # App Router. Routes only. No business logic here.
  (marketing)/            # Route group: public pages. No layout chrome from app.
  (app)/                  # Route group: authenticated product. Shared <AppShell>.
    layout.tsx            # Guards the group: redirects to /login if no session.
    dashboard/page.tsx
  api/
    webhooks/stripe/route.ts   # Only for third parties that can't call a Server Action.
  layout.tsx              # Root layout: <html>, fonts, providers.
lib/
  db/
    index.ts              # The db singleton. The ONLY file that opens the connection.
    schema.ts             # Zod schemas + inferred TS types per table.
    queries/              # One file per table. Pure functions: (db, args) -> rows.
      users.ts
      projects.ts
  auth.ts                 # Session create/validate/destroy.
  env.ts                  # Zod-parsed process.env. Import this, never process.env directly.
actions/                  # Server Actions ("use server"). The write path for the UI.
components/
  ui/                     # Dumb, reusable primitives (Button, Input). No data fetching.
  <feature>/              # Feature components, can be Server Components that fetch.
db/
  migrations/             # 0001_init.sql, 0002_add_projects.sql ... forward-only.
  migrate.ts              # The runner invoked by pnpm db:migrate.
data/
  app.sqlite              # The database file. GITIGNORED. Never commit it.
```

**Rules that make this structure work:**

- **`app/` holds routing, not logic.** A `page.tsx` calls a query function and
  renders. If you're writing a SQL string inside `app/`, it belongs in
  `lib/db/queries/` instead — so it's testable without spinning up Next.

- **Path alias `@/` maps to the project root.** Always `import { db } from
  '@/lib/db'`, never `../../../lib/db`. Relative chains break the moment a file
  moves; the alias doesn't.

- **One queries file per table.** When you change a table's schema, every query
  that touches it is in one file you can review in one diff.

---

## Naming conventions

| Thing                     | Convention            | Example                         |
|---------------------------|-----------------------|---------------------------------|
| Files & folders           | `kebab-case`          | `lib/db/queries/billing-events.ts` |
| React components          | `PascalCase`          | `function ProjectCard() {}`     |
| Component files           | `kebab-case.tsx`      | `components/project/project-card.tsx` |
| Functions & variables     | `camelCase`           | `getUserById`                   |
| Types & interfaces        | `PascalCase`, no `I`  | `type User`, not `IUser`        |
| DB tables                 | `snake_case`, **singular** | `user`, `billing_event`    |
| DB columns                | `snake_case`          | `created_at`, `stripe_customer_id` |
| Booleans (col + var)      | `is_` / `has_` prefix | `is_active`, `hasPaid`          |
| Timestamps                | `_at` suffix, store as **unix epoch INTEGER** | `created_at INTEGER` |
| Money                     | integer **cents**, never float | `amount_cents INTEGER`   |
| Env vars                  | `SCREAMING_SNAKE_CASE`| `DATABASE_PATH`                 |

**Why these specific ones:**

- **Tables are singular** (`user`, not `users`) so a row maps cleanly to one
  `User` type and joins read like English: `project.user_id = user.id`.
- **Timestamps as unix INTEGER**, not TEXT or SQLite's `DATETIME`. SQLite has no
  real date type; storing ISO strings invites timezone ambiguity and breaks
  `ORDER BY` on mixed formats. Integers sort and compare correctly, always UTC.
- **Money in integer cents.** SQLite `REAL` is IEEE-754 floating point —
  `0.1 + 0.2 != 0.3`. You will not round customer invoices with float.

---

## SQL / migration conventions

### The connection (read this before writing any query)

`lib/db/index.ts` is the **only** place a connection is opened, and it is a
module-level singleton:

```ts
import Database from 'better-sqlite3'
import { env } from '@/lib/env'

export const db = new Database(env.DATABASE_PATH)
db.pragma('journal_mode = WAL')   // readers don't block the writer
db.pragma('foreign_keys = ON')    // OFF by default in SQLite — turn it on every connection
db.pragma('busy_timeout = 5000')  // wait, don't throw, if the single writer is busy
```

- **WAL mode is mandatory.** The default rollback journal makes every read block
  writes and vice-versa. WAL lets concurrent Server Component reads proceed while
  a write is in flight — essential under Next's parallel rendering.
- **`foreign_keys = ON` is per-connection.** SQLite ships with FK enforcement
  *off*. If you forget this pragma, `ON DELETE CASCADE` silently does nothing and
  you get orphan rows. It's in the singleton so no one can forget.
- **One connection, no pool.** better-sqlite3 is synchronous; a pool would buy
  nothing and SQLite allows only one writer anyway.

### Writing queries

- **Always use prepared statements with bound parameters.** Never interpolate
  values into SQL — that's an injection hole, and prepared statements are also
  cached and faster.

  ```ts
  // GOOD
  const getUser = db.prepare('SELECT * FROM user WHERE id = ?')
  export const findUser = (id: string) => getUser.get(id) as User | undefined

  // NEVER
  db.prepare(`SELECT * FROM user WHERE id = '${id}'`)
  ```

- **Wrap multi-statement writes in `db.transaction()`.** It's atomic *and* an
  order of magnitude faster (one fsync, not N):

  ```ts
  const createProjectWithOwner = db.transaction((p: NewProject) => {
    const project = insertProject.get(p)
    insertMembership.run(project.id, p.ownerId)
    return project
  })
  ```

- **Validate rows back into types with Zod at the boundary**, or at minimum
  `as User`. The DB returns `unknown`; don't let untyped rows leak into the app.

### Migrations

- **Forward-only, never edit an applied migration.** Files are
  `NNNN_description.sql` (e.g. `0003_add_subscription_status.sql`), applied in
  numeric order, each recorded in a `_migrations` table. Once a migration has run
  anywhere (a teammate's machine, prod), it is immutable history. Need a change?
  Add `0004_...`. Editing `0003` means two databases silently disagree on schema.

- **Each migration runs inside a transaction** by the runner, so a failing
  migration rolls back whole — you never get a half-applied schema.

- **Schema changes and the code that uses them ship in the same PR.** A migration
  without the query update (or vice-versa) is a broken `main`.

- **Migrations are pure SQL, no app code.** They must replay identically years
  from now without importing a function whose behavior has since changed.

  ```sql
  -- 0002_add_projects.sql
  CREATE TABLE project (
    id          TEXT PRIMARY KEY,              -- app-generated via nanoid (lib/id.ts), not autoincrement
    user_id     TEXT NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    created_at  INTEGER NOT NULL DEFAULT (unixepoch())
  ) STRICT;                                    -- reject wrong-typed values instead of coercing

  CREATE INDEX idx_project_user_id ON project(user_id);  -- index every FK you filter on
  ```

- **Use `STRICT` tables.** Without it SQLite happily stores `"hello"` in an
  INTEGER column (type affinity). `STRICT` makes the column type mean what it says.
- **Text primary keys generated by the app** via `nanoid` from `lib/id.ts`, not
  `INTEGER AUTOINCREMENT`. App-generated IDs are known before insert, don't leak
  row counts to customers, and survive a future move off SQLite.

---

## Component patterns

### Server Components are the default

Every component is a Server Component unless it *needs* the browser. A component
needs `"use client"` only if it uses hooks (`useState`, `useEffect`), event
handlers (`onClick`), or browser APIs. **Why default to server:** server
components ship zero JS, can query the DB directly, and never leak secrets.

```tsx
// app/(app)/dashboard/page.tsx — Server Component. Queries the DB in the render.
import { listProjects } from '@/lib/db/queries/projects'
import { requireUser } from '@/lib/auth'

export default async function DashboardPage() {
  const user = await requireUser()
  const projects = listProjects(user.id)   // synchronous SQLite call, runs on the server
  return <ProjectList projects={projects} />
}
```

### Push `"use client"` to the leaves

When you need interactivity, make a small Client Component and keep its parent on
the server. Don't make a whole page a Client Component because one button needs
`onClick` — that drags all its children (and their data fetching) to the client.

```tsx
'use client'
// components/project/delete-button.tsx — only this leaf is client.
export function DeleteButton({ projectId }: { projectId: string }) {
  return <button onClick={() => deleteProject(projectId)}>Delete</button>
}
```

### Writes go through Server Actions

Mutations use Server Actions, not hand-written `fetch` to API routes. The action
runs on Node, can hit the DB directly, validates input with Zod, and
`revalidatePath`s the affected route.

```ts
'use server'
// actions/projects.ts
import { z } from 'zod'
import { revalidatePath } from 'next/cache'
import { requireUser } from '@/lib/auth'
import { insertProject } from '@/lib/db/queries/projects'

const NewProject = z.object({ name: z.string().min(1).max(80) })

export async function createProject(formData: FormData) {
  const user = await requireUser()
  const { name } = NewProject.parse({ name: formData.get('name') }) // validate the boundary
  insertProject({ userId: user.id, name })
  revalidatePath('/dashboard')                                       // re-render with fresh data
}
```

- **API routes (`app/api/.../route.ts`) are only for callers that can't invoke a
  Server Action** — Stripe webhooks, OAuth callbacks, public/mobile APIs. The UI
  uses actions.
- **Authorize inside every action and query path, not in the UI.** Hiding a
  button is not security. `requireUser()` / ownership checks live server-side.

---

## What we don't do (and why)

- **❌ No `runtime = 'edge'` on anything that touches the DB.** better-sqlite3 is a
  native Node addon; the Edge runtime can't load it. The build may pass and then
  explode at request time.

- **❌ No DB imports in Client Components.** `'use client'` + `import { db }` bundles
  (or tries to) your database driver and credentials into the browser. Data flows
  server → client as props/serialized results, never the connection itself.

- **❌ No heavyweight ORM (Prisma) for SQLite.** Prisma adds a query engine binary,
  an async API that defeats SQLite's synchronous speed, and its own migration
  format on top of SQL. Raw queries + a thin Zod layer is faster and debuggable.
  (Drizzle is acceptable if the team wants typed query building — but never
  alongside Prisma, and migrations stay as reviewable SQL.)

- **❌ No editing applied migrations.** See the migration section. Forward-only,
  always. The fix for a bad migration is the next migration.

- **❌ No `SELECT *` in app code paths that map to types.** List the columns. A
  `SELECT *` silently changes shape when you add a column and breaks the `as User`
  cast's honesty. (It's fine in throwaway debugging.)

- **❌ No floats for money, no TEXT for timestamps.** Integer cents and unix epoch
  integers. (See naming conventions for why.)

- **❌ No business logic in `app/`.** Routes orchestrate; logic lives in
  `lib/db/queries/`, `actions/`, and `lib/`. Keeps logic testable without Next.

- **❌ No `process.env.X` scattered through the code.** Import from `@/lib/env`,
  which Zod-parses and fails loudly at boot if a var is missing — instead of a
  cryptic `undefined` deep in a request.

- **❌ No client-side data fetching for initial render.** No `useEffect(() =>
  fetch(...))` for data a Server Component can read directly. That pattern adds a
  loading spinner, a waterfall, and an API route you didn't need.

- **❌ Don't commit `data/app.sqlite` or `*.sqlite-wal` / `*.sqlite-shm`.** The DB
  is environment state, not source. It's gitignored; rebuild it with
  `pnpm db:migrate`.

---

## When in doubt

1. Could this run on the server instead of the client? Then it should.
2. Is this value coming from outside (HTTP, env, DB)? Validate it with Zod.
3. Am I about to interpolate into SQL? Use a bound `?` parameter instead.
4. Am I changing the schema? Write a new numbered migration; never edit an old one.
5. Does `pnpm typecheck && pnpm lint && pnpm test` pass? If you haven't run it, you're not done.
