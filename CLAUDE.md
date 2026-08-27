# CLAUDE.md — Next.js 15 + SQLite SaaS

This project is a production-oriented SaaS built with Next.js 15 App Router, TypeScript, and SQLite. Prefer boring, explicit, easily testable code over clever abstractions.

## Stack and versions

- Next.js 15 with App Router. Reason: server-first rendering and route handlers are the default architecture.
- TypeScript with `strict` enabled. Reason: domain mistakes should fail at compile time where possible.
- React Server Components by default. Reason: less client JavaScript, simpler data access, and fewer hydration problems.
- SQLite through `better-sqlite3` for single-node deployments or Turso/libSQL for distributed/hosted deployments. Reason: both preserve SQLite semantics without introducing an ORM-only mental model.
- Drizzle ORM is preferred for typed SQL and migrations. Reason: schema remains close to SQL and migration output is inspectable.
- Zod at trust boundaries only: forms, API input, environment variables, webhook payloads. Reason: avoid duplicating validation everywhere.

Do not silently upgrade major framework or database versions inside unrelated work.

## Project structure

Use this layout unless a feature gives a strong reason not to:

```text
app/
  (auth)/
  (dashboard)/
  api/
components/
  ui/
  forms/
db/
  schema.ts
  migrations/
  queries/
lib/
  auth/
  validation/
  server/
  client/
types/
tests/
```

Rules:
- Route-specific components stay next to their route when they are not reused elsewhere. Reason: local code should remain local.
- Shared presentational components go in `components/ui`. Reason: keeps cross-feature primitives obvious.
- Database access belongs in `db/queries` or narrowly scoped server modules. Reason: pages and components should not contain ad-hoc SQL.
- Cross-cutting helpers belong in `lib`; feature-specific helpers do not. Reason: `lib` must not become a junk drawer.
- Never put secrets, database handles, or filesystem access in modules imported by Client Components. Reason: client/server boundaries must remain explicit.

## Naming conventions

- Files and folders: `kebab-case`.
- React components and exported types: `PascalCase`.
- Functions, variables, DB columns in TypeScript: `camelCase`.
- SQL tables: `snake_case`, plural nouns (`users`, `subscriptions`).
- SQL columns: `snake_case` (`created_at`, `user_id`).
- Booleans start with `is`, `has`, `can`, or `should` in TypeScript. Reason: call sites read unambiguously.
- Route handlers use standard HTTP verbs and return typed JSON helpers where practical.

Avoid abbreviations unless universally understood (`id`, `url`, `api`). Reason: explicit names reduce maintenance cost.

## Database rules

### Schema ownership

`db/schema.ts` is the source of truth for application schema. Every schema change must have a migration.

### Migrations

- Never edit an already-applied migration. Reason: deployed databases must have reproducible history.
- Create a new forward migration for every schema change.
- Migrations must be deterministic and idempotency-safe at the deployment layer.
- Do not use `db push` or equivalent schema-sync commands in production. Reason: production changes must be reviewable.
- Destructive changes require a staged migration: add new shape -> backfill -> switch reads/writes -> remove old shape in a later release. Reason: avoid irreversible deployment coupling.
- New non-null columns on populated tables must have a safe default or staged backfill.
- Add indexes for columns used by frequent filters, joins, or uniqueness constraints, but do not index speculatively.

### Query rules

- Prefer explicit column selection over `SELECT *`. Reason: stable data contracts and less accidental exposure.
- Parameterize every dynamic value. Never concatenate user input into SQL.
- Keep transactions short and synchronous when using `better-sqlite3`.
- N+1 queries are defects when a bounded join or batch query is practical.
- Repository/query functions return domain-friendly shapes rather than leaking raw driver objects.

## Server and client component patterns

- Components are Server Components unless they need browser-only APIs, local interactive state, or event handlers.
- Add `"use client"` only at the smallest boundary that requires it. Reason: client boundaries pull their dependency graph into the browser.
- Fetch server data directly in Server Components or server-only query modules.
- Do not fetch your own internal API route from a Server Component. Call the underlying server function directly. Reason: avoids unnecessary HTTP hops and duplicated auth handling.
- Pass serializable props across server/client boundaries.
- Use Suspense intentionally for independent slow regions, not as decoration.

## Forms and mutations

Prefer Server Actions for application-internal form mutations.

Each mutation must:
1. Authenticate the caller.
2. Authorize the specific resource/action.
3. Validate input with Zod.
4. Perform the database change.
5. Revalidate or redirect explicitly.

Never trust hidden form fields for ownership or authorization. Reason: clients can modify them.

For public/external integrations, use Route Handlers instead of Server Actions.

## Authentication and authorization

- Authentication answers who the caller is; authorization is checked separately at the operation boundary.
- Never rely on UI visibility as authorization.
- Resource queries that depend on ownership should include ownership/tenant constraints in the query where practical.
- Multi-tenant tables include a tenant/workspace identifier and relevant indexes.
- Do not log tokens, session cookies, password material, or full webhook secrets.

## Error handling

- Throw or return typed domain errors for expected failures.
- User-facing errors must be actionable but must not expose stack traces, SQL, secrets, or internal paths.
- Unexpected server errors are logged with enough context to diagnose the operation, not sensitive payloads.
- Do not catch errors merely to rethrow the same error.

## Dev commands

Use package scripts as the public interface. Expected commands:

```bash
npm run dev
npm run build
npm run lint
npm run typecheck
npm test
npm run db:generate
npm run db:migrate
```

Before marking work complete, run the narrowest relevant checks first, then at minimum:

```bash
npm run lint && npm run typecheck && npm test
```

Run `npm run build` for changes affecting routing, server/client boundaries, configuration, or deployment behavior.

## Testing strategy

- Unit-test pure domain logic.
- Integration-test database queries against a temporary SQLite database.
- Test Route Handlers and Server Actions at their authorization and validation boundaries.
- Prefer behavior assertions over snapshots for business logic.
- Every bug fix should add a regression test when practical.
- Tests must not depend on execution order or a developer's local database.

## Environment variables

- Validate required server environment variables once at startup through a server-only module.
- Prefix only intentionally public values with `NEXT_PUBLIC_`.
- `.env.example` contains names and safe placeholders only, never real credentials.
- Missing required environment variables should fail fast with a clear message.

## Patterns to follow

- Small route modules that delegate to named domain/query functions.
- Server Components for read-heavy pages.
- Server Actions for authenticated first-party mutations.
- Explicit transactions around multi-write invariants.
- Schema-derived TypeScript types where possible.
- Progressive enhancement for critical forms.
- Pagination for unbounded lists.
- UTC timestamps in storage; localize only at presentation time.

## What we do not do

- **No Pages Router for new features.** Reason: mixing routing models increases cognitive overhead.
- **No giant generic repository/service layer.** Reason: hides useful SQL semantics and creates abstraction tax.
- **No database calls from Client Components.** Reason: violates security and deployment boundaries.
- **No `any` to silence type errors.** Use `unknown`, narrow it, or model the type correctly.
- **No unchecked user input.** Validate all external data at the boundary.
- **No production schema mutation without a migration.** Reason: deployments must be reproducible.
- **No destructive migration bundled with a code switch unless proven safe for rollback.**
- **No business logic embedded in JSX when it can be a named function.** Reason: keeps rendering readable and logic testable.
- **No global state library by default.** Prefer URL state, server state, and local component state first.
- **No premature caching.** Add caching only after identifying a stable read path and invalidation strategy.
- **No secrets in logs, client bundles, repository files, fixtures, or screenshots.**

## Definition of done

A change is done when:
- behavior matches the requested requirement,
- auth and tenant boundaries remain correct,
- migrations are included for schema changes,
- relevant tests exist and pass,
- lint and typecheck pass,
- server/client boundaries are valid,
- no secrets or generated local artifacts are committed,
- documentation is updated when the developer workflow changes.

When requirements are ambiguous, prefer the smallest production-safe implementation consistent with these rules instead of inventing a large framework or abstraction.