# Next.js 15 + SQLite SaaS

## Stack and Versions

- Next.js 15 App Router with React 19 Server Components and TypeScript strict mode.
- `better-sqlite3` for a single-process, locally embedded SaaS. It is selected instead of Turso until traffic requires a separated database.
- Zod for every external input boundary and Vitest for unit tests.
- Node.js 20. The database code runs only in the Node.js runtime, never in Edge Middleware.
- ESLint with `typescript-eslint` and `eslint-plugin-import`.

Reason: this stack removes the first infrastructure decision before implementation starts, so the agent can build features instead of proposing alternatives.

## Folder Structure

```text
src/
  app/                     # routing only: layouts, pages, route handlers
  features/<domain>/       # one folder per business capability
    actions.ts             # server actions for that domain
    queries.ts             # all SQL for that domain
    schema.ts              # Zod input and output schemas
    components/            # UI used only by this feature
  db/
    client.ts              # singleton better-sqlite3 connection
    migrations/            # timestamped, forward-only SQL files
  lib/
    env.ts                 # parsed and exported environment variables
    result.ts              # shared success/error result type
scripts/
  migrate.mjs              # applies pending migrations inside one transaction each
tests/
  db.test.ts
```

Rules:

- `src/app/**` may render components and expose handlers, but it does not contain business rules.
- A feature owns its SQL, validation, actions, and UI. Do not create a global `components/`, `services/`, or `utils/` folder until the same code is used by two features.
- Server-only database files import `server-only`. Client components never import `queries.ts`, `actions.ts`, or `db/client.ts`.
- Test files live beside the code as `*.test.ts` or in `tests/` when testing database migrations.

Reason: route-driven trees become unmaintainable once one SaaS feature touches pages, mutations, SQL, and emails. Domain folders keep every change in one place.

## Commands

```bash
npm install
npm run db:migrate
npm run dev
npm test -- --run
npm run lint
```

- `db:migrate` runs every unapplied file in `src/db/migrations` in lexical order and records it in `_migrations`.
- `db:reset` deletes local `data/app.db`, recreates the data directory, and runs every migration. It is never run in production.
- If a greenfield project does not yet have `db:migrate`, first create `scripts/migrate.mjs`, the `scripts` entry, and `src/db/client.ts`; then implement features.

Reason: naming the bootstrap step explicitly prevents an agent from inventing an ad-hoc database setup inside a route.

## SQL and Migration Conventions

### Connection

- Create one `better-sqlite3` connection in `src/db/client.ts`.
- Set `PRAGMA foreign_keys = ON`, `PRAGMA journal_mode = WAL`, and `PRAGMA busy_timeout = 5000` immediately after opening.
- Reuse the connection in the current process. Do not open a connection per request.
- Keep `data/*.db`, `data/*.db-shm`, and `data/*.db-wal` ignored.

### Migrations

- Name files `0001_create_users.sql`, `0002_add_subscription_status.sql`, and so on. Do not use timestamps that make ordering ambiguous.
- Each migration is forward-only and has one purpose. Never edit an applied migration.
- Wrap each migration in `BEGIN IMMEDIATE;` and `COMMIT;`.
- Use concrete columns, constraints, defaults, indexes, and foreign keys. Do not create permissive placeholder tables.
- Add `user_id` and `organization_id` columns at creation time when the table can ever be scoped to a customer, even if the first feature only has one user.
- Use `npm run db:migrate` only. Never execute `CREATE TABLE`, `ALTER TABLE`, or `DROP TABLE` from application code.

Reason: SQLite migrations are cheap to run but easy to corrupt. Deterministic files and forward-only transactions make local and production databases reproducible.

### Queries

- Put every SQL statement in `features/<domain>/queries.ts` and prepare it at module scope where possible.
- Bind every user value with `?`. String concatenation and template interpolation into SQL are prohibited.
- Return domain objects, not raw rows, from query functions.
- Use a transaction in `db/client.ts` when a user action changes more than one table.
- Add an index for every query filter that can grow with customer data. Do not add speculative indexes.

Reason: one prepared-query module per domain is easy to review, keeps SQL injection impossible, and gives the AI agent a stable place to edit.

## Server Component Patterns

1. A page is a Server Component. It calls `queries.ts` directly and renders HTML.
2. Forms use Server Actions defined in `features/<domain>/actions.ts`.
3. Every action accepts one plain object, validates it with Zod, checks authorization, writes through `queries.ts`, then calls `revalidatePath` or `redirect`.
4. Return `{ ok: false, message: "..." }` to the form for user-fixable errors. Throw only for programming errors or unexpected database failures.
5. Route handlers are reserved for webhooks, mobile/API clients, and third-party callbacks. They do not render internal pages.
6. Client components are limited to form state, optimistic UI, browser-only widgets, and event-heavy interactions. They do not fetch from internal route handlers that only render the same data.

Reason: Next.js 15 App Router already provides a clear boundary. Mixing database access, generic fetch wrappers, and client-side routing creates duplicate caches and authorization gaps.

## Naming

- Files: `kebab-case.ts`, `kebab-case.tsx`.
- Components and types: `PascalCase`.
- Variables, functions, database columns, and query keys: `snake_case` in SQL and `camelCase` in TypeScript.
- Server Actions: `createInvoice`, `updateSubscription`, `inviteMember`; avoid `handleSubmit`, `doStuff`, and `manage`.
- Boolean values read as assertions: `isActive`, `hasPaidTrial`, `canManageBilling`.

Reason: predictable names make generated edits searchable and prevent the same concept from appearing under several spelling styles.

## What We Do Not Do

- Do not add Prisma, Drizzle, Redis, Docker, Stripe, or a second database "for later." Choose them only after the user asks for the concrete need.
- Do not put SQL in pages, server actions, route handlers, or React components. SQL belongs only in `queries.ts`.
- Do not use `any`, `as unknown as`, or a global `types.ts` containing unrelated models.
- Do not catch an error and return HTTP 200 with `{ success: false }`; preserve successful, failed, and unauthorized semantics.
- Do not query the database in a client component or pass a database connection across the server/client boundary.
- Do not create a `pages/` directory. This project uses only App Router.
- Do not run destructive SQL or `db:reset` without explicit confirmation.
- Do not store secrets in SQLite rows, logs, or client components.

Reason: each of these either breaks the App Router security model, hides type information, or adds infrastructure that slows the first paying version.

## Definition of Done

- Inputs are validated with Zod at the action or route-handler boundary.
- Authorization is checked before the first database read or write.
- New SQL has a forward-only migration and uses the existing connection.
- User-facing failures return a readable message; unexpected failures are logged without sensitive data.
- `npm run lint` and `npm test -- --run` pass.
- UI works without JavaScript for basic navigation and form submission unless a browser-only feature requires JavaScript.

Reason: these checks keep a small SaaS shippable and auditable without turning every task into an architecture debate.
