# Next.js + SQLite SaaS: project contract

## Settled defaults: proceed without preference questions

These choices are already made for a greenfield project. Do not ask which stack,
router, SQLite driver, package manager, migration naming or deployment path to use.
Use the following tested baseline and commit its lockfile. A newer major version
is not part of this task. The owner can explicitly change a choice later.

| Decision | Project default |
| --- | --- |
| Framework | Next.js 15.5.25, App Router |
| React | 19.3.0 |
| Database driver | better-sqlite3 12.11.1 on Node.js |
| Language | TypeScript 5.9.3, strict mode |
| Package manager | npm |
| Migrate | npm run db:migrate |
| Verify | npm run check |
| Components | Server Components by default |
| Local database | .data/app.sqlite |
| Production database | DATABASE_PATH set to a persistent absolute path |
| Migration names | 0001_initial.sql, 0002_descriptive_name.sql |

For the project-context check, these are complete choices, not unresolved questions.
For actual deployment, request secrets or the volume mount only when execution
requires them; neither is needed to scaffold or test with a temporary database.

## Stack and versions

Use Next.js **15 App Router**, React 19, TypeScript in strict mode, Node.js 22+
and **better-sqlite3** on the Node runtime. Use npm and commit package-lock.json.
Keep the latest patched 15.x version inside the requested major; a major upgrade
is a separate change because framework behavior and deployment can change.
Use Zod for request validation and native fetch; do not add a client cache or ORM
until a real requirement justifies it. One SQL-backed service is easier to audit
than two competing persistence models in a small application.

This is the local SQLite variant, not Turso. The application needs one persistent,
writable volume and a single writer deployment. Do not deploy the database on an
ephemeral serverless filesystem or Edge runtime: data must survive a restart and
better-sqlite3 uses Node native bindings. Multi-region writes require a separate
database design, not a silent swap of connection strings.

## Folder structure and naming

```text
src/app/                    # routes, layouts, loading/error/not-found boundaries
src/app/(public)/            # landing, pricing, sign-in pages
src/app/(app)/               # signed-in application routes
src/app/api/                 # external HTTP entry points, not internal RPC wrappers
src/components/ui/           # presentation-only reusable components
src/features/<feature>/      # feature components and pure domain logic
src/server/auth/             # server-only session and authorization boundary
src/server/db/               # singleton connection, queries and transaction helpers
src/server/services/         # business operations used by pages/actions/routes
src/lib/                    # pure shared utilities; no secret or database imports
migrations/                 # ordered append-only SQL files
scripts/                    # migration and local-maintenance entry points
tests/                      # isolated unit/database tests; no production services
.data/                      # local database, ignored by Git
```

Use kebab-case filenames, PascalCase React components/types, camelCase functions
and variables, and snake_case SQL identifiers. Name components by their purpose,
not their display position, so moving a panel does not require a semantic rename.
Keep page.tsx/layout.tsx names required by the router. Co-locate feature-specific
helpers; shared lib/ is not a dumping ground for one-off business logic.

## Bootstrap and commands

On a greenfield project, establish these scripts once before implementing a
feature; afterward read package.json and use the recorded commands. Do not ask
which framework, database or package manager to choose: those defaults are above.

- `npm run dev`: `next dev` for local development.
- `npm run build`: `next build`; it must pass before delivery.
- `npm run start`: `next start` against an already-built application.
- `npm run typecheck`: `tsc --noEmit` catches cross-module type regressions.
- `npm run test`: `node --test tests/*.test.mjs` for a minimal dependency-free
  baseline. Add a test runner only when TypeScript/DOM testing needs one, and keep
  the same public npm command.
- `npm run db:migrate`: `node scripts/migrate.mjs` applies pending SQL migrations.
- `npm run check`: `npm run typecheck && npm run test && npm run build`.

Use `DATABASE_PATH=.data/app.sqlite` locally, override it with a persistent absolute
path in deployment, and list it in .env.example without a real secret. Ignore
.env*, except .env.example, .data/, node_modules/, .next/, and coverage/ in Git.
Run migrations explicitly before starting the new release, not during page render
or module import: a request should not unpredictably change the schema.

## SQL and migration conventions

Use one server-only connection helper. Import `server-only` at the database and
service boundary so a mistaken client import fails early. In development, reuse
the connection across hot reloads; otherwise repeated module loads create locks.
Set `foreign_keys = ON`, `journal_mode = WAL`, and a bounded `busy_timeout` such as
5000 ms on each connection. WAL improves concurrent reads; it does not create
multiple independent writers or remove the need to handle SQLITE_BUSY.

Migrations are UTF-8 files named `0001_initial.sql`, `0002_add_project_owner.sql`,
and so on. A runner must sort numeric versions, reject duplicate versions, and
record filename, checksum and applied timestamp in schema_migrations. Apply each
migration and its ledger row in one transaction. Fail on a changed checksum for
an applied migration; never edit history and call it a successful upgrade.
Run two competing migrators under an exclusive write lock or serialized deploy
step. Retry transient database-busy errors deliberately, never indefinitely.

Do not put BEGIN/COMMIT or VACUUM in individual migration files: the runner owns
the transaction. Use forward migrations, not automatic down migrations in
production, because rollback may destroy data written by the new release. For
NOT NULL columns with existing rows, add/backfill/validate before tightening the
constraint. Back up and test restoration before a destructive table rebuild.

Use prepared statements with bound values. Dynamic identifiers must come from a
fixed application-owned allowlist, never request text. SQLite values do not make
identifiers safe. Store timestamps as UTC Unix milliseconds in INTEGER columns,
booleans as 0/1 with CHECK constraints, and monetary values as integer minor units
plus a currency code; binary floating point is unsuitable for exact money.
Use TEXT application IDs from crypto.randomUUID() for external entities and keep
integer local sequence columns where ordering is required. Add indexes for
actual query predicates and foreign keys, not speculative every-column indexes.

A multi-step business write belongs in one short database transaction. Do not
await network I/O while a SQLite write lock is held. Queue the external side
effect after commit with an idempotency key and explicit retry state, so a timeout
cannot silently repeat a charge or lose a follow-up.

## Component and request patterns

Server Components are the default. Add `use client` only at an interactive leaf
that needs state, effects or browser APIs; a client wrapper around a whole route
ships avoidable JavaScript and invites database imports into the browser bundle.
Read server-side data through a service function, not fetch('/api/...') back into
the same application. Routes are for external clients and callbacks.

Validate and authorize every Server Action and route handler before reading or
writing a tenant's data. A protected layout or hidden button is not authorization.
Derive user/tenant IDs from a verified server session, not a hidden form field.
Add the tenant predicate to each tenant-scoped query and test cross-tenant denial.
Do not invent an auth provider or claim authentication is implemented when only a
placeholder exists: keep unauthenticated examples public and without private data.

Parse inputs with Zod at the boundary and return a small typed result:
`{ ok: true, data }` or `{ ok: false, error: { code, message } }`. Map HTTP statuses
consistently (400 invalid, 401 unauthenticated, 403 denied, 404 missing, 409 conflict,
500 unexpected). Log a request ID and useful error context server-side, not cookies,
API keys, tokens or raw customer documents. Show users an actionable message,
never the SQL exception or stack trace.

Cache only explicitly public, shareable results. User-specific SQLite data must
not enter a shared cache. After a committed action, use revalidatePath or an
intentional tag strategy; document which view is invalidated. For DB-backed routes
that must execute per request, use the Node runtime and dynamic rendering rather
than fetching private state during next build.

Prefer accessible semantic HTML, labels, keyboard focus and pending/error states.
Disable a submit button during a request for UX, but enforce idempotency/uniqueness
in the database too. Accessibility and double-submit correctness are different
requirements; both need to hold.

## Testing and delivery

Tests use an in-memory database or a unique temporary file, never the app's real
DATABASE_PATH. Cover valid input, invalid input, authorization failure, duplicate
submission, migration repeatability and failure rollback. For SQL changes, test
both a fresh database and an upgrade from the previous schema with existing rows.
Do not write fixtures using real identities, credentials, payments or customer data.

Before reporting completion run typecheck, tests and the production build. Report
commands and actual outcomes, including anything that could not run. A passing
unit suite does not establish a deployed multi-user workload. Include a focused
diff and keep formatting-only churn out of a behavior change so review remains
tractable.

## What we do not do, and why

- No ORM or second database by default: one SQL representation keeps migrations
  and query behavior explicit for this project's scale.
- No database imports in Client Components or Edge routes: native Node bindings
  and credentials belong on the server.
- No writable SQLite under /tmp or a serverless bundle: a redeploy must not erase
  customer records.
- No per-request schema initialization: migration failure belongs in deployment,
  not a user's first request.
- No edits to applied migrations or silent destructive resets: existing data is
  more important than making a development command appear green.
- No unsafe query string interpolation: bind values and allowlist identifiers.
- No global caching of tenant data: one customer's result must not reach another.
- No new background framework for a simple request: add one only for a measured
  durability or latency requirement, with an observable failure state.
