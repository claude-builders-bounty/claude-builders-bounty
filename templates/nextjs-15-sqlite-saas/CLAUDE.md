# CLAUDE.md

## Stack & versions

Use **Next.js 15 App Router**, **React 19**, strict **TypeScript 5**, and **better-sqlite3** on a persistent single-node runtime. Use Node.js 22 LTS and npm 10; commit `package-lock.json`. These versions are fixed because a greenfield guide must give Claude one unambiguous implementation target rather than make it rediscover the stack.

## Project structure

```text
app/                 # routes, layouts, loading/error UI, server actions
components/ui/       # reusable presentational components
components/features/ # feature-specific composition
lib/auth/            # server-only identity and authorization
lib/db/              # connection, schema access, repositories
lib/validation/      # shared boundary schemas
migrations/          # immutable numbered SQL migrations
scripts/             # migration and maintenance entry points
tests/               # unit and integration tests
```

Keep route-specific code beside its route because locality makes ownership clear. Put database access in `lib/db`, not components or route files, because one auditable boundary prevents SQL and tenant rules from drifting.

## Naming conventions

- React components and their files use `PascalCase`; this makes JSX symbols immediately recognizable.
- Functions, variables, server actions, and TypeScript modules use `camelCase`; this follows the language ecosystem and avoids case-only import mistakes.
- Route folders and URL segments use `kebab-case`; URLs remain predictable and portable across filesystems.
- SQL tables and columns use `snake_case`; raw SQL stays readable without quoting mixed-case identifiers.
- Boolean names begin with `is`, `has`, or `can` because the call site should reveal the value's meaning.
- Server actions use verb-first names such as `createProject`; mutations should never look like passive data reads.

## Development commands

```bash
npm ci
npm run dev
npm run lint
npm run typecheck
npm test
npm run build
npm run db:migrate
```

Use only scripts that exist in `package.json`; if this greenfield project lacks one of these required scripts, add it deliberately with its implementation rather than silently substituting an ad-hoc command.

## SQL / migration conventions

Use numbered immutable files such as `migrations/0001_initial.sql`. Add a new forward migration for every schema change and never edit an applied migration, because changing history makes two environments with the same recorded version structurally different. Run migrations in a transaction when SQLite supports every included statement. Record each applied filename and checksum in a migration table because filenames alone cannot detect accidental mutation. Use parameterized queries because string interpolation turns user-controlled values into executable SQL. Keep network calls outside transactions because SQLite serializes writers and long transactions amplify lock contention.

## Component patterns to follow

- Default to Server Components because they keep credentials and database dependencies out of browser bundles.
- Make a component client-side only when it needs browser state, effects, or event handlers; place the client boundary as low as possible to reduce shipped JavaScript.
- Fetch data in the closest server route or feature boundary and pass a narrow typed value to presentation components because broad database objects leak coupling.
- Validate Server Action and Route Handler input with a schema, authenticate, authorize the concrete record, then mutate because every server entry point is independently callable.
- Return controlled result objects for expected validation and conflict errors; reserve thrown exceptions for unexpected failures so UI recovery remains explicit.

## Anti-patterns — what we do not do (and why)

- Do not use the Pages Router because maintaining two routing models creates duplicate conventions and confusing data-fetch boundaries.
- Do not import `lib/db` from a Client Component because the bundler boundary must never expose privileged implementation details.
- Do not put authorization only in middleware because direct actions and record-level ownership still require server-side checks.
- Do not use an ORM unless the project explicitly adopts one because this template's SQL migrations and better-sqlite3 repository layer are the chosen source of truth.
- Do not generate schema with `db push` in shared environments because unreviewed drift has no durable migration or rollback evidence.
- Do not deploy the database on ephemeral storage or multiple independent replicas because a local SQLite file is neither durable nor automatically shared.
- Do not add speculative abstractions because unused layers increase context cost and obscure the behavior being changed.

## Project overview

This repository is a SaaS application built with Next.js, TypeScript, and SQLite. Make the smallest correct change that satisfies the request while preserving data, authentication boundaries, accessibility, and existing behavior.

## Source of truth

Before editing, inspect the repository rather than assuming a particular starter layout. Treat these as authoritative when present:

1. `package.json` scripts and dependency versions
2. lockfile and package-manager metadata
3. existing application and test code
4. database schema and committed migrations
5. `.env.example` and framework configuration
6. CI workflows and deployment documentation

Do not replace an established library or architectural pattern merely because another option is familiar.

## Common commands

Use the package manager selected by the committed lockfile:

- `pnpm-lock.yaml` → `pnpm`
- `yarn.lock` → `yarn`
- `package-lock.json` → `npm`
- `bun.lock` or `bun.lockb` → `bun`

Discover actual scripts with `package.json`. Typical checks are:

```bash
npm ci
npm run lint
npm run typecheck
npm test
npm run build
```

Do not invent missing scripts. Do not update the lockfile unless the task requires a dependency change.

## Working rules

- Read relevant code, tests, schema, and migrations before changing behavior.
- Keep diffs focused. Avoid unrelated formatting, renames, dependency upgrades, or generated-file churn.
- Preserve strict TypeScript types; do not silence errors with `any`, unsafe assertions, or blanket ignores.
- Prefer existing shared components, validation helpers, database utilities, and error conventions.
- Validate untrusted data at the server boundary, even when the client already validates it.
- Never expose secrets, database paths, stack traces, internal IDs, or authorization decisions to the browser unnecessarily.
- Never commit `.env*`, SQLite database files, WAL/SHM files, logs, credentials, or production data.
- Do not run destructive database commands against an existing database unless the task explicitly requires it and a backup/rollback path is documented.

## Next.js boundaries

- Follow the router already used by the repository (`app/` or `pages/`). Do not mix routing models without an explicit migration task.
- Default to Server Components in the App Router. Add `"use client"` only where browser state, effects, or event handlers require it.
- Keep database access, secrets, authorization, billing logic, and privileged SDKs in server-only modules.
- Treat Server Actions and Route Handlers as public request boundaries: authenticate, authorize, validate, and return controlled errors.
- Do not trust hidden fields, query parameters, cookies, client-supplied tenant IDs, prices, roles, or ownership claims.
- Use framework navigation, metadata, caching, and revalidation APIs consistent with the installed Next.js version.
- After a mutation, revalidate or redirect deliberately so stale cached data is not presented as current.
- Avoid importing Node-only modules into Client Components.

## Authentication and authorization

Authentication answers who the caller is; authorization must separately prove that the caller may perform this action.

For every protected read or mutation:

1. Resolve the authenticated server-side identity.
2. Reject missing or invalid sessions.
3. Derive tenant/user ownership from trusted server data, not request input alone.
4. Scope the database operation to that tenant/user.
5. Return a generic not-found or forbidden response without leaking another tenant's data.

Never rely solely on middleware, disabled buttons, hidden UI, or client redirects for authorization.

## SQLite safety

- Use the existing ORM/query layer and migration system when present.
- Always use parameterized queries. Never interpolate user input into SQL.
- Enable and respect foreign-key constraints.
- Keep write transactions short; do not perform network calls inside them.
- Use a transaction when multiple writes must succeed or fail together.
- Handle uniqueness and constraint failures as expected application outcomes.
- Avoid read-modify-write races; prefer an atomic update or a guarded transaction.
- Add indexes only for demonstrated query patterns, and document material tradeoffs.
- Do not edit a migration that may already have run. Add a new forward migration unless repository policy explicitly says otherwise.
- For destructive schema changes, provide a staged migration, data-copy plan, validation query, and rollback/recovery notes.
- Do not assume SQLite behaves like PostgreSQL for types, concurrent writes, `ALTER TABLE`, or deployment topology.

If the app can run in multiple server processes or ephemeral/serverless environments, verify that its SQLite storage is persistent and shared as required. Do not claim production scalability without checking the deployment architecture.

## Multi-tenant data access

For tenant-owned records, scope queries in SQL rather than fetching broadly and filtering in application code. Prefer patterns equivalent to:

```sql
SELECT * FROM projects
WHERE id = ? AND workspace_id = ?;
```

Mutations should include the ownership predicate as well. A prior ownership check alone may race with a later update.

## Validation and errors

- Use the repository's existing schema-validation library when available.
- Normalize and validate strings, enums, IDs, dates, URLs, pagination, and numeric bounds server-side.
- Distinguish validation, authentication, authorization, conflict, not-found, rate-limit, and internal failures.
- Log actionable server context without logging tokens, passwords, full payment data, or unnecessary personal information.
- Show users concise recovery guidance; do not expose raw exceptions.

## Billing and webhooks

When billing exists:

- Treat provider-signed webhooks as authoritative for asynchronous payment state.
- Verify signatures against the raw request body as required by the provider.
- Make webhook handling idempotent using the provider event ID or another durable unique key.
- Store money as integer minor units plus an explicit currency; never use floating-point arithmetic.
- Compute prices and entitlements on the server.
- Do not grant an entitlement before the authoritative paid state is recorded.

## UI and accessibility

- Preserve responsive layouts and the established design system.
- Use semantic HTML and associated labels.
- Support keyboard navigation and visible focus.
- Provide loading, empty, validation, error, and success states for changed flows.
- Do not encode meaning by color alone.
- Avoid optimistic UI for irreversible or billing-sensitive actions unless rollback behavior is explicit.

## Testing expectations

Add or update the narrowest tests that prove the requested behavior. Important paths should cover:

- successful behavior
- invalid input
- unauthenticated access
- cross-user or cross-tenant denial
- missing records
- uniqueness/conflict handling
- transaction rollback or idempotency where relevant

Prefer behavior-focused tests over implementation snapshots. Never weaken or delete a failing test merely to make the suite green.

For a database change, test against a fresh database and, when feasible, a representative pre-migration fixture. Confirm that existing data survives and constraints/indexes are present.

## Verification before completion

Run the repository's relevant checks, ordinarily:

1. focused tests for changed behavior
2. lint
3. TypeScript/typecheck
4. broader tests when practical
5. production build for framework/configuration changes
6. migration checks for schema changes

If a check cannot run, report the exact command, blocker, and what remains unverified. Do not say a check passed unless it actually ran successfully.

## Completion report

Summarize:

- behavior changed
- important files changed
- database or migration impact
- security/authorization considerations
- checks run and their results
- known limitations or follow-up work

Do not claim that code is secure, production-ready, backward-compatible, or fully tested without evidence.
