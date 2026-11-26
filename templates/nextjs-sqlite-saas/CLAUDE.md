# CLAUDE.md — Next.js 15 + SQLite SaaS

You are working in a production SaaS codebase. Everything below is a decision
that has already been made; follow it instead of proposing alternatives. If a
task genuinely conflicts with a rule here, say so and quote the rule before
doing anything else.

## 1. Stack & versions (do not upgrade without a task)

| Layer | Choice | Why this and not the alternative |
|---|---|---|
| Framework | Next.js 15.x, **App Router only** | Server Components remove the "where does this run" ambiguity that Pages Router never solved |
| Language | TypeScript 5.x, `strict: true` | Non-strict TS in a server/client boundary codebase hides the exact bugs that hurt most (undefined props crossing `use client`) |
| Runtime | Node 20 LTS (`nodejs20.x`) | better-sqlite3 ships prebuilt binaries for 20; Node 22 changes are still settling |
| DB | SQLite via **better-sqlite3** | Synchronous API means no connection pool, no async transaction bugs, and ~5 µs queries. A network DB buys nothing at single-node SaaS scale |
| DB hosting | Local file `./data/app.db`, WAL mode | WAL gives concurrent readers + one writer, with zero ops |
| Migrations | Hand-written SQL files + a 40-line runner | Drizzle/Prisma generate SQL you must still review; at this size the generator is the cost, not the benefit |
| Validation | Zod at every boundary | The only place a type can be wrong is runtime input |
| Auth | `iron-session`-style encrypted cookies | No third-party session store, no JWT revocation problem |
| Styling | Tailwind 3.x + `clsx` | Boring, greppable, no CSS-in-JS runtime |
| Forms | React Server Actions + `useFormState` | One round trip, no client-side API layer to keep in sync |
| Tests | Vitest (unit) + Playwright (one happy-path E2E) | Fast unit loop; one E2E proves the wiring |
| Package manager | **pnpm**, lockfile committed | `npm install` on a stale lockfile is how production drifts |

Versions are pinned in `package.json` with exact versions. `^` and `~` are
allowed only for dev tooling.

## 2. Folder structure

```
app/
  (marketing)/              # public pages, no auth
    page.tsx
    pricing/page.tsx
  (app)/                    # authenticated shell
    layout.tsx              # reads session, redirects if absent
    dashboard/page.tsx
    settings/
      page.tsx              # Server Component: data
      settings-form.tsx     # Client Component: 'use client'
  api/
    webhooks/stripe/route.ts
  layout.tsx
  globals.css
components/
  ui/                       # dumb, reusable: button.tsx, input.tsx, card.tsx
  <domain>/                 # feature-scoped: billing/, projects/
lib/
  db/
    client.ts               # the single better-sqlite3 instance
    schema.sql              # canonical schema, mirrors migrations
    migrate.ts              # migration runner
    migrations/
      0001_init.sql
      0002_add_projects.sql
  auth/
    session.ts
  env.ts                    # Zod-parsed process.env, throws at boot
  money.ts                  # integer cents helpers
db/
  seed.ts
tests/
  unit/
  e2e/
data/
  app.db                    # gitignored
```

Rules:
- **One feature = one folder.** A component used by two features moves to
  `components/ui/`; otherwise it stays next to its feature. Reason: deleting a
  feature should be one `rm -rf` of a folder, not a hunt.
- **`lib/` never imports from `app/` or `components/`.** Dependency direction is
  `app → components → lib`. Reason: a cycle through `app/` makes every import
  graph ambiguous and breaks test isolation.
- **No `utils.ts`, no `helpers.ts`.** A file with no domain name becomes the
  junk drawer; name the concern (`money.ts`, `slug.ts`, `dates.ts`).
- **Nothing outside `app/` may use `next/headers`.** Only route handlers and
  Server Components have a request context.

## 3. Naming conventions

| Thing | Convention | Example |
|---|---|---|
| Files (components) | `kebab-case.tsx` | `settings-form.tsx` |
| Files (modules) | `kebab-case.ts` | `session.ts` |
| React components | `PascalCase` export | `export function SettingsForm()` |
| Hooks | `useX` | `useOptimisticRows` |
| Server Actions | `verbNoun` + `'use server'` file | `updateProject()` in `actions.ts` |
| DB tables | plural `snake_case` | `projects`, `invoice_lines` |
| DB columns | `snake_case` | `created_at` |
| TS variables | `camelCase`; DB rows keep snake_case | `row.created_at` |
| Env vars | `SCREAMING_SNAKE`, prefix by service | `STRIPE_SECRET_KEY` |
| Migrations | `NNNN_snake_description.sql`, zero-padded, never renumbered | `0003_add_invoice_lines.sql` |

**`snake_case` in the DB and `camelCase` in TS is deliberate and enforced at the
boundary** (`lib/db/map.ts`). Reason: SQL is case-insensitive on identifiers,
JS is not; renaming in one place only is how "column not found" bugs appear.

## 4. SQL & migration conventions

```ts
// lib/db/client.ts — the only place a Database is constructed
import Database from 'better-sqlite3';
import { env } from '@/lib/env';

const db = new Database(env.DATABASE_PATH);
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');
db.pragma('busy_timeout = 5000');
export default db;
```

Rules, each with the failure it prevents:

1. **All schema changes go through a numbered migration.** No `db.exec()` at
   runtime, no `CREATE TABLE IF NOT EXISTS` in a route handler. Reason: a schema
   that appears in two places is a schema that diverges in production.
2. **Migrations are forward-only and immutable.** A shipped migration is never
   edited; a mistake gets a new `NNNN_fix_*.sql`. Reason: environments that
   already ran the old file keep the old result, so edits silently fork the
   schema.
3. **Every migration is a single transaction** and must be safe to re-run on a
   fresh DB: `BEGIN; … COMMIT;` written by the runner, not by the file.
4. **`PRAGMA foreign_keys = ON` is assumed.** Foreign keys are declared
   `REFERENCES other(id) ON DELETE CASCADE` or `ON DELETE RESTRICT` — never left
   implicit. Reason: SQLite defaults to *off* and silently accepts orphans.
5. **Timestamps are `TEXT` ISO-8601 UTC** (`strftime('%Y-%m-%dT%H:%M:%fZ','now')`),
   never `DATETIME` or local time. Reason: SQLite has no timezone type; storing
   local time guarantees a DST incident.
6. **Money is `INTEGER` cents**, named `*_cents`. Reason: floats and currency do
   not mix.
7. **Indexes are added in the migration that adds the query**, not "later".
   `CREATE INDEX idx_projects_user_created ON projects(user_id, created_at DESC)`
   — the column order follows the WHERE-then-ORDER-BY shape of the query.
8. **No queries in components.** Data access lives in `lib/db/queries/<domain>.ts`
   and is typed with an explicit `Row` interface. Reason: a `db.prepare()` inside
   JSX cannot be unit-tested or cached.
9. **Prepared statements are module-level constants**, not per-call:
   ```ts
   const selectProject = db.prepare<[string], ProjectRow>(
     'SELECT * FROM projects WHERE id = ?',
   );
   ```
   Reason: preparing per request adds ~50 µs and defeats statement caching.
10. **Multi-statement writes use `db.transaction()`** and never nest.
    Reason: better-sqlite3 transactions are synchronous; nesting throws.
11. **`LIMIT` is mandatory on every list query**, default 50, max 200, and the
    cursor is `(created_at, id)`. Reason: unbounded lists are how a single-node
    DB falls over.
12. **No `SELECT *` outside the typed query layer** — select the columns the
    mapper declares, so a new column cannot silently change a payload.

## 5. Component & route patterns

- **Server Component by default.** Add `'use client'` only when the file uses
  state, effects, refs, or browser APIs. Never add it "to be safe": it moves the
  whole subtree into the browser bundle.
- **Data flows down, actions flow up.** A Client Component never fetches data it
  could have received as props; a Server Component never calls a Server Action
  defined in a Client file.
- **Server Actions are the write path.** No `fetch('/api/...')` from the app's
  own UI. Reason: internal HTTP adds a hop, a JSON contract, and a CORS class of
  bugs for nothing.
- **Validate at the edge of every action**:
  ```ts
  'use server';
  const schema = z.object({ projectId: z.string().uuid(), name: z.string().min(1).max(120) });
  export async function updateProject(_prev: FormState, formData: FormData) {
    const parsed = schema.safeParse(Object.fromEntries(formData));
    if (!parsed.success) return { ok: false, errors: parsed.error.flatten().fieldErrors };
    const session = await requireSession();            // throws/redirects, never returns null
    ...
  }
  ```
- **Authorise inside the query, not only in the UI.** Every mutation re-checks
  `session.user.id` against the row owner in SQL (`WHERE id = ? AND user_id = ?`).
  Reason: UI guards are cosmetic; the action is the security boundary.
- **Error shape is fixed**: `{ ok: boolean; message?: string; fieldErrors?: Record<string, string[]> }`.
  No thrown errors across the action boundary.
- **`revalidatePath()` after a mutation**, never `router.refresh()` from the client.
- **`loading.tsx` per route segment**, no global spinner component.
- **Accessibility is part of the component**: every interactive element is a real
  `<button>`/`<a>`, every input has a `<label htmlFor>`, focus is never removed
  without a visible replacement.
- **No component over ~120 lines.** Split by responsibility (`*-form.tsx` for the
  inputs, `*-list.tsx` for the rows).

### Route handler rules
- `app/api/**` is reserved for **webhooks and machine clients** only, and every
  handler verifies its signature before parsing the body.
- Handlers export `runtime = 'nodejs'` explicitly (better-sqlite3 needs Node).
- A handler returns `Response.json()` with an explicit status; no `NextResponse`
  sugar that hides the status.

## 6. Dev commands (memorise these, do not invent scripts)

```bash
pnpm install                      # deps
pnpm db:migrate                   # apply pending migrations
pnpm db:seed                      # deterministic seed data
pnpm dev                          # next dev on :3000
pnpm test                         # vitest unit
pnpm test:e2e                     # playwright happy path
pnpm lint && pnpm typecheck       # tsc --noEmit, no build needed
pnpm build                        # production build (CI parity)
```

`pnpm db:reset` drops `./data/app.db`, re-migrates and re-seeds — **local only**,
refuses to run when `NODE_ENV=production`.

## 7. Environment & secrets

- `lib/env.ts` parses `process.env` with Zod at import time and throws on boot.
  Missing config must fail at startup, not at the first request.
- `.env.example` is the contract; a new variable is added there in the same
  commit that reads it.
- Secrets never reach a Client Component: only `NEXT_PUBLIC_*` may cross the
  boundary, and those are never secrets.

## 8. What we don't do (and why)

| Anti-pattern | Why not |
|---|---|
| Prisma / Drizzle ORM | Generated SQL you still review, plus a query engine you cannot `EXPLAIN`; at one SQLite file the abstraction costs more than it saves |
| `pages/` directory, `getServerSideProps` | Two routing models in one repo guarantees a wrong assumption in every task |
| Client-side data fetching (`useEffect` + `fetch`) for own-API data | Duplicates the server's authority, breaks caching, and needs loading/error states that Server Components already solve |
| Redux / Zustand for server state | Server state belongs on the server; a client store is a second source of truth |
| Global CSS resets per component | Tailwind handles resets once; per-component resets fight each other |
| `any`, `as unknown as T`, `@ts-ignore` | These are the three ways a typecheck stops meaning anything; use `unknown` + a Zod parse |
| `useEffect` for derived state | Derived values belong in render; effects add a frame of stale UI |
| `console.log` in committed code | Use the seeded `logger` (`lib/log.ts`); unstructured logs are unsearchable at 3 a.m. |
| Multi-tenant row-level scoping by convention | Tenant id is passed explicitly to every query function and asserted in SQL; "everyone remembers" is not a security model |
| Background jobs inside `app/` | Cron/queue work runs in `scripts/` against the same `lib/db`; request lifetimes must not own long tasks |
| New dependency without a stated reason | Every dep is an upgrade obligation; justify it in the PR body or do not add it |

## 9. Testing & definition of done

- Unit test every `lib/db/queries/*` and every validation schema against a
  temporary `:memory:` DB built from `schema.sql`.
- A change is done when: `pnpm lint && pnpm typecheck && pnpm test && pnpm build`
  pass, the migration runs on a fresh DB, and the UI path is exercised once
  manually or by the E2E spec.
- Do not "fix" a failing test by loosening its assertion; a flaky test is a bug
  in the test, fix the cause.

## 10. Working agreement (how to behave in this repo)

1. Read the nearest `CLAUDE.md` section for the area before editing; if a rule is
   wrong, say so and propose the change — do not silently diverge.
2. Prefer editing an existing file over adding a new one; prefer deleting code to
   commenting it out.
3. When a task is ambiguous, pick the interpretation that keeps the dependency
   direction `app → components → lib` and state the assumption in one sentence.
4. Never run `pnpm db:reset`, `rm -rf`, or a destructive migration against
   `./data/app.db` without explicit confirmation.
5. Report back with: files changed, why, commands run, and anything you could not
   verify.
