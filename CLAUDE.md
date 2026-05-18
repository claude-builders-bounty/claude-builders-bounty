# CLAUDE.md — Next.js 15 + SQLite SaaS

## Stack & versions

- Next.js 15 App Router, React 19, TypeScript strict mode.
- SQLite via `better-sqlite3` for single-node/local-first apps, or Turso/libSQL when the app needs hosted edge-friendly SQLite.
- Server-first architecture: React Server Components by default, Client Components only for browser state/effects.
- Styling assumes Tailwind CSS plus small local components. Do not introduce a component library unless the product already uses one.
- Auth, billing, and email providers are adapters under `src/lib/*`; product code must not import vendor SDKs directly.

Reason: this stack is fast when the database boundary is explicit and most UI stays server-rendered. Vendor code at the edges keeps migrations cheap.

## Folder structure

Use this layout for a greenfield SaaS:

```txt
src/
  app/
    (marketing)/
    (app)/
    api/
    layout.tsx
  components/
    ui/
    forms/
  features/
    <feature>/
      actions.ts
      components/
      queries.ts
      schema.ts
      types.ts
  lib/
    auth/
    db/
    email/
    billing/
    env.ts
  migrations/
    0001_initial.sql
  test/
```

Rules:

- `src/app` owns routing only: layouts, pages, route handlers, metadata.
- `src/features/<feature>` owns product behavior. Put feature-specific SQL, server actions, validation, and UI there.
- `src/lib/db` owns the SQLite connection, transaction helper, and shared low-level SQL utilities.
- `src/components/ui` is generic and product-agnostic. If a component knows about invoices, teams, projects, etc., it belongs in `features/*/components`.
- Keep tests next to the code for unit tests or under `src/test` for integration helpers.

Reason: App Router projects become messy when routes, SQL, and UI logic all live in `app`. Feature folders keep business changes localized.

## Naming conventions

- Files: kebab-case for components and utilities, e.g. `team-switcher.tsx`, `create-project.ts`.
- React components: PascalCase exports, e.g. `TeamSwitcher`.
- Server actions: verb-first names, e.g. `createProjectAction`, `inviteMemberAction`.
- Queries: data-shaped names, e.g. `getProjectById`, `listProjectsForUser`.
- Database tables: plural snake_case, e.g. `users`, `team_members`, `billing_events`.
- Columns: snake_case. Always include `id`, `created_at`, and `updated_at` unless it is a join table or append-only event table.
- IDs: use text UUID/ULID in app code. Do not expose SQLite rowids.

Reason: the app crosses TS, SQL, and React. Strict naming removes translation guesswork.

## Dev commands

Use these commands unless the project README says otherwise:

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm db:migrate
pnpm db:reset
```

Expected scripts:

```json
{
  "dev": "next dev",
  "build": "next build",
  "lint": "next lint",
  "typecheck": "tsc --noEmit",
  "test": "vitest run",
  "db:migrate": "tsx src/lib/db/migrate.ts",
  "db:reset": "tsx src/lib/db/reset.ts"
}
```

Before finishing any code change, run the smallest relevant check first, then `pnpm typecheck` and `pnpm lint` if files changed broadly.

Reason: Next.js catches routing/build issues late; TypeScript and lint should fail before review.

## SQL / migration conventions

- Migrations live in `src/migrations` and are numbered: `0001_initial.sql`, `0002_add_team_invites.sql`.
- Migrations are append-only. Never edit a migration that may have run outside your machine.
- Every migration must run inside a transaction.
- Enable foreign keys for every connection: `PRAGMA foreign_keys = ON`.
- Prefer explicit constraints over app-only checks: `NOT NULL`, `UNIQUE`, `CHECK`, `FOREIGN KEY`.
- Store timestamps as ISO-8601 UTC text unless the project has a documented integer epoch convention.
- Use join tables for many-to-many relationships; do not store comma-separated IDs or JSON arrays for relational data.
- Add indexes in the same migration as the query that needs them.
- Do not use `SELECT *` in app queries. Select named columns so UI changes do not accidentally depend on schema shape.
- Wrap multi-write flows in a transaction helper, e.g. `db.transaction(() => { ... })`.

Reason: SQLite is reliable when constraints and migrations are boring. Most SaaS data bugs come from implicit rules that only exist in TypeScript.

## Database access pattern

- All SQL is server-only. Never import database modules from Client Components.
- Put reusable reads in `queries.ts` and writes in server actions or service functions.
- Validate all external input with the feature's `schema.ts` before it reaches SQL.
- Return plain objects from queries. Do not leak driver rows or statements across module boundaries.
- Convert database nullability into explicit TypeScript types at the query boundary.

Reason: a narrow DB boundary prevents accidental client bundling and makes auth checks reviewable.

## Component patterns

- Pages and layouts are Server Components unless they need browser APIs, local state, or event handlers.
- Put `'use client'` at leaf components, not at route/page level.
- Fetch data in Server Components or server actions. Do not fetch internal API routes from Server Components.
- Forms should use server actions for mutations. Keep optimistic UI small and reversible.
- Keep components focused: if a component both fetches data and manages complex client state, split it.
- Use accessible HTML first. Buttons are buttons, links are links, labels are connected to inputs.
- Loading and error states belong beside the route segment that owns the data.

Reason: App Router performs best when the server does data work and the client handles only interaction.

## Auth and authorization

- Authentication proves who the user is; authorization proves they can access a resource. Check both.
- Every query or mutation scoped to a team/account must include that scope in SQL, not only in TypeScript.
- Do not trust IDs from params or forms. Verify ownership in the same operation that reads or writes data.
- Keep auth helpers in `src/lib/auth`. Feature code may call helpers like `requireUser()` or `requireTeamMember(teamId)`.

Reason: SaaS security bugs usually happen when a valid user supplies another user's ID.

## Environment variables

- Read env vars through `src/lib/env.ts` only.
- Validate required env vars at startup with a schema.
- Prefix only browser-safe variables with `NEXT_PUBLIC_`.
- Do not read `process.env` inside components or feature modules.

Reason: central validation makes deploy failures obvious and prevents secret leakage to the browser.

## Error handling

- Show user-safe messages in UI. Log detailed errors on the server.
- Do not swallow database errors. If a constraint can fail, handle that specific error and explain the user action needed.
- Use `notFound()` for missing route resources and explicit forbidden handling for unauthorized access.
- Avoid catch-all `try/catch` blocks that return success-shaped data.

Reason: silent failures create corrupted product state and make Claude debug the wrong layer.

## Testing expectations

- Unit test pure validation, formatting, and permission helpers.
- Integration test migrations and important SQL queries against a temporary SQLite database.
- Test one successful path and one authorization failure for every important mutation.
- Do not snapshot large React trees. Prefer assertions on visible text, roles, and resulting data.

Reason: SQLite-backed apps can test real persistence cheaply; mocks hide migration/query bugs.

## Patterns to follow

- Start with the schema and user flow, then implement UI.
- Keep server actions thin: validate input, authorize, call one focused write function, revalidate/redirect.
- Prefer explicit props over global client stores.
- Use route groups for marketing vs authenticated app areas.
- Revalidate cache paths/tags immediately after mutations that change visible data.
- Add comments only for business rules or non-obvious tradeoffs, not for what the code literally does.

## Anti-patterns to avoid

- No generic repository layer over SQLite. It hides SQL and makes constraints harder to review.
- No Prisma-style assumptions unless Prisma is actually installed. This project uses SQLite directly.
- No database calls in Client Components.
- No internal `fetch('/api/...')` from Server Components. Import the server function/query instead.
- No editing old migrations after they have shipped.
- No broad `any` types to silence schema mismatches.
- No premature multi-tenant abstraction. Implement team/account scope directly, then extract only after repetition is real.
- No background jobs hidden in route handlers. Use an explicit job/queue mechanism if needed.

Reason: these shortcuts feel fast, but they make small SaaS projects hard to evolve and hard for Claude to reason about.

## How Claude should work in this repo

1. Read the route, feature folder, and migration that relate to the task before editing.
2. State any assumption that affects schema, auth, or billing behavior.
3. Make the smallest change that satisfies the requested behavior.
4. Add or update the closest relevant test when changing validation, SQL, auth, or money-related logic.
5. Run the relevant command and report the exact result.
6. If a command cannot run because dependencies or env vars are missing, say that directly and provide the next concrete command.

Reason: this keeps changes reviewable and prevents broad rewrites from a vague prompt.
