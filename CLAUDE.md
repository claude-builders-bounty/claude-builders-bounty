# CLAUDE.md

## Mission

This repository describes a production-ready SaaS built with Next.js 15 App Router and SQLite. Prefer explicit, boring, testable code over clever abstractions. Keep server and browser responsibilities obvious, keep migrations reproducible, and make every authorization decision enforceable on the server.

This is an operating guide for Claude Code and human contributors. Before changing code, inspect the existing route, feature, data-access code, tests, and package scripts. Extend a sound existing pattern; do not create a parallel architecture for a single task.

## Stack and versions

- Next.js 15 with the App Router in app/.
- React 19 and React Server Components by default.
- TypeScript in strict mode; no unchecked any.
- Node.js 22 LTS for local and server runtimes.
- pnpm as the package manager; the lockfile and package scripts are authoritative.
- SQLite as the system of record.
- better-sqlite3 for Node.js and single-process deployments; Turso/libSQL only when remote or edge-friendly persistence is required. Do not mix adapters inside one runtime.
- Zod, or the existing validation library, at trust boundaries.
- Tailwind CSS when the project uses it; shared primitives belong in components/ui/.
- Vitest for unit/integration tests and Playwright for browser smoke tests when configured.

Reason: a small fixed stack keeps local behavior close to production, makes the database inspectable, and gives Claude Code fewer inconsistent choices.

## Project structure

Use this layout for a greenfield app. Keep route-specific helpers beside their route until reused.

~~~text
app/
  (marketing)/              # public landing, pricing, and docs
  (app)/                    # authenticated product routes
  api/                      # Route Handlers for real HTTP boundaries
  layout.tsx
  page.tsx
components/
  ui/                       # accessible reusable presentation primitives
  features/                 # product-specific composed components
lib/
  auth/                     # session identity and authorization helpers
  config/                   # typed environment/config parsing
  db/
    client.ts               # one database client/factory boundary
    migrations.ts           # migration runner and status checks
    queries/                # focused query modules
  services/                 # domain operations and transaction boundaries
  validators/               # schemas for actions and Route Handlers
migrations/                 # ordered immutable SQL migrations
scripts/                    # explicit maintenance and local tooling
public/                     # static assets only
tests/
  unit/
  integration/
  e2e/
~~~

Rules:
- Put business rules in lib/services/, not in JSX or event handlers.
- Keep SQL in lib/db/ and migrations/, not scattered through pages.
- Keep Route Handlers and Server Actions thin: authenticate, validate, call a service, map the response.
- Keep database modules server-only; never import them from a Client Component.
- Keep external integrations behind small adapters so retries, timeouts, and error mapping are testable.

Reason: clear ownership keeps security checks, data access, and UI behavior reviewable instead of blending them into a page.

## Naming conventions

- React components and exported types use PascalCase: BillingSummary.tsx, WorkspaceRole.
- Functions, variables, and schemas use camelCase: createWorkspace, workspaceSchema.
- Server Actions use verb-first names and live in *.actions.ts: createProject, archiveInvoice.
- Services use domain names and live in *.service.ts: projects.service.ts.
- Query modules use domain names under lib/db/queries/.
- Tables are plural snake_case and columns are snake_case: team_members, created_at.
- Boolean names start with is, has, can, or should.
- Environment variables use SCREAMING_SNAKE_CASE and are parsed in one config module.
- Migrations use zero-padded sequence numbers: 0001_create_workspaces.sql.
- Avoid vague names such as utils.ts, helpers.ts, data.ts, or misc when a domain name exists.

Reason: names reveal layer and intent without opening the file, reducing accidental cross-boundary imports.

## Dev commands

Expose these equivalents in package.json; use existing repository scripts when present:

~~~bash
pnpm dev                 # start the local Next.js server
pnpm build               # create the production build
pnpm start               # serve the production build
pnpm lint                # run ESLint
pnpm typecheck           # run tsc --noEmit
pnpm test                # run unit and integration tests
pnpm test:e2e            # run browser smoke tests when configured
pnpm db:migrate          # apply pending migrations
pnpm db:status           # show applied and pending migrations
pnpm db:seed             # load deterministic local fixtures, if provided
~~~

Run the narrowest relevant check first. Before a PR, run lint, typecheck, tests, and build; run migration checks whenever schema or query code changes. Never claim a command passed unless it actually ran.

Reason: focused checks shorten feedback loops, while a production build catches App Router and server/client boundary errors that typecheck cannot.

## Server and client boundaries

- Start every page and component as a Server Component.
- Add "use client" only for browser APIs, event handlers, local interactive state, browser effects, charts, or keyboard/drag interactions.
- Keep Client Components at interaction leaves; do not turn an entire route tree into client code for one button.
- Pass serializable data from Server Components to Client Components. Do not pass database clients, secrets, functions, or class instances.
- Read secrets, sessions, and SQLite only on the server.
- Use Server Actions for authenticated mutations initiated by the app UI.
- Use Route Handlers for webhooks, public APIs, OAuth callbacks, file downloads, health checks, and non-React clients.
- Revalidate the smallest affected path or cache tag after a mutation.

Reason: server-side data work reduces bundle size and prevents credentials or authorization logic leaking into the browser.

## Component and UI patterns

- Prefer semantic HTML before custom widgets: button, label, nav, main, dialog, and a correct heading hierarchy.
- Every form control has a label, useful invalid state, and a keyboard path.
- Shared primitives are prop-driven and do not fetch from the database.
- Feature components compose primitives and receive data from a Server Component or focused action.
- Use progressive enhancement: the server mutation remains correct without client orchestration; client code improves pending/error UX.
- Keep loading, empty, error, and permission-denied states explicit.
- Avoid global client state for server-owned data; use the URL, server fetches, or narrowly scoped state only when justified.

Reason: accessible, small components stay portable and easier to test than hidden state inside a page.

## Data flow and service boundaries

All writes pass through a service owning validation, authorization, transactions, and side effects. A typical shape is:

~~~ts
export async function createProject(input: unknown, actor: Actor) {
  const data = createProjectSchema.parse(input)
  await requireWorkspaceRole(actor, data.workspaceId, "member")
  return db.transaction(() => {
    const project = projects.insert(data, actor.userId)
    audit.log({ actorId: actor.userId, action: "project.created", projectId: project.id })
    return project
  })
}
~~~

Rules:

- Validate external input before calling a query or service.
- Derive identity and ownership from the session, not hidden form fields.
- Keep transactions inside the service coordinating related writes.
- Return small typed objects, never raw database handles.
- Make retries safe for webhooks, payments, emails, and imports with an idempotency key or unique event ID.
- Map expected domain failures to stable user-facing errors and log unexpected failures with a request ID.

Reason: one write boundary makes permissions, invariants, audit logging, and retry behavior enforceable in one place.

## SQL and migration conventions

- Every schema change is a new ordered SQL migration under migrations/.
- Applied migrations are immutable. Repair a deployed mistake with a new migration; never edit history.
- The runner records a checksum and applies migrations in order inside a transaction when supported.
- A migration must work on an empty database and on the immediately previous schema.
- Prefer additive evolution: add a nullable/defaulted column, backfill, switch code, then tighten constraints later.
- Never run destructive schema changes from application startup or a request path.
- Enable PRAGMA foreign_keys = ON for every connection. For file SQLite, use WAL mode and a bounded busy timeout at connection setup.
- Use parameterized statements only. Map approved sort keys to fixed SQL fragments rather than concatenating input.
- Enforce invariants with NOT NULL, UNIQUE, CHECK, and FOREIGN KEY constraints as well as application validation.
- Add indexes for foreign keys and measured query paths; inspect query plans before speculative indexes.
- Use one ID style consistently within a domain: server-generated TEXT IDs or INTEGER primary keys.
- Store timestamps as UTC Unix milliseconds in INTEGER columns; convert at the application boundary.
- Store money as integer minor units plus an ISO currency code, never floating point.
- Use soft deletion only where audit/recovery requires it; every query must state whether deleted rows are included.

Reason: SQLite is dependable when schema history, constraints, locking, and units are explicit and reproducible.

## SQLite runtime rules

- Keep one database entry point in lib/db/client.ts; do not open ad hoc connections from routes.
- Prepare statements where the adapter supports it and keep query functions small enough to review.
- Use a transaction for related inserts, updates, ledger changes, or outbox writes that must succeed together.
- Never hold a transaction open across network calls, user prompts, or long computation.
- Use an outbox row for work that must happen after commit; workers can retry it safely.
- Back up before destructive maintenance and document restore steps.
- For Turso/libSQL, keep the same logical migrations and verify adapter-specific transaction/consistency behavior.

Reason: one connection boundary and short transactions avoid locked-database surprises while preserving atomic business changes.

## Server Actions and Route Handlers

Use a Server Action for an authenticated form mutation used only by this app. Use a Route Handler for webhooks, public APIs, OAuth callbacks, file transfers, health monitors, or other non-React callers.

Every boundary must:

- Authenticate when required.
- Authorize the specific user, workspace, role, and resource again on the server.
- Parse and validate body, query, params, and headers.
- Apply rate limits and idempotency where retries are plausible.
- Return stable status codes and error shapes without stack traces, SQL, tokens, or private identifiers.
- Revalidate affected data after a successful mutation.

Never trust hidden inputs for user IDs, workspace IDs, roles, prices, entitlements, or approval state. Session and database state are authoritative.

Reason: a browser boundary is an untrusted API even when only the product UI calls it.

## Authentication and authorization

- Authentication proves identity; authorization decides whether that identity may act on this resource.
- Perform authorization in the service/query boundary, not only by hiding a button or route segment.
- Model workspace membership and roles explicitly in SQLite.
- Deny by default if role, ownership, entitlement, or workspace membership is missing or ambiguous.
- Scope every tenant query by the authenticated workspace or user. Never fetch by an unscoped object ID and filter later.
- Use server-derived IDs for ownership and audit rows; ignore client-supplied owner fields.
- Re-check admin and billing permissions for every mutation, including Server Actions and webhooks.
- Log security-relevant changes without logging secrets.

Reason: UI state is not an authorization boundary, and tenant scoping errors are high-impact SaaS failures.

## Configuration and secrets

- Parse all environment variables through lib/config/env.ts using a typed schema at startup.
- Keep .env.example complete with placeholders and no real credentials.
- Do not read process.env throughout the codebase.
- Never put secrets in NEXT_PUBLIC_*, source files, fixtures, screenshots, logs, or SQLite data.
- Do not commit .env, local databases, production dumps, private keys, webhook secrets, or payment credentials.
- Fail fast for missing server configuration with safe local-development errors.
- Use separate credentials and databases for local, preview, and production.

Reason: centralized configuration prevents silent misconfiguration and makes secret exposure auditable.

## Validation, errors, and observability

- Validate forms, URLs, webhook payloads, imports, and API requests at the boundary.
- Return field-level messages for user-correctable input and generic messages for unexpected failures.
- Use structured logs with event name and request/correlation ID.
- Never log passwords, tokens, API keys, webhook signatures, full payment payloads, or unnecessary personal data.
- Treat not-found and unauthorized as separate internal cases, even if both use a safe outward response.
- Set timeouts and bounded retries for external services; never blindly retry non-idempotent writes.
- Add readiness checks for process and database connectivity without exposing data.

Reason: predictable error contracts and useful telemetry reduce recovery time without creating a second security problem.

## Testing expectations

- Unit-test pure functions, validators, permission checks, and domain services.
- Integration-test migrations, constraints, important SQL queries, and transaction rollback against an isolated database.
- Add a deterministic regression test for each bug fix.
- Add browser smoke coverage for sign-in, the primary create/edit flow, and the most important failure state when Playwright is configured.
- Test unauthorized, cross-workspace, duplicate, missing, and malformed cases, not only the happy path.
- Keep tests independent and deterministic; do not depend on production services or wall-clock timing.
- Assert behavior and public error contracts rather than implementation details.

Reason: the highest-value tests protect permissions, migrations, billing invariants, and user data rather than only increasing line coverage.

## Caching and rendering

- Decide explicitly whether data is static, revalidated, request-scoped, or always dynamic.
- Do not cache tenant-specific or permission-sensitive data under a shared key.
- Revalidate the narrowest path or tag after a write.
- Load data in the nearest Server Component that owns the view.
- Do not use useEffect for initial server data fetching.

Reason: explicit cache decisions prevent stale or cross-tenant data and keep App Router behavior understandable.

## Patterns to follow

- Thin pages, Route Handlers, and Server Actions calling typed services.
- Server Components for data fetching and Client Components isolated at interaction leaves.
- Prepared SQL, explicit constraints, short transactions, and immutable migrations.
- Integer minor units for money and UTC timestamps with one repository representation.
- Schema validation at every external boundary.
- Idempotent webhook/job processing with an outbox or unique event key.
- Audit rows for destructive, permission, and billing-related actions.
- Small focused modules with tests covering failure cases.

## What we do not do, and why

- Do not use SQL string interpolation. It creates injection risk and makes review unreliable.
- Do not call the database from Client Components. Secrets and authorization belong on the server.
- Do not use useEffect for initial data fetching. Server Components provide data with less client code and fewer races.
- Do not make every component a Client Component. It increases JavaScript cost and blurs the server boundary.
- Do not skip migrations with runtime CREATE TABLE IF NOT EXISTS. Schema state must be reviewable and repeatable.
- Do not edit an applied migration. Deployed databases would diverge from repository history.
- Do not use floating point for money. Rounding errors become accounting bugs.
- Do not trust hidden fields for authorization, pricing, ownership, or entitlements. A user can edit them in the browser.
- Do not create an internal API route for a mutation only the app UI needs. A Server Action is a smaller surface.
- Do not add an ORM, state library, or dependency for one awkward query. Keep the SQLite boundary direct unless a demonstrated need justifies change.
- Do not create a giant utils.ts or catch-all service. Domain ownership becomes unclear.
- Do not swallow errors or return success after a failed write. Callers need a truthful retryable state.
- Do not disable TypeScript, lint, security checks, or tests as a shortcut.
- Do not put secrets in logs, fixtures, screenshots, or public environment variables.

## Claude Code change workflow

1. Read the nearest route, component, service, query, migration, and tests before editing.
2. State the smallest behavior change and its trust boundaries.
3. Make the minimum coherent patch; do not refactor unrelated code.
4. For schema changes, add a migration and verify empty-database and upgrade paths.
5. Add or update tests for changed behavior and failure cases.
6. Run focused checks, then lint, typecheck, and build as appropriate.
7. Report exact commands and remaining risk in the pull request.
8. For auth, money, deletion, or callbacks, identify the server-side safety check before writing code.

## Definition of done

A change is complete when behavior is implemented, server-side authorization is enforced, input is validated, relevant tests cover success and failure, migrations are reproducible, lint/typecheck/build are clean when applicable, accessibility states are handled, and the implementation is understandable without undocumented assumptions.
