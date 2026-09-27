# Next.js 15 + SQLite SaaS

Use this guide for a small production SaaS built with the Next.js App Router and `better-sqlite3`. Follow the repository's existing conventions when they are already established. If a requirement is missing but a safe, reversible choice is available, make that choice and state it; ask only when the missing detail changes product behavior, authorization, or data handling.

## Stack

- Next.js 15 App Router, React 19, TypeScript 5 with `strict: true`.
- Node.js 22 or newer. Use the Node runtime for every route that imports SQLite.
- `better-sqlite3` 13 for a local, single-instance database. Keep it behind a server-only module. Choose Turso/libSQL instead when the app needs remote access or multiple application instances; do not mix both drivers.
- Zod for input validation and Vitest for unit and integration tests.

Pin dependency versions in the lockfile. Check installed package types and documentation before using an API; do not assume a different Next.js major's caching or route behavior.
Run `npm audit` before release. Prefer an upstream patched release; use a compatible, tested transitive override when the requested framework major has not yet updated its dependency, and record any issue that cannot be resolved safely.

## Layout and names

```text
src/app/                   routes, layouts, loading/error/not-found UI
src/components/            shared UI; add client components only for interaction
src/lib/server/db.ts       SQLite connection and pragmas
src/lib/server/services/   domain operations and queries
src/lib/validation/        shared Zod schemas
db/migrations/             ordered, immutable SQL migrations
scripts/                   explicit database and maintenance commands
tests/                     unit and database integration tests
```

- Use `kebab-case` for route segments and filenames, `PascalCase` for React components and types, and `camelCase` for functions and variables.
- Keep SQL and domain rules in server-side service modules. Pages and components should compose results, not own persistence logic.
- Prefer small named exports. Keep route handlers thin and call the same service functions used by other server entry points.

## SQLite and migrations

- Store the database at `DATABASE_PATH`; default local development to `.data/app.sqlite`. Create its parent directory before opening it and keep `.data/` out of version control.
- Set `PRAGMA foreign_keys = ON` and a bounded `busy_timeout` on each connection. Use WAL for a persistent local database; do not rely on WAL files in ephemeral/serverless storage.
- Create one connection per Node process and reuse it. Use prepared statements for values; never interpolate user input into SQL. Add indexes for query patterns and declare foreign keys and uniqueness in the schema.
- Put every schema change in a new numbered SQL file. Applied migrations are immutable. A migration runner must create a `schema_migrations` table, apply each pending migration in a transaction, record its identifier only after success, and stop on the first failure.
- Run migrations explicitly with `npm run db:migrate`, before serving traffic during a release. Do not run them on module import, per request, or from a Next.js build step.
- Use additive changes when possible. For a destructive or long-running change, write a forward/backward data plan and test it against a copy before rollout.
- Keep local SQLite to a single persistent application instance. For multiple replicas, serverless functions, or shared remote writes, use Turso/libSQL rather than placing a SQLite file on ephemeral or shared network storage.

## Next.js patterns

- Server Components are the default. Add `'use client'` only at the smallest interactive boundary; never import database code into a client module.
- Read through server-side services. For writes, use a Server Action for UI-originated mutations or a Route Handler for an HTTP API. Both must authenticate, authorize the specific resource, validate input with a shared schema, and return a deliberate success/error shape.
- Set `export const runtime = 'nodejs'` on any route segment that uses `better-sqlite3`; SQLite cannot run in the Edge runtime.
- Choose caching explicitly for data reads. If a page or handler depends on fresh database state, opt out of caching and revalidate after a successful write. Do not rely on defaults inherited from another Next.js version.
- Return plain serializable values from server boundaries. Do not pass database handles, statements, or `bigint` values to Client Components.
- Keep secrets server-side in environment variables. Commit `.env.example` with names and safe placeholders only; never log credentials, session tokens, or unnecessary personal data.

## Commands and checks

Keep these scripts available and update them if the project uses different tooling:

```json
{
  "dev": "next dev",
  "build": "next build",
  "start": "next start",
  "lint": "eslint .",
  "typecheck": "tsc --noEmit",
  "test": "vitest run",
  "db:migrate": "tsx scripts/migrate.ts",
  "db:check": "tsx scripts/check-db.ts"
}
```

Before finishing a change, run the narrowest relevant tests, then `npm run lint`, `npm run typecheck`, and `npm run build` when the environment supports them. For a migration, test both a fresh database and an upgrade from the previous schema. Report commands that could not run and why; never describe an unrun check as passing.

## Avoid these patterns

- **No SQLite in client code or Edge routes:** the driver requires Node APIs and can expose data outside the server boundary.
- **No local SQLite file on ephemeral storage or multiple replicas:** writes can disappear or diverge; use Turso/libSQL for shared access.
- **No schema changes at startup or request time:** concurrent workers can race and deployments become hard to roll back; use the explicit migration command.
- **No editing an applied migration:** existing installations would not receive the new schema; add a new migration instead.
- **No SQL or authorization rules in page components:** shared services keep route, action, and job behavior consistent.
- **No unvalidated Server Actions or Route Handlers:** TypeScript types do not validate untrusted HTTP or form input.
- **No implicit caching for mutable account data:** stale reads can show the wrong state after a write; choose and test the cache policy.
- **No fake success after partial failure:** use a transaction for related writes and return an error if any required write fails.
