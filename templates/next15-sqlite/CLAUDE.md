# Working on this SaaS

## Runtime and commands

Use Next.js 15 App Router with React 19 and TypeScript. Run server code on Node.js 24. Use npm and commit the lockfile so a fresh checkout installs the same tree. Start with `npm ci`, `npm run dev`, `npm run build` and `npm start`. If creating the project from scratch, use `npx create-next-app@15 --ts --app --src-dir --use-npm`, then install `@libsql/client` and `server-only` with npm. Keep Next on a patched 15.x release for this template.

Use `@libsql/client` with a persistent local SQLite file. Default `DATABASE_URL` to `file:./app.db` in development. A local process can run this setup without a Turso account or a token. Ignore the database, its journal/WAL/SHM companions and local environment files in Git. Production requires persistent storage shared by the app and the migration runner. Use a single deployment owner for the local file. If deploying multiple isolated instances, decide how to share the database before shipping writes.

## Where code belongs

Keep route entry points in `src/app`. Use route groups such as `(account)` for organization without changing public URLs. Keep a route-specific UI under its own `_components/`. Put reusable components in `src/components/` once a second feature needs them. Use PascalCase for React exports, kebab-case for feature files, and Next's reserved filenames for framework entry points.

Keep connection creation in `src/server/db.ts`, with `import 'server-only'` as its first import. Export one client per process so rendering components do not repeatedly open the database. Put named query functions beside each feature in `src/server/<feature>/queries.ts`. Pass narrow data objects to the UI so a schema change stays local. Keep schema migrations under `db/migrations/` and the deploy-time runner under `scripts/`.

## SQL and releases

Use snake_case table and column names, integers for Unix timestamps in seconds, UUID strings for public IDs, and bind values through `client.execute({ sql, args })`. Bind the authenticated tenant ID on reads, updates and deletes. Derive it from the authenticated server-side session. Index tenant-scoped lookups starting with `tenant_id`, and use composite foreign keys for relationships that must stay within one tenant. Enforce foreign keys on each application and migration connection, then read the setting back to catch configuration drift.

Use immutable, ordered migrations such as `0001_create_projects.sql`. Record applied IDs in a `schema_migrations` table. Verify the applied prefix matches the release before applying pending files. Use a single migration job per release to serialize schema changes. Apply each migration and its ledger entry in one write transaction. A failure must roll back both. Keep migrations out of request handlers, module initialization and `next build` so builds can run in parallel and requests cannot race a deployment. Rehearse upgrades on a copy of the preceding schema and an empty database. Open and verify a restored backup before a destructive migration.

## Page and component pattern

Default to async Server Components. Read data directly through a server query. Use a small Client Component only for interaction that needs browser state, events or browser APIs. Keep credentials and database imports out of the client dependency graph. Await Next 15 request APIs, including `cookies()`, `headers()` and dynamic route `params`, before accessing their values.

Treat Server Actions and route handlers as public entry points. Parse input, authenticate, authorize the tenant and perform the write in that order. Check affected-row counts when updating or deleting a tenant-scoped row. Revalidate only after the transaction commits. Fetch user-specific rows per request. Global caches keyed only by a resource ID can leak data across sessions.

## What to verify before handing off

Run the app's configured type check, tests and `npm run build`. Read the package scripts first so a fresh scaffold never depends on imaginary commands. Exercise one successful write, an unauthenticated request, and an attempt by tenant B to read or edit tenant A's row. Check a second migration run is a no-op. Keep private inputs, database URLs and query arguments out of error reports.

For a new tenant-owned resource, make the migration first, add the tenant-scoped query and its negative test, then connect a Server Component or action to it. This order catches a missing isolation constraint before it reaches a route.
