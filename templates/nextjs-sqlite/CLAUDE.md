# CLAUDE.md

This project is a production SaaS application built with Next.js 15 App Router,
TypeScript, React Server Components, and SQLite through either `better-sqlite3`
for single-node deployments or Turso/libSQL for hosted edge-friendly storage.

Use this file as the default operating context. Make the smallest correct
change, keep data contracts explicit, and verify database behavior with real
migrations or tests before claiming a feature works.

## Stack And Versions

- Next.js 15 App Router with TypeScript.
  Reason: App Router gives server-first data loading, route handlers, layouts,
  metadata, and nested loading/error boundaries without a separate API server.
- React Server Components by default; client components only when browser state,
  effects, refs, or event handlers are required.
  Reason: keeping components server-side reduces bundle size and avoids leaking
  database or secret access into the browser.
- SQLite as the source of truth through `better-sqlite3` locally or Turso/libSQL
  in hosted environments.
  Reason: SaaS CRUD flows need transactional consistency more than distributed
  complexity at this stage.
- Zod at request and form boundaries.
  Reason: TypeScript does not validate user input at runtime.
- Tailwind CSS plus small local components.
  Reason: most SaaS UI should be dense, predictable, and easy to scan.

## Dev Commands

Use these commands unless the package manager or scripts prove otherwise:

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm db:migrate
pnpm db:seed
```

If a script is missing, inspect `package.json` and use the nearest existing
command. Do not invent a script name without adding it to `package.json`.
Reason: commands are part of the developer contract and must be reproducible.

## Folder Structure

Use this layout for new code:

```text
app/
  (marketing)/
  (app)/
  api/
  layout.tsx
  page.tsx
components/
  ui/
  forms/
  data/
db/
  client.ts
  migrations/
  schema.ts
  queries/
lib/
  auth/
  env.ts
  validation/
server/
  actions/
  services/
tests/
  unit/
  integration/
```

- `app/` owns routes, layouts, loading states, and route handlers.
  Reason: colocating route behavior with URLs keeps navigation and data loading
  easy to trace.
- `components/ui/` contains generic visual primitives only.
  Reason: domain data dependencies in UI primitives create reuse traps.
- `components/data/` contains domain-aware display components.
  Reason: tables, lists, and detail panels often need formatting and empty
  states tied to product concepts.
- `db/migrations/` contains ordered SQL migrations.
  Reason: SQLite schema changes must be replayable on a blank database.
- `db/queries/` contains named query functions.
  Reason: central query functions make authorization, pagination, and test setup
  reviewable.
- `server/actions/` contains server actions that mutate data.
  Reason: mutations need validation, authorization, transactions, and redirects
  in one obvious place.

## Naming Conventions

- Route folders use kebab case: `app/(app)/billing-settings/page.tsx`.
  Reason: URL-oriented names should read like URLs.
- React components use PascalCase and one component per file when exported.
  Reason: stack traces, imports, and test names stay predictable.
- Query functions use verb-first names: `listInvoices`, `getUserById`,
  `createWorkspace`.
  Reason: call sites should reveal whether a function reads or mutates.
- Database tables use snake case plural nouns: `workspaces`, `user_sessions`.
  Reason: SQL remains readable and avoids JavaScript casing leakage.
- Primary keys are `id`; foreign keys are `<table_singular>_id`.
  Reason: joins and indexes stay obvious without custom naming.

## Environment Rules

- Define environment variables in `lib/env.ts` and validate them with Zod.
  Reason: missing secrets should fail at boot, not during a user request.
- Use `DATABASE_URL` for Turso/libSQL and `SQLITE_PATH` for local
  `better-sqlite3`; support one active adapter at a time.
  Reason: explicit adapter selection prevents accidental production writes.
- Never read `process.env` directly in components or query files.
  Reason: direct reads hide dependencies and complicate tests.

## SQL And Migration Conventions

- Every schema change gets a new migration file named
  `YYYYMMDDHHMMSS_short_description.sql`.
  Reason: lexical order should be execution order.
- Migrations are forward-only.
  Reason: production SQLite rollback is usually restore-from-backup plus forward
  fix, not ad hoc down migrations.
- Add indexes in the same migration that introduces the query pattern.
  Reason: performance regressions are easier to catch when schema and access
  path are reviewed together.
- Use transactions for multi-row writes.
  Reason: SaaS billing, membership, and permission changes cannot be half-applied.
- Store timestamps as ISO 8601 UTC text or integer epoch milliseconds; choose one
  per project and keep it consistent.
  Reason: mixed timestamp formats create subtle ordering and timezone bugs.
- Use `ON DELETE` rules deliberately and document destructive cascades in the
  migration comment.
  Reason: account deletion and workspace deletion have different product risk.
- Never concatenate SQL with user input.
  Reason: SQLite is still vulnerable to injection; use parameters for values.

## Data Access Pattern

Use this shape for query functions:

```ts
export async function getWorkspaceBySlug(slug: string) {
  const parsed = workspaceSlugSchema.parse(slug);
  return db.prepare("select * from workspaces where slug = ?").get(parsed);
}
```

- Validate external inputs before queries.
  Reason: query functions are often reused by route handlers and server actions.
- Return plain objects, not class instances.
  Reason: Server Components and serialization work best with simple data.
- Keep authorization close to the query or service that exposes data.
  Reason: route-only authorization is easy to bypass through reuse.

## Component Patterns

- Prefer server components for pages, tables, dashboards, and detail views.
  Reason: these views mostly render data and should not ship unnecessary JS.
- Use client components for forms with optimistic state, comboboxes, menus,
  drag/drop, charts, and anything requiring browser APIs.
  Reason: interactivity belongs at the smallest possible boundary.
- Put loading and error UI in `loading.tsx` and `error.tsx` near the route.
  Reason: route-specific states are clearer than global spinners.
- Use real empty, loading, error, and permission-denied states.
  Reason: SaaS workflows repeatedly hit partial-data states.
- Tables should support pagination or explicit bounded limits.
  Reason: unbounded SQLite reads will eventually hurt production latency.

## Server Actions And Route Handlers

- Server actions handle product mutations from app UI.
  Reason: they integrate cleanly with forms, redirects, and cache invalidation.
- Route handlers handle webhooks, public APIs, and third-party callbacks.
  Reason: these entry points need HTTP-specific validation and status codes.
- Always validate payloads with Zod before mutation.
  Reason: form data, JSON, and webhook bodies are untrusted.
- Use idempotency keys for billing, webhooks, and email sends.
  Reason: retries are normal and should not double-charge or double-send.
- Revalidate or redirect after mutation.
  Reason: stale UI after writes creates support issues and duplicate actions.

## Testing Rules

- Unit test pure validation, formatting, and authorization helpers.
  Reason: these fail fastest and prevent broad regressions.
- Integration test migrations and query functions against a temporary SQLite DB.
  Reason: SQL bugs need a real database.
- Add at least one route or server-action test for each critical mutation.
  Reason: most SaaS incidents happen at write boundaries.
- Do not mock the database for migration or query behavior.
  Reason: mocks hide SQL syntax, constraints, indexes, and transaction bugs.

## Security Defaults

- Treat workspace membership and role checks as mandatory on every workspace
  resource.
  Reason: multi-tenant data leaks are the highest SaaS risk.
- Use parameterized SQL for every user-controlled value.
  Reason: escaping by hand is brittle and unnecessary.
- Keep secrets on the server only.
  Reason: client bundles are public.
- Audit destructive actions with actor, target, timestamp, and request id.
  Reason: support and incident response need a factual trail.
- Rate-limit auth, invite, billing, and export endpoints.
  Reason: these endpoints are common abuse targets.

## What We Do Not Do

- Do not create a custom ORM layer unless repeated query code proves the need.
  Reason: premature abstraction hides SQL and slows debugging.
- Do not put business logic in React components.
  Reason: product rules need tests and reuse outside rendering.
- Do not use global mutable singletons for request-specific state.
  Reason: server runtimes can reuse modules across requests.
- Do not add client state libraries for server-owned data.
  Reason: App Router already gives server data loading and cache primitives.
- Do not create migrations that depend on local seed data.
  Reason: production databases will not match local assumptions.
- Do not ask for clarification when the existing conventions answer the
  question; inspect files and proceed with the smallest consistent change.
  Reason: this template is meant to make a greenfield SaaS project immediately
  actionable for Claude Code.
