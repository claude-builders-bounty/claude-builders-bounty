# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

You are working on a production SaaS app. Next.js 15 App Router, TypeScript strict, SQLite (better-sqlite3 locally, Turso in production). Every rule below exists because violating it caused a real bug or a real outage. Follow them without asking.

## Stack & versions

- Node.js >= 20.11 (native fetch, stable test runner)
- Next.js 15.x, App Router only. No `pages/` directory, ever.
- TypeScript 5.x, `"strict": true`. No `any`. No `@ts-ignore` without a linked issue number.
- SQLite: `better-sqlite3` (dev/self-host) or `@libsql/client` (Turso). Same SQL, one thin wrapper in `lib/db/index.ts`.
- Styling: Tailwind CSS 4. No CSS modules, no styled-components.
- Validation: `zod` at every trust boundary (API input, env vars, webhook payloads).
- Auth: `better-auth` or `next-auth` v5. Sessions in DB, not JWT-only.

## Dev commands

```bash
npm run dev          # next dev --turbopack, port 3000
npm run build        # must pass before any PR
npm run db:migrate   # run pending migrations (see below)
npm run db:studio    # inspect DB (better-sqlite3 only)
npm test             # node --test (no jest, no vitest unless already present)
```

## Folder structure

```
app/                  # routes only. Thin files. No business logic here.
  (marketing)/        # route group: public pages
  (app)/              # route group: authed app pages
  api/                # route handlers, one folder per resource
lib/
  db/
    index.ts          # single db export. Only file that imports better-sqlite3.
    migrations/       # NNN_name.sql, applied in order, tracked in _migrations table
    schema.sql        # full schema, regenerated from migrations (reference only)
  auth/               # session helpers: requireUser(), optionalUser()
  services/           # business logic. Pure functions taking db + args. No imports from app/.
components/
  ui/                 # dumb components: Button, Input, Card. No data fetching, no services.
  forms/              # forms with server actions
tests/                # *.test.ts next to nothing; all tests live here
```

Rules:
- `app/` files import from `lib/` and `components/`, never the reverse.
- `lib/services/` is where logic lives. Route handlers are 10-20 lines: parse input with zod, call service, return Response.
- One route handler file per resource: `app/api/projects/route.ts` handles GET (list) and POST (create). `app/api/projects/[id]/route.ts` handles GET/PATCH/DELETE.

## Naming conventions

- Files: kebab-case (`user-settings.ts`), except React components which are PascalCase files (`ProjectCard.tsx`).
- DB tables: snake_case plural (`projects`, `project_members`).
- TS types: singular PascalCase matching table (`Project`).
- Server actions: verb-first (`createProject`, `deleteProject`), defined in `app/(app)/.../actions.ts`.
- Env vars: `DATABASE_URL`, `AUTH_SECRET`, third-party prefixed (`RESEND_API_KEY`). All validated in `lib/env.ts` with zod at startup; app crashes fast if missing.

## SQL & migration conventions

- Migrations are forward-only. Never edit an applied migration; add a new one.
- Filename: `NNN_short_name.sql` where NNN is zero-padded sequence (`001_init.sql`).
- Every migration is idempotent: `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`.
- SQLite has no real `ALTER COLUMN`. To change a column: create new table, copy, drop, rename — inside one migration wrapped in a transaction.
- Always `PRAGMA foreign_keys = ON` (set once in `lib/db/index.ts`). FKs are declared on every reference column.
- IDs: `TEXT PRIMARY KEY` with ULIDs generated in app code (`ulid()`), not INTEGER AUTOINCREMENT. Sortable, no enumeration.
- Timestamps: `created_at` and `updated_at` as ISO-8601 TEXT, set in app code, not `CURRENT_TIMESTAMP` (timezone traps).
- Indexes: one per FK column, one per column used in WHERE/ORDER BY. Name them `idx_<table>_<column>`.

Example migration:

```sql
-- 003_add_project_archived.sql
BEGIN;
ALTER TABLE projects ADD COLUMN archived_at TEXT;
CREATE INDEX IF NOT EXISTS idx_projects_archived_at ON projects(archived_at);
COMMIT;
```

## Component patterns

- Server Components by default. Add `"use client"` only when the component needs state, effects, or browser APIs. Push `"use client"` to the leaves.
- Data fetching happens in Server Components or route handlers, never in client components.
- Mutations go through server actions or `fetch` to our own API routes. Forms use `action={serverAction}` + `useFormStatus` for pending state.
- Loading: `loading.tsx` per route group. Errors: `error.tsx` with a retry button. No blank screens.
- Every component in `components/ui/` takes explicit props; no hidden context reads except theme.

## Patterns to follow

- Parse, then act: zod schema first, service call second, `Response.json()` third. In every route handler.
- Return proper status codes: 201 on create, 204 on delete, 400 with `{ error: string }` on validation failure, 404 when the row is not the user's or missing.
- Auth check first line of every authed handler: `const user = await requireUser()` — it throws 401.
- Wrap multi-statement writes in a transaction: `db.transaction(() => { ... })()`.
- Log errors with the route + input shape, never the raw user input (PII).

## What we don't do (and why)

- No ORM. better-sqlite3 is synchronous and tiny; an ORM adds a layer that hides the SQL we must review. Raw SQL in services, typed return values.
- No client-side data-fetching libraries (SWR/React Query) unless a page genuinely needs polling. Server Components + revalidate cover 95% of cases.
- No `useEffect` for data you could fetch server-side. Effects are for browser APIs only.
- No secrets in `NEXT_PUBLIC_*`. Anything prefixed NEXT_PUBLIC ships to the browser.
- No direct `better-sqlite3` imports outside `lib/db/index.ts`. One choke point means one place to swap Turso, add logging, or mock in tests.
- No `any`, no non-null assertions to silence the compiler. Fix the type.
- No new runtime dependencies without checking bundle impact. Prefer stdlib; the best dependency is the one not added.

## Testing

- `node --test` with plain asserts. One file per service: `tests/projects.test.ts`.
- Tests get a fresh in-memory or temp-file DB via `createTestDb()` in `tests/helpers.ts`; migrations run on it.
- Test services, not route handlers. If a service is tested, the handler is glue code.
- A PR touching a service without a test for the changed path does not merge.
