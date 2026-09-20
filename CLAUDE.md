# Next.js 15 + SQLite SaaS project contract

This is a greenfield SaaS application. Follow these rules without asking for
architecture decisions that this document already answers. If a task conflicts
with a rule, explain the conflict and propose the smallest safe exception.

## Stack and versions

- Next.js 15 App Router with React 19 and TypeScript in strict mode.
- Node.js 22 LTS, npm, and `npm ci` for reproducible installs.
- SQLite through `better-sqlite3` behind a small server-only repository layer.
  Production may use Turso/libSQL through the same repository interface.
- Zod for validating external input; Vitest for unit/integration tests and
  Playwright for browser flows.
- Tailwind CSS for styling; use accessible semantic HTML before adding classes.

Why: these choices keep rendering, persistence, validation, and tests explicit
and make a local SQLite app portable to a hosted SQLite-compatible service.
Do not add a second ORM, validation library, or CSS system without a written
reason and a migration plan.

## Project structure

```text
app/
  (marketing)/       public landing and pricing pages
  (app)/             authenticated product pages and layouts
  api/               thin Route Handlers; no business logic here
  layout.tsx         root metadata and providers
components/
  ui/                reusable presentational primitives
  features/<name>/   feature-specific components
db/
  client.ts           server-only connection factory
  repositories/       persistence queries grouped by aggregate
  migrations/         ordered SQL files, never edited after release
  migrate.ts          idempotent migration runner
lib/
  env.ts              validated environment variables
  errors.ts            public error mapping
  services/           application use-cases
  validators/         Zod schemas shared by callers and handlers
  server/              server-only helpers
tests/
  unit/               pure functions and services with fakes
  integration/        repository and Route Handler tests
e2e/                  Playwright scenarios
scripts/              explicit maintenance commands
```

Why: boundaries make it possible to test a service without a browser or live
database and prevent a UI component from accidentally importing server code.
Keep route files as adapters: parse input, call a service, map the response.

## Naming and module rules

- Use `PascalCase` for React components and `camelCase` for functions and
  variables. Use `kebab-case` for route folders and migration filenames.
- Name a feature's service after its business action (`createInvoice`), not
  its transport (`postInvoice`).
- Use `type` imports and explicit return types on exported functions.
- Keep secrets, database clients, and Node-only modules in files marked with
  `import 'server-only'`.
- Prefer small named functions over clever abstractions; each exported service
  should have a focused test.

Why: names communicate the boundary being crossed and prevent accidental
client bundling of credentials or database drivers.

## Database and migrations

- Every schema change is a new file in `db/migrations/` with a sortable prefix,
  for example `0003_add_invoice_status.sql`.
- A migration is forward-only, transactional where SQLite permits it, and
  safe to run twice through the migration runner's applied-migration table.
- Never edit a migration that has reached a shared environment. Add a repair
  migration instead.
- Every table has an integer primary key or stable text ID, `created_at`, and
  `updated_at` unless a documented reason says otherwise.
- Store timestamps as UTC ISO text at the application boundary and use bound
  parameters for every value. Never concatenate user input into SQL.
- Add an index only for a demonstrated query path; explain its expected lookup
  in the migration comment.
- Repository functions return domain-shaped records and own SQL details. A
  component, Server Action, or Route Handler must never call `db.prepare`.
- Tests use a temporary database and run all migrations before each suite;
  production credentials are never used by tests.

Why: ordered immutable migrations make deploys repeatable, while a repository
boundary prevents SQL and connection lifecycle details leaking through the app.

## Server/client and component patterns

- Default to Server Components. Add `'use client'` only for browser state,
  event handlers, or APIs unavailable on the server.
- Fetch data in the server route/layout that owns the UI. Do not fetch the
  application's own API from a Server Component; call the service directly.
- Use Server Actions only for short mutations with an explicit Zod input schema;
  revalidate the affected path or tag after a successful mutation.
- Use Route Handlers for webhooks, public API consumers, and non-HTML clients.
  Authenticate and validate before doing any write.
- Every loading, empty, error, and unauthorized state gets an intentional UI.
- Forms show field-level errors without echoing secrets or raw stack traces.

Why: this keeps the server boundary observable, reduces needless HTTP hops, and
makes cache invalidation explicit instead of relying on accidental refreshes.

## API, auth, and error handling

- Validate params, query strings, JSON bodies, and webhook payloads with Zod at
  the boundary. Treat all request data as hostile.
- Return stable error codes and appropriate HTTP status values. Log an internal
  request ID and context, never passwords, tokens, cookies, or full payment data.
- Check authorization inside the service as well as in the UI. A hidden button
  is not an authorization boundary.
- Use secure, httpOnly, sameSite cookies for sessions; never put session tokens
  in localStorage or URLs.
- Webhooks verify their signature before parsing business payloads and are
  idempotent on the provider event ID.

Why: clients can bypass UI checks, and retries are normal in distributed
systems. The service must be safe when called directly and more than once.

## Required commands

```bash
npm ci
npm run dev
npm run lint
npm run typecheck
npm test
npm run test:e2e
npm run db:migrate
npm run db:migration -- add_short_description
```

`lint`, `typecheck`, and `test` must pass before a PR is opened. A database
migration must be included in the same change as the code that depends on it.

## What we do not do

- Do not use `any` to silence a type error; model the value or narrow `unknown`.
- Do not use `SELECT *`; enumerate columns so schema changes are visible.
- Do not put business logic in React components, Route Handlers, or migrations.
- Do not use client-side authorization, optimistic writes without rollback, or
  unbounded list queries.
- Do not disable TypeScript, ESLint, CSRF protections, or tests to make a build
  green.
- Do not commit `.env`, tokens, database files, generated secrets, or personal
  data.
- Do not introduce a dependency for a helper that is five clear lines of code.

Why: these shortcuts create hidden coupling, security gaps, or irreproducible
deploys; the short-term speed is not worth the operational cost.

## Definition of done

A change is ready when its acceptance behavior is covered by a test, input
validation and authorization are explicit, migrations run from a clean database,
`npm run lint && npm run typecheck && npm test` passes, and the PR explains any
trade-off or exception to this contract.
