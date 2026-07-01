# CLAUDE.md

Guidance for Claude Code working in this repository. This is a **SaaS app on
Next.js 15 (App Router) + SQLite**. Follow these conventions; they are
opinionated on purpose and each rule states *why* so you can apply judgment when
a situation isn't covered.

---

## Stack & versions

| Concern | Choice | Why |
|---|---|---|
| Framework | **Next.js 15**, App Router only | Server Components are the default; we do not maintain a `pages/` dir. |
| Language | **TypeScript**, `strict: true` | Catches the class of bugs SQLite's dynamic typing won't. |
| DB (local/single-node) | **better-sqlite3** | Synchronous API → no `await` noise in server code; fastest option for a single instance. |
| DB (hosted/edge) | **Turso** (libSQL) | Same SQL dialect as better-sqlite3, so swapping is a driver change, not a rewrite. |
| Migrations | Plain SQL files + a tiny runner | No ORM migration magic; you can always read exactly what will run. |
| Data access | **Hand-written SQL** in a repository layer | No ORM. SQLite is simple enough that an ORM adds indirection without payoff. |
| Auth | Cookie session (httpOnly) + `lucia`-style table | Stateful sessions are trivial with a local DB and avoid JWT footguns. |
| Styling | Tailwind CSS | Colocated, no separate CSS files to name. |
| Validation | **zod** at every trust boundary | One schema validates the request *and* gives you the TypeScript type. |
| Testing | **vitest** + Playwright | vitest for units/repos, Playwright for the handful of critical flows. |
| Package manager | Whatever the lockfile says | Don't switch pm; don't commit a second lockfile. |

**Never** add an ORM (Prisma/Drizzle), a data-fetching library (React Query) for
server-rendered data, or a state manager (Redux/Zustand) before there's a
concrete need. Server Components + the DB are the state.

---

## Folder structure

```
app/                      # App Router — routes, layouts, server actions
  (marketing)/            # Route groups for unauthenticated pages
  (app)/                  # Authenticated product; guarded by app/(app)/layout.tsx
  api/                    # Route handlers ONLY for webhooks & non-UI endpoints
lib/
  db/
    index.ts              # opens the connection, exports `db` (singleton)
    schema.sql            # canonical schema (source of truth for a fresh DB)
    migrations/           # 0001_name.sql, 0002_name.sql … applied in order
    migrate.ts            # the migration runner
  repos/                  # one file per table: users.ts, subscriptions.ts …
  auth.ts                 # session helpers: getSession(), requireUser()
  validation/             # zod schemas, one file per domain
components/
  ui/                     # dumb, reusable primitives (Button, Input) — no data
  <feature>/              # feature components, may be async Server Components
```

Rules:
- **Routes are thin.** A `page.tsx` fetches via a repo and renders. Business
  logic lives in `lib/`, not in the route — so it's testable without Next.
- **`api/` is not for your own UI.** Client components mutate via **Server
  Actions**, not `fetch('/api/...')`. Reserve `api/` for webhooks (Stripe) and
  third-party callbacks. Why: Server Actions are type-safe end to end and skip a
  network hop you'd otherwise hand-write.
- **`components/ui/` never imports from `lib/db` or `lib/repos`.** Primitives stay
  data-agnostic so they're reusable and Storybook-able.

---

## Naming conventions

- **Files:** `kebab-case.ts` for modules, `PascalCase.tsx` for component files
  that default-export a component. Why: matches the ecosystem; the case tells you
  what's inside at a glance.
- **DB:** tables `snake_case` **plural** (`users`, `api_keys`); columns
  `snake_case`. Timestamps are `created_at` / `updated_at`, stored as
  **`INTEGER` unix-epoch-millis** (see below), boolean as `INTEGER` 0/1.
- **Repos:** functions read like sentences — `getUserById`, `listActiveSubscriptions`,
  `insertApiKey`. Return domain types (camelCase), not raw rows.
- **Zod schemas:** `xInput` / `xRow` (`createOrgInput`, `userRow`).
- **Env vars:** `SCREAMING_SNAKE`, validated once in `lib/env.ts` — never read
  `process.env.X` deep in the app.

---

## SQL / migration conventions

- **Every schema change is a migration file.** Never hand-edit the DB or mutate
  `schema.sql` without a matching `migrations/NNNN_*.sql`. Why: prod has data;
  the only safe path forward is an ordered, append-only migration log.
- **Migrations are forward-only and immutable once merged.** Fix a bad migration
  with a *new* migration, never by editing the old one — someone has already run it.
- Filenames: `0001_snake_case_description.sql`, zero-padded, strictly increasing.
- The runner records applied files in a `_migrations` table and applies pending
  ones **inside a transaction**; a failed migration rolls back and stops.
- **Write SQL by hand** in repos, always **parameterized** (`?` placeholders) —
  never string-interpolate user input. Why: string interpolation is how SQLite
  injection happens; there is no exception to this rule.
- **Store timestamps as `INTEGER` epoch-millis**, not TEXT. Why: SQLite has no
  real date type; integers sort correctly, compare cheaply, and map straight to
  `new Date(n)`. Default with `DEFAULT (unixepoch() * 1000)`.
- **Money is `INTEGER` minor units** (cents), never a float. Why: floats lose
  cents; SQLite has no decimal type.
- Turn on the right pragmas at connection open: `journal_mode = WAL` (concurrent
  reads during writes) and `foreign_keys = ON` (SQLite disables FK enforcement by
  default — a classic silent-corruption trap).

---

## Component patterns

- **Server Components by default.** Add `'use client'` only when you need state,
  effects, or browser APIs. Why: less JS shipped, and data fetching stays on the
  server next to the DB.
- **Fetch in the page/server component, pass plain data down.** Client components
  receive props, not DB handles. A client component never touches `lib/repos`.
- **Mutations = Server Actions** in a `actions.ts` colocated with the feature.
  Each action: `requireUser()` → `zod.parse(input)` → repo call → `revalidatePath`.
  Why: that order means every mutation is authenticated, validated, and the UI
  refreshes without client state juggling.
- **`loading.tsx` and `error.tsx` per route segment** that fetches. Why: Suspense
  and error boundaries are free with the App Router; use them instead of manual
  `isLoading` flags.
- Keep components **async and small**; extract data shaping into repos so the JSX
  stays declarative.

---

## Dev commands

```bash
npm run dev            # next dev
npm run db:migrate     # apply pending migrations (lib/db/migrate.ts)
npm run db:reset       # DROP the local db file, recreate from migrations (DEV ONLY)
npm run test           # vitest
npm run test:e2e       # playwright
npm run typecheck      # tsc --noEmit  (run before every commit)
npm run build          # next build — must pass before merging
```

Before you consider a change done: `npm run typecheck && npm run test && npm run build`.

---

## What we don't do (and why)

- **No ORM.** Hand-written parameterized SQL against SQLite is readable and fast;
  an ORM hides the query and adds a migration DSL we'd have to learn and trust.
- **No `pages/` router.** App Router only — mixing the two fractures layouts,
  data fetching, and auth.
- **No client-side fetching of our own data.** Server Components + Server Actions.
  Reaching for `useEffect(() => fetch('/api/...'))` means you're fighting the framework.
- **No floats for money or booleans-as-strings.** Integers (see SQL conventions).
- **No `process.env` scattered through the app.** Validate once in `lib/env.ts`;
  a missing var should fail at boot, not at 2am in a request handler.
- **No editing an already-merged migration.** Append a new one.
- **No business logic in route files or React components.** It goes in `lib/` so
  it's unit-testable and reusable.
- **No new dependency without a reason in the PR description.** Every dep is
  attack surface, bundle weight, and a future upgrade chore.

When a task conflicts with a rule here, say so and propose the smallest deviation
rather than silently breaking the convention.
