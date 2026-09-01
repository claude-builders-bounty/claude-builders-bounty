# CLAUDE.md

## Project Purpose

This repository is a production-oriented SaaS built with **Next.js 15 App Router**, **TypeScript**, and **SQLite**.

Claude should optimize for correctness before cleverness, small reviewable changes, server-first architecture, explicit migrations, secure input handling, deterministic tests, and code that a new contributor can understand without extra clarification.

Do not introduce new frameworks, ORMs, state libraries, background services, or infrastructure unless the task explicitly requires them.

## Stack and Versions

Use these defaults unless the repository already pins a compatible alternative:

- Next.js 15, App Router only
- React 19
- TypeScript with `strict: true`
- Node.js 20.9+
- SQLite
- `better-sqlite3` for direct SQLite access
- Zod for validation
- Vitest for unit/integration tests
- Playwright for end-to-end tests
- ESLint for linting
- npm scripts as the canonical development interface

Before changing dependencies, inspect `package.json` and preserve existing choices when compatible.

## Canonical Project Structure

```text
.
├── app/
│   ├── (auth)/
│   ├── (dashboard)/
│   ├── api/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── error.tsx
│   ├── loading.tsx
│   └── not-found.tsx
├── components/
│   ├── ui/
│   └── feature-name/
├── db/
│   ├── migrations/
│   ├── schema.sql
│   ├── seed.ts
│   └── index.ts
├── lib/
│   ├── auth/
│   ├── validation/
│   ├── services/
│   └── utils/
├── public/
├── tests/
│   ├── integration/
│   └── e2e/
├── types/
├── package.json
└── tsconfig.json
```

Rules:
- `app/` owns routing, route-level boundaries, layouts, pages, Route Handlers, and route-local Server Actions.
- `components/` contains reusable presentation components.
- `lib/` contains application logic, validation, authorization helpers, services, and pure utilities.
- `db/` owns the SQLite connection, migrations, schema, seeds, and database-specific helpers.
- `types/` is only for shared types that do not naturally belong beside their implementation.
- Prefer colocating feature-specific code near the feature.
- Do not add a `pages/` router unless the task explicitly requires legacy compatibility.

## Naming Conventions

Use:
- files/folders: `kebab-case`
- React components and exported classes/types: `PascalCase`
- functions, variables, hooks: `camelCase`
- true constants: `UPPER_SNAKE_CASE`
- SQLite tables/columns: `snake_case`
- migration files: `NNNN_short_description.sql`

Use plural table names (`users`, `organizations`, `subscriptions`), `id` for primary keys, and explicit foreign keys such as `user_id`.

Avoid ambiguous names such as `data`, `item`, `thing`, or `handler` when a domain name is available.

## Server Components and Client Components

Server Components are the default.

Use a Client Component only when browser-side interactivity is required: event handlers, React state/effects, browser APIs, or client-only libraries.

Rules:
- Do not add `"use client"` merely because one child is interactive.
- Push the client boundary as far down the tree as practical.
- Fetch server-owned data in Server Components when possible.
- Never expose database handles, secrets, or privileged server logic to Client Components.
- Pass minimal serializable props across the server/client boundary.
- Do not fetch initial page data with `useEffect` when it can be fetched directly in a Server Component.

## Data Access

All SQLite access is server-only.

Use one canonical database module, for example `db/index.ts`.

```ts
import Database from "better-sqlite3";

const globalForDb = globalThis as unknown as {
  db?: Database.Database;
};

export const db =
  globalForDb.db ??
  new Database(process.env.DATABASE_PATH ?? "./data/app.db");

if (process.env.NODE_ENV !== "production") {
  globalForDb.db = db;
}

db.pragma("foreign_keys = ON");
```

Rules:
- Never import the database module from a Client Component.
- Never construct SQL by concatenating untrusted values.
- Use parameterized statements.
- Keep queries explicit and readable.
- Prefer focused repository/service functions over duplicated SQL.
- Select only needed columns.
- Use a consistent timestamp representation, preferably UTC ISO-8601 text unless the project already standardizes another.
- Define foreign keys explicitly.
- Add indexes for demonstrated lookup/join patterns, not speculatively.

## SQLite Migrations

Every schema change requires a committed migration.

Do not modify an already-applied migration to represent a new change.

Migration rules:
1. Create a new monotonically numbered file in `db/migrations/`.
2. Keep each migration focused on one coherent schema change.
3. Make destructive changes explicit and reviewable.
4. Use a transaction when SQLite supports the operations involved.
5. Backfill explicitly when adding a new invariant to existing rows.
6. Add indexes and constraints as part of the migration that requires them.
7. Never use application startup as an implicit substitute for versioned migrations.

Example:

```sql
BEGIN;

ALTER TABLE users ADD COLUMN display_name TEXT;

CREATE INDEX IF NOT EXISTS idx_users_email
  ON users(email);

COMMIT;
```

For SQLite operations requiring table reconstruction:
- create the replacement table,
- copy/transform data explicitly,
- drop the old table,
- rename the replacement,
- recreate indexes/triggers,
- verify foreign keys.

Never silently drop production data.

## Transactions

Use a transaction whenever multiple writes must succeed or fail together, such as:
- creating an organization and owner membership,
- creating an order and line items,
- consuming a one-time token and updating its record,
- changing subscription state while writing an audit event.

Do not split one logical invariant across unrelated writes without a transaction.

## Validation

Treat all external input as untrusted: form data, route/search params, JSON bodies, headers, cookies, webhook payloads, and environment variables.

Use Zod at trust boundaries.

```ts
const CreateProjectInput = z.object({
  name: z.string().trim().min(1).max(120),
});

const parsed = CreateProjectInput.safeParse(input);

if (!parsed.success) {
  return {
    ok: false,
    error: "INVALID_INPUT",
    issues: parsed.error.flatten(),
  };
}
```

Rules:
- validate before authorization-sensitive mutation,
- normalize once at the boundary,
- never rely on TypeScript types as runtime validation,
- return stable application error codes where useful,
- do not leak stack traces or sensitive internals.

## Authentication and Authorization

Authentication answers **who is the user**.
Authorization answers **may this user perform this action**.

Never treat authentication alone as authorization.

For every protected mutation:
1. identify the current user,
2. validate input,
3. load the target resource,
4. verify tenant/organization ownership or role,
5. perform the mutation,
6. write an audit record when security- or billing-sensitive.

Never trust tenant IDs, organization IDs, roles, or user IDs merely because they came from the client.

Server Actions and Route Handlers are public attack surfaces. Apply authorization inside the action/handler itself.

## Server Actions

Use Server Actions for mutations closely coupled to App Router UI.

Place reusable actions in focused server-only files and mark them:

```ts
"use server";
```

Rules:
- validate every action input,
- authorize every protected action,
- move reusable business logic into a service,
- revalidate affected paths/tags after successful writes when required,
- perform redirects after mutation/error handling so redirect control flow is not swallowed by broad `try/catch`,
- return typed predictable results for expected validation/business errors.

Do not create an API endpoint only to call it from a Server Component when direct server-side invocation is sufficient.

## Route Handlers

Use `app/**/route.ts` when an HTTP boundary is actually needed: public/external APIs, webhooks, integrations, machine-to-machine calls, or endpoints consumed outside the Next.js app.

Rules:
- use the correct HTTP method,
- validate payloads,
- authenticate/authorize as required,
- verify webhook signatures before processing,
- return intentional status codes,
- avoid leaking internal exceptions,
- make retryable external operations idempotent when possible.

Do not create redundant Route Handlers for purely internal server-side data access.

## Caching and Revalidation

Do not assume legacy Next.js caching behavior.

For each data flow, decide explicitly whether data should be request-time dynamic, cached, or revalidated after mutation.

After a successful mutation, revalidate only affected paths/tags when needed.

Do not add caching merely for theoretical performance gains. Correctness and freshness come first.

## Error Handling

Use:
- expected typed results for normal validation/business failures,
- `notFound()` for legitimately missing route resources,
- route-level `error.tsx` for unexpected rendering failures,
- server logs for diagnostic detail,
- user-safe messages at the UI boundary.

Never expose SQL with sensitive values, environment variables, secrets, stack traces, or raw database errors to end users.

## Component Patterns

Prefer small components with clear responsibilities, but do not fragment trivial markup unnecessarily.

Reusable UI components should:
- have explicit typed props,
- avoid hidden global dependencies,
- be accessible by default,
- accept composition through `children` where useful,
- remain server-compatible unless client behavior is required.

Feature components belong under `components/<feature>/`.
Generic primitives belong under `components/ui/`.

Do not create barrel `index.ts` files automatically; add them only for a stable public module boundary.

## State Management

Default order:
1. Server Component data
2. URL/search params for shareable navigation state
3. local component state
4. React context for genuinely shared UI state
5. external state library only when the existing app already requires one

Do not add Zustand, Redux, or another state library for state that is naturally server-owned or local.

## Security Rules

Never:
- commit secrets,
- expose server environment variables to the browser,
- interpolate untrusted values into SQL,
- trust authorization claims from client input,
- disable security protections for convenience,
- log passwords, tokens, session cookies, or payment credentials,
- use `dangerouslySetInnerHTML` with untrusted content.

Use `NEXT_PUBLIC_` only for values intentionally safe to expose to browsers.

For uploaded files validate size/type, generate server-side storage names, and never trust the original filename as a filesystem path.

## Environment Variables

Validate required server environment variables at startup or first server use.

Maintain `.env.example` with placeholder values only.

Never commit secrets or `.env` files.

If a variable is secret, it must not use the `NEXT_PUBLIC_` prefix.

## Development Commands

Prefer these canonical scripts:

```bash
npm install
npm run dev
npm run lint
npm run typecheck
npm test
npm run test:e2e
npm run build
npm run db:migrate
npm run db:seed
```

Before claiming a change is complete, inspect `package.json` and run commands that actually exist.

Typical verification:

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

Run focused tests first while iterating, then the broader relevant suite.

Never claim a command passed unless it actually executed successfully.

## Testing Rules

Test externally observable contracts.

Unit tests:
- pure validation,
- calculations,
- domain helpers.

Integration tests:
- SQLite queries,
- transaction behavior,
- authorization,
- Server Actions/services,
- Route Handlers where practical.

E2E tests:
- critical user flows,
- authentication boundaries,
- billing or other high-impact workflows.

Tests must be deterministic and independent of execution order.
Use isolated test databases or transactions where practical.
A reproducible bug fix should include a regression test.

## Database Test Discipline

Never point automated tests at a production SQLite file.

Use a temporary or dedicated test database.

When testing migrations:
- start from the previous schema state,
- apply the migration,
- verify schema/data transformations,
- verify key constraints/indexes.

## Patterns We Prefer

Prefer explicit validation:

```ts
const input = Schema.parse(rawInput);
const project = projectService.create(input);
```

Prefer ownership-aware loading:

```ts
const project = await getProjectForUser(projectId, user.id);
```

Prefer atomic related writes:

```ts
db.transaction(() => {
  // all related writes
})();
```

Prefer Server Components for initial data access over client-side fetch-on-mount.
Prefer explicit SQL and schema migrations over implicit runtime schema mutation.
Prefer a small focused dependency set over packages for trivial utilities.

## Anti-Patterns

### Do not fetch initial server-owned data in `useEffect`
Why: extra client round trip, more JavaScript, duplicated loading state, and weaker App Router architecture.

### Do not mark large trees `"use client"`
Why: larger client bundles and weaker server/client separation.

### Do not concatenate SQL
Why: SQL injection risk and broken escaping. Use bound parameters.

### Do not edit old migrations to create new schema state
Why: existing databases may already have applied them.

### Do not use `SELECT *` by default
Why: hidden data dependencies and accidental data exposure.

### Do not put authorization only in the UI
Why: UI controls are not a security boundary.

### Do not duplicate business rules in Server Actions and Route Handlers
Why: behavior drifts. Put reusable rules in a server-side service.

### Do not add abstractions before repetition or a real boundary exists
Why: premature abstractions make generated code harder to review and evolve.

## Change Workflow for Claude

For every task:

1. Read relevant existing files before editing.
2. Identify the smallest coherent change.
3. Preserve existing architecture unless the task requires migration.
4. If schema changes, create a new migration.
5. Validate all new external input.
6. Verify authorization for protected operations.
7. Add/update tests for changed behavior.
8. Run focused verification.
9. Run broader relevant checks.
10. Inspect the final diff for unrelated changes.
11. Summarize what changed, tests run, and unresolved risk.

Do not:
- rewrite unrelated files,
- rename public APIs casually,
- change package managers,
- introduce a new ORM or UI framework without explicit requirement,
- weaken tests to make them pass,
- claim success when verification failed.

## Definition of Done

A task is complete only when:
- requested behavior is implemented,
- acceptance criteria are met,
- schema changes have versioned migrations,
- security/authorization implications are handled,
- relevant tests pass,
- lint/typecheck/build pass when applicable,
- no unrelated changes are included,
- and the final response states exactly what changed and how it was verified.

If a required product decision cannot be inferred safely from the repository, state the ambiguity explicitly instead of inventing behavior.
