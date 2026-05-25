# CLAUDE.md: Next.js 15 + SQLite SaaS Template

This file is the operating manual for a greenfield SaaS app built with
Next.js 15 App Router, TypeScript, SQLite, and either `better-sqlite3` for a
local-first app or Turso/libSQL for hosted SQLite.

## Stack And Versions

- Runtime: Node.js 22 LTS or newer. Use one package manager per project.
- Framework: Next.js 15 with the App Router only. Do not add the Pages Router.
- Language: TypeScript in strict mode. Treat `any` as a bug unless an external
  library forces it and the callsite validates the value immediately.
- Database: SQLite with Drizzle ORM migrations. Use `better-sqlite3` for local
  file storage or Turso/libSQL for remote storage.
- UI: Server Components by default, Client Components only for browser state,
  event handlers, refs, effects, or client-only libraries.
- Auth, billing, email, and storage integrations must live behind small server
  modules so product code does not depend on vendor SDK details.

Reason: this stack keeps the app deployable, type-safe, easy to inspect, and
cheap to operate while still matching modern Next.js conventions.

## Dev Commands

Use these names unless the project README says otherwise:

```bash
npm run dev          # Start Next.js locally
npm run lint         # ESLint and framework checks
npm run typecheck    # tsc --noEmit
npm run test         # Unit and integration tests
npm run db:generate  # Generate Drizzle migrations after schema edits
npm run db:migrate   # Apply migrations locally
npm run db:studio    # Inspect local SQLite data
```

Before opening a PR, run `lint`, `typecheck`, `test`, and the relevant database
migration command. If a command is unavailable, add it before adding features.

## Folder Structure

Prefer this structure for new work:

```text
app/
  (marketing)/          Public landing and docs routes
  (app)/                Authenticated product routes
  api/                  Route handlers for webhooks and external callbacks
components/
  ui/                   Low-level reusable controls
  forms/                Form components tied to server actions
db/
  schema.ts             Drizzle schema, relations, indexes
  client.ts             SQLite/Turso client factory
  migrations/           Generated SQL migrations only
features/
  billing/              Billing domain logic and UI
  organizations/        Multi-tenant organization logic
  users/                User profile and account logic
lib/
  auth/                 Session helpers and guards
  env.ts                Typed environment variable parser
  validators/           Zod schemas shared by forms and server actions
tests/
  factories/            Test data builders
  integration/          Server action and database tests
```

Reason: routing, reusable UI, database code, and domain logic stay separate.
Claude should add files where future maintainers will expect them.

## Naming Conventions

- Routes use kebab-case folder names: `app/(app)/billing/settings/page.tsx`.
- React components use PascalCase filenames: `InvoiceTable.tsx`.
- Server actions end in `.actions.ts`; database queries end in `.queries.ts`.
- Zod schemas end in `.schema.ts`; Drizzle tables use plural snake_case names.
- Environment variables are read only through `lib/env.ts`.

Reason: predictable names let Claude navigate without asking where code belongs.

## SQL And Migration Rules

- Change `db/schema.ts` first, then generate a migration. Do not hand-edit a
  generated migration unless fixing a generator defect.
- Every table must include `id`, `created_at`, and `updated_at` unless it is a
  pure join table. Join tables must have a composite unique index.
- Use foreign keys for ownership boundaries such as `organization_id` and
  `user_id`. Add indexes for every foreign key and every frequent lookup.
- Store money in integer minor units, never floating point.
- Store timestamps as ISO strings or integer milliseconds consistently across
  the project. Do not mix formats in one schema.
- Migrations must be forward-only. If data movement is needed, write a small
  idempotent migration script and document the rollback plan in the PR.
- Tests that touch the database must use an isolated SQLite file or in-memory
  database and must not reuse development data.

Reason: SQLite is forgiving, so these rules prevent silent data drift and
production-only bugs.

## Server And Component Patterns

- Fetch data in Server Components or server-only query functions. Pass plain
  serializable props to Client Components.
- Use Server Actions for mutations from forms. Validate inputs with Zod at the
  server boundary and return typed field errors.
- Keep Client Components small. They should manage UI state, not permissions,
  billing decisions, or database writes.
- Use route handlers for webhooks. Verify signatures before parsing or mutating
  data.
- Put authorization checks next to the data access they protect. Never rely on
  hidden buttons as security.
- Prefer simple composition over global state. Add context providers only when
  multiple sibling routes need the same client-side state.

Reason: Next.js App Router works best when server data, client interaction, and
authorization are explicit.

## Testing Expectations

- Add tests for validation, authorization, billing states, and database queries.
- For a new mutation, test the success path and at least one denied path.
- For a schema change, test that the relevant query still works against a fresh
  migrated database.
- Include a short manual verification note in PRs for browser-only behavior.

Reason: SaaS bugs are usually permission, billing, or data-shape bugs; tests
should focus there first.

## What We Do Not Do

- Do not add the Pages Router. Mixing routers creates two mental models.
- Do not use `any` to silence type errors. Validate unknown data instead.
- Do not query SQLite directly from React components. Keep queries server-side.
- Do not place business logic in route files. Route files should assemble
  domain functions, not become the domain layer.
- Do not create migrations without reviewing the generated SQL.
- Do not store secrets, API keys, tokens, or webhook payload samples in git.
- Do not add broad abstractions before two real callsites need them.
- Do not install UI or state libraries for one screen. Use platform and React
  primitives first.

## PR Checklist For Claude

Before saying work is complete, confirm:

- The change follows the folder and naming conventions above.
- Database changes include schema edits, generated migrations, and query tests.
- Mutations validate input, check authorization, and return typed errors.
- `lint`, `typecheck`, `test`, and relevant `db:*` commands pass or are
  explicitly documented as unavailable.
- The PR summary names the affected route, schema/table, and user-facing impact.

If any item is unknown, inspect the repo instead of asking the user first.
