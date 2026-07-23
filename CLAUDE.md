# CLAUDE.md — Next.js 15 + SQLite SaaS

This file is the operating contract for an opinionated SaaS application using Next.js 15 App Router, TypeScript, and SQLite. Follow it without inventing architecture. Prefer the smallest change that preserves tenant isolation, data integrity, and production operability.

## Stack and versions

- Node.js 22 LTS; use the repository's `.nvmrc` or `engines` field when present.
- Package manager: pnpm. Use the version in `packageManager` from `package.json`; do not switch package managers.
- Next.js 15 App Router with React Server Components by default.
- TypeScript in strict mode. Do not add `any`; use `unknown` and narrow it.
- SQLite for local and single-instance deployments. Use `better-sqlite3` for a synchronous server-side connection unless the repository already standardizes on Turso/libSQL.
- Zod for parsing untrusted input at boundaries.
- Vitest for unit tests and Playwright for browser tests when those tools are present.
- ESLint and Prettier/oxfmt follow the repository configuration. Never add a second formatter.

Why: pinned tool choices make a greenfield project reproducible and keep generated migrations, lockfiles, and CI behavior consistent.

## First commands

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm start
```

If a command is absent, inspect `package.json` before inventing a replacement. Do not silently skip a requested check; report that it is unavailable.

## Repository structure

```text
src/
  app/                    # routes, layouts, loading/error/not-found boundaries
    (public)/              # unauthenticated pages
    (auth)/                # sign-in and account recovery
    app/                   # authenticated product UI
    api/                   # route handlers; one resource per route
  components/              # reusable UI; no database access
  server/
    db/
      client.ts            # one server-only SQLite connection factory
      migrations/          # ordered, immutable SQL migrations
      queries/              # typed query functions grouped by feature
    auth/                   # session verification and authorization
    services/               # domain operations and transaction boundaries
  lib/                     # pure utilities and schemas
  styles/
public/
  # static assets only
scripts/
  migrate.ts
  seed.ts
  check-env.ts
 tests/
  unit/
  e2e/
```

Keep database access out of React components and client modules. Keep route handlers thin: authenticate, validate, call a service, map errors to an HTTP response.

Why: this makes security-sensitive code reviewable and prevents accidental server-only imports from entering client bundles.

## Naming conventions

- Components: `PascalCase.tsx`; hooks: `useThing.ts`; utilities: `kebab-case.ts`.
- Route folders use lowercase URL segments. Dynamic segments use `[id]`; route groups use `(name)`.
- Database tables and columns use `snake_case`; TypeScript properties use `camelCase`.
- Functions describe actions: `createProject`, `listProjectsForUser`; avoid generic `getData`.
- Zod schemas end in `Schema`; inferred types use `z.infer<typeof schema>`.
- Every exported server operation has an explicit return type.
- IDs are opaque strings (UUID/ULID); never expose sequential internal database IDs as tenant identifiers.

## App Router rules

- Prefer Server Components. Add `'use client'` only for interaction, browser APIs, or client state.
- Do not call the database, read secrets, or access `process.env` from client modules.
- Fetch data in server components or server services; do not create an API route merely to call it from a server component.
- Use route handlers for external clients, webhooks, browser mutations that need an HTTP boundary, and public API consumers.
- Add `loading.tsx`, `error.tsx`, and `not-found.tsx` at meaningful product boundaries.
- Set `export const runtime = 'nodejs'` for SQLite, webhook, filesystem, or Node-only routes. Never use Edge runtime for those routes.
- Validate route params, search params, JSON bodies, and headers before use.
- Return stable error shapes: `{ error: { code, message, requestId } }`.

## Authentication and authorization

Authentication answers “who is this?” Authorization answers “may this identity perform this action on this tenant and resource?” Always perform both.

- Resolve the session on the server from the configured secure cookie/session mechanism.
- Treat every client-provided `userId`, `tenantId`, `organizationId`, and resource ID as untrusted.
- Derive the effective user and tenant from the authenticated session, not from request body fields.
- Check membership and role inside the service that performs the mutation.
- Use deny-by-default roles. A UI hiding a button is not authorization.
- Use `httpOnly`, `secure` in production, `sameSite=lax` or stricter, short-lived sessions, and rotation on privilege changes.
- Never log tokens, cookies, password-reset URLs, API keys, or full request bodies.

## Tenant isolation

Every tenant-owned table includes `tenant_id NOT NULL`. Every query touching tenant data requires tenant scope in the SQL predicate.

```ts
const project = db
  .prepare(
    `SELECT id, name
       FROM projects
      WHERE id = ? AND tenant_id = ? AND deleted_at IS NULL`,
  )
  .get(projectId, session.tenantId) as ProjectRow | undefined;
```

Rules:

- Never fetch by resource ID alone.
- Never accept a tenant ID from a hidden form field as authority.
- Add composite indexes such as `(tenant_id, id)` and feature-specific `(tenant_id, created_at)` indexes.
- Add tests proving user A cannot read, update, delete, or infer user B's records.
- When a resource crosses tenants by design, document the controlled access path and audit it.

Why: most SaaS data leaks are authorization omissions in ordinary queries, not exotic exploits.

## SQLite and migrations

- Enable foreign keys on every connection: `PRAGMA foreign_keys = ON`.
- Use WAL mode for a long-running server: `PRAGMA journal_mode = WAL`.
- Set a busy timeout and use transactions for multi-statement invariants.
- Store timestamps as UTC ISO 8601 text or integer epoch consistently; do not mix formats.
- Use `NOT NULL` and `CHECK` constraints for invariants that must survive application bugs.
- Migration filenames are immutable and ordered, for example `0001_initial.sql`, `0002_add_projects.sql`.
- Never edit an applied migration. Add a new migration.
- Record applied migrations in a table with the migration name and checksum.
- Run migrations once during deployment, not on every request.
- Back up the SQLite database before migrations and test restore regularly.
- Do not use `db.exec(userInput)`; parameters are mandatory for values.

A migration must include the forward change, indexes needed by real queries, and a rollback note in its accompanying documentation. Destructive changes require a two-step expand/migrate/contract rollout.

## Transactions and domain services

Put business invariants in server services, not UI handlers. Use one transaction when several writes must succeed together.

```ts
const createProject = db.transaction((input: CreateProjectInput) => {
  const projectId = createId();
  insertProject.run(projectId, input.tenantId, input.name);
  insertAuditEvent.run(createId(), input.tenantId, 'project.created', projectId);
  return projectId;
});
```

- Validate before opening a transaction where possible.
- Keep transactions short; do not call remote APIs while holding one.
- Make retryable operations idempotent with a unique request/event key.
- Write an audit event for billing, membership, permission, and destructive changes.

## Forms, APIs, and errors

- Parse all external input with Zod.
- Enforce body size, pagination limits, and reasonable string lengths.
- Use cursor pagination for large or frequently changing lists; cap `limit`.
- Return `404` for resources the caller is not authorized to know exist when that avoids enumeration.
- Map expected domain errors explicitly. Do not expose stack traces or SQL messages.
- Include a request ID in logs and responses.
- Rate-limit login, password recovery, public APIs, expensive AI operations, and webhook retries.

## Billing and webhooks

- Treat the payment provider event as the source of truth for subscription state.
- Verify webhook signatures against the raw request body before parsing JSON.
- Webhook route handlers use the Node runtime and disable body transformations that invalidate signatures.
- Store provider event IDs with a unique constraint; duplicate delivery must be a no-op.
- Process events idempotently and record processing status/error for replay.
- Never grant entitlements from a client redirect alone.
- Keep checkout, portal, subscription, invoice, and entitlement state transitions auditable.
- Use sandbox/test mode for local verification. Never place real secrets in `.env.example` or source control.

## AI and external integrations

- Treat model output as untrusted data. Validate structured output before use.
- Tool calls require an explicit allowlist, argument schema, tenant scope, timeout, and audit event.
- Do not allow model-generated SQL, shell commands, URLs, or emails to execute without deterministic policy checks and human approval where impact is external.
- Set token, time, and cost budgets per request.
- Store prompts and outputs only when necessary; redact secrets and customer data.
- Keep provider adapters behind a server-side interface so local and hosted models can be swapped without route changes.

## Testing requirements

Minimum gates before merge:

```bash
pnpm lint
pnpm typecheck
pnpm test -- --run
pnpm build
```

Add tests for:

- tenant isolation on every tenant-owned resource
- authentication failure and authorization failure
- schema rejection and bounded pagination
- migration application on a fresh database and an existing database
- transaction rollback when a later write fails
- webhook signature rejection, duplicate delivery, and out-of-order events
- billing entitlement transitions
- AI tool allow/deny policy and malformed model output

For a greenfield smoke test, create a temporary database, run migrations, seed one tenant/user/project, start the app, verify the public page, authenticate with a test session, create/read/update/delete a project, and confirm a second tenant receives `404` or `403` without data leakage.

## Security and privacy

- Commit `.env.example` with names only; keep real secrets outside Git.
- Add `.env*` to `.gitignore` except `.env.example`.
- Run secret scanning and dependency auditing in CI.
- Pin GitHub Actions to immutable commit SHAs when the project’s security policy requires it.
- Use least-privilege database and provider credentials.
- Do not include customer data in fixtures, screenshots, logs, or error messages.
- Report security issues privately using the repository's security policy; do not open public exploit details first.

## Git and changes

- Make one focused change per branch. Branch names: `feat/short-name`, `fix/short-name`, `chore/short-name`.
- Read the relevant files before editing. Preserve the existing architecture and lockfile.
- Do not run `git add -A`; stage explicit paths.
- Do not rewrite history or force-push shared branches.
- Commit messages use imperative mood and explain the user-visible change.
- Before opening a PR, run the gates above and `git diff --check`.
- PR descriptions must include root cause, files changed, verification commands/output, migration notes, security impact, and rollback path.

## What we do not do

- No Pages Router for new routes.
- No Edge runtime for SQLite or signature verification.
- No client-side authorization.
- No unscoped tenant queries.
- No `any`, `@ts-ignore`, or disabled lint rules to hide failures.
- No manual edits to generated lockfiles or applied migrations.
- No silent catch blocks.
- No placeholder TODO implementation presented as complete.
- No production deploy with failing typecheck, tests, or build.
- No real payment, customer email, or destructive data migration from a local development command.

When uncertain: inspect the repository conventions, choose the smallest reversible change, add a regression test, and state the uncertainty instead of guessing.
