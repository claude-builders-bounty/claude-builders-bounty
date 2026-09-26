# Project guide

This file is the working contract for a greenfield SaaS built with the Next.js 15 App Router and SQLite. Keep the repository's actual manifests and configuration as the source of truth; do not invent versions, scripts, or existing behavior.

## Stack and runtime

- Baseline: Next.js 15.5.x App Router, React 19.x, TypeScript 5.x in strict mode, and SQLite 3 through `better-sqlite3`. Keep the exact compatible patch versions in the lockfile; do not upgrade dependencies as part of an unrelated task.
- Use Node.js LTS, pinned in `.nvmrc` or `.node-version`, and declare the supported range in `package.json`.
- Default local SQLite driver: `better-sqlite3`, on the Node.js runtime. It is synchronous and native; never import it into a Client Component or run it in the Edge runtime. A Node-based serverless deployment is suitable only after verifying native-binary support, durable storage, and the expected concurrency model.
- Keep one SQLite implementation. If the repository uses Turso/libSQL, use its server-only remote client and documented connection, transaction, durability, and migration model. Do not add `better-sqlite3` or apply local database-file and WAL rules to a remote libSQL database.
- Use npm and commit `package-lock.json` unless the repository already has a different package manager and lockfile.

## Why these defaults

| Default | Reason |
| --- | --- |
| Pin exact dependency patches and Node.js in the repository | Native SQLite builds and framework behavior must match across local development, CI, and deploys. |
| Keep `better-sqlite3` on a Node.js server | It uses a native binding and synchronous file access; the Edge runtime cannot provide that contract. |
| Keep one database provider | A local file and a remote SQLite service have different durability and transaction boundaries; mixing them creates split-brain data. |
| Prefer Server Components and narrow Client Components | Database access and secrets stay server-side while browser JavaScript stays smaller. |
| Derive tenant identity from the session and include it in SQL | A guessed or leaked row ID must not grant cross-workspace access. |
| Add migrations instead of rewriting applied SQL | Shared databases need a reproducible history that does not depend on each developer's checkout. |
| Assume SQLite has one writer and needs persistent storage | A local file is not a horizontally shared database; deployments must preserve it and handle write contention. |
| Choose caching explicitly for user-specific data | Implicit caching can serve stale or incorrectly shared results. |
| Discover commands from `package.json` | Running invented scripts wastes time and can hide the checks the project actually uses. |

When adding a project rule, include the failure or cost it prevents. These defaults should be relaxed only when the actual deployment or codebase provides a safer, tested alternative.

## Inspect before changing

1. Read `package.json`, the lockfile, `next.config.*`, `tsconfig.json`, `.env.example`, the route tree, database modules, migrations, and relevant tests.
2. Follow existing conventions when they are consistent with this guide. Do not replace working libraries, rename broad parts of the app, or add dependencies for a one-off helper.
3. If a necessary fact is missing, inspect adjacent code and tests first. Make a small, reversible assumption when safe; ask only when the answer changes data ownership, security, or an irreversible operation.
4. Before editing, state the files and behavior that need to change. After editing, run the narrow relevant checks and then the repository's lint, type-check, test, and build scripts when available.

## Project layout

Keep routes thin and feature code close to the domain that owns it. Use this layout for a new project; do not move existing files solely to match it.

```text
src/
  app/
    (marketing)/             # public routes
    (app)/                   # authenticated product routes
    api/                     # HTTP integrations and webhooks
  components/
    ui/                      # reusable, domain-neutral UI
  features/
    <feature>/
      components/            # feature-specific UI
      schemas.ts             # input validation
      server/                # queries and mutations; server-only
  server/
    auth/                    # session and authorization helpers
    db/
      client.ts              # process-local connection
      migrate.ts             # ordered migration runner
      migrations/            # append-only SQL files
```

`page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`, and `route.ts` are Next.js entry points. Keep private helpers in `_lib/` or feature `server/` folders so their purpose and server boundary are visible. A route group such as `(app)` organizes layouts without changing the URL.

## Naming

- Route folders use lowercase URL segments. Dynamic segments use Next.js brackets, such as `[projectId]`.
- React components and component files use `PascalCase`; ordinary functions, variables, and server modules use `camelCase`.
- SQL tables and columns use `snake_case`; migration filenames use an increasing, sortable prefix, for example `0004_add_project_archive.sql`.
- Use domain terms consistently across routes, TypeScript types, validation schemas, and SQL. Do not abbreviate names unless the abbreviation is established in the codebase.
- Prefer specific types and narrow return values. Do not add `any` to work around a type error.

## Server and client components

- Pages and layouts are Server Components by default. Read data near the source on the server; this keeps credentials and database code out of the browser bundle.
- Add `'use client'` only to the smallest component that needs state, event handlers, effects, or browser APIs. Keep the rest of its parent tree on the server.
- Pass serializable display data to Client Components, never a database handle, secret, session token, or privileged server object.
- Put database and credential-bearing modules behind `import 'server-only'` where supported. Only values intentionally safe for browsers may use the `NEXT_PUBLIC_` prefix.
- Routes and mutations that import `better-sqlite3` must explicitly use the Node.js runtime (for example, `export const runtime = 'nodejs'`). Do not move them to Edge to solve unrelated performance or deployment problems.
- In Next.js 15, treat dynamic route `params` and `searchParams` as promises and `await` them. Confirm the exact installed Next.js minor version before copying APIs from newer documentation.

## Data access and tenant boundaries

- Keep SQL in server-only feature query/mutation modules or a small shared repository layer. Pages, Client Components, and UI components must not issue SQL.
- Use prepared statements with bound values for all data values. For dynamic sort columns or SQL identifiers, map an allow-listed enum to fixed SQL text; never interpolate raw request data.
- Validate every form, Server Action, and Route Handler input on the server. A TypeScript type or browser-side validation is not a trust boundary.
- Authenticate first and authorize every operation on the server. Derive the active user and workspace from the verified session; never trust a submitted `user_id`, `workspace_id`, or owner field.
- Scope each tenant-owned read, update, and delete by the authenticated workspace/user in the SQL predicate. Add composite unique constraints and indexes that include the tenant key where needed. This prevents a valid ID from another tenant being enough to access a row.
- Return only fields the caller needs. Do not log credentials, session material, raw payment details, or full customer records.
- Keep mutation behavior explicit: validate, authenticate, authorize, write, then revalidate or redirect after the transaction commits. Never report success before the write succeeds.

## SQLite and migrations

### Local `better-sqlite3` database

- Store the database file outside `public/` and source control. Read its path from a server-only environment variable; provide a safe local default only for development and tests.
- Reuse one connection per Node.js process and preserve that singleton across Next.js development hot reloads. Set `PRAGMA foreign_keys = ON` for every connection and verify it in the database setup test; SQLite does not enable foreign-key enforcement by default on every connection.
- Use WAL mode only when the persistent local storage supports it. Set a bounded busy timeout. SQLite allows one writer at a time: document persistent-volume and backup requirements, and do not put the file on an ephemeral serverless filesystem or a shared network drive.
- Do not assume that a Node-based serverless filesystem is durable. Use this local-file setup in production only when the deployment can preserve the file and meet the app's concurrency requirements.

### Remote Turso/libSQL database

- Keep the remote database URL and credentials server-only. Do not require a local database path, a process-local native SQLite connection, or local-file WAL configuration for this provider.
- Follow the selected libSQL driver's documented connection reuse, transaction, retry, durability, backup, and migration behavior. Verify which SQLite pragmas and migration statements that provider supports before relying on them.

### Rules shared by both providers

- Run migrations as an explicit deployment step before serving traffic, not from a page request or on every serverless cold start. Record applied migration IDs in a migration table.
- Add a new ordered migration for every schema change. Never edit a migration that has reached a shared environment; correct it with a new forward migration.
- Make each migration transactional when the selected provider supports the statements involved. Do not perform network calls or unrelated asynchronous work inside a transaction.
- Include constraints in the schema (`NOT NULL`, `UNIQUE`, `CHECK`, and foreign keys) so invalid data cannot enter through a path that bypasses application validation.
- Use integer minor units for money and store the ISO currency code separately. Use one UTC timestamp representation consistently; prefer ISO-8601 UTC text for audit fields.
- Test migrations against an isolated database using the same driver as the application. Run migrations twice and verify the resulting schema; for SQLite engines that support them, also run `PRAGMA foreign_key_check` and `PRAGMA integrity_check`.

## Mutations, transactions, and caching

- Use a Server Action for a form mutation that belongs to the app UI. Use a Route Handler for webhooks, public HTTP APIs, or integrations with explicit HTTP semantics.
- Keep `better-sqlite3` transactions synchronous: do not `await`, call remote services, send email, or publish jobs from inside the transaction callback. For remote libSQL, use the driver's documented transaction API, keep the transaction short, and never hold it open while waiting for an unrelated remote service.
- Commit database state before sending external effects. If an effect must reliably follow a write, use an outbox/job record and process it separately.
- Do not assume a route or query is cached or uncached. Read the installed Next.js version and current route configuration, then choose and test cache/revalidation behavior explicitly for user-specific data.

## Commands

Read the actual `scripts` in `package.json` first; use the package manager that owns the lockfile. For a greenfield npm project, define and use these script names:

```sh
npm run dev
npm run lint
npm run typecheck
npm test
npm run db:migrate
npm run build
npm run start
```

`typecheck` should run `tsc --noEmit`; `db:migrate` should run the migration runner against the explicitly configured local/test database. If any script is absent, say so and add the smallest appropriate script only when the task requires it. Never point tests or local migration commands at production.

## Avoid

- Do not put database access, secrets, authorization decisions, or privileged mutations in Client Components.
- Do not use `better-sqlite3` in the Edge runtime. Use it in a serverless Node.js deployment only after verifying native-module support, durable storage, and concurrency; otherwise use a remote provider such as Turso/libSQL.
- Do not apply local-file path, WAL, or native-connection rules to a remote libSQL database.
- Do not build SQL by concatenating user input, trust IDs submitted by the browser, or treat hidden UI controls as authorization.
- Do not use `as any`, disable strict checks, or swallow database errors to make a build pass.
- Do not add `'use client'` to an entire route tree for one interactive widget.
- Do not edit applied migrations, reset a shared database, delete production data, or run migrations against an unverified database path.
- Do not perform slow work inside a synchronous SQLite transaction, or hold a transaction open while waiting on an external service.
- Do not change caching, package versions, database providers, or authentication behavior without tracing the existing contract and testing the affected user path.

## References

- [Next.js 15 project structure](https://nextjs.org/docs/15/app/getting-started/project-structure)
- [Next.js 15 Server and Client Components](https://nextjs.org/docs/15/app/getting-started/server-and-client-components)
- [Next.js 15 Route Handlers](https://nextjs.org/docs/15/app/api-reference/file-conventions/route)
- [Next.js 15 forms and Server Actions](https://nextjs.org/docs/15/app/guides/forms)
- [better-sqlite3 usage](https://github.com/WiseLibs/better-sqlite3#usage)
- [SQLite foreign-key support](https://www.sqlite.org/foreignkeys.html)
- [SQLite transactions](https://www.sqlite.org/lang_transaction.html)
