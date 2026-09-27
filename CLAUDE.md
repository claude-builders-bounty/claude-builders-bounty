# CLAUDE.md — Next.js 15 + SQLite SaaS

This file is the operating contract for an opinionated, production-ready SaaS built with Next.js 15 App Router, TypeScript, React 19, and SQLite. Follow it without asking for choices that are already settled here. If a request conflicts with a security or data-integrity rule, stop and explain the conflict before changing code.

## Stack and versions

- Node.js 20 LTS or newer LTS; use the version declared in `.nvmrc` or `engines`. **Why:** one declared runtime makes local development and CI reproducible.
- Next.js 15 App Router with React 19 and TypeScript in strict mode. **Why:** a fixed stack lets a greenfield project follow examples and tooling without choosing compatible versions.
- `pnpm` is the package manager. Never mix `npm`, `yarn`, and `pnpm` lockfiles. **Why:** competing lockfiles can resolve different dependency trees on different machines.
- SQLite for local and single-instance deployments, using `better-sqlite3` behind a small repository layer. Turso/libSQL is the production-compatible remote option; application code must use the same repository interface for both. **Why:** one data contract supports local development and remote SQLite without scattering driver-specific code.
- Zod validates every untrusted boundary: form data, route params, search params, webhook bodies, and environment variables. **Why:** parsing at entry points prevents invalid values from reaching privileged operations.
- Vitest is the unit-test runner; Playwright covers critical browser flows. **Why:** fast isolated checks and a small number of real-browser journeys catch different classes of regression.

When a repository already pins a compatible patch version, keep that pin. Do not upgrade the framework, database driver, or auth library as part of an unrelated feature. **Why:** unrelated upgrades expand the review surface and can introduce regressions unrelated to the requested change.

## Non-negotiable rules

1. **Server by default.** Files are React Server Components unless they require browser state, event handlers, or a browser-only API. Add `"use client"` only at the smallest interactive leaf. **Why:** limiting the client boundary avoids shipping data access and secrets into the browser by accident.
2. **Validate at the boundary.** Parse inputs before authorization, queries, or mutations. Return a typed validation error; never pass raw request data into SQL, redirects, shell commands, or HTML. **Why:** one validated representation prevents the same hostile value from reaching several sinks.
3. **Authorize on the server.** UI hiding is not authorization. Every Server Action, Route Handler, and service entry point resolves the current user and tenant membership before data access. Repository methods never trust a client-supplied tenant or resource ID alone; scope each read and write by the authorized tenant and principal (for example, `WHERE id = ? AND workspace_id = ?`). **Why:** a caller can bypass the UI, and query-level scoping prevents an overlooked call path from crossing accounts.
4. **Parameterized SQL only.** Never interpolate values into SQL. Keep migrations and queries in the data layer; route and component code calls named repository functions. **Why:** a narrow data boundary makes injection and tenant-scope mistakes auditable.
5. **No secret leakage.** Only variables explicitly prefixed `NEXT_PUBLIC_` may reach client bundles. Do not log tokens, cookies, passwords, full webhook bodies, or personal data. **Why:** browser bundles and logs have wider, harder-to-revoke visibility than server memory.
6. **Mutations are deliberate.** Destructive operations require an explicit confirmation in the UI, a server-side authorization check, and an audit record. Prefer soft delete and reversible state transitions. **Why:** users and operators need a recovery path when a mutation is mistaken.
7. **Errors are typed and useful.** Show users a safe message with a request/correlation id; log the detailed cause on the server with secrets and personal data redacted. **Why:** support can correlate a failure without leaking its internals to an attacker.
8. **Tests must be hermetic.** Unit tests use an isolated temporary SQLite database and mocked network boundaries. No test depends on a developer's database, clock, filesystem layout, or network service. **Why:** deterministic tests make regressions reproducible in CI and on a new machine.

## Project structure

```text
app/
  (auth)/                 # sign-in, sign-up, password reset
  (dashboard)/            # authenticated product UI
  api/                    # thin Route Handlers; parse, authorize, delegate
  actions/                # Server Actions grouped by capability
  layout.tsx              # root providers, metadata, global error boundary
  loading.tsx             # route-level pending UI
  error.tsx               # route-level recoverable error UI
components/
  ui/                     # presentational, reusable primitives
  features/<feature>/     # feature-specific components and schemas
lib/
  auth/                   # session and authorization helpers
  db/                     # client, migrations, repository functions
  env.ts                  # validated environment variables
  http/                   # safe fetch wrapper and correlation ids
  validation/             # shared Zod schemas
tests/
  unit/                   # repository, schema, and pure-function tests
  integration/            # Route Handler and Server Action tests
  e2e/                    # Playwright critical journeys
public/                   # immutable static assets only
scripts/                  # safe, repeatable maintenance commands
```

Keep feature code close to its route, but keep database access, authorization, and validation in `lib/` so they can be tested without rendering React.

## Naming conventions

- Use `kebab-case` for route folders, feature folders, file names, database migration files, and URL slugs. **Why:** predictable paths keep imports, links, and deploy tooling portable across case-sensitive filesystems.
- Use `PascalCase` for React component files, exported component names, domain types, and Zod schemas (for example, `InvoiceTable.tsx`, `Invoice`, and `InvoiceInput`). **Why:** a reader can distinguish a renderable/type contract from a function at a glance.
- Use `camelCase` for functions, local values, Server Actions, and repository methods (for example, `createInvoice` and `findInvoiceById`). **Why:** this matches TypeScript and Next.js conventions without inventing a second naming dialect.
- Prefix custom React hooks with `use` and place them in `hooks/` or next to the feature that owns them. **Why:** the prefix lets React tooling and reviewers recognize hook call rules.
- Name repository methods with an explicit verb and aggregate (`findWorkspaceMember`, `listInvoicesForWorkspace`, `createInvoice`). **Why:** vague `getData` helpers hide authorization and query intent.
- Number migrations with a sortable UTC prefix and a `kebab-case` intent (for example, `20260327_120000_add-invoice-status.sql`). **Why:** immutable ordering prevents different environments from applying schema changes in a different sequence.

## Package scripts

The root `package.json` must expose these commands (an existing project may add flags, but must keep the intent). **Why:** consistent entry points make setup, CI, and handoff predictable for a new contributor:

```json
{
  "dev": "next dev",
  "build": "next build",
  "start": "next start",
  "lint": "next lint",
  "typecheck": "tsc --noEmit",
  "test": "vitest run",
  "test:watch": "vitest",
  "test:e2e": "playwright test",
  "db:migrate": "tsx scripts/db-migrate.ts",
  "db:status": "tsx scripts/db-status.ts"
}
```

Before opening a PR, run `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`, and the relevant Playwright project. A failed check is a stop signal, not something to hide with a skipped test. **Why:** checking static analysis, behavior, production compilation, and a real browser path catches distinct failure modes before review.

## Environment and configuration

Create `.env.example` with names and safe example values; keep real `.env*` files out of Git. Parse configuration once in `lib/env.ts` with Zod and import that module instead of reading `process.env` throughout the app. **Why:** a single validated configuration boundary documents setup without leaking secrets or allowing inconsistent parsing.

Required production categories:

- `DATABASE_URL` (SQLite path or Turso URL) and, for Turso, `DATABASE_AUTH_TOKEN`. **Why:** the data adapter needs an explicit target and authenticated remote access.
- `AUTH_SECRET` with a documented minimum length; never use a development fallback in production. **Why:** predictable secret strength protects signed sessions, while a fallback would make production credentials guessable.
- `APP_URL` validated as an absolute HTTPS URL in production. **Why:** canonical origin validation prevents insecure callback and redirect configuration.
- Provider credentials and webhook secrets, if used. **Why:** integrations should fail clearly when configured but missing their authentication material.

Fail fast at startup for missing production variables. Development may provide explicit local defaults only when the value cannot authenticate to a real service. **Why:** configuration errors surface before serving traffic, while harmless local defaults avoid blocking setup without granting production access.

## Database and migration rules

- Every schema change is a numbered, committed migration. Migrations are forward-only, idempotent, run in a transaction where SQLite permits it, and record their version in a migrations table. **Why:** a durable ordered ledger lets every environment reproduce the same schema safely.
- Never edit an applied migration. Add a new migration for corrections. **Why:** changing history makes already-upgraded databases diverge from fresh installs.
- Add indexes only for demonstrated query paths; document the query they support. **Why:** indexes have write and storage costs, so each should solve an observable query need.
- New columns are nullable or have a safe default before application code relies on them. Backfill in a separate bounded step, then tighten constraints in a later migration. **Why:** staged expansion avoids breaking old application versions and large live tables.
- Preserve user data. Do not use `DROP TABLE`, `DELETE` without a narrow predicate, or a destructive reset in a production path. **Why:** a mistaken migration or predicate must not irreversibly erase customer records.
- Enable foreign keys on every connection and use UTC ISO-8601 timestamps (or integer epoch milliseconds) consistently. **Why:** connection-local enforcement prevents orphan rows, and one time representation avoids locale-dependent comparisons.
- Transactions must include all writes that must succeed or fail together. Do not perform network calls while holding a database transaction. **Why:** atomic local changes stay consistent without making locks depend on a remote service.
- Repositories return domain-shaped values, not raw driver rows. Map nullable database fields explicitly. **Why:** callers should not depend on SQL column shape or mistake database nullability for a domain guarantee.

For SQLite concurrency, keep transactions short, set a busy timeout, and prefer WAL mode. For Turso, avoid relying on local process state or SQLite-specific filesystem APIs. **Why:** bounded locks improve local contention behavior, while remote deployments cannot safely depend on one process's filesystem or memory.

## Components, routes, and Server Actions

- Define the data contract first: Zod input schema, domain result, and safe error codes. **Why:** agreeing on valid input and failure shapes prevents UI and persistence layers from inventing incompatible behavior.
- Use `loading.tsx`, `error.tsx`, and `not-found.tsx` at route boundaries where a slow or missing resource is expected. **Why:** users receive an explicit pending, recovery, or absence state instead of a blank screen or leaked exception.
- Mutating forms use a Server Action or Route Handler that validates the complete payload again. Disable the submit control while pending and make success/failure visible without relying on a toast alone. **Why:** server validation is the trust boundary, and visible state helps prevent duplicate submissions and silent failures.
- Use stable IDs and accessible labels. Every interactive control has a keyboard path, visible focus state, and a meaningful name. **Why:** stable identity prevents list-state bugs and accessible controls support keyboard and assistive-technology users.
- Do not fetch the same server data again from a Client Component when the Server Component already owns it; pass the smallest serializable props. **Why:** duplicate requests add latency and can expose more data to the browser than the UI needs.
- Cache only public or explicitly scoped data. Mark user-specific data dynamic and revalidate after mutations. **Why:** cache leakage can cross account boundaries, and stale views misrepresent a successful write.
- Use `redirect()` only after successful authorization and mutation; never place untrusted input directly in a redirect target. **Why:** this avoids redirecting unauthorized users or creating open redirects from attacker-controlled data.

## Authentication, authorization, and webhooks

- Store only a session identifier in an HttpOnly, Secure, SameSite cookie. Rotate sessions after sign-in and privilege changes. **Why:** cookie flags reduce browser exposure and rotation invalidates sessions issued under an older identity state.
- Resolve the current session and tenant membership in every Server Action or Route Handler before data access. Every repository query and mutation must include the authorized tenant/resource scope (and user ID when data is user-owned); never rely on a client-provided scope or UI hiding. Test that a cross-tenant ID is denied or returns no data and cannot mutate another tenant's records. **Why:** every call path, including direct requests and background work, must enforce the same data boundary.
- Rate-limit login, password reset, search, and webhook endpoints. Verify webhook signatures over the raw body before parsing JSON, reject stale timestamps, and make event handling idempotent. **Why:** these controls constrain brute force and replay while making retried deliveries safe.
- Return the same safe response shape for authentication failures to avoid account enumeration. **Why:** different failure details can reveal which identities exist.

## SQL, API, and external service conventions

- Repository functions accept typed arguments and return typed results. Use explicit column lists; never rely on `SELECT *` across migrations. **Why:** explicit shape makes schema changes reviewable and limits accidental data exposure.
- Route handlers set correct status codes (`400` validation, `401` unauthenticated, `403` unauthorized, `404` absent, `409` conflict, `429` rate limit, `5xx` unexpected). **Why:** clients and operators need a stable way to distinguish recoverable input errors from access and server failures.
- Outbound `fetch` calls have an allowlisted origin, timeout, bounded retries only for idempotent operations, and structured error handling. Never retry a payment or other non-idempotent mutation without an idempotency key. **Why:** bounded network behavior reduces hangs and prevents retries from duplicating side effects.
- Keep third-party response bodies out of logs unless explicitly redacted and bounded. **Why:** provider payloads can contain secrets or personal data and may be arbitrarily large.

## Testing and review checklist

For every feature or bug fix, add the smallest tests that prove the behavior and its failure modes:

- schema tests for missing, wrong-type, boundary, and extra fields. **Why:** boundary cases reveal invalid states that happy-path samples miss.
- repository tests for authorization scope, empty results, conflicts, and transaction rollback. **Why:** data-layer tests protect tenant isolation and atomicity without a browser.
- route/action tests for status codes and safe error envelopes. **Why:** consumers rely on these externally observable contracts.
- regression tests for the reported bug. **Why:** a reproducible failing case prevents the same defect from returning.
- an accessibility smoke check for new interactive UI. **Why:** keyboard and label regressions are easy to introduce while changing visible controls.
- an end-to-end happy path and one recovery path for user-visible flows. **Why:** the two paths prove both normal use and the most relevant failure recovery across layers.

Use deterministic clocks and IDs in tests. Assert observable behavior, not private implementation details. Do not weaken a test because a production bug makes it inconvenient. **Why:** deterministic observable checks remain stable through refactors and keep failures reproducible.

The minimum pre-PR gate is:

```bash
pnpm lint
pnpm typecheck
pnpm test -- --coverage
pnpm build
pnpm test:e2e --project=chromium
```

Record the commands and their results in the PR description. If a command cannot run in a constrained environment, state the exact limitation and run the closest hermetic substitute. **Why:** explicit evidence distinguishes a completed gate from an unavailable or skipped one.

## What we do not do (and why)

| Avoid | Reason |
| --- | --- |
| Generic rules such as “write clean code” without a concrete, checkable behavior | An agent cannot reliably execute an aspiration; a reviewer needs a behavior to verify. |
| Committing `.env`, database files, credentials, generated build output, or personal data | Source control persists and replicates those values beyond their intended audience. |
| Adding global client state when URL state, server data, or local component state is sufficient | Global state creates stale-data and authorization synchronization paths that a SaaS does not need. |
| Silently coercing invalid input, guessing an account/tenant, or selecting the first ambiguous result | Guessing can direct a valid request to the wrong customer's data. |
| Using `any` to bypass a type error | `any` removes the compiler signal at precisely the boundary where runtime validation is needed. |
| No floating-point money | Binary floating-point rounding can make invoices and ledger totals disagree; store integer minor units with an ISO currency code instead. |
| Making unrelated formatting, dependency, or architecture changes in a focused PR | A narrow diff keeps regression review and rollback feasible. |
| Claiming a test, benchmark, deployment, or payment that was not actually run, observed, or received | Evidence must remain auditable; an unobserved claim misleads maintainers and users. |

## Greenfield verification protocol

Run the structural contract check after copying this file into a new Next.js + SQLite project:

```bash
python -B -m unittest discover -s tests -v
```

Then perform the behavioral smoke test with an authenticated Claude Code installation: create a new project, paste this file at its root, and request a small authenticated CRUD feature. The expected result is that Claude Code uses the declared stack, layout, names, migration rules, validation, and test gate without asking the owner to choose among those settled defaults. Record the exact prompt, Claude Code version, and observed result in the PR or project evidence. This repository does **not** claim that a live Claude Code session has been run merely because the structural test passes.

## Definition of done

A change is ready only when the acceptance criteria are implemented, the relevant tests and build pass, migrations are reviewed for rollback/data safety, user-facing errors are understandable, secrets are absent from the diff, and the PR records exactly what was run. Keep the change small enough that a maintainer can verify it from the diff and the commands above.
