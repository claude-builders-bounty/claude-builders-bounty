# CLAUDE.md

This project is a greenfield SaaS app using Next.js 15 App Router, TypeScript, SQLite, and server-first React. Treat this file as the operating manual for code generation, reviews, migrations, and refactors.

## Stack And Versions

- Next.js 15 with the App Router. Use Server Components by default because they reduce client JavaScript and keep data access near the route.
- React 19 conventions. Use `use client` only when browser state, effects, refs, or event handlers are required.
- TypeScript in strict mode. Prefer explicit domain types over `any` because SaaS bugs usually come from ambiguous data shape changes.
- SQLite through either `better-sqlite3` for local/single-node deployments or Turso/libSQL for hosted deployments. Keep the repository API stable so the storage driver can change without rewriting UI code.
- SQL migrations live in the repo and are reviewed like code. The database schema is part of the product contract.
- Styling uses Tailwind CSS plus small shared UI primitives. Avoid one-off component CSS unless the styling is genuinely local.

## Project Structure

Use this structure unless an existing project has already established a stricter one:

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
  layout/
db/
  client.ts
  migrations/
  schema.sql
lib/
  auth/
  config/
  server/
  utils/
modules/
  billing/
  organizations/
  users/
tests/
  unit/
  integration/
  e2e/
```

Reasons:

- Route groups keep public marketing pages separate from authenticated product pages.
- `modules/*` owns business behavior so features do not become tangled across `app/`.
- `db/*` owns connection, schema, and migrations so database changes are easy to audit.
- `components/ui/*` is generic; feature-specific components stay in the owning module or route.

## Naming Conventions

- Files and folders use kebab-case: `create-organization-form.tsx`.
- React components use PascalCase exports: `CreateOrganizationForm`.
- Server actions end with `.action.ts`: `create-organization.action.ts`.
- Data access files end with `.repo.ts`: `organization.repo.ts`.
- Validation schemas end with `.schema.ts`: `organization.schema.ts`.
- Tests mirror the file under test: `organization.repo.test.ts`.

Reason: suffixes make intent obvious to Claude Code and prevent mixing UI, validation, and persistence in one file.

## Development Commands

Prefer these package scripts:

```bash
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm db:migrate
pnpm db:studio
```

Before opening a PR, run at minimum:

```bash
pnpm lint && pnpm typecheck && pnpm test
```

Reason: App Router code can fail in type-only paths that a browser smoke test will not hit.

## Environment And Config

- Read environment variables through `lib/config/env.ts`, not directly from `process.env` throughout the app.
- Validate env at startup with a schema and fail fast when required values are missing.
- Keep `.env.example` complete and safe. Never include secrets, production URLs with tokens, or personal credentials.
- Treat database URLs as secrets even for SQLite/Turso because hosted database tokens often ride in the same value.

Reason: centralized config makes deployments reproducible and prevents silent fallback to unsafe defaults.

## SQLite And Migration Rules

- Every schema change gets a numbered migration in `db/migrations/`.
- Migration names use `YYYYMMDDHHMM_description.sql`.
- Migrations must be forward-only. Do not edit a migration after it has been merged; create a new one.
- Use explicit transactions around multi-statement migrations.
- Prefer additive migrations: create columns/tables first, backfill second, enforce constraints last.
- Foreign keys must be enabled for local SQLite connections with `PRAGMA foreign_keys = ON`.
- Add indexes for every foreign key and every frequently filtered SaaS field such as `organization_id`, `user_id`, `status`, and `created_at`.
- Store timestamps as ISO 8601 text or integer epoch milliseconds, then use one convention everywhere.
- Use `TEXT` ids with generated UUID/ULID values for public-facing entities. Avoid exposing autoincrement ids in URLs.

Reason: SQLite is reliable when constraints and migrations are explicit; most production issues come from implicit schema drift.

## Data Access Pattern

- UI and Server Actions must not contain raw SQL.
- Put raw SQL in `*.repo.ts` files and export small functions with domain names.
- Repositories return typed domain objects, not driver-specific rows.
- Keep transaction boundaries in service functions under `lib/server/` or `modules/*`.
- Never build SQL by string concatenating user input. Use prepared statements or tagged parameter APIs.

Example shape:

```ts
// modules/organizations/organization.repo.ts
export async function getOrganizationBySlug(slug: string): Promise<Organization | null> {
  return db.prepare("select * from organizations where slug = ?").get(slug) ?? null;
}
```

Reason: isolating SQL makes migrations, tests, and driver swaps manageable.

## App Router Patterns

- Fetch data in Server Components when possible.
- Use Server Actions for form mutations that belong to the current route.
- Use Route Handlers for webhooks, public APIs, file uploads, and integrations that need HTTP semantics.
- After a mutation, call `revalidatePath` or `revalidateTag` for the smallest affected surface.
- Keep `loading.tsx`, `error.tsx`, and `not-found.tsx` close to the route that owns the state.

Reason: App Router works best when data loading, mutation, and cache invalidation are scoped to route ownership.

## Component Patterns

- Components are Server Components unless they need browser interactivity.
- Client Components receive serializable props only.
- Move form state, optimistic UI, and browser APIs into small leaf Client Components.
- Keep page components as orchestration layers; move reusable product UI into `modules/*`.
- Shared UI primitives in `components/ui` must not import business modules.

Reason: this keeps the client bundle small and prevents circular dependencies between generic UI and product logic.

## Forms And Validation

- Validate all user input on the server, even if the client already validates it.
- Use one schema per mutation and share it between form parsing and tests.
- Return field-level errors for expected validation failures.
- Throw only for unexpected system failures.
- Never trust `organization_id`, `user_id`, role, or price values from the client. Derive them from the session or database.

Reason: SaaS forms are security boundaries, not just UI helpers.

## Authentication And Authorization

- Authentication answers "who is this user"; authorization answers "can this user do this action".
- Check authorization in the server action, route handler, or service function that performs the mutation.
- Do not rely on hidden buttons or protected pages as the only authorization control.
- Organization-scoped queries must include `organization_id` in the SQL predicate.
- Admin-only actions must be audited with actor id, target id, action, and timestamp.

Reason: multi-tenant data leaks usually happen when authorization is checked in UI but not in the write path.

## Error Handling

- User-caused errors return typed results: `{ ok: false, fieldErrors }`.
- System errors are logged server-side and shown as a generic message.
- Do not expose SQL, stack traces, tokens, or provider payloads to users.
- Webhooks should be idempotent and log duplicate delivery attempts at debug level.

Reason: predictable error shapes make Claude Code generate safer forms and tests.

## Testing Rules

- Unit test validation, formatters, and pure business logic.
- Integration test repositories against a temporary SQLite database.
- E2E test one happy path per critical workflow: sign in, create organization, invite user, change billing state.
- Every migration that changes data shape needs at least one test or smoke script proving old rows still read correctly.
- Do not mock authorization in mutation tests; create realistic users, organizations, and roles.

Reason: the highest-risk bugs are schema changes and tenant-boundary mistakes.

## Patterns To Follow

- Small modules with clear ownership.
- Server-first rendering.
- Prepared SQL statements.
- Forward-only migrations.
- Route-local loading and error states.
- Explicit cache invalidation after mutation.
- Accessibility in every interactive component: label, focus state, keyboard path, and error text.

## Anti-Patterns To Avoid

- Do not put raw SQL in React components. It couples UI to storage and makes tests brittle.
- Do not mark an entire layout as `use client`. It ships unnecessary JavaScript to every page.
- Do not edit old migrations. Teammates and production databases may already have run them.
- Do not use `SELECT *` in long-lived repository functions. Schema additions should not silently change API shape.
- Do not use global mutable singletons for request-specific data. Server rendering can interleave requests.
- Do not trust client-provided tenant ids. Always derive tenant scope from the authenticated session.
- Do not catch errors and return `null` unless `null` is a valid domain result. Silent failures hide production data issues.
- Do not add a dependency for a one-line helper. SaaS projects accumulate dependency risk quickly.

## Completion Checklist For Claude Code

Before considering a task complete:

- The change follows the folder and suffix conventions above.
- Database changes include a migration and a test or smoke verification.
- Mutations validate input and check authorization server-side.
- Client Components are limited to interactive leaves.
- `pnpm lint`, `pnpm typecheck`, and relevant tests pass or the PR explains why they could not run.
- The PR summary states the user-visible behavior, data model changes, and test coverage.

When unsure, prefer the smaller server-side change with explicit tests over a broad abstraction.
