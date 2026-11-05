# Next.js 15 + SQLite SaaS

## Stack and Versions

- Use Next.js 15 App Router, React 19, TypeScript 5 strict mode, Node.js 22 LTS or newer supported LTS, and npm. Stay within these major versions and use patched releases; the package lock is the exact-version authority, so upgrades remain reviewable.
- Use `@libsql/client` for SQLite locally and Turso remotely. Do not add a second driver or ORM: one asynchronous query contract avoids differing transaction behavior between development and production.
- Default to a local `file:./data/app.db` database. Use server-only `DATABASE_URL` and optional `DATABASE_AUTH_TOKEN` for configured deployments; a local file needs no token. Create `data/` before opening the file, because SQLite cannot create parent directories.
- Keep `.env*`, database files, WAL/SHM sidecars and backups out of Git except a redacted `.env.example`; they can contain customer data or credentials. Never prefix database credentials with `NEXT_PUBLIC_`, because those values are sent to browsers.
- Local file SQLite requires a writable persistent volume and one application writer deployment. Use remote Turso for ephemeral or horizontally scaled hosting; copying an SQLite file between replicas is not replication. Never claim a deployment is production-ready merely because it builds.

## Folder Structure and Naming

```text
src/app/                    routes, layouts, loading/error/not-found boundaries
src/app/(app)/              signed-in UI grouping, not an authorization boundary
src/app/api/                external HTTP integrations and verified webhooks
src/components/             shared presentation components
src/features/<feature>/     feature UI and its schemas
src/server/auth/            session verification and membership lookup
src/server/db/              server-only client and parameterized queries
src/server/services/        business operations shared by actions and routes
migrations/                 immutable numbered SQL files
scripts/                    migration and maintenance entry points
tests/                      isolated database and request-boundary tests
data/                       local-only SQLite files, ignored by Git
```

- This is a greenfield layout: create each directory only when the first relevant file is needed, because empty abstractions make navigation harder. Preserve framework-reserved filenames such as `page.tsx`, `layout.tsx`, `route.ts`, `loading.tsx` and `error.tsx`.
- Use kebab-case application filenames, PascalCase component/type names, camelCase functions and variables, and snake_case SQL tables/columns. Predictable boundaries make imports and queries searchable.
- Put `import 'server-only'` in application database and auth modules. Only server modules may import them, so client bundle leakage fails at build time rather than at runtime. A standalone migration script may import the driver directly; it is not a Client Component.

## Commands and First Run

- Inspect `package.json` before running commands: do not claim a missing script exists. Existing scripts and the lockfile take precedence over these greenfield defaults, because reproducible builds depend on the actual project.
- Install missing greenfield dependencies with `npm install next@15 react@19 react-dom@19 @libsql/client server-only --legacy-peer-deps` and `npm install --save-dev typescript@5 @types/node@22 @types/react@19 @types/react-dom@19 --legacy-peer-deps`. Commit the resolved lockfile and review the audit report; do not use `npm audit fix --force` to change major versions silently.
- Use `npm exec -- next dev` for development, `npm exec -- tsc --noEmit` for types, `npm exec -- next build` for a production build, and `npm exec -- next start` to inspect that build. These commands do not depend on invented npm script names. Run the existing lint/test scripts if present; report absent test infrastructure rather than pretending it passed.
- Create `scripts/migrate.mjs` according to the migration contract below before using `node scripts/migrate.mjs`. A missing script is implementation work, not a reason to run ad hoc schema changes. Keep migrations separate from `next build` and request handling so a build or GET request cannot mutate a production database.
- Default product decisions to the stated stack and local database without clarification. Ask only about a material missing business rule, destructive operation or deployment permission; guessing tenant membership or production access is not a harmless default.

## SQL and Migration Conventions

- Use positional bind parameters for values and an explicit allowlist for dynamic identifiers/order clauses. Parameters cannot bind table names, so interpolating request-supplied identifiers is not safe.
- Use text UUID primary keys, integer UTC epoch milliseconds for timestamps, integer minor units plus a currency code for money, and integer booleans with `CHECK (value IN (0, 1))`. These choices avoid floating-point money and ambiguous timezone/boolean storage. Preserve existing schema conventions during a narrow change instead of converting old data opportunistically.
- For tenant-owned records, require `tenant_id` and query/update/delete by both the verified tenant and record ID. Resolve membership from the authenticated session on the server, not from FormData, URL parameters or a hidden field; possession of an ID does not authorize access.
- Where child rows refer to tenant-owned parents, use a unique parent `(tenant_id, id)` key and a composite foreign key containing both columns. A globally valid parent ID must not create a cross-tenant relationship. Enable and verify foreign-key enforcement for the actual adapter/connection and test rejection; do not assume a PRAGMA sent on one pooled connection configures another.
- Name migrations `0001_description.sql`, `0002_description.sql`, and so on. Applied files are immutable; store version, SHA-256 checksum and applied timestamp in a migration ledger, and reject changed checksums, missing applied files, duplicate versions or out-of-order insertion. Otherwise a fresh database and an upgraded database can silently disagree.
- Use one serialized migration writer. Re-read the ledger after acquiring the write transaction and execute the migration plus ledger insert atomically on that transaction. Roll back on failure and always close the transaction. Do not split SQL with `text.split(';')`: semicolons can occur in strings and trigger bodies; use the driver's SQL script API. Do not put transaction-control statements in migration files, because the runner owns the transaction.
- New tenant-scoped reads need a matching composite index, normally beginning with `tenant_id`; validate query plans for large tables rather than adding indexes to every column. Unbounded reads become latency and memory failures as a SaaS grows.
- Prefer additive expand/backfill/contract migrations. Destructive SQL requires explicit approval, a tested restore/backup plan and evidence of compatibility with the deployed app; never reset or delete a production database to fix a migration error.

## Component and Mutation Patterns

- Use Server Components by default and add `'use client'` only at the smallest boundary needing browser state or event handlers. This limits shipped JavaScript and prevents accidentally moving database work into a browser.
- Server Components call server services directly rather than fetching the app's own API; an internal HTTP round trip adds latency and duplicates authentication plumbing.
- Every Server Action and Route Handler is an entry point: validate input, authenticate, authorize the resource/tenant, perform a bounded transaction, then invalidate the affected data. A route group, hidden button or layout check is not authorization for the action endpoint.
- Await `cookies()`, `headers()`, and asynchronous route `params`/`searchParams` in Next.js 15. Keeping the asynchronous contract avoids relying on deprecated synchronous compatibility.
- Keep transactions short and database-only. Do not await email, billing or other network work while holding a write transaction; SQLite has a single writer. For durable side effects, insert an outbox record in the same transaction and process it separately with retries/idempotency.
- Do not globally cache authenticated tenant data. Make tenant identity part of any deliberate cache key and invalidation policy, or keep the request dynamic; a shared cache can leak one customer's data to another.
- Return explicit, serializable success/error results and show pending, validation, empty and failure states. Do not return raw database exceptions, tokens, full rows or stack traces to the client; clients need a stable contract, not implementation details.

## What We Do Not Do, and Why

- No SQL or database credentials in Client Components, no Edge runtime for local-file SQLite, and no file database on ephemeral deployment storage: these cross runtime or persistence boundaries.
- No schema push/reset on production, in-place edits to applied migrations, or swallowed migration failures: these destroy migration history or create false success.
- No trusting client-supplied tenant IDs, client-only access checks, or authorization only in middleware/layouts: callers can reach actions and handlers directly.
- No `any` to suppress a boundary error, disabled type checks to make a build green, or unrelated formatting/refactors: these conceal defects and enlarge review scope.
- No real customer data in fixtures, plaintext secrets in logs, automatic deploy/payment/email actions, or live credentials during tests: test evidence must not create production side effects.

## Completion Evidence

- For a database change, test a fresh migration, a second no-op run, an upgrade from the previous schema, checksum drift rejection, rollback after a failing statement, and foreign-key enforcement. Each catches a distinct fresh-install versus upgrade failure.
- For tenant CRUD, test authorized access plus unauthenticated, wrong-tenant and tampered-identifier requests, and prove rejected writes leave rows unchanged. A successful happy-path request does not establish isolation.
- Run available type, lint, test and build checks. Record exact commands, results and any untested platform/remote behavior; do not convert a local SQLite check into a claim that remote Turso, authentication, billing or deployment was tested.
