# Next.js 15 + SQLite SaaS rules

This is a greenfield SaaS application. Keep the default architecture boring and
explicit: Next.js 15 App Router, React 19, TypeScript in strict mode, Node.js
20 LTS or newer, and SQLite through `better-sqlite3`. If the deployment uses
Turso, keep the same repository boundaries and swap only the database adapter.

## Operating principles

- Prefer a Server Component. Add `"use client"` only for browser APIs or local
  interactive state; never import the database, filesystem, or secrets into a
  Client Component.
- Put business rules in `src/lib/` or `src/server/`, not in route handlers or
  JSX. A route handler should authenticate, validate, call a service, and map
  the result to an HTTP response.
- Treat every value crossing a request boundary as untrusted. Validate JSON,
  query strings, route parameters, cookies, and webhook bodies with a schema
  before using them.
- Keep secrets in environment variables. Read them in server-only modules and
  fail fast when a required variable is missing; do not expose them through
  `NEXT_PUBLIC_*`.

## Folder structure

```text
src/app/                 routes, layouts, loading and error boundaries
src/components/          reusable UI; client components stay here when needed
src/lib/                 pure domain utilities and validation schemas
src/server/              services, authorization, and server-only adapters
src/server/db/           connection, migrations, repositories, and seed data
src/app/api/              thin HTTP adapters only
tests/                   unit and integration tests
scripts/                 repeatable local and CI tasks
```

Use feature-oriented names inside these directories. A component named after
an implementation detail (`ThingClient`, `DataWrapper2`) is a smell; name it
after the user-facing capability.

## Commands and quality gates

The project must provide these scripts and they must work from a clean clone:

```text
npm run dev
npm run build
npm run lint
npm run typecheck
npm test
npm run db:migrate
npm run db:rollback   # only for local development
```

Run `lint`, `typecheck`, tests, and a production build before opening a PR.
Do not hide failures with `|| true`, skipped tests, or an ignored TypeScript
error. Update tests with behavior changes, especially authorization and
migration changes.

## SQLite and migrations

- Keep SQL migrations in `src/server/db/migrations/` with immutable, sortable
  names such as `0001_create_accounts.sql`.
- Never edit an applied migration. Add a new migration for every schema change;
  the migration runner records applied names in a metadata table and runs each
  pending migration inside a transaction.
- Enable foreign keys, WAL mode, and a bounded busy timeout on every connection.
  The development connection may be cached on `globalThis` to survive Next.js
  hot reload, but production must create one deliberately managed connection.
- Use parameterized queries only. Repository functions own SQL and return
  domain objects; callers must not concatenate table names, filters, or values.
- Use UTC timestamps and integer minor units for money. Never use floating point
  arithmetic for balances, and never delete financial history to “fix” data.
- Keep seed data deterministic and opt-in. A production start must never reset
  or reseed a database.

## Components, data, and mutations

- Fetch initial data on the server and pass serializable props to the client.
  Use a client cache only when the interaction truly needs revalidation.
- Mutations belong in Server Actions or route handlers with explicit input
  schemas, authorization checks, and replay/idempotency protection.
- Revalidate the smallest affected path or tag after a successful mutation.
  Never rely on a browser refresh to make stale state correct.
- Use stable IDs as React keys. Do not use array indexes for reorderable or
  user-generated lists.
- Add `loading.tsx`, `error.tsx`, and an intentional empty state for each
  user-facing data boundary.

## API, auth, and errors

- Authenticate before loading tenant or account data, then authorize every
  resource by tenant and role. “The UI hides the button” is not authorization.
- Return a consistent JSON error shape: `{ error: { code, message, details? } }`.
  Messages may be shown to users; stack traces and SQL must remain server logs.
- Rate-limit login, password reset, webhooks, and other expensive endpoints.
  Verify webhook signatures against the raw body before parsing it.
- Use `redirect()` only after a successful authorization decision. Prevent open
  redirects by allowing only known internal paths.
- Log request IDs, actor IDs, and event names, never passwords, cookies, tokens,
  full payment data, or unredacted personal data.

## What we do not do (and why)

- Do not put database calls in Client Components: it leaks boundaries and makes
  secrets and connection behavior hard to reason about.
- Do not use `any`, blanket lint disables, or `@ts-ignore` to ship around a
  design problem: strict types are part of the application contract.
- Do not modify old migrations, run destructive startup code, or use
  `DROP TABLE` outside an explicitly named local reset command: deployments
  must be forward-compatible and recoverable.
- Do not interpolate SQL, shell commands, URLs, or HTML: use parameters,
  allowlists, and framework escaping to prevent injection.
- Do not put authorization in middleware alone: middleware can narrow traffic,
  but the server-side service must enforce the resource decision.
- Do not make a page dynamic just to avoid understanding caching. Choose and
  document the intended cache and revalidation behavior.
- Do not add a dependency for a small pure helper. When a dependency is
  justified, record why and verify its license, maintenance, and bundle cost.

## Definition of done

A change is ready only when the behavior is covered by a focused test, the
database transition is represented by a new migration when applicable, the
loading/empty/error states are intentional, authorization is tested for both
allow and deny paths, and `npm run lint`, `npm run typecheck`, `npm test`, and
`npm run build` pass from a clean checkout.
