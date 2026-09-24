# CLAUDE.md

Guidance for Claude Code when working in this repository. Every rule is opinionated and exists
for a concrete reason; follow it unless the user explicitly overrides it.

## Stack & versions (fixed — do not change without asking)

- **Next.js 15** (App Router, React Server Components by default) + **React 19** + **TypeScript** in `strict` mode.
- **SQLite** via **better-sqlite3** (synchronous, file-based, local-first).
- **Drizzle ORM** (`drizzle-orm/better-sqlite3`) for schema, migrations, and typed queries. Use Drizzle's `sql` tag for anything it can't express.
- **Tailwind CSS v4** for styling.
- **Zod** for runtime validation at every trust boundary (forms, route handlers, env vars).
- **Vitest** for unit tests; **Playwright** for end-to-end tests.
- **pnpm** is the only allowed package manager.

> Reason: pinning the stack removes a whole class of decision-cost and keeps the codebase
> consistent. better-sqlite3 is synchronous and ideal for a single-node SaaS. Drizzle keeps SQL
> visible (no hidden ORM magic). Zod stops unvalidated data from reaching the DB.

## Dev commands

| command | purpose |
|---|---|
| `pnpm dev` | run the dev server (Turbopack) |
| `pnpm build` | production build — must pass before any PR |
| `pnpm lint` | ESLint (`next lint`) — zero warnings allowed |
| `pnpm typecheck` | `tsc --noEmit` — zero errors allowed |
| `pnpm test` | Vitest unit tests |
| `pnpm test:e2e` | Playwright end-to-end tests |
| `pnpm db:generate` | `drizzle-kit generate` — create a migration from schema changes |
| `pnpm db:migrate` | apply pending migrations |
| `pnpm db:studio` | Drizzle Studio (visual DB inspector) |

> Before committing: `pnpm lint && pnpm typecheck && pnpm test` must all pass.

## Folder structure

```
src/
  app/                 # App Router routes (page.tsx, layout.tsx, route.ts)
    (marketing)/       # public marketing pages
    (app)/             # authenticated shell (single layout + session guard)
      dashboard/
    api/               # route handlers (REST)
  components/
    ui/                # presentational components; NO data fetching
    features/          # feature components; may fetch data on the server
  lib/
    db/                # schema.ts, client.ts, migrations/
    auth/              # session / auth helpers
    validation/        # zod schemas
  server/              # server-only code (queries, actions)
```

> Reason: grouping by role ("app" vs "components" vs "server") keeps what can run on the server
> separate from what ships to the browser. `server/` is importable only from Server Components and
> route handlers, which prevents accidentally bundling DB code into the client.

## SQL / migration conventions

- All schema lives in `src/lib/db/schema.ts` (Drizzle `sqliteTable`).
- Migrations are generated (`pnpm db:generate`) and committed. **Never edit a committed migration** — write a NEW migration instead.
- `PRAGMA foreign_keys = ON` is enabled on every connection (see `src/lib/db/client.ts`).
- Timestamps are `TEXT` ISO-8601 strings (`datetime({ mode: 'text' })`), never integers.
- Primary keys are `text` UUIDs (`crypto.randomUUID()` via Drizzle `$defaultFn`), never auto-increment integers.
- Every table has `createdAt` and `updatedAt`; `updatedAt` is maintained in application code.

> Reason: committed migrations are append-only history — editing one breaks every other
> environment. UUIDs avoid enumeration and merge conflicts. TEXT timestamps are readable and sortable.

## Component patterns

- **Server Components are the default.** Add `'use client'` only for state, effects, or browser APIs.
- Data fetching happens in Server Components / route handlers via `server/` queries — never in client components.
- Mutations go through Server Actions (in `server/actions/`) or `app/api` route handlers.
- Forms validate with Zod BEFORE invoking the action; errors are returned as a typed object, never thrown.
- `app/(app)/` is wrapped in one auth layout; every authenticated route re-checks the session server-side.

## What we don't do (and why)

- **No Prisma.** Client generation and connection pooling add complexity a single-node SQLite app doesn't need. Drizzle keeps SQL explicit and migrations predictable.
- **No Turso / libSQL** until multi-region reads are actually required. better-sqlite3 is simpler and synchronous; adding a remote DB before you need one is premature.
- **No `any`.** Strict TypeScript is on. If a type is painful, fix the type — don't cast.
- **No client-side secrets.** Anything prefixed `NEXT_PUBLIC_` is public. Server-only values go in `process.env` and are read on the server.
- **No SQL string interpolation.** Use Drizzle or the `sql` tagged template with bound parameters — never concatenate user input into SQL.
- **No `useEffect` for data fetching.** Fetch in Server Components or route handlers.
- **No N+1 queries.** Batch with `inArray(...)` or Drizzle `findMany`.

## Implementing a feature (order of operations)

1. Add/change the Zod schema first.
2. Add/change the Drizzle schema, then generate a migration (`pnpm db:generate`) and run it locally.
3. Write the query/Server Action, then the UI.
4. Add a Vitest test for pure logic (validation, query filters, formatting).
5. Run `pnpm lint && pnpm typecheck && pnpm test` before committing.
