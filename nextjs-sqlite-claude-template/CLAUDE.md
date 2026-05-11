# Project Instructions

This project is a production SaaS app built with Next.js 15 App Router, TypeScript, SQLite, and server-first React.

## Stack And Versions

- Next.js 15 App Router with React Server Components by default.
- TypeScript in `strict` mode.
- SQLite through `better-sqlite3` for local/single-node deployments or Turso/libSQL when remote replication is required.
- SQL migrations are plain `.sql` files committed to the repo.
- Server actions are allowed for form mutations, but data access stays in dedicated server modules.

Reason: this stack is small, inspectable, and reliable for SaaS features without adding a separate API server or ORM layer too early.

## Dev Commands

- `pnpm dev`: run the app locally.
- `pnpm build`: compile and type-check production output.
- `pnpm lint`: run lint checks.
- `pnpm test`: run unit and integration tests.
- `pnpm db:migrate`: apply pending SQL migrations.
- `pnpm db:studio`: open the database browser if the project provides one.

If the package manager is not `pnpm`, inspect `package.json` and use the existing scripts rather than inventing new commands.

## Folder Structure

```text
app/
  (marketing)/
  (app)/
  api/
components/
  ui/
  forms/
  layout/
db/
  migrations/
  schema.sql
  seed.ts
lib/
  auth/
  db/
  domain/
  env.ts
  validation/
tests/
  unit/
  integration/
```

- Route-specific UI stays under the matching `app/` segment.
- Reusable presentational pieces go in `components/`.
- Database connection, prepared statements, and transaction helpers live in `lib/db/`.
- Business rules live in `lib/domain/`, not in route handlers or components.
- Environment parsing lives in `lib/env.ts` and must validate required variables at startup.

Reason: this keeps route code thin and prevents server/database logic from leaking into client components.

## Naming Conventions

- Components use `PascalCase.tsx`.
- Hooks use `useThing.ts`.
- Server-only modules use clear names like `queries.ts`, `mutations.ts`, `repository.ts`, or `service.ts`.
- SQL migration files use `YYYYMMDDHHMM_description.sql`.
- Database tables use `snake_case`; TypeScript values use `camelCase`.
- IDs are named by domain: `userId`, `organizationId`, `subscriptionId`.

Reason: consistent names make it obvious whether code is UI, server logic, or persistent data.

## SQL And Migration Rules

- Never change an existing migration after it has been committed. Add a new migration.
- Every migration must be safe to run once in order on a fresh database.
- Prefer explicit constraints: `NOT NULL`, `UNIQUE`, `CHECK`, and foreign keys.
- Always create indexes for foreign keys and common lookup fields.
- Use transactions for multi-step writes.
- Store timestamps as ISO-8601 text or integer milliseconds consistently across the app; do not mix formats.
- Do not build SQL with string interpolation. Use prepared statements and bound parameters.

Reason: SQLite is robust when schema changes are explicit and application code treats writes as transactional.

## Data Access Patterns

- Server components may call read-only query functions directly.
- Mutations go through server actions or route handlers that call `lib/domain/*` services.
- Each write path validates input with a schema before touching the database.
- Return domain-shaped objects from query modules. Do not expose raw row names like `created_at` to UI components.
- Keep authorization checks near the data access boundary, not only in the page.

Reason: SaaS bugs usually come from missing authorization or inconsistent validation, not from rendering code.

## Component Patterns

- Use server components by default.
- Add `"use client"` only for state, effects, browser APIs, or event handlers.
- Keep client components small and pass serializable props.
- Forms should have pending, success, empty, and error states.
- Shared UI components should accept clear props and avoid fetching data.
- Use accessible native controls before custom widgets.

Reason: server-first components reduce shipped JavaScript and keep data loading straightforward.

## Auth And Multi-Tenancy

- Treat every query as tenant-scoped once organizations/workspaces exist.
- Never trust `organizationId`, `userId`, or role values from client input.
- Resolve the current user/session on the server.
- Check membership and permissions before reads and writes.
- Add tests for cross-tenant access whenever touching authorization.

Reason: tenant isolation failures are high-impact SaaS bugs.

## Testing Rules

- Unit test pure domain logic.
- Integration test database queries and migrations against a temporary SQLite database.
- Add regression tests for every bug fix that touches auth, billing, or data mutation.
- Avoid snapshot tests for complex pages unless the output is intentionally stable.
- Tests should create their own data and clean up after themselves.

Reason: focused tests catch the failures this stack is most likely to produce.

## Patterns To Follow

- Validate environment variables once in `lib/env.ts`.
- Put Zod or equivalent schemas next to the feature that owns the input.
- Use prepared SQL statements for hot paths.
- Keep route handlers as adapters: parse input, call domain logic, return response.
- Prefer boring HTML forms with server actions for CRUD workflows.
- Use optimistic UI only after the server mutation path is correct.

## Anti-Patterns To Avoid

- Do not add Prisma, Drizzle, tRPC, Redux, or a separate backend unless the task explicitly requires it.
- Do not put secrets in client components or `NEXT_PUBLIC_*` variables.
- Do not fetch from this app's own API routes inside server components; call the server module directly.
- Do not create generic `utils.ts` dumping grounds.
- Do not silently catch database errors. Surface a useful error path and log server details.
- Do not use `any` to bypass domain typing.
- Do not implement auth checks only in middleware.

Reason: unnecessary abstractions make a small SaaS harder to debug and easier to mis-secure.

## Before Finishing A Change

- Run the narrowest relevant tests first, then `pnpm build` for user-facing changes.
- Confirm migrations apply to a fresh database.
- Check that changed forms handle loading and error states.
- Verify server-only code is not imported by client components.
- Note any command that could not be run and why.
