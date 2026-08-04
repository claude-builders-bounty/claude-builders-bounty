# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

Opinionated agent guide for a greenfield multi-tenant SaaS. Paste at repo root.
Stack is fixed so Claude Code does not invent alternatives.

## Stack & versions (pin these)

| Layer | Choice | Why |
|-------|--------|-----|
| Runtime | Node.js 22 LTS | Native `fetch`, stable `node:` imports |
| Framework | **Next.js 15** App Router only | RSC + route handlers; no Pages Router |
| Language | TypeScript **strict** | Fail at compile, not in prod |
| UI | React 19 + Tailwind CSS 4 | Default Next scaffold |
| DB | **SQLite** via `better-sqlite3` **or** Turso (`@libsql/client`) | One file / edge-friendly; no Postgres until you have a reason |
| Migrations | SQL files in `db/migrations/` applied in lexical order | Reviewable diffs; no black-box ORM migrate |
| Auth | Session cookie + `users` table (Lucia-style or Auth.js DB adapter) | No pure JWT-in-localStorage for session |
| Validation | Zod at every boundary (forms, route bodies, env) | Single source of truth for shapes |
| Package manager | `pnpm` | Strict peer deps, fast CI |

**Do not** introduce Prisma, Drizzle, Mongo, Redux, or Pages Router unless the human explicitly asks.

## Folder structure

```text
app/                      # App Router only
  (marketing)/            # public marketing routes
  (app)/                  # authenticated product shell
    layout.tsx
    dashboard/page.tsx
  api/                    # Route Handlers only (no separate Express)
  layout.tsx
  globals.css
components/
  ui/                     # dumb presentational
  forms/                  # client forms with Zod
  server/                 # server components that load data
db/
  migrations/             # 0001_init.sql, 0002_....sql
  schema.sql              # optional dump of current ideal schema
  client.ts               # single getDb() factory
  queries/                # pure functions: (db, input) => rows
lib/
  auth.ts
  env.ts                  # Zod-parsed process.env
  errors.ts               # AppError + toResponse()
  money.ts                # integer cents helpers if billing
scripts/
  migrate.ts              # applies pending migrations
  seed.ts
tests/
  unit/
  integration/            # real SQLite temp file
public/
CLAUDE.md                 # this file
```

### Naming

- Files: `kebab-case.ts` for modules; `PascalCase.tsx` for components.
- DB tables: `snake_case` plural (`users`, `org_members`).
- Columns: `snake_case`; booleans `is_` / `has_`; timestamps `*_at` UTC ISO or unix.
- Route groups `(name)` never appear in URLs.
- Prefer `getX` / `listX` / `createX` in `db/queries/*` — no generic repository class.

## Dev commands

```bash
pnpm install
pnpm db:migrate          # node --import tsx scripts/migrate.ts
pnpm db:seed             # optional
pnpm dev                 # next dev --turbopack
pnpm build && pnpm start
pnpm test                # vitest
pnpm typecheck           # tsc --noEmit
pnpm lint
```

Env (validated in `lib/env.ts`):

```bash
DATABASE_URL=file:./data/app.db          # better-sqlite3 path or libsql URL
SESSION_SECRET=                          # ≥32 random bytes
APP_URL=http://localhost:3000
```

Never read `process.env.FOO` outside `lib/env.ts`.

## SQL / migration rules

1. **Migrations are append-only.** Never edit a shipped `db/migrations/00xx_*.sql`.
2. Each migration is pure SQL, transactional where SQLite allows.
3. Every table gets `id` (text ULID/UUID or integer PK — pick one per project and stick to it), `created_at`, `updated_at`.
4. Multi-tenant rows carry `org_id` NOT NULL + index. Enforce org scope in **every** query helper.
5. Soft-delete only when product requires restore: `deleted_at`. Default = hard delete in transactions.
6. Money = **integer minor units** (`amount_cents`). Never float.
7. FTS: SQLite FTS5 virtual table in its own migration if search is needed.
8. `PRAGMA foreign_keys = ON` on every connection.
9. better-sqlite3: one write connection, sync API inside server actions / route handlers. No `await db.query` fiction.
10. Turso/libsql: use batched writes; still keep SQL in migrations identical.

Example query helper shape:

```ts
// db/queries/projects.ts
export function listProjectsForOrg(db: Db, orgId: string) {
  return db
    .prepare(
      `SELECT id, name, created_at
       FROM projects
       WHERE org_id = ? AND deleted_at IS NULL
       ORDER BY created_at DESC`
    )
    .all(org_id);
}
```

## Component & data patterns

### Server-first

- Default to Server Components. Add `"use client"` only for interactivity (forms with local state, charts).
- Load data in server components or route handlers via `db/queries/*`. Do not fetch your own public HTTP API from RSC.
- Mutations: Server Actions **or** `POST app/api/...` with Zod. One style per resource family; prefer Server Actions for UI forms.

### Forms

1. Zod schema in `lib/validators/*.ts` shared by client + server.
2. On failure return field errors; never throw raw SQL messages to the client.
3. CSRF: Next Server Actions are cookie-bound; for raw route handlers require same-site session cookie only (no `Access-Control-Allow-Origin: *` with credentials).

### AuthZ

- Session resolves to `userId` + active `orgId`.
- **Every** mutation checks membership (`org_members`) before write.
- Capability flags live on membership row (`role`: `owner` | `admin` | `member`), not only on JWT claims.

### Errors

```ts
// lib/errors.ts — pattern
throw new AppError({ code: "NOT_FOUND", status: 404, message: "Project not found" });
```

Map `AppError` in one place; log `cause` server-side only.

## What we don't do (and why)

| Anti-pattern | Why not |
|--------------|---------|
| Pages Router (`pages/`) | Two routing mental models; App Router is the product |
| Prisma/Drizzle "for speed" | Extra abstraction over SQLite; SQL migrations are clearer for agents |
| Shared mutable globals for request auth | Leaks identity across concurrent requests |
| `select *` in app queries | Breaks when columns added; explicit columns document intent |
| Storing secrets in `NEXT_PUBLIC_*` | Bundled to browser |
| Client-side SQL or exposing DB URL | Instant data breach |
| Float money | Rounding bugs in billing |
| Cross-org queries without `org_id` predicate | Tenant data leaks — treat as P0 |
| `any` / disabling `strict` | Hides the bugs this file exists to prevent |
| Giant `utils.ts` | Prefer `lib/<domain>.ts` |
| Installing a component library "just in case" | Start with Tailwind + small `components/ui`; add Radix only when needed |

## Agent workflow (Claude Code)

When implementing a feature:

1. Read this file + `db/migrations/*` + relevant `db/queries/*`.
2. If schema changes → **new** migration file; update query helpers; add a test.
3. Add Zod schema first, then UI/action.
4. Run `pnpm typecheck` and targeted `pnpm test` before claiming done.
5. Do not open drive-by refactors outside the task path.
6. Do not add dependencies without stating why one-liners failed.

## Minimal acceptance for new endpoints

- [ ] Zod input
- [ ] Session + org membership check
- [ ] Parameterized SQL only
- [ ] `AppError` mapping
- [ ] Test for happy path + unauthorized org access

## Greenfield bootstrap (human or agent)

```bash
pnpm create next-app@latest . --ts --tailwind --eslint --app --src-dir=false --import-alias "@/*"
pnpm add better-sqlite3 zod
pnpm add -D @types/better-sqlite3 vitest tsx
mkdir -p db/migrations db/queries lib components/ui scripts tests
# add 0001_init.sql (users, orgs, org_members, sessions)
# implement lib/env.ts, db/client.ts, scripts/migrate.ts
```

After paste, Claude should assume the above structure exists or is being created — **ask zero clarifying questions about stack** unless the human overrides a row in the stack table.
