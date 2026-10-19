# CLAUDE.md — Next.js 15 + SQLite SaaS

Operating manual for this repository. Read it before your first edit.
Every rule has a reason attached. If a rule blocks you, argue it in the PR — do not silently ignore it.

## 1. Stack & versions (do not drift)

| Layer | Choice | Why |
|---|---|---|
| Framework | Next.js 15, App Router only | Pages Router is not used anywhere; mixing routers breaks streaming and server actions |
| Runtime | Node 20 LTS, pinned in `.nvmrc` | Next 15 needs 18.18+; 20 is the oldest line still getting security patches |
| Language | TypeScript, `strict`, `noUncheckedIndexedAccess` | Index access is where most production crashes hide |
| DB | SQLite — `better-sqlite3` locally, Turso (`@libsql/client`) in prod | Same SQL in both; sync driver locally is ~10x faster than async wrappers |
| Validation | `zod` at every boundary | One schema does runtime parsing and gives you the static type |
| Styling | Tailwind CSS + `cn()` | Server components cannot ship a CSS-in-JS runtime |
| Tests | `vitest` against a real temp SQLite file | Mocked DB tests stay green while production breaks |
| Package manager | `npm`, lockfile committed | One lockfile; workspaces are not used |

Adding a native dependency? Verify it installs on Windows before you commit.
Why: CI is Linux-only and will not catch your local build break.

- **Pin `next` to ≥15.5.28.** Why: npm flags 15.5.4 on the 15 line for CVE-2025-66478; a template that pins a known-vulnerable version is worse than no pin at all.
- **`@types/better-sqlite3` is a required devDependency.** Why: `better-sqlite3` ships no type declarations, so `tsc --noEmit` fails on the import and `next build` stops at type-check before emitting a single page. Verified: removing it turns a green build red.

## 2. Folder structure

```
src/
  app/                    routes only — thin, no business logic
  features/<domain>/      the actual product code, one folder per domain
    components/           domain UI (client or server)
    queries.ts            reads  (server-only)
    actions.ts            writes (server actions, 'use server' at top)
    schema.ts             zod schemas for this domain
  lib/                    cross-domain infrastructure (db, auth, env, utils)
  db/
    schema.sql            desired state, human-readable
    migrations/           0001_init.sql, 0002_add_invoices.sql …
    migrate.ts            migration runner
```

- **`app/` holds routing only.** A page renders imports from `features/`.
  Why: keeping logic out of routes lets you migrate routing without touching product code.
- **One folder per domain, not per layer.** No `src/services/`, `src/models/` dumps.
  Why: a feature change should touch one folder, so reviews stay small.
- **`queries.ts` never imports from `components/`.** Data flows one way.
  Why: circular imports between UI and data are the #1 cause of "server-only module imported into client" errors.
- **Anything touching `db` or secrets lives in `lib/` or `*/queries.ts`** and starts with `import 'server-only'`.
  Why: that import turns a leaked client import into a build error instead of a runtime secret leak.

## 3. Naming conventions

| Thing | Convention | Why |
|---|---|---|
| Files & folders | `kebab-case` (`user-profile.tsx`) | Matches Next's own convention; macOS/Windows case-insensitive FS hides casing bugs |
| React components | `PascalCase` export, named not default (except `page`/`layout`/`error`) | Framework needs default exports at route files; everything else named so renames are safe |
| Hooks | `use-*.ts` file, `useXxx` export | Grep for `use-` finds every hook |
| Server actions | verb-first: `createInvoice`, `updateInvoiceStatus` | Reading a call site tells you the effect without opening the file |
| DB tables | `snake_case`, plural (`invoices`, `invoice_items`) | SQL has no namespaces; plural table names keep joins unambiguous |
| DB columns | `snake_case`; `id`, `created_at`, `updated_at` on every table | Uniform columns make migrations and audit queries mechanical |
| Booleans | `is_*` / `has_*` in DB, `isX` in TS | `status` vs `is_active` must be readable without the schema |
| Env vars | `SCREAMING_SNAKE`, server-only unless prefixed `NEXT_PUBLIC_` | The prefix is the only thing protecting a value from the client bundle |

## 4. Dev commands

```bash
npm install                 # install
npm run dev                 # next dev (Turbopack) on :3000
npm run build               # production build — must pass before any PR
npm run lint                # eslint
npx tsc --noEmit            # type check — CI runs exactly this
npm test                    # vitest, uses a temp SQLite file
npm run db:migrate          # apply pending migrations, idempotent
```

Run `npm run build && npx tsc --noEmit && npm test` before opening a PR.
Why: CI runs these three in that order and a red pipeline blocks merge, not review.

- If the repo also has an `AGENTS.md` (Next.js 15.5+ writes one with version-specific breaking-change notes), put `@AGENTS.md` on its own line under the title of this file.
  Why: Claude Code reads `AGENTS.md` only when no `CLAUDE.md` exists — without the import, Next's own migration notes are silently dropped.

## 5. SQL & migration rules

- **Migrations are forward-only, numbered, never edited after merge.** `0007_add_invoice_status.sql`.
  Why: an edited migration silently diverges between a laptop that already ran it and CI that never did.
- **Each migration file starts with a comment stating intent and rollback plan**, even if the rollback is "restore backup".
  Why: at 2am you will not reconstruct intent from `ALTER TABLE`.
- **One DDL concern per migration.** Table + index + trigger may share a file; two features may not.
  Why: partial failure then has one obvious cause.
- **Always declare foreign keys and run `PRAGMA foreign_keys = ON` on every connection.**
  Why: SQLite defaults it OFF — orphan rows accumulate silently.
- **Use `STRICT` tables and explicit types.** No bare `INTEGER` holding dates as strings.
  Why: SQLite's dynamic typing accepts `'abc'` into a numeric column and you find out in production.
- **Timestamps are `TEXT` ISO-8601 UTC** (`2026-10-19T09:30:00Z`), written by the app, not by SQLite's `datetime()`.
  Why: one format everywhere; comparing mixed local/UTC strings is unfixable later.
- **Every `CREATE INDEX` names its table first**: `idx_invoices_customer_created`.
  Why: `EXPLAIN QUERY PLAN` output becomes readable.
- **No destructive `DROP`/`RENAME` in the same PR that adds the replacement.** Two PRs, two deploys.
  Why: a single deploy cannot be rolled back to a state where both old and new code work.
- **Migration runner records applied versions in `_migrations(version, applied_at)`** and wraps each file in a transaction.
  Why: idempotency you can prove, not hope for.

## 6. Data access

- **Every statement is prepared with bound parameters.** ``db.prepare('select * from invoices where id = ?').get(id)``.
  Why: string interpolation is SQL injection, and SQLite has no privilege separation to contain the blast radius.
- **Never accept a table name, column name, or `ORDER BY` value from the request.** Map it through a literal allow-list.
  Why: identifiers cannot be bound; an allow-list is the only safe shape.
- **Multi-statement writes go in a transaction** (`db.transaction(fn)`).
  Why: SQLite is single-writer; a half-applied invoice + items pair is a support ticket.
- **WAL mode + `busy_timeout = 5000` set once at connection open.**
  Why: without WAL, a read during a write throws `SQLITE_BUSY` under normal traffic.
- **Queries return domain types, not rows.** Map inside `queries.ts`.
  Why: `snake_case` leaking into components means a schema rename breaks the UI.

## 7. Component patterns

- **Server components are the default. Add `'use client'` at the leaf, never at the page.**
  Why: one directive at the top of a page drags the whole subtree into the client bundle.
- **Fetch data in the server component that renders it.** No `useEffect` data loading.
  Why: avoids waterfalls, loading spinners, and the "why does it flash" bug class.
- **Mutations are server actions, not `fetch('/api/...')` from a component.**
  Why: actions ship without an HTTP surface to secure and give you progressive enhancement for free.
- **Every action re-checks auth server-side** — `await requireUser()` as the first line.
  Why: a hidden button is not authorization; anything callable is public.
- **Loading and error states are files, not conditionals**: `loading.tsx`, `error.tsx` per route segment.
  Why: the framework already handles the boundary; hand-rolled `isLoading` duplicates it and misses suspense.
- **Composition over props**: children and slot props, not 12 boolean flags.
  Why: boolean explosion is how a `Button` ends up with 40 variants and no owner.

## 8. Testing

- **Test against a real SQLite database created in a temp file per suite**, migrated with the same runner as prod.
  Why: in-memory + schema drift is how migrations pass tests and fail deploys.
- **Name tests by behaviour**: `it('rejects an invoice with a negative total')`.
  Why: failures read as a bug report instead of `expected true to be false`.
- **Cover, at minimum**: every server action's validation failure, the migration runner's idempotency, and one happy path per domain query.
  Why: those are the three places where a silent break costs money.

## 9. Security

- **Secrets never appear in `NEXT_PUBLIC_*`.** Anything with that prefix is public.
  Why: the prefix inlines the value into the JS bundle shipped to browsers.
- **Validate with zod at the action boundary, then trust the parsed object inside.**
  Why: re-validating in three layers produces inconsistent rules and false confidence.
- **Parameterised SQL only, plus an allow-list for identifiers** (see §6).
- **Rate-limit anything that writes and is reachable without a session** (signup, password reset, webhooks).
  Why: SQLite writes are serialised; 100 concurrent signups is an outage.

## 10. What we don't do (and why)

- **No ORM in v1** (no Prisma, no Drizzle). Plain SQL + `queries.ts`.
  Why: the schema is small, SQLite's type system is already loose, and an ORM hides the one thing we must see — the query plan. Revisit if the schema passes ~15 tables.
- **No `any`.** Use `unknown` + a zod parse. Why: `any` disables the only tool that catches schema drift.
- **No client-side database access**, including Turso's HTTP client in the browser.
  Why: it means shipping a token to the client.
- **No `pages/` directory, no `getServerSideProps`, no `middleware.ts` doing auth.**
  Why: middleware runs on the edge without DB access; auth decisions belong where the session is verified.
- **No global state library** (Redux/Zustand) until a real cross-route client state need exists.
  Why: URL + server state covers this app; a store adds a second source of truth.
- **No `moment`, `lodash`, `axios`.** Use `Intl`, native array methods, `fetch`.
  Why: bundle weight for functions in the platform.
- **No committed `*.db`, `*.sqlite`, or `-wal` files.** Add to `.gitignore`.
  Why: a committed DB file overwrites a teammate's local data on pull.
- **No invented endpoints or table names.** If something is missing, stop and ask.
  Why: confident guessing produces code that compiles and does not run.

## 11. Definition of done

A task is done when all of these are true:

- [ ] `npm run build` passes
- [ ] `npx tsc --noEmit` passes
- [ ] `npm test` passes, and new behaviour has a test
- [ ] A migration exists for every schema change, and `npm run db:migrate` is idempotent
- [ ] No `any`, no client-side secret, no string-interpolated SQL
- [ ] The PR description states what changed, why, and how it was verified
