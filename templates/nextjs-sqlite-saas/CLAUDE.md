# CLAUDE.md - Next.js 15 + SQLite SaaS

## Stack And Versions

- Framework: Next.js 15 App Router with React Server Components by default.
- Language: TypeScript in strict mode. Use `.tsx` for React components and `.ts` for everything else.
- Runtime: Node.js for routes that touch SQLite. Do not move database code to the Edge runtime.
- Database: SQLite through `better-sqlite3` for local and single-node deployments. Use Turso/libSQL only when distributed reads are required.
- Styling: Tailwind CSS with small local components. Avoid broad theme abstractions until there are repeated screens.
- Auth and billing: keep provider-specific code isolated behind `src/lib/auth/*` and `src/lib/billing/*`.

Reason: this stack optimizes for a small SaaS team that needs fast local development, predictable deploys, and easy debugging more than premature scale.

## Project Shape

Use this structure unless an existing project already has a stronger convention:

```text
.
|-- CLAUDE.md
|-- package.json
|-- src
|   |-- app
|   |   |-- (marketing)
|   |   |-- (app)
|   |   |-- api
|   |   `-- layout.tsx
|   |-- components
|   |   |-- ui
|   |   `-- domain
|   |-- db
|   |   |-- client.ts
|   |   |-- migrations
|   |   |-- queries
|   |   `-- schema.ts
|   |-- lib
|   |   |-- auth
|   |   |-- billing
|   |   |-- env.ts
|   |   `-- validation.ts
|   `-- tests
`-- scripts
    `-- migrate.ts
```

Rules:

- Put route UI in `src/app/**/page.tsx` and reusable UI in `src/components`.
- Put database reads and writes in `src/db/queries`. Pages and actions should call query functions, not inline SQL.
- Put schema and migration helpers in `src/db`; never bury SQL inside components.
- Put one-off maintenance scripts in `scripts`, not in route handlers.

Reason: App Router files are already part routing and part UI. Keeping persistence, validation, and provider integrations outside `app` makes changes safer.

## Commands

Use these command names in examples and scripts:

```bash
npm run dev
npm run lint
npm run typecheck
npm test
npm run db:migrate
npm run db:studio
```

If the project does not define one of these commands, add it before depending on it in docs or automation.

Reason: Claude Code should be able to run the same small command vocabulary every time.

## Naming Conventions

- Components: `PascalCase.tsx`, for example `InvoiceStatusBadge.tsx`.
- Hooks: `useThing.ts`, only in client-only code.
- Server actions: `thing.actions.ts`.
- Query modules: `thing.queries.ts`.
- Validation schemas: `thing.schema.ts`.
- Migrations: `YYYYMMDDHHMM_description.sql`.
- Database columns: `snake_case`.
- TypeScript variables and functions: `camelCase`.

Reason: database names should map cleanly to SQL, while TypeScript names should remain idiomatic in app code.

## Data Access Rules

- Server Components may read data directly through `src/db/queries`.
- Client Components must receive data as props or call a route/action. They must not import database modules.
- Server actions may write data, but every action must validate input before calling a query.
- Route handlers are for webhooks, third-party callbacks, and public API surfaces. Do not use them for internal UI mutations when a server action fits.
- All multi-tenant queries must include `workspace_id` or `organization_id` in the `WHERE` clause.

Reason: this prevents accidental client-side database imports and reduces tenant data leakage risk.

## SQLite Conventions

- Prefer explicit SQL or a thin query builder. Do not generate unclear SQL for core billing, auth, or permission checks.
- Use `INTEGER PRIMARY KEY` for local-only IDs. Use `TEXT` UUIDs for records that may sync across systems.
- Store timestamps as ISO 8601 UTC text in `created_at` and `updated_at`.
- Use `CHECK` constraints for known enum-like values.
- Enable foreign keys on every connection with `PRAGMA foreign_keys = ON`.
- Keep transactions close to the write boundary. A query function that writes multiple tables owns the transaction.
- Avoid long-running transactions around network calls.

Reason: SQLite is reliable when constraints are explicit and transactions are short.

## Migration Rules

- Migrations are forward-only SQL files in `src/db/migrations`.
- Never edit an applied migration. Add a new migration instead.
- Each migration must be safe to run once in CI and once in production.
- Wrap schema changes and backfills in an explicit transaction unless SQLite forbids that operation.
- Add indexes in the same migration as the query pattern that needs them.
- Destructive changes require a two-step migration: add replacement first, deploy code, then drop old data in a later migration.
- Seed data belongs in `scripts/seed.ts`, not in migrations.

Reason: small SaaS apps often skip migration discipline until the first production incident. Do the boring thing early.

## Component Patterns

- Default to Server Components.
- Add `"use client"` only for browser state, effects, event handlers, or browser-only APIs.
- Keep Client Components shallow. Pass serialized data in; do not make them responsible for fetching initial page data.
- Use forms plus server actions for authenticated mutations.
- Use optimistic UI only after the server-side mutation path is already correct.
- Keep shared UI components plain and accessible. Domain components can know about invoices, plans, users, or workspaces.
- Use loading and error boundaries at route segment level when data fetches can fail independently.

Reason: App Router works best when server rendering owns data and client code owns interaction.

## Validation And Errors

- Validate all external input with a schema in `src/lib/validation.ts` or `*.schema.ts`.
- Return field-level errors for form submissions.
- Throw typed errors from query and service functions; convert them to user-facing copy at the route/action boundary.
- Log the internal error, but do not show SQL, secrets, tokens, or provider payloads to users.

Reason: validation near the boundary keeps database functions simple and keeps user-facing errors intentional.

## Environment Variables

- Read environment variables through `src/lib/env.ts`.
- Validate required variables at startup.
- Never read `process.env` directly in components or query modules.
- Prefix only browser-safe values with `NEXT_PUBLIC_`.

Reason: central env validation catches broken deploys before a user clicks into a failing workflow.

## Auth, Tenancy, And Permissions

- Resolve the current user and workspace on the server.
- Check authorization before reading or mutating tenant-scoped rows.
- Treat subscription status as authorization-adjacent. A disabled subscription should block paid features but not account management.
- Webhook handlers must be idempotent and verify signatures before parsing business fields.

Reason: SaaS bugs usually hurt most when auth, tenancy, and billing drift apart.

## Testing Expectations

- Add unit tests for pure validation and formatting logic.
- Add integration tests for database queries that encode permissions, billing state, or migration behavior.
- Add one smoke test for the authenticated app shell.
- For migrations, test against a real temporary SQLite database, not only mocks.

Reason: the riskiest code in this stack is usually data access, not component rendering.

## What We Do Not Do

- Do not put SQL in React components. It couples UI changes to persistence.
- Do not import `src/db/*` from Client Components. It breaks bundling and leaks server assumptions.
- Do not use the Edge runtime for SQLite routes. SQLite needs Node-compatible runtime behavior.
- Do not create generic `utils.ts` dumping grounds. Name modules by domain or responsibility.
- Do not add an ORM migration without reviewing the generated SQL. Generated migrations can hide destructive changes.
- Do not store money as floats. Store cents as integers and format at the edge.
- Do not add global state for server data. Fetch it on the server and pass it down.
- Do not ask clarifying questions when the task matches these defaults. Apply the conventions and note assumptions in the final response.

Reason: these rules prevent common small-SaaS failure modes while keeping the project easy to change.

## Claude Code Workflow

When implementing a task:

1. Inspect `package.json`, `src/db/schema.ts`, and the relevant route segment first.
2. Prefer the existing project style if it conflicts with this file.
3. Make the smallest coherent change that preserves the conventions above.
4. Add or update tests when touching validation, migrations, permissions, or billing behavior.
5. Run `npm run typecheck`, `npm run lint`, and the narrowest relevant test command.
6. In the final response, mention changed files, validation run, and any assumptions.

When generating new code for a greenfield project:

1. Use the folder structure in this file.
2. Create database access through `src/db/queries`.
3. Default to Server Components and server actions.
4. Include migration and validation code with the feature, not as a follow-up.
