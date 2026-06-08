# CLAUDE.md

This file is the operating contract for a greenfield SaaS built with Next.js 15 App Router, TypeScript, Tailwind CSS, and SQLite via Drizzle ORM with either `better-sqlite3` locally or Turso in hosted environments.

## Product Shape

- Build a small-team SaaS, not a marketing demo. Reason: the app should optimize for repeatable authenticated workflows, predictable data changes, and fast debugging.
- Treat the first customer-facing objects as `User`, `Account`, `Membership`, `Workspace`, and one core domain record. Reason: this gives billing, authorization, and product data separate boundaries from day one.
- Prefer boring UI and explicit copy over clever abstractions. Reason: SaaS operators need clarity when they create, edit, invite, cancel, and recover data.

## Default Commands

Use `pnpm` unless the project already chose another package manager.

```bash
pnpm dev            # Start the Next.js dev server
pnpm build          # Run the production build
pnpm lint           # Run ESLint
pnpm typecheck      # Run TypeScript without emitting files
pnpm test           # Run unit tests
pnpm db:generate    # Generate Drizzle migrations from schema changes
pnpm db:migrate     # Apply pending migrations
pnpm db:studio      # Inspect the local database
pnpm db:seed        # Seed local development data
```

- Run `pnpm typecheck`, `pnpm lint`, and the most relevant tests before finishing code changes. Reason: App Router errors often appear at type/build time rather than in the edited file.
- Do not invent new commands until `package.json` confirms them. Reason: stale command names waste review time and hide real failures.

## Project Structure

Use this structure unless the existing project has already committed to a different one:

```text
src/
  app/
    (auth)/
    (dashboard)/
    api/
    layout.tsx
    page.tsx
  components/
    ui/
    forms/
    layout/
  db/
    client.ts
    migrate.ts
    schema.ts
    seed.ts
  features/
    billing/
    workspaces/
    <domain>/
  lib/
    auth.ts
    env.ts
    errors.ts
    ids.ts
    logger.ts
    validators.ts
  server/
    actions/
    queries/
    services/
  tests/
    factories/
    setup.ts
db/
  migrations/
```

- Keep route handlers in `src/app/api` thin. Reason: request parsing belongs at the edge, while business rules belong in `src/server/services`.
- Keep database access in `src/server/queries`, `src/server/services`, or `src/db`. Reason: a single data boundary makes transactions, tests, and authorization auditable.
- Put feature-specific components under `src/features/<feature>`. Reason: repeated dashboard workflows stay close to their forms, tables, validators, and actions.
- Keep generic visual primitives in `src/components/ui`. Reason: shared UI should not import product data or database code.
- Keep environment parsing in `src/lib/env.ts`. Reason: failing fast on boot is safer than discovering missing secrets during a request.

## Naming Conventions

- Use `PascalCase` for React components and files that export one component. Reason: component imports stay visually distinct from utilities.
- Use `camelCase` for functions, variables, and server actions. Reason: it matches TypeScript and avoids mixed naming in call sites.
- Use `kebab-case` for route segments and non-component files. Reason: URLs and filesystem paths stay readable on every platform.
- Name server actions with a verb phrase, such as `createWorkspace` or `inviteMember`. Reason: mutations should read like auditable events.
- Name query functions with `get`, `list`, or `find`. Reason: read paths should be clearly separate from writes.
- Name database tables in plural snake_case, such as `workspaces` and `workspace_memberships`. Reason: SQL reads naturally and Drizzle relation names stay predictable.

## App Router Rules

- Default to Server Components. Reason: less client JavaScript keeps dashboards faster and data loading simpler.
- Add `"use client"` only for interactivity, browser APIs, local state, or client-only libraries. Reason: accidental client components can leak server-only imports and increase bundle size.
- Use route groups such as `(auth)` and `(dashboard)` for layout separation. Reason: auth pages and app pages need different chrome without changing URLs.
- Put loading and error states next to the route that owns them. Reason: App Router boundaries are easiest to reason about when colocated.
- Use `notFound()` for missing records and explicit authorization errors for forbidden records. Reason: missing and forbidden states need different audit and UX behavior.

## SQLite And Drizzle Rules

- Define all tables in `src/db/schema.ts`. Reason: Drizzle migrations, relations, and inferred types need one source of truth.
- Commit generated migration files under `db/migrations`. Reason: production database history must be reproducible.
- Never edit an already-applied migration. Reason: SQLite migrations are history; changing history breaks deployed databases.
- Write a new migration for every schema change. Reason: reviewers can understand the exact database transition.
- Use forward-only migrations. Reason: SQLite rollback support is limited and destructive rollbacks are unsafe for customer data.
- Do not drop columns or tables in the same PR that stops using them. Reason: two-step removal allows deploys, backfills, and recovery.
- Wrap multi-row writes in transactions. Reason: SQLite is reliable when writes are atomic and short.
- Keep transactions small and avoid network calls inside them. Reason: SQLite has a single-writer model, so long writes block the app.
- Store timestamps as integer milliseconds or ISO strings consistently across all tables. Reason: mixed timestamp formats cause subtle sorting and filtering bugs.
- Use application-generated IDs from `src/lib/ids.ts`. Reason: stable IDs make tests, URLs, and imports independent of SQLite rowid behavior.
- Keep raw SQL inside `src/db` or a named query helper. Reason: ad hoc SQL in routes bypasses validation and authorization.
- Use `better-sqlite3` for local file-backed development and Turso/libSQL for hosted deployments. Reason: local development should work offline while production can use managed replication.

## Environment Variables

Minimum expected variables:

```bash
DATABASE_URL="file:./data/app.db"
NEXT_PUBLIC_APP_URL="http://localhost:3000"
AUTH_SECRET="replace-with-32-plus-random-bytes"
```

For Turso:

```bash
TURSO_DATABASE_URL="libsql://..."
TURSO_AUTH_TOKEN="..."
```

- Never read `process.env` outside `src/lib/env.ts`. Reason: typed parsing prevents optional secrets from becoming runtime surprises.
- Prefix only browser-safe values with `NEXT_PUBLIC_`. Reason: public values are bundled into client JavaScript.
- Do not add default production secrets. Reason: silent fallback secrets create insecure deployments.

## Server Actions And API Routes

- Validate every server action input with Zod before touching the database. Reason: UI validation is not a security boundary.
- Return typed result objects from actions: `{ ok: true, data }` or `{ ok: false, error }`. Reason: forms can show predictable messages without string matching exceptions.
- Use API routes for external webhooks and machine clients. Reason: server actions are best for first-party React flows.
- Verify webhook signatures before parsing business payloads. Reason: unauthenticated webhooks are remote write access.
- Keep authorization checks near the query or service method. Reason: callers should not need to remember security rules.

## Forms And UI

- Use server actions for simple dashboard mutations. Reason: the App Router can refresh server data without building a separate client API.
- Use optimistic UI only when rollback is obvious. Reason: admin workflows must not imply data was saved when it was rejected.
- Put form schemas in the feature folder that owns the form. Reason: validation changes should review with the feature, not a global dumping ground.
- Render empty, loading, error, and success states for every table or list. Reason: SaaS screens are often used with zero data, slow data, or partial failure.
- Keep copy specific: "Invite member" beats "Submit". Reason: buttons should describe the side effect they trigger.

## Testing Rules

- Test pure utilities with unit tests. Reason: they are cheap and should not require Next.js runtime setup.
- Test server services with a temporary SQLite database. Reason: migrations, constraints, and transactions are part of the behavior.
- Test one happy path and one failure path for each important server action. Reason: form and validation regressions are common in SaaS dashboards.
- Prefer factories in `src/tests/factories` over inline object literals. Reason: schema changes should update tests in one place.
- Do not mock the database for service tests unless the dependency is external. Reason: SQLite is fast enough and the SQL is what needs confidence.

## Error Handling

- Use typed domain errors from `src/lib/errors.ts`. Reason: UI messages, logs, and HTTP statuses should not depend on raw exception strings.
- Log unexpected errors with request context, not secrets. Reason: production debugging needs correlation without leaking credentials.
- Show users recovery-oriented messages. Reason: "Try again" or "Contact support" is more useful than stack traces.

## Anti-Patterns To Avoid

- Do not put database calls directly in Client Components. Reason: client code cannot protect secrets or database credentials.
- Do not pass whole database rows to Client Components when only a few fields are needed. Reason: over-sharing increases privacy and coupling risk.
- Do not create a generic `utils.ts` for unrelated helpers. Reason: it becomes a dependency magnet and hides ownership.
- Do not use global mutable state for request-specific data. Reason: server rendering can reuse modules across users.
- Do not add an ORM, auth provider, queue, or UI framework without a concrete feature need. Reason: greenfield SaaS projects fail fastest when infrastructure grows before workflows.
- Do not store money as floating-point numbers. Reason: billing and credits need integer cents or decimal strings.
- Do not rely on `Date.now()` scattered through business logic. Reason: injectable time makes tests deterministic.

## Implementation Checklist

Before opening a PR:

- Confirm routes compile with `pnpm build`.
- Confirm `pnpm typecheck` passes.
- Confirm migrations are generated and committed when schema changes.
- Confirm new server actions validate input and check authorization.
- Confirm new UI has loading, empty, error, and success states.
- Confirm secrets are documented in `.env.example`, not hard-coded.

## When Unsure

- Choose the smallest change that preserves the boundaries above. Reason: clear ownership beats premature abstraction.
- Ask for clarification only if product behavior is ambiguous. Reason: technical defaults are already defined here.
- Prefer explicit code over magic. Reason: future contributors should understand SaaS workflows without reverse-engineering framework tricks.
