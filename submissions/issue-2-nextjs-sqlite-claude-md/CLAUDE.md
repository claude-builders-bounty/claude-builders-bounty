# CLAUDE.md: Next.js 15 App Router + SQLite SaaS

Use this file as the operating contract for a greenfield SaaS built with Next.js 15 App Router, TypeScript, React Server Components, and SQLite through either `better-sqlite3` for local/single-region deployments or Turso/libSQL for hosted/serverless deployments.

## Stack And Versions

- Next.js 15 with the App Router in `app/`; do not add `pages/`.
- TypeScript in strict mode; all database rows and command inputs are typed.
- SQLite is the system of record. Use `better-sqlite3` for a local file database and `@libsql/client` for Turso.
- React Server Components are the default. Add `"use client"` only for browser state, effects, or event handlers.
- Server Actions handle form mutations close to UI. Route Handlers handle webhooks, public API endpoints, and non-UI HTTP integrations.

Reason: App Router already gives file-based routing, layouts, Server Components, Server Actions, and route handlers. Mixing older patterns makes the project harder to reason about.

## Folder Structure

```text
app/
  (auth)/
  (dashboard)/
  api/
    health/route.ts
  layout.tsx
  page.tsx
components/
  ui/
  forms/
db/
  client.ts
  migrate.ts
  migrations/
    0001_initial.sql
  queries/
    accounts.ts
    invoices.ts
  schema.ts
lib/
  auth.ts
  env.ts
  money.ts
server/
  actions/
  services/
tests/
```

- Put route segments and colocated loading/error UI under `app/`.
- Put reusable presentational components under `components/`; do not put database calls there.
- Put all SQL and migration code under `db/`.
- Put Server Actions under `server/actions/` when shared by multiple routes; colocate only when truly route-specific.
- Put business workflows under `server/services/`; Server Actions and Route Handlers should call services rather than duplicate logic.

Reason: UI, database, and business workflows change at different speeds. The folder structure keeps those boundaries visible.

## Naming Conventions

- Route folders use kebab-case: `app/(dashboard)/customer-invoices/page.tsx`.
- React components use PascalCase file names: `InvoiceTable.tsx`.
- Server Actions use verb-first names: `createInvoice`, `archiveCustomer`.
- Database query functions use table/domain-first names: `invoicesByAccountId`, `insertInvoice`.
- SQL migrations are monotonic and irreversible by default: `0001_initial.sql`, `0002_add_invoice_status.sql`.
- Environment variables are read only through `lib/env.ts`.

Reason: The name should reveal where code runs, what domain it touches, and whether it mutates state.

## SQL And Migration Conventions

- Every schema change is a new `.sql` file under `db/migrations/`; never edit a migration after it has run.
- Migrations run in lexical order inside a transaction.
- Maintain a `_migrations` table with `id`, `name`, `checksum`, and `applied_at`.
- Prefer explicit SQL over ORM magic for core billing, account, and permission tables.
- Use foreign keys and enable them when opening local SQLite connections.
- Store money as integer cents, timestamps as ISO-8601 UTC text, and booleans as `0`/`1`.
- Use `ON DELETE RESTRICT` for billing/account ownership records and `ON DELETE CASCADE` only for disposable child records.
- For Turso/libSQL, keep migrations compatible with SQLite semantics and run them through a controlled deploy step, not lazily during page render.

Reason: SaaS billing and account data need predictable migrations, reversible deployments, and auditability more than they need clever abstractions.

## Database Access Patterns

`db/client.ts` owns the database connection. Do not create ad hoc connections in components, Server Actions, or route handlers.

For `better-sqlite3`:

- Open the database once per Node.js process.
- Enable `PRAGMA foreign_keys = ON`.
- Use prepared statements for all user input.
- Wrap multi-write workflows in `db.transaction(...)`.

For Turso/libSQL:

- Create a single client from `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN`.
- Keep database calls server-only.
- Do not expose Turso credentials to Client Components.

Reason: SQLite is simple when connection ownership is boring. Most bugs come from casual connection creation and untracked migration state.

## Component Patterns

- Fetch data in Server Components and pass plain serializable props to Client Components.
- Keep Client Components small: form controls, menus, charts, optimistic UI, and browser-only widgets.
- Use Server Actions for authenticated dashboard mutations.
- Use Route Handlers for webhooks, health checks, background job callbacks, and external API consumers.
- Use `loading.tsx`, `error.tsx`, and `not-found.tsx` at route boundaries.
- Validate every form payload on the server before touching the database.

Reason: Server Components reduce client JavaScript. Client Components should buy interactivity, not become the default place for app logic.

## Auth, Tenancy, And Permissions

- Every user-owned table includes `account_id` unless it is global reference data.
- Every query for account-scoped data filters by `account_id`.
- Permission checks happen in services before mutation, not only in UI.
- Do not trust route params, hidden fields, cookies, or client-side role labels.
- Use a `memberships` table for account roles instead of storing one global role on `users`.

Reason: SaaS bugs often become cross-tenant data leaks. Make tenant scoping impossible to forget.

## Dev Commands

Use these scripts in `package.json`:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "db:migrate": "tsx db/migrate.ts",
    "db:seed": "tsx db/seed.ts",
    "test": "vitest run"
  }
}
```

Before opening a PR, run:

```bash
npm run typecheck
npm run lint
npm run test
npm run build
```

Reason: A SaaS project needs both framework correctness and schema correctness. `db:migrate` is a first-class dev command, not an afterthought.

## Patterns To Follow

- Keep SQL beside typed query functions in `db/queries/`.
- Return domain objects from services, not raw database rows.
- Use explicit input objects for mutations: `createInvoice({ accountId, customerId, amountCents })`.
- Make dangerous operations two-step in UI and one transaction in the database.
- Prefer boring tables with clear constraints over JSON blobs for core SaaS state.
- Add tests for permission boundaries and migration behavior when touching billing, accounts, auth, or webhooks.

Reason: These patterns make the codebase friendly to agents and humans. The next change should be easy to locate and safe to test.

## Anti-Patterns To Avoid

- Do not add `pages/api`; App Router Route Handlers live under `app/api/**/route.ts`.
- Do not import `db/client.ts` into Client Components.
- Do not run migrations during request handling or React rendering.
- Do not use string interpolation for SQL values.
- Do not mix cents and floating-point money.
- Do not hide account scoping inside UI filters.
- Do not add a global state library until at least two routes need the same client-only state.
- Do not introduce Prisma, Drizzle, or a job queue without a written reason in the PR.

Reason: Each anti-pattern increases hidden state or deployment risk. This template optimizes for a small SaaS team shipping safely.

## How To Answer New Tasks

When asked to implement a feature:

1. Identify route, service, and database boundaries.
2. Check whether a migration is needed.
3. Add or update typed query functions.
4. Add service-level permission checks.
5. Keep UI server-rendered unless browser interactivity is required.
6. Add focused tests for changed business rules.
7. Run typecheck, lint, tests, and build.

If the request is ambiguous, make the smallest assumption that preserves tenant isolation and migration safety, then state it in the final response.
