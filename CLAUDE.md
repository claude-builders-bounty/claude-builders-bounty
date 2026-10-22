# Next.js + SQLite SaaS engineering contract

This file is the starting contract for a greenfield, single-region Next.js SaaS. Use these defaults without asking the owner to choose architecture. Ask only when a requested feature leaves an actual product or security decision unspecified. Never invent completed tests or authentication.

These are target conventions, not evidence that any named file already exists. Inspect the scaffold first. In an empty project create the connection, migration runner and tests before adding feature migrations; never assume an existing workspace schema or session adapter.

## Stack and deployment

- Next.js 15 App Router, React 19, TypeScript strict, Node.js 22 LTS, npm with committed package-lock.json. Use a patched 15.x release; no canary versions. Inspect the lockfile before using a version-sensitive API.
- SQLite through better-sqlite3, using parameterized SQL rather than an ORM. This template chooses local SQLite, not Turso; do not mix their drivers or transaction APIs.
- Node runtime only for database routes: `export const runtime = 'nodejs'`. Never import the database from Edge middleware or client components.
- Production is one persistent Node service with a durable local volume. Do not deploy the writable database to ephemeral/serverless storage or a shared network filesystem. Replicas require a separately reviewed database architecture.
- `DATABASE_PATH` defaults to `./data/app.db` locally. Ignore data files, journals, secrets and `.env*` except a values-free `.env.example`. Do not print database rows or credentials in logs.

## Directory layout and names

```text
src/app/                    App Router pages, layouts and route handlers
src/app/(public)/           marketing and sign-in surfaces
src/app/(app)/              authenticated product surfaces (route groups are NOT auth)
src/components/ui/         reusable visual primitives
src/features/<feature>/    feature-specific server logic and components
src/lib/db.ts              server-only SQLite connection factory
src/lib/auth.ts            server-only session and membership boundary
src/lib/errors.ts          typed domain errors / safe public mapping
db/migrations/             immutable numbered SQL files: 0001_initial.sql
scripts/migrate.ts         explicit deployment-time migration command
tests/                     integration and authorization tests
data/                      local ignored database files
```

Use kebab-case filenames except framework filenames, PascalCase React components, camelCase TypeScript values, snake_case SQL identifiers, and singular domain type names. Keep SQL in server-side repository functions near its feature. Route handlers validate and delegate; they do not contain business workflows.

## Commands and initial bootstrap

If starting in an empty repository, scaffold Next.js 15 with TypeScript, App Router and `src/`; add better-sqlite3, its types and tsx. Create these npm scripts and preserve their meanings:

| Command | Meaning |
|---|---|
| `npm run dev` | `next dev` |
| `npm run build` | `next build` |
| `npm start` | `next start` |
| `npm run typecheck` | `tsc --noEmit` |
| `npm run db:migrate` | `tsx scripts/migrate.ts` |
| `npm test` | `tsx --test tests/*.test.ts` |

Install with `npm ci` after the lockfile exists. Run migrations explicitly before starting the service, never during module import, rendering, or a production build. Before proposing a PR run migration replay tests, typecheck, tests and build. Report exact commands and failures. A build passing does not prove runtime authorization.

## SQLite connection and transactions

- Mark database modules `import 'server-only'`. Reuse one connection per process (including a `globalThis` cache in development); do not open a new connection per request.
- Configure `foreign_keys = ON`, `journal_mode = WAL`, `busy_timeout = 5000` for each file-backed connection. Configure these outside active transactions. WAL allows concurrent readers, not unlimited writers.
- Enable constraints in the schema, including tenant ownership. Use bound parameters for every value; allowlist dynamic column names because SQL identifiers cannot be bound.
- Use `db.transaction(...)` for multi-step mutations. better-sqlite3 transactions must be synchronous: no `async` callbacks, no network calls or `await` inside them. Prepare external work first, then commit a short transaction.
- Use ISO-8601 UTC timestamps consistently and integer minor units plus a currency code for money. Use UUID text IDs and NOT NULL constraints. Never use floating point for charges.
- Do not automatically retry non-idempotent writes. Return a safe retryable error on lock contention; use a unique idempotency key where business retries are needed.

## Migrations

- SQL files have increasing four-digit prefixes and descriptive names. Apply them in lexical order. Never edit a migration already released; add a new one.
- The runner creates `_migrations(name TEXT PRIMARY KEY, checksum TEXT NOT NULL, applied_at TEXT NOT NULL)`, computes SHA-256 over each file, and refuses changed checksums or duplicate prefixes.
- Acquire a SQLite write transaction before checking pending migrations; re-read the migration ledger under that transaction so concurrent runners cannot both apply a migration. Apply each SQL file and its ledger row atomically. Roll back both on failure.
- Schema SQL must not contain its own BEGIN/COMMIT, connection PRAGMAs, or external side effects. The runner owns the transaction. Fail on unknown ledger entries rather than silently accepting a partial migration directory.
- Test a fresh database, a second no-op run, checksum drift and a failing migration rollback using temporary files. Never use a developer or production database in tests.
- Before a production migration, take a SQLite-consistent backup using the backup API or stop the service; copying only the live `.db` while WAL is active is not a valid backup. Prefer forward repairs. Destructive migrations require an explicit retention/backup plan.

## Authentication and tenant boundaries

- Until a real session adapter is configured, protected operations fail closed with 401. Do not create a pretend user, hard-coded workspace, or trust an `x-user-id` header to make a demo work.
- Session cookies are HttpOnly, Secure in production, SameSite=Lax; rotate on login and revoke on logout. Never store credentials in localStorage. Do not implement password cryptography from scratch.
- Resolve authenticated user and workspace membership on the server for EVERY read and mutation. Client IDs, route groups and middleware redirects are not authorization.
- Scope every tenant-owned query by workspace_id derived from verified membership. Mutation queries include both id and workspace_id. Cross-tenant misses return 404 without revealing whether another tenant owns the record.
- Cookie-authenticated mutations validate Origin against the configured application origin and use the framework's supported CSRF protections. GET handlers never mutate data. Webhooks verify provider signatures and deduplicate event IDs before applying state.
- Tests must prove anonymous rejection, same-tenant success, cross-tenant read/mutation denial, invalid input rejection and rollback on partial failure.

## Components, validation and caching

- Server Components are the default. Use `use client` only for interaction; pass minimal serializable view models, never database handles, secrets or raw account records.
- Prefer server-rendered reads. Use a route handler for external API access; use Server Actions for app form mutations when appropriate. Both call the same validated server-side feature functions and enforce auth themselves.
- In Next.js 15, await asynchronous `cookies()`, `headers()` and route params as required by the installed version. Keep runtime database access out of build-time prerendering.
- Validate untrusted input at the server boundary with a schema. Bound lengths, page size (maximum 100) and sort choices. Return field errors for expected validation failures; log unexpected errors with an opaque request ID, not payloads.
- Tenant data is not globally cached. Use request-local reads initially; if adding caching, include the tenant and authorization context in keys and explicitly invalidate after mutations.
- Provide accessible labels, pending states, keyboard operation, error messages and empty states. Disable duplicate submit UI but enforce idempotency on the server too.

## Default workspace CRUD behavior

For a new internal workspace record feature with no further product requirements, use these defaults and state them in the plan rather than asking a round of setup questions:

- Verified workspace members can read records in their workspace. Only the record's creator may update or archive it; check both membership and creator identity server-side. No public sharing or collaborator editing unless explicitly requested.
- Plain text title and body, with limits of 200 and 100,000 characters respectively. Render as text, not HTML or Markdown. Rich text is an explicit feature, not an implicit dependency.
- Delete means soft archive with a nullable `archived_at` UTC timestamp; exclude archived records from normal reads. Permanent purge and retention policies are out of the initial scope and require an explicit product request.
- Sort newest first using `(created_at, id)` for stable pagination, default page size 25 and maximum 100. Use last-write-wins initially; do not silently add realtime collaboration.
- If user requirements contradict these defaults or involve regulated retention/payment workflows, identify the specific conflict. Otherwise proceed using the defaults, with protected operations remaining closed until real authentication exists.

## What we do not do (and why)

- No generated SQL from user strings: injection and uncontrolled query cost.
- No client-only role checks: requests bypass the UI.
- No automatic schema synchronization: it loses reviewed migration history.
- No new database/ORM/auth stack without a concrete need: mixed abstractions obscure transaction and authorization guarantees.
- No payments or external email calls in tests: use explicit local fakes and verify their inputs.
- No speculative abstractions or broad rewrites for a small feature: keep review and regression scope bounded.
- No suppressing type/test errors or claiming unexecuted checks passed: reviewers need reproducible evidence.

For each change, first inspect existing files, state a short implementation plan using these defaults, then implement and validate. If a command cannot run, report the actual blocker and leave that check unverified.
