# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

Opinionated rules for a greenfield SaaS. Prefer these over inventing new structure mid-session.

## Stack (locked)

- **Next.js 15** App Router (`app/`), React Server Components by default
- **TypeScript** strict (`"strict": true`)
- **SQLite** via `better-sqlite3` **or** Turso (`@libsql/client`) — pick one per project; never mix drivers in `lib/db`
- **Auth**: session cookies + server-side validation (no JWT-in-localStorage)
- **Styling**: Tailwind CSS utility classes only (no CSS modules unless third-party)

## Project structure

```
app/
  (marketing)/          # public pages
  (app)/                # authenticated product shell
    layout.tsx
    dashboard/
  api/                  # Route Handlers only for webhooks / public API
  actions/              # server actions co-located or under app/actions
components/
  ui/                   # primitives (Button, Input, Dialog)
  features/             # domain widgets (BillingCard, ProjectList)
lib/
  db/
    client.ts           # single DB singleton
    schema.ts           # tables + types
    migrations/         # numbered SQL files 001_*.sql
  auth.ts
  env.ts                # zod-validated env
scripts/
  migrate.ts
```

**Why:** App Router route groups keep marketing vs product layouts separate. One `lib/db/client.ts` prevents connection leaks from ad-hoc `new Database()` calls.

## Naming

| Kind | Convention | Example |
|------|------------|---------|
| Files (components) | PascalCase | `ProjectList.tsx` |
| Files (utils) | kebab-case | `format-currency.ts` |
| Server Actions | `verbNounAction` | `createProjectAction` |
| Tables | snake_plural | `projects`, `project_members` |
| Columns | snake_case | `created_at`, `owner_id` |
| Env vars | SCREAMING_SNAKE | `DATABASE_URL` |

## Database rules

1. **Migrations only** — never `CREATE TABLE` in request handlers.
2. Migrations live in `lib/db/migrations/00N_description.sql` and run via `npm run db:migrate`.
3. Every table gets `id TEXT PRIMARY KEY` (ulid/uuid) + `created_at` + `updated_at`.
4. Foreign keys **ON**; enable with `PRAGMA foreign_keys = ON` on each connection.
5. Soft-delete with `deleted_at` when user data must be recoverable; hard-delete for ephemeral rows (sessions, rate limits).
6. **No raw string concat SQL** — always bound parameters (`db.prepare(...).run(...)`).
7. Transactions for multi-row writes: `db.transaction(() => { ... })()`.

### Turso vs better-sqlite3

| | better-sqlite3 | Turso/libsql |
|--|----------------|--------------|
| Local/dev | Default | Optional remote |
| Edge/serverless | No | Yes |
| Sync API | Sync | Async |

If using Turso, wrap all DB helpers as `async` and never call sync better-sqlite3 APIs.

## Server vs client components

- Default to **Server Components**.
- Add `"use client"` only for: event handlers, `useState`/`useEffect`, browser-only APIs.
- Data fetching: server components + `lib/db` or server actions — **never** import `lib/db` into client components.

## Server actions pattern

```ts
"use server";
import { z } from "zod";
import { requireUser } from "@/lib/auth";
import { db } from "@/lib/db/client";

const schema = z.object({ name: z.string().min(1).max(80) });

export async function createProjectAction(input: unknown) {
  const user = await requireUser();
  const data = schema.parse(input);
  // write with bound params; revalidatePath after
}
```

**Why zod at the boundary:** untrusted form/body data must not reach SQL.

## Dev commands

```bash
npm run dev          # next dev
npm run build        # production build
npm run start        # next start
npm run lint         # eslint
npm run typecheck    # tsc --noEmit
npm run db:migrate   # apply lib/db/migrations
npm run db:studio    # optional local sqlite browser
```

## Patterns to follow

1. **Feature folders under `components/features`** for multi-file UI, not deep nesting under `app/`.
2. **`lib/env.ts`** fails fast if required env missing.
3. **RLS-style checks in code**: every mutation checks `owner_id` / membership before write.
4. **Idempotent migrations** with explicit version table `schema_migrations(id TEXT PRIMARY KEY)`.
5. **Loading + error UI**: `loading.tsx` / `error.tsx` at route segment boundaries for product pages.
6. **Rate-limit** public POST route handlers (simple SQLite counter table is fine for MVP).

## Anti-patterns (do not)

- Do not put secrets in `NEXT_PUBLIC_*`.
- Do not use `useEffect` to fetch initial page data (use RSC).
- Do not share a mutable global better-sqlite3 instance across edge runtimes.
- Do not disable TypeScript errors with `@ts-ignore` to ship.
- Do not run DDL from server actions.
- Do not store passwords in plain text — use a proven lib (e.g. `@node-rs/argon2`).
- Do not commit `*.db`, `.env`, or `.env.local`.

## Minimal schema seed

```sql
-- 001_init.sql
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  owner_id TEXT NOT NULL REFERENCES users(id),
  name TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS schema_migrations (
  id TEXT PRIMARY KEY,
  applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

## Definition of done for a feature

1. Types pass (`npm run typecheck`)
2. Lint clean
3. Migration added if schema changed
4. Authz check on every write path
5. `loading.tsx` / empty states for list UIs
6. No new client boundary without need

## When unsure

Prefer: **server component + server action + zod + bound SQL + revalidatePath**. That is the default SaaS path for this stack.
