# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & versions

- Next.js 15 App Router with React Server Components by default.
- TypeScript in strict mode.
- SQLite via `better-sqlite3` for local/single-node deployments or Turso/libSQL when hosted edge/global reads are needed.
- Server actions or route handlers for mutations; never direct DB access from client components.
- Tailwind/shadcn-style components are fine, but business logic stays outside UI components.

Reason: this stack is fastest when server/client boundaries are explicit and the database remains boring, typed, and migration-driven.

## Dev commands

Use these names unless the project documents otherwise:

```bash
npm run dev        # start local app
npm run build      # production build
npm run lint       # eslint/next lint
npm run typecheck  # tsc --noEmit
npm run test       # unit/integration tests if present
npm run db:migrate # apply migrations
npm run db:studio  # optional DB browser
```

Before finishing any code change, run the smallest relevant gate: typecheck for TS-only work, lint for style-sensitive work, tests for behavior, build for route/config changes.

## Folder structure

```text
app/
  (marketing)/        # public pages
  (app)/              # authenticated product area
  api/                # route handlers for webhooks/external APIs
  actions/            # server actions grouped by domain
components/
  ui/                 # primitive reusable UI
  feature/            # composed product components
lib/
  db/                 # connection, migrations, query helpers
  auth/               # session/user helpers
  domain/             # business rules and service functions
  validators/         # zod schemas and input parsing
migrations/           # ordered SQL migrations
scripts/              # one-off maintenance scripts
```

Reason: App Router routing can get messy fast. Keep business rules in `lib/domain`, not in `app` files.

## Naming conventions

- Files: `kebab-case.tsx` for components/routes, `camelCase.ts` for utility modules only when exporting a single function.
- React components: `PascalCase` exports.
- Server actions: `verbNounAction`, e.g. `createProjectAction`.
- DB tables: plural snake_case, e.g. `users`, `projects`, `billing_events`.
- Columns: snake_case, with `created_at`, `updated_at`, and foreign keys like `user_id`.
- Types inferred from schemas where possible; otherwise name DB row types `UserRow`, public DTOs `UserDTO`.

Reason: SQL and TypeScript have different idioms. Do not force one naming style everywhere.

## SQL / migration conventions

- Every schema change is a new immutable migration file: `YYYYMMDDHHMM_description.sql`.
- Never edit an applied migration; add a new one.
- Migrations must be safe to run once and obvious to review.
- Use explicit constraints: `not null`, `unique`, `check`, and foreign keys where SQLite supports the intended behavior.
- Enable foreign keys on every SQLite connection: `PRAGMA foreign_keys = ON`.
- Prefer simple SQL over ORM magic. If using Drizzle/Prisma, generated migrations still need review.
- Do not store JSON blobs when fields need filtering, sorting, or constraints.
- Add indexes for lookup paths used by pages/actions, not speculative indexes.

Reason: SQLite is reliable when the schema is deliberate. Most SaaS bugs come from vague migrations and hidden data assumptions.

## Database access rules

- Centralize DB connection code in `lib/db`.
- Expose small query functions such as `getProjectById`, `insertInvite`, `listUserProjects`.
- Query functions validate ownership/tenant scope or are called only by domain functions that do.
- Never concatenate user input into SQL. Use parameters.
- Return plain serializable objects from DB/domain layers.

Reason: authorization leaks happen when every route writes its own SQL.

## Component patterns

- Default to Server Components.
- Add `'use client'` only for state, browser APIs, effects, or event handlers.
- Keep client components thin: collect input, call server action, render optimistic state if needed.
- Fetch data in page/layout Server Components or domain loaders, not inside random nested clients.
- Forms should use shared validators from `lib/validators`.
- Loading/error UI belongs near route segments: `loading.tsx`, `error.tsx`, `not-found.tsx`.

Reason: Next.js performs best when data stays server-side and client JS is intentional.

## Server actions & route handlers

- Server actions handle product mutations from the app UI.
- Route handlers handle webhooks, public APIs, and third-party callbacks.
- Validate all inputs at the boundary with zod or equivalent.
- Re-check auth and tenant ownership inside every mutation.
- Return typed success/error objects; do not throw for expected validation failures.
- Revalidate paths/tags after mutations that affect cached UI.

Reason: boundary validation keeps bad data out and makes Claude Code changes safer.

## Auth and tenancy

- Treat `user_id`/`organization_id` as mandatory on tenant-owned tables.
- Never trust IDs from forms without checking ownership.
- Keep auth helpers in `lib/auth`; do not duplicate session parsing.
- Admin-only paths must have explicit server-side checks.

Reason: SaaS security is mostly boring ownership checks done consistently.

## Error handling

- User-facing errors should be short and non-sensitive.
- Logs may include internal details but never secrets, tokens, or raw payment payloads beyond what is needed for debugging.
- Expected states return structured errors. Unexpected states throw and are logged.

## What we don't do — and why

- No client-side DB calls — leaks credentials and bypasses auth boundaries.
- No editing old migrations — breaks other environments.
- No business logic inside React components — impossible to test and reuse.
- No giant `utils.ts` files — unclear ownership creates duplicated behavior.
- No untyped `any` for request bodies — hides boundary bugs.
- No speculative abstraction — build the second use case before generalizing.
- No silent catch blocks — they create ghost failures.
- No fake green checks — if tests/build were not run, say so.

## Claude Code operating rules

When modifying this project:

1. Inspect nearby files before inventing patterns.
2. Prefer the smallest coherent change.
3. Preserve existing public APIs unless asked to change them.
4. Add or update migrations for schema changes.
5. Update validators when form/API input changes.
6. Run relevant checks and report exact commands/results.
7. If blocked by missing env vars, credentials, or product decisions, say exactly what is missing.
