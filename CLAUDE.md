# CLAUDE.md

Guidance for Claude Code when building or maintaining a production Next.js 15 App Router SaaS project with SQLite.

## Product Assumptions

- The app is a multi-tenant SaaS with authenticated users, organizations, billing-aware limits, and server-rendered dashboards.
- The primary runtime is Node.js, not Edge, because SQLite drivers such as `better-sqlite3` require Node APIs.
- The database is SQLite in local development and either Turso/libSQL or a managed SQLite-compatible service in production.
- Correctness, data integrity, and predictable server behavior matter more than clever abstractions.

## Stack

- Next.js 15 with App Router and React Server Components.
- TypeScript in strict mode.
- SQLite with migrations committed to the repository.
- Prefer `better-sqlite3` for single-node/local apps.
- Prefer Turso/libSQL when the app needs hosted production SQLite.
- Zod for runtime validation at server boundaries.
- Vitest for unit tests.
- Playwright for critical user flows.

## Commands

Use the package manager already present in the repository. Do not introduce a second lockfile.

```bash
npm install
npm run dev
npm run lint
npm run typecheck
npm test
npm run test:e2e
npm run db:migrate
npm run db:studio
```

If a command does not exist, add it to `package.json` before referencing it in docs or CI.

## Project Structure

Use this structure unless the repository already has a clear convention:

```text
app/
  (marketing)/
  (auth)/
  dashboard/
  api/
components/
  ui/
  forms/
  layout/
db/
  client.ts
  schema.ts
  migrations/
  queries/
lib/
  auth/
  billing/
  config/
  validation/
server/
  actions/
  services/
tests/
  unit/
  e2e/
```

Responsibilities:

- `app/` owns routes, layouts, loading states, and page composition.
- `components/ui/` contains reusable presentational primitives.
- `components/forms/` contains form components and client interaction shells.
- `db/` owns schema, migrations, connection setup, and query helpers.
- `server/actions/` owns server actions called by forms or client components.
- `server/services/` owns business workflows that can be tested without rendering React.
- `lib/config/` validates environment variables once and exports typed config.

## Naming Conventions

- React components: `PascalCase.tsx`.
- Hooks: `useSomething.ts`.
- Server actions: `verbNounAction`, for example `createProjectAction`.
- Database query helpers: `verbNoun`, for example `getProjectById`.
- Migrations: `YYYYMMDDHHMM_descriptive_name.sql`.
- Route groups use lowercase names: `(marketing)`, `(auth)`.
- URL segments use kebab case.
- Database tables use snake case plural nouns: `users`, `organizations`, `project_members`.
- Database columns use snake case: `created_at`, `updated_at`, `organization_id`.

## Server And Client Components

Default to Server Components.

Use Client Components only for:

- Local UI state.
- Browser APIs.
- Event handlers.
- Interactive forms that cannot be handled by native form posts.

Do not fetch database data from Client Components. Fetch in Server Components, server actions, route handlers, or service functions.

Keep Client Components small. Pass serialized data into them from the server instead of passing database clients, auth objects, or raw request objects.

## Data Access

All database access must go through `db/queries/` or `server/services/`.

Rules:

- Use parameterized SQL only.
- Never build SQL by concatenating user input.
- Keep transactions explicit for multi-step writes.
- Return plain objects from query helpers.
- Convert database timestamps at the boundary and keep one timestamp format across the app.
- Validate all external input with Zod before it reaches a query.

Example transaction shape:

```ts
const createProject = db.transaction((input: CreateProjectInput) => {
  const project = insertProject(input);
  insertAuditEvent({
    type: "project.created",
    projectId: project.id,
    actorId: input.actorId,
  });
  return project;
});
```

## SQLite And Migrations

SQLite is strict enough for production if constraints are treated seriously.

Migration rules:

- Every schema change gets a migration file.
- Never edit a migration that may already have run outside your machine.
- Prefer additive migrations.
- Include `not null`, `check`, `unique`, and foreign key constraints where the domain requires them.
- Enable foreign keys on every SQLite connection with `PRAGMA foreign_keys = ON`.
- Use ISO-8601 text or integer epoch timestamps consistently. Do not mix formats.
- Add indexes for foreign keys and common dashboard filters.
- Avoid long write transactions in request paths.

Production Turso/libSQL notes:

- Keep database access behind an adapter so local `better-sqlite3` and remote libSQL do not leak into application code.
- Avoid SQLite-specific behavior that is unavailable in the production driver.
- Treat network database calls as fallible and surface user-safe errors.

## Server Actions

Server actions must:

- Re-check authentication and authorization.
- Validate input with Zod.
- Call a service function for business logic.
- Return a typed success/error result.
- Revalidate only the affected paths or tags.
- Avoid leaking raw exception messages to users.

Preferred result shape:

```ts
type ActionResult<T> =
  | { ok: true; data: T }
  | { ok: false; fieldErrors?: Record<string, string>; message: string };
```

## Route Handlers

Use route handlers for webhooks, external API integrations, downloads, and endpoints that are not naturally modeled as form actions.

Rules:

- Verify webhook signatures before parsing trusted fields.
- Make webhook handlers idempotent.
- Return correct status codes.
- Keep secrets on the server only.
- Rate-limit public mutation endpoints.

## Authentication And Authorization

Authentication answers "who is this user"; authorization answers "can this user do this here".

Rules:

- Check authorization in service functions, not only in pages.
- Scope every tenant-owned query by `organization_id` or equivalent.
- Never trust organization IDs from the client without membership checks.
- Add tests for cross-tenant access denial.
- Keep admin-only behavior behind explicit role checks.

## Environment Variables

Create a single typed config module. Do not read `process.env` throughout the app.

Required behavior:

- Validate required env vars during startup.
- Separate server-only env vars from public `NEXT_PUBLIC_` values.
- Never expose API keys, database tokens, signing secrets, or webhook secrets to Client Components.

## Forms And Validation

- Validate on the server even if the client also validates.
- Keep validation schemas near the feature or in `lib/validation/`.
- Preserve user input after validation errors.
- Display field-level errors for expected validation failures.
- Use optimistic UI only when rollback behavior is clear.

## Errors And Logging

- Use expected error types for validation, auth, not found, and conflict cases.
- Log unexpected errors on the server with enough context to debug.
- Do not log secrets, session tokens, full payment payloads, or private user content.
- User-facing messages should be specific enough to act on but not expose internals.

## Testing

Required coverage for meaningful changes:

- Unit tests for service functions and query helpers.
- Migration tests for non-trivial schema changes.
- E2E tests for login, onboarding, billing gates, and core dashboard workflows.
- Regression tests for every fixed bug.

SQLite test rules:

- Use isolated test databases.
- Reset state between tests.
- Test constraints, not just happy paths.
- Include at least one authorization failure test for tenant-owned data.

## Performance

- Avoid N+1 queries in dashboards.
- Add indexes before adding filters to large tables.
- Prefer server pagination for tables and activity feeds.
- Use `revalidatePath` or `revalidateTag` narrowly.
- Do not move server data fetching into Client Components to fix loading states.

## Accessibility And UX

- Use semantic HTML first.
- Form controls need labels.
- Buttons perform actions; links navigate.
- Dialogs must be keyboard accessible.
- Loading, empty, and error states are part of the feature, not polish.

## Patterns To Follow

- Put business rules in services so they can be tested without rendering pages.
- Keep route files thin.
- Use explicit transactions for workflows that create multiple records.
- Make authorization checks close to the data mutation.
- Prefer boring, readable code over generic frameworks inside the app.
- Keep generated types, schemas, and migrations synchronized in the same PR.

## Anti-Patterns To Avoid

- Do not use SQLite from Edge runtime.
- Do not pass raw request data directly into SQL.
- Do not rely on client-side checks for authorization.
- Do not create a new database connection per query in hot paths.
- Do not catch errors only to return `{ ok: true }`.
- Do not introduce global mutable state for request-specific data.
- Do not make every component a Client Component.
- Do not edit old migrations after they may have run.
- Do not mix ORMs, query builders, and raw SQL without a clear reason.

## Pre-PR Checklist

Before opening a PR, verify:

- `npm run lint` passes.
- `npm run typecheck` passes.
- `npm test` passes.
- Migrations apply on a fresh database.
- New server actions check auth, validate input, and return typed errors.
- Tenant-owned queries are scoped by tenant.
- No secret is exposed through `NEXT_PUBLIC_`, logs, client bundles, or error messages.
- User-facing flows include loading, empty, and error states.
- The PR description lists schema changes, migration steps, and test coverage.

