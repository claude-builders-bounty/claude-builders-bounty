# CLAUDE.md

> Opinionated guidance for Claude Code in this Next.js 15 + SQLite SaaS project.
> Every rule has a reason; no rule is decoration.

## Stack & versions

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | Next.js 15, App Router | RSC data fetching removes most client-side loading states |
| Runtime | Node 20+, `runtime = 'nodejs'` for DB routes | `better-sqlite3` is native; Edge has no fs |
| DB | SQLite via `better-sqlite3` (local) / Turso (prod) | same SQL dialect, one driver swap |
| Validation | Zod, at every boundary | types at compile time ≠ trust at runtime |
| Auth | session cookie + `iron-session` | no third-party session service to leak |
| Styling | Tailwind CSS | co-located, no runtime CSS cost |
| Tests | Vitest + Playwright | unit fast, e2e real browser |

**Never** add Prisma, Drizzle, or an ORM without discussing it first. The whole
point of this stack is a thin, debuggable SQL layer — an ORM hides the queries
you will need to read at 2am.

## Folder structure

```
src/
  app/
    (marketing)/page.tsx        # public, statically rendered
    (app)/dashboard/page.tsx    # authed, dynamic
    api/<resource>/route.ts     # route handlers; thin — delegate to services
  db/
    client.ts                   # the ONLY place a connection is created
    migrations/                 # 0001_init.sql, 0002_add_x.sql ...
    schema.ts                   # typed table/column names
  features/<feature>/
    <feature>.service.ts        # ALL business logic + SQL lives here
    <feature>.schema.ts         # Zod input/output contracts
    <feature>.test.ts           # unit tests beside the code
  lib/                          # framework-free helpers only
```

Rule: **`app/` orchestrates, `features/` decides, `db/` persists.** A route
handler that contains a SQL string is a bug.

## SQL & migration conventions

- One migration per change, `NNNN_snake_case.sql`, **append-only** — never edit a
  shipped migration; add a new one.
- Every migration must be reversible: pair it with a `-- down` block.
- Table/column names are `snake_case`; plural table names (`users`, `orders`).
- Every table has `id TEXT PRIMARY KEY` (a UUID), `created_at`, `updated_at`.
- Foreign keys are enforced: `PRAGMA foreign_keys = ON;` in `db/client.ts`.
- Queries are **parameterised, always** — `db.prepare('... WHERE id = ?').get(id)`.
  String-interpolated SQL fails review.
- Multi-step writes go in a transaction (`db.transaction(...)`), never a bare loop.

## Naming conventions

| Thing | Convention | Example |
|-------|------------|---------|
| Files (components) | PascalCase | `UserCard.tsx` |
| Files (everything else) | kebab-case | `user.service.ts`, `audit-log.ts` |
| React components | PascalCase | `export function UserCard()` |
| Functions / variables | camelCase | `getUserById` |
| Types / interfaces | PascalCase, no `I` prefix | `type User` |
| DB tables / columns | snake_case | `order_items.item_count` |
| Zod schemas | `<thing>Schema` | `createUserSchema` |
| Server Actions | verb-first, `Action` suffix | `createUserAction` |
| Route folders | kebab-case, plural | `app/api/audit-logs/route.ts` |

Rule: a name that needs a comment to explain it is the wrong name. Rename it.

## Component patterns

- Server Components by default. Add `'use client'` only for state, effects, or
  browser APIs — and put it as low in the tree as possible.
- Data fetching happens in Server Components or route handlers, **not** `useEffect`.
- Forms use Server Actions; validate with the feature's Zod schema, return field
  errors as data, never throw for expected failures.
- Props are typed with an explicit `type`; no `any`, no `as` casts to silence errors.
- One component per file; file name = component name.

## What we don't do (and why)

- **No ORM** — we need to read the SQL that runs in production.
- **No client-side auth guards** — the server decides; hidden UI is not security.
- **No `useEffect` data fetching** — it double-fires in dev and duplicates server work.
- **No global mutable singletons** — a DB handle is exported, state is not.
- **No migrations that drop columns** — add a new column, backfill, stop using the
  old one; dropping is a separate, later migration.
- **No `SELECT *` in application code** — name the columns you use.
- **No secrets in `NEXT_PUBLIC_*`** — that prefix ships to the browser.

## Dev commands

```bash
npm run dev          # local server
npm run db:migrate   # apply pending migrations
npm run test         # vitest (unit)
npm run test:e2e     # playwright
npm run lint && npm run typecheck
```

Run `npm run typecheck && npm run test` before declaring any task done.
