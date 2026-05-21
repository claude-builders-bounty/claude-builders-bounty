# CLAUDE.md: Next.js 15 + SQLite SaaS

Use this file as the operating context for a greenfield SaaS product built with Next.js 15 App Router, TypeScript, React Server Components, and SQLite through `better-sqlite3` or Turso/libSQL.

## Stack And Versions

- Next.js 15 App Router with TypeScript.
- React Server Components by default; Client Components only for browser-only state, event handlers, or effects.
- SQLite for the source of truth. Use `better-sqlite3` for local/server deployments or Turso/libSQL for hosted SQLite.
- Server Actions or Route Handlers own mutations. UI components never write to the database directly.
- Zod validates all external input before it reaches business logic.
- Tailwind CSS is acceptable for styling, but component structure matters more than utility density.

Reason: this stack is fast for SaaS MVPs when data ownership, rendering mode, and mutation boundaries stay predictable.

## Folder Structure

```text
app/
  (marketing)/
  (app)/
    dashboard/
    settings/
  api/
components/
  ui/
  forms/
  tables/
db/
  client.ts
  migrations/
  queries/
  schema.sql
lib/
  auth/
  billing/
  env.ts
  validation/
server/
  actions/
  services/
tests/
```

- `app/` contains route segments, layouts, loading states, and page composition.
- `components/ui/` contains reusable presentational components only.
- `components/forms/` contains form shells that call server actions.
- `db/client.ts` creates the database connection and applies connection options.
- `db/queries/` contains SQL access functions. Keep SQL near the data boundary.
- `server/services/` contains use-case logic that coordinates validation, queries, and side effects.
- `server/actions/` exposes narrow mutation entrypoints to the UI.

Reason: this separates routing, presentation, domain operations, and SQL so Claude can edit the right layer without guessing.

## Naming Conventions

- Route folders use kebab-case: `billing-history`, `team-settings`.
- React components use PascalCase: `InvoiceTable.tsx`.
- Server actions end with `Action`: `createWorkspaceAction`.
- Query functions use verb-noun names: `getWorkspaceBySlug`, `insertAuditEvent`.
- Database tables use snake_case plural nouns: `workspaces`, `workspace_members`.
- Primary keys are `id`; foreign keys are `<table_singular>_id`.

Reason: predictable names let the agent infer ownership and avoid cross-layer edits.

## Data Model Rules

- Every tenant-owned table includes `workspace_id` unless it is truly global.
- Every mutable business table includes `created_at` and `updated_at`.
- Use ISO timestamp strings or integer milliseconds consistently. Do not mix formats in one project.
- Store money as integer cents plus a currency column.
- Soft delete only when product behavior requires restoration or audit. Otherwise delete intentionally.
- Never store provider secrets in plaintext. Use environment variables or an encrypted secret store.

Reason: SaaS bugs usually come from tenant isolation, timestamps, money precision, and secret handling.

## SQL And Migration Conventions

- Migrations are numbered and immutable: `0001_initial.sql`, `0002_add_workspace_members.sql`.
- Each migration must be safe to run exactly once and should not depend on local machine state.
- Prefer explicit `CREATE TABLE` and `ALTER TABLE` statements over ORM magic.
- Add indexes for foreign keys and high-cardinality lookup columns.
- Do not rewrite old migrations after they are committed. Add a new migration.
- For destructive migrations, add a comment explaining data impact and rollback expectations.

Reason: SQLite is reliable when schema evolution is boring, reviewable, and reversible enough for small teams.

## Query Rules

- Parameterize every SQL statement. Never interpolate user input into SQL strings.
- Keep one query function responsible for one database operation.
- Return typed domain objects, not raw unshaped rows, from `db/queries/`.
- Transactions wrap multi-step writes that must succeed or fail together.
- Do not call database queries from Client Components.

Reason: this prevents SQL injection, partial writes, and accidental client-side database access.

## Server Action Rules

- Server actions validate input with Zod first.
- Server actions check authentication and workspace authorization before mutation.
- Server actions call services or query functions; they do not contain large SQL blocks inline.
- Return typed success/error results that forms can render.
- Revalidate paths or tags after mutations that affect rendered pages.

Reason: server actions are public mutation boundaries and must be small, auditable, and safe.

## Component Patterns

- Keep pages as composition roots that fetch data and assemble components.
- Keep forms small: field state, submit state, and error rendering only.
- Extract tables when columns, empty states, or row actions become nontrivial.
- Use Client Components only where interactivity requires them.
- Do not pass secrets, raw database rows with hidden fields, or internal error details into Client Components.

Reason: App Router works best when server rendering owns data and client code only owns interaction.

## Environment Rules

- Define required environment variables in `lib/env.ts`.
- Validate env at process startup with clear error messages.
- Use separate values for development, test, and production.
- Never commit `.env`, `.env.local`, database files with production data, or provider tokens.

Reason: environment drift causes deployment failures and accidental secret leaks.

## Authentication And Authorization

- Authentication identifies the user. Authorization checks workspace membership and role.
- Every workspace-scoped query must receive `workspace_id` from trusted server context, not from unchecked form data.
- Admin-only actions must check role at the server boundary.
- Audit important account, billing, team, and data export actions.

Reason: multi-tenant SaaS security depends on server-side ownership checks, not UI hiding.

## Testing Expectations

- Unit test pure validation and service functions.
- Integration test critical query functions against a temporary SQLite database.
- Smoke test core flows: sign in, create workspace, create/update the main product object, invite member, export or view billing state.
- Add a regression test for every bug fix that touches data, auth, billing, or permissions.

Reason: small SaaS teams need tests that protect money, data ownership, and core workflows without slowing every UI change.

## Dev Commands

Use these command names unless the project defines different scripts:

```bash
npm run dev
npm run lint
npm run typecheck
npm run test
npm run db:migrate
npm run db:seed
```

If a command is missing, inspect `package.json` and use the closest available script. Do not invent a passing command.

## What We Do Not Do

- Do not add a second database layer unless the project already has one.
- Do not introduce a heavy ORM unless the user explicitly asks for it.
- Do not put business rules in React components.
- Do not fetch workspace data using IDs supplied only by the browser.
- Do not weaken validation to make a form submit.
- Do not silently catch database errors that should be visible in logs.
- Do not add new UI libraries for one component.
- Do not create a landing page when the task asks for the app workflow.

Reason: these shortcuts make the project harder to ship, debug, and secure.

## Default Implementation Flow

1. Read `package.json`, `db/schema.sql`, existing migrations, and the target route.
2. Identify whether the change belongs in UI, server action, service, query, or migration.
3. Add or update validation before touching mutations.
4. Make the smallest coherent change.
5. Run the most relevant checks: lint, typecheck, test, migration check, or smoke flow.
6. Explain any command that could not be run.

Reason: this keeps changes scoped and gives the user a reliable audit trail.
