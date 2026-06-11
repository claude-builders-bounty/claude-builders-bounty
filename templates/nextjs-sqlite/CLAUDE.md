# CLAUDE.md — Next.js 15 App Router + SQLite SaaS

This file is the working agreement for Claude Code in a greenfield SaaS built with Next.js 15, React 19, TypeScript, Tailwind CSS, and SQLite via `better-sqlite3` for local/single-node apps or Turso/libSQL for hosted edge-friendly deployments.

## Product baseline

- Build a multi-tenant SaaS with email/password or OAuth auth, billing-ready account pages, audit-friendly data access, and admin-safe defaults.
- Optimize for correctness, small diffs, and boring maintainability over clever abstractions.
- Treat SQLite as the source of truth. Do not hide schema changes behind implicit ORM magic.
- Prefer server-first code. Client components are only for stateful UI interactions.

## Stack and versions

- Next.js 15 App Router under `app/`.
- React 19 with Server Components by default.
- TypeScript in `strict` mode.
- SQLite:
  - `better-sqlite3` for local, test, CLI, and simple VPS deployments.
  - Turso/libSQL when remote replication or hosted SQLite is required.
- Zod for external input validation.
- Tailwind CSS for styling.
- Vitest for unit tests and Playwright only for critical flows.

Reason: this stack keeps the app deployable, debuggable, and easy for Claude to reason about without splitting business logic across too many frameworks.

## Required project structure

```text
app/
  (marketing)/
  (app)/
  api/
components/
  ui/
  forms/
  shell/
db/
  client.ts
  migrations/
  schema.sql
  queries/
lib/
  auth/
  config/
  domain/
  validation/
scripts/
  db-migrate.ts
  db-seed.ts
tests/
  unit/
  integration/
```

Rules:

- Route groups separate public marketing pages from authenticated product pages because auth layout and caching rules differ.
- `components/ui` contains generic primitives only; product-specific components live near their route or in `components/forms` / `components/shell`.
- `db/queries` is the only place that imports the database client directly.
- `lib/domain` contains pure business rules with no Next.js imports.
- `app/api` route handlers must be thin: validate input, call domain/query functions, return typed responses.

## Naming conventions

- Files: kebab-case (`invoice-list.tsx`, `create-team.ts`).
- React components: PascalCase exports (`InvoiceList`).
- Server actions: verb-first names ending in `Action` (`createTeamAction`).
- Query functions: intent-first names (`getUserByEmail`, `listInvoicesForTeam`).
- Mutations: imperative names (`insertInvoice`, `updateSubscriptionStatus`).
- Migrations: zero-padded timestamp and action (`0001_create_users.sql`, `0002_add_team_members.sql`).

Reason: consistent naming lets Claude locate the right layer before editing and prevents duplicate helpers.

## Development commands

Use these defaults unless `package.json` says otherwise:

```bash
npm install
npm run dev
npm run typecheck
npm run lint
npm run test
npm run db:migrate
npm run db:seed
```

If a command is missing, add it to `package.json` before adding new tooling. Do not invent one-off shell commands in PR descriptions.

## Environment variables

Define every variable in `.env.example` with a safe placeholder:

```text
DATABASE_URL="file:./dev.db"
AUTH_SECRET="change-me-in-development"
APP_URL="http://localhost:3000"
```

- Never read `process.env` outside `lib/config/env.ts`.
- Validate env vars once at startup with Zod.
- Never commit `.env`, local SQLite databases, secrets, session cookies, or API keys.

Reason: one validated config boundary prevents runtime-only failures and secret leaks.

## SQLite and migration conventions

- Every schema change must be a SQL migration in `db/migrations`.
- Migrations are append-only. Never edit a migration that may have run outside your machine.
- Keep `db/schema.sql` updated as the full current schema snapshot.
- Use explicit constraints: `not null`, `unique`, `check`, and foreign keys.
- Enable foreign keys for every connection: `PRAGMA foreign_keys = ON`.
- Store timestamps as ISO-8601 UTC text unless the project already standardizes on integer epoch milliseconds.
- Use transactions for multi-step writes.
- Create indexes for every foreign key and high-cardinality lookup used in production routes.

Example migration style:

```sql
create table teams (
  id text primary key,
  name text not null check (length(name) between 2 and 80),
  created_at text not null default (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

create table team_members (
  team_id text not null references teams(id) on delete cascade,
  user_id text not null references users(id) on delete cascade,
  role text not null check (role in ('owner', 'admin', 'member')),
  created_at text not null default (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  primary key (team_id, user_id)
);

create index team_members_user_id_idx on team_members(user_id);
```

Reason: SQLite is reliable when the schema is explicit and migrations are auditable.

## Database access patterns

- Do not query the database directly in React components.
- Server Components may call query functions from `db/queries`.
- Client Components must call Server Actions or route handlers; they never import database modules.
- Return plain objects from query functions. Do not leak driver-specific rows through the app.
- Validate all external input before a write. Validate database output only at trust boundaries or when reading JSON columns.

Preferred query shape:

```ts
export async function getTeamForUser(teamId: string, userId: string) {
  return db
    .prepare(`
      select t.id, t.name, tm.role
      from teams t
      join team_members tm on tm.team_id = t.id
      where t.id = ? and tm.user_id = ?
    `)
    .get(teamId, userId) as TeamForUser | undefined;
}
```

Reason: colocated SQL is easier to review than hidden query builders for a small SaaS.

## App Router patterns

- Use Server Components by default.
- Add `'use client'` only at the smallest interactive boundary.
- Fetch authenticated data on the server; never expose privileged API endpoints just to hydrate a page.
- Use `loading.tsx`, `error.tsx`, and `not-found.tsx` for product routes.
- Use `revalidatePath` or `revalidateTag` after mutations that affect cached pages.
- Set `dynamic = 'force-dynamic'` for pages that depend on per-request auth.

Reason: these rules avoid accidental data leaks and reduce client JavaScript.

## Server Actions and route handlers

- Server Actions are for form-like mutations from the app UI.
- Route handlers are for webhooks, external integrations, and public API endpoints.
- Every mutation returns a typed result: `{ ok: true, data }` or `{ ok: false, error }`.
- Never throw user-facing validation errors across the network boundary.
- Use idempotency keys for payment, webhook, invite, and email-sending flows.

Reason: predictable mutation contracts make Claude-generated UI and tests much safer.

## Component patterns

- Keep components small and named by product intent.
- Prefer composition over prop bags with many booleans.
- Form components receive `defaultValues`, call one action, and render field-level errors.
- UI primitives do not import app-specific domain types.
- Avoid global client state unless URL params or server state cannot model the interaction.

Reason: this keeps the component tree understandable and prevents frontend-only business logic.

## Auth and authorization

- Authentication answers “who is this user?” Authorization answers “can this user do this action?” Keep them separate.
- Every query that reads tenant data must include the authenticated `userId` or verified `teamId` membership.
- Never trust route params as authorization proof.
- Admin routes must check role on the server for every request.
- Log security-relevant events: login, logout, role change, API key creation, billing changes.

Reason: most SaaS data leaks come from missing tenant filters, not broken login.

## Error handling and observability

- User errors: return typed validation messages.
- System errors: log server-side context and show a generic user-safe message.
- Include request or operation IDs for webhook and billing flows.
- Never log passwords, tokens, cookies, OAuth codes, or full payment payloads.

Reason: logs should help debug production without becoming a data breach.

## Testing expectations

- Unit test pure domain rules in `lib/domain`.
- Integration test `db/queries` against a temporary SQLite database.
- Add regression tests for every bug fix.
- For Server Actions, test validation and authorization branches.
- For critical SaaS flows, add Playwright coverage only after the server-side logic is tested.

Minimum PR check before asking for review:

```bash
npm run typecheck
npm run lint
npm run test
npm run db:migrate
```

Reason: fast tests catch most Claude-generated mistakes before review.

## Anti-patterns we do not allow

- Do not create generic `utils.ts` dumping grounds because they hide ownership.
- Do not import `db/client.ts` outside `db/queries`, scripts, or tests because it bypasses authorization patterns.
- Do not make everything a Client Component because it leaks data concerns into the browser.
- Do not silently modify old migrations because teammates and production databases cannot replay history safely.
- Do not add an ORM unless the project explicitly chooses one because raw SQL is clearer for SQLite SaaS scale.
- Do not catch and ignore errors because failed writes must be visible.
- Do not add new dependencies for simple formatting, date, or validation tasks already covered by the stack.

## How Claude should work in this repository

1. Read `package.json`, `db/schema.sql`, and the relevant route before editing.
2. Identify whether the change belongs in UI, domain logic, query code, migration, or config.
3. Make the smallest coherent diff.
4. Add or update tests for changed behavior.
5. Run the minimum PR check and report exact command output.
6. If a requirement conflicts with this file, ask for clarification before changing architecture.

Reason: Claude should preserve the architecture instead of solving every task with a new pattern.
