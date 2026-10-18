# CLAUDE.md — Next.js 15 + SQLite SaaS

Opinionated project conventions. Every rule exists because a specific failure
taught it. If a rule blocks you, say so — don't route around it silently.

## Stack & versions

- **Next.js 15** App Router, React 19, TypeScript strict
- **SQLite** via `better-sqlite3` (sync driver — fine at this scale, and sync
  transactions are simpler to reason about than async ones)
- **Tailwind CSS** + shadcn/ui for components
- **Zod** for every boundary: API inputs, env vars, DB rows that cross into
  client components
- Dev commands: `npm run dev`, `npm run build`, `npm run lint`,
  `npm run db:migrate`, `npm test`

## Folder structure

```
app/                    # routes only — pages, layouts, route handlers, actions
  (auth)/               # route groups for layout, never for logic
  api/                  # route handlers — thin: parse → call lib → respond
components/             # dumb UI only; no data fetching, no business logic
lib/                    # all business logic lives here, framework-agnostic
  db/                   # connection, migrations, query functions
  db/migrations/        # numbered SQL files: 0001_init.sql, 0002_...
tests/                  # vitest; mirrors lib/ structure
```

`app/` is the shell, `lib/` is the product. If code can run without HTTP,
it belongs in `lib/` — that's what keeps it testable.

## Database rules

- **Migrations are SQL files, numbered, forward-only.** Never edit an applied
  migration — write a new one. `0003_fix_users_email.sql`, not a rewrite of `0001`.
- **One connection per process**, created in `lib/db/index.ts` as a singleton.
  SQLite is single-writer; a second connection is a `SQLITE_BUSY` generator.
- **`PRAGMA journal_mode=WAL` and `PRAGMA foreign_keys=ON`** are set at
  connection time, not in migrations.
- Queries live in `lib/db/` as named functions (`getUserByEmail`). SQL strings
  inside components or route handlers are a bug.
- All params bound — **never** interpolate values into SQL. Not even "safe" IDs.
- Timestamps are `INTEGER` unix seconds. Booleans are `INTEGER` 0/1. SQLite
  has neither type; pretending otherwise corrupts silently.

## Component patterns

- Server components by default. `"use client"` only when the component needs
  state, effects, or browser APIs — and then the client boundary should be as
  far down the tree as the need requires.
- Server actions for mutations, named verbs: `createInvoice`, not
  `invoiceAction`. Every action revalidates what it touches explicitly.
- Data fetching happens in page/layout server components via `lib/` functions,
  passed down as props. No `useEffect` fetch waterfalls.
- Forms: `useActionState` + server action + Zod parse on the server. Client-side
  validation is UX only; the server re-validates everything.

## Conventions

- File names: `kebab-case.tsx` for components, `camelCase.ts` for lib modules.
- Errors: `lib/` throws typed errors; route handlers map them to status codes.
  A caught error that returns `{ error: "something went wrong" }` with no
  logging is forbidden — log once at the boundary.
- Env vars parsed once through Zod in `lib/env.ts`; `process.env` read
  anywhere else is a bug.

## What we don't do (and why)

- **No ORM.** better-sqlite3 + hand SQL + Zod row parsers. An ORM adds a query
  planner you must debug on top of the one SQLite already has.
- **No client-side auth checks for authorization.** Middleware + server checks;
  a hidden button is not security.
- **No `any`, no `// @ts-ignore`** without a comment linking the upstream issue.
- **No fetching in `useEffect`.** App Router gives you server components;
  effect-fetch is the old architecture leaking through.
- **No premature "scale" work.** No Redis, no queues, no microservices. SQLite
  in WAL handles more than this app will ever see; when it doesn't, Turso is
  the migration path, not a rewrite.
