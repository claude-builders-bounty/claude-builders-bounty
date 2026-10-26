# CLAUDE.md — Working Agreement for Claude Code

This file tells Claude Code how to work in this repo. Treat it as the source of truth: follow the rules below by default and do **not** ask clarifying questions for things they already decide. If a task contradicts a rule here, surface the conflict before proceeding instead of silently choosing.

## Stack & Versions

| Concern | Choice | Why |
| --- | --- | --- |
| Framework | Next.js 15 (App Router), React 19 | Server Components by default; route handlers for the API |
| Language | TypeScript, `"strict": true` | no `any`, no silent casts |
| Database | SQLite via `better-sqlite3` | zero-ops, single file, fast synchronous reads |
| ORM + migrations | `drizzle-orm` + `drizzle-kit` | typed queries, SQL-file migration history |
| Auth | Auth.js (`next-auth` v5) | cookie sessions, usable in `middleware.ts` |
| Tests | Vitest + `@testing-library/react` | native ESM, fast, no Jest config ceremony |
| Tooling | npm, ESLint (`next/core-web-vitals`), Prettier | one lockfile, consistent formatting |

Node.js >= 20 LTS. The local database file is always `data/app.db`.

## Dev Commands

```bash
npm run dev           # dev server on http://localhost:3000
npm run build         # production build
npm start             # serve the production build (run db:migrate first)
npm test              # run all tests once
npm run test:watch    # tests in watch mode
npm run lint          # ESLint
npm run typecheck     # tsc --noEmit
npm run db:generate   # generate a new SQL migration from schema.ts changes
npm run db:migrate    # apply pending migrations to data/app.db
npm run db:seed       # wipe and repopulate local data (destructive)
npm run db:studio     # Drizzle Studio browser UI for the local DB
```

Non-negotiables:

- Any change to `lib/db/schema.ts` **must** be followed by `npm run db:generate`, and the new `drizzle/NNNN_*.sql` file must be committed in the same change — a schema edit without its migration breaks everyone else's database.
- Apply migrations only with `npm run db:migrate`; in production it runs once at deploy time before the server starts.
- `npm run db:seed` is destructive (drops all rows); run it deliberately, never "just to try".

## Folder Structure

```
app/                        # App Router: pages, layouts, route handlers
  layout.tsx                # root layout: providers, <html>, <body>
  page.tsx                  # landing page
  login/page.tsx            # auth pages
  dashboard/page.tsx        # protected app UI
  api/
    projects/route.ts       # one route.ts per API endpoint (GET/POST/...)
  not-found.tsx
components/                 # presentational components only (props in, no data)
  ui/                       # buttons, inputs, cards
lib/
  db/
    client.ts               # the single better-sqlite3 + drizzle instance
    schema.ts               # all table definitions (drizzle)
    queries/                # one module per table: projects.ts, users.ts, ...
  auth.ts                   # Auth.js config; the auth() export
  env.ts                    # validated access to process.env
  utils.ts                  # id, date, and shared helpers
middleware.ts               # redirects unauthenticated users to /login
drizzle/                    # generated migrations — never hand-edit
drizzle.config.ts           # drizzle-kit config (schema path, dialect: sqlite)
test/
  db.ts                     # in-memory test database factory
  setup.ts                  # vitest setup (jsdom, cleanup)
vitest.config.ts
scripts/seed.ts             # implementation of db:seed
data/app.db                 # local SQLite file (gitignored)
```

Rules for the map:

- Data access lives only in `lib/db/queries/*` — components and route handlers never call drizzle directly, so SQL has exactly one home to read, test, and rewrite.
- One concern per file: no barrel `index.ts` re-export files, no 500-line catch-all components.

## Naming Conventions

- Files: kebab-case — `project-card.tsx`, `project-list.ts`, `route.ts`.
- Components: PascalCase, one default export per file.
- Query functions: verb + singular noun matching the operation — `listProjects()`, `getProject(id)`, `createProject(input)`, `updateProject(id, patch)`, `deleteProject(id)`.
- Tables: plural snake_case (`projects`, `users`, `subscriptions`); columns snake_case; timestamps are always `created_at` / `updated_at`.
- Route handlers export functions named `GET`, `POST`, `PATCH`, `DELETE` from `route.ts`.
- Tests live next to the code: `projects.test.ts`, `project-card.test.tsx`.

## Patterns to Follow

### Route handlers (API)

Every API route follows the same shape: parse → validate → call a query → JSON response.

```ts
// app/api/projects/route.ts
import { NextResponse } from "next/server";
import { createProject } from "@/lib/db/queries/projects";

export async function POST(req: Request) {
  const body: unknown = await req.json().catch(() => null);
  if (!body || typeof (body as { name?: unknown }).name !== "string") {
    return NextResponse.json({ error: "name is required" }, { status: 400 });
  }
  const project = createProject({ name: (body as { name: string }).name });
  return NextResponse.json(project, { status: 201 });
}
```

- Success responses return the resource JSON; failures return `{ "error": "one human-readable sentence" }` with a 4xx/500. Errors are always JSON — never throw to the client.
- Validate at the edge (in the handler); query functions may assume valid input.
- Authenticated mutations call `auth()` from `lib/auth.ts` and return `401` before touching the database.

### Database access

- Import `db` only from `lib/db/client.ts`. That module opens the single connection, sets `journal_mode = WAL` and `busy_timeout = 5000`, and hands out the drizzle instance — it is the only place `better-sqlite3` is imported.
- Multi-statement writes go in `db.transaction((tx) => { ... })`; a write that spans two statements is a bug if it isn't atomic.
- IDs are TEXT primary keys generated in app code (`crypto.randomUUID()`), not auto-increment integers — row counts never leak through IDs and databases merge cleanly.
- Datetimes are stored as TEXT, ISO-8601 UTC (`2026-10-26T18:43:54.000Z`): write `new Date().toISOString()`, read back `new Date(value)`. Never store a `Date` object or a local-time string.

### Components

- Server Components by default. Add `"use client"` only when you use hooks, event handlers, or browser APIs.
- Reads happen in server components by calling query functions directly — they are synchronous, so never `fetch` your own API from the server.
- Mutations go to `app/api/*` from client components via `fetch` — one stable contract for the API, easy to test.
- Components receive data as props and contain no fetching or SQL of their own.

### Testing

- `npm test` runs Vitest over every `*.test.ts(x)` file; UI tests use `@testing-library/react` (`render`, `screen`, `userEvent`) in a jsdom environment.
- DB tests never touch `data/app.db`. Use `createTestDb()` from `test/db.ts`: it opens an in-memory SQLite, runs the generated migrations into it, and returns a drizzle instance — one fresh database per test, so tests cannot leak state into each other.
- Test behavior, not implementation: assert on rendered DOM and returned JSON, not on how many queries ran.

### Security

- SQL injection: parameters only. The drizzle builder parameterizes everything; never interpolate user input into a `sql` template or a string, and never `db.run()` a hand-built SQL string.
- Auth: `middleware.ts` guards protected routes (redirect to `/login`); server-side code re-checks `auth()` and returns `401`/`403` — never trust client-side state for authorization.
- Env vars: secrets live only in `.env` (gitignored) and are read only through `lib/env.ts`, which validates at startup and fails fast when a variable is missing. Nothing secret goes into `NEXT_PUBLIC_*`.
- Cookie-session mutations: issue a per-session CSRF token (held in `lib/auth.ts`) and verify it in mutating route handlers, because App Router `fetch` POSTs get no CSRF protection for free.

## SQL / Migration Conventions

1. Define the change in `lib/db/schema.ts` — the schema file is the source of truth.
2. Run `npm run db:generate` and review the new `drizzle/NNNN_*.sql`: it should do exactly what you intended and nothing else.
3. Commit schema + migration together. `npm run db:migrate` applies them; already-applied migrations are never modified — append a new one instead, because rewriting history breaks fresh databases.
4. `drizzle-kit push` is a local-only convenience and is forbidden on shared or production databases: it syncs the DB without producing migration files, so two machines silently diverge.
5. Renames and drops: generate the step, then read the SQL before applying — destructive changes deserve a human pass.

## SQLite Gotchas

- **One connection.** `better-sqlite3` is synchronous and file-locked; the shared connection in `client.ts` is deliberate. Per-request connections cause `SQLITE_BUSY` and thrash the file.
- **No concurrent writers.** SQLite serializes writes; keep transactions short and batch work into one transaction instead of many. WAL (enabled in `client.ts`) lets readers proceed during writes.
- **Single instance.** Deploy as one process with persistent disk (VM, Fly.io, Render). Serverless platforms don't keep a file-backed SQLite, and two processes writing one file will corrupt it.
- **Backups** are `VACUUM INTO 'backup.db'` — a consistent snapshot even under WAL — not a raw file copy taken mid-write.
- **Ceiling:** this stack is comfortable up to hundreds of thousands of rows; past that, moving to Postgres is an architectural decision, not a tuning knob.

## What We Don't Do (and Why)

- **No SQL in components or route handlers** — queries live in `lib/db/queries/*` so there is one place to read, test, and rewrite when the schema changes.
- **No hand-editing `drizzle/*.sql`** — generated files are the replayable history; hand edits break `db:migrate` on fresh databases.
- **No `drizzle-kit push` on shared/production databases** — see Migration Conventions, rule 4.
- **No second ORM or driver** — drizzle is the only layer that touches SQLite; adding prisma/kysely/raw sqlite3 creates two sources of truth.
- **No auto-increment integer IDs** — they leak row counts and block database merges; UUID TEXT keys instead.
- **No local-time or `Date` storage** — every time string is UTC ISO-8601 or timezones become a bug farm.
- **No `any` / `@ts-ignore`** — the strictness is the point; fix the type instead.
- **No committing `.env`, `data/*.db`, or `node_modules/`** — secrets and local state stay local.
- **No pnpm/yarn** — the repo uses npm and `package-lock.json`; switching package managers mid-project causes dependency drift.

## How to Use This Template

This file is drop-in ready: paste it into the root of a fresh `npx create-next-app` project (TypeScript, App Router), install the dependencies from Stack & Versions, and build the folder structure above. Customize only where your project diverges:

1. **DB driver** — if you choose Turso/libsql instead of `better-sqlite3`, swap `lib/db/client.ts` (same drizzle API, `@libsql/client` dialect) and the `dialect` in `drizzle.config.ts`.
2. **Auth provider** — `lib/auth.ts` is written for credentials; swap in the OAuth provider you need.
3. **Seed script** — replace `scripts/seed.ts` with your domain's fixtures.
4. **Env var names** — mirror `lib/env.ts` to your deploy platform's variables.
5. **Project-specific rules** — append them at the end of this file (billing provider, feature flags, domain-specific naming), one bullet each.

Everything else — commands, patterns, conventions, anti-patterns — should stay as written; that part is what makes Claude Code predictable across sessions.
