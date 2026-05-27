# CLAUDE.md - Next.js 15 + SQLite SaaS

Use this file as the default project context for a greenfield SaaS built with
Next.js 15 App Router, TypeScript, SQLite, and either `better-sqlite3` for local
single-node deployments or Turso/libSQL for hosted SQLite.

## Stack And Versions

- Next.js 15 with App Router. Reason: server components, route handlers, and
  server actions keep most product logic on the server by default.
- TypeScript with strict mode. Reason: database rows and form payloads otherwise
  drift silently as the app grows.
- SQLite through `better-sqlite3` for local/dev or `@libsql/client` for Turso.
  Reason: both keep the relational model simple while supporting different
  deployment targets.
- Zod at every external boundary. Reason: forms, webhooks, and route handlers
  need runtime validation, not just TypeScript types.
- No global state library by default. Reason: most SaaS state belongs in the URL,
  server data, or small client components.

## Project Structure

Prefer this layout:

```txt
app/
  (marketing)/
  (auth)/
  (app)/
    dashboard/
    settings/
  api/
    webhooks/
components/
  ui/
  forms/
  layout/
db/
  client.ts
  migrations/
  queries/
  schema.sql
lib/
  auth/
  billing/
  env.ts
  permissions.ts
server/
  actions/
  services/
  jobs/
tests/
  unit/
  integration/
```

Reasons:

- Route groups keep marketing, auth, and signed-in product surfaces separate.
- `db/queries` contains SQL and row mapping; React files should not contain SQL.
- `server/services` owns workflows that touch more than one table or external
  API.
- `components/ui` stays generic; product-specific components live near routes or
  in `components/forms`.

## Dev Commands

Use these scripts unless the repo already defines equivalents:

```bash
npm run dev
npm run lint
npm run typecheck
npm run test
npm run db:migrate
npm run db:studio
```

If a command is missing, add the script before relying on it in docs or CI.
Reason: Claude should never invent commands during implementation.

## Environment Rules

- Read environment variables only through `lib/env.ts`.
- Validate env with Zod at process startup.
- Split public and server-only values: `NEXT_PUBLIC_*` is allowed only for
  browser-safe values.
- Never import `process.env` directly inside components, server actions, or
  query modules.

Reason: central env validation prevents production-only failures and accidental
secret exposure.

## SQLite And Migration Conventions

- Every schema change gets a numbered migration:
  `db/migrations/0001_create_users.sql`.
- Migrations are append-only. Never edit an applied migration.
- Use explicit foreign keys and enable `PRAGMA foreign_keys = ON`.
- Store timestamps as ISO strings or integer epoch milliseconds; do not mix both.
- Use `TEXT` IDs generated in application code unless there is a measured reason
  to use integer IDs.
- Add indexes in the same migration as the query pattern that requires them.
- Keep SQL in `.sql` files or tagged query helpers, not inside UI components.

Reason: SQLite is forgiving, so the project must be strict about migration
history and data shape.

## Query Patterns

- Name query functions by intent: `getWorkspaceBySlug`, `listInvoicesForUser`.
- Return domain objects, not raw driver rows, from `db/queries`.
- Map nullable database fields to explicit TypeScript unions.
- Do not return `any` from database helpers.
- Wrap multi-step writes in transactions.

Example:

```ts
export async function createWorkspace(input: CreateWorkspaceInput) {
  const data = createWorkspaceSchema.parse(input);
  return db.transaction(() => {
    const workspace = insertWorkspace(data);
    insertMembership({ workspaceId: workspace.id, role: "owner" });
    return workspace;
  })();
}
```

Reason: SaaS bugs often come from partial writes and unclear row mapping.

## Server And Client Component Rules

- Components are server components unless they need browser-only APIs, local
  state, effects, or event handlers.
- Put `"use client"` at the leaf component, not at the page level.
- Fetch data in server components or services; pass plain serializable props to
  client components.
- Mutations go through server actions or route handlers with Zod validation.
- Never call database helpers from client components.

Reason: App Router is strongest when server/client boundaries are explicit and
small.

## Server Actions

- Keep server actions thin: validate input, check permission, call a service,
  return a typed result.
- Every action must answer these questions in code:
  - Who is the actor?
  - What resource are they touching?
  - What permission allows it?
  - What validation protects the write?
- Return discriminated unions such as `{ ok: true, data }` or
  `{ ok: false, error }`.

Reason: actions become untestable when auth, validation, SQL, and UI state are
mixed together.

## Auth And Permissions

- Authentication proves identity; authorization checks resource access. Keep
  them separate.
- All app routes under `(app)` must require a user session before data access.
- Permission helpers live in `lib/permissions.ts`.
- Never trust workspace IDs, user IDs, or role names from client payloads.

Reason: most SaaS security bugs are confused-deputy bugs across workspaces.

## Component Patterns

- Shared UI primitives in `components/ui` must not import app services.
- Forms use a schema shared by the client and server action.
- Use optimistic UI only after the server mutation has a clear rollback path.
- Empty, loading, and error states are part of the component contract.

Reason: product UI should stay predictable when latency or validation fails.

## Error Handling

- Throw only for programmer errors or truly unexpected infrastructure failures.
- Expected validation and permission failures return typed errors.
- Log server-side errors with enough context to debug, but never log secrets,
  tokens, raw cookies, full payment payloads, or personal documents.
- Route handlers should return structured JSON errors with stable `code` values.

Reason: SaaS support depends on repeatable error codes and safe logs.

## Testing Rules

- Unit-test pure services and permission helpers.
- Integration-test database queries with an isolated SQLite file or in-memory DB.
- Add regression tests for every fixed bug.
- Test migrations on an empty database and on a database with representative
  existing rows.
- Do not mock the database for query tests; use SQLite.

Reason: mocks hide the constraints and transaction behavior that matter most.

## Naming Conventions

- Files and routes: kebab-case.
- React components: PascalCase.
- Server actions: verb-first names, e.g. `createWorkspaceAction`.
- Query functions: intent-first names, e.g. `listWorkspaceMembers`.
- Tables: snake_case plural nouns.
- Columns: snake_case.

Reason: predictable names reduce the context Claude needs before editing.

## What We Do Not Do

- Do not put SQL in React components. Reason: it couples UI churn to data access.
- Do not add an ORM unless asked. Reason: SQLite-first apps often benefit from
  explicit SQL and simple migrations.
- Do not create client components for static display. Reason: it increases bundle
  size and weakens server boundaries.
- Do not silently create tables at runtime. Reason: deploys should run explicit
  migrations.
- Do not catch and ignore database errors. Reason: failed writes must be visible.
- Do not introduce background jobs without idempotency keys. Reason: retries can
  duplicate invoices, emails, or workspace changes.
- Do not store money as floating point. Reason: use integer minor units.

## Before Editing Checklist

1. Identify whether the change is UI, server action, service, query, migration,
   or route handler.
2. Read the closest existing file in that category and follow its pattern.
3. If a table changes, add a migration and update `db/schema.sql`.
4. If behavior changes, add or update a focused test.
5. Run lint, typecheck, tests, and migrations before claiming completion.

## Completion Checklist

- `npm run lint` passes.
- `npm run typecheck` passes.
- `npm run test` passes.
- `npm run db:migrate` passes on a clean database.
- New or changed environment variables are documented in `.env.example`.
- The final response lists changed files, verification commands, and any known
  risk.

