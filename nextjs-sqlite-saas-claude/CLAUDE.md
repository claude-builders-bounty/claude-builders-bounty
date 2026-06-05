# CLAUDE.md

This file defines how Claude Code should work inside a production-oriented Next.js 15 App Router SaaS project backed by SQLite. Treat this as the project contract. If a request conflicts with this file, ask before changing architecture.

## Stack and Versions

- Runtime: Node.js 22 LTS.
- Package manager: pnpm 10. Do not introduce npm, yarn, or bun lockfiles.
- Framework: Next.js 15 with App Router only.
- UI runtime: React 19 with Server Components by default.
- Language: TypeScript 5 with `strict` enabled.
- Database: SQLite through Drizzle ORM.
- Local database driver: `better-sqlite3`.
- Production database driver: Turso/libSQL through `@libsql/client`.
- Validation: Zod for all untrusted input.
- Styling: Tailwind CSS plus local component primitives. Do not add a full UI framework unless requested.
- Testing: Vitest for unit/integration tests, Playwright for critical browser flows.

Reason: this stack keeps the app deployable as a small SaaS, avoids a separate database server for early stages, and still leaves a clean path from local SQLite to Turso.

## Commands

Use these commands unless the repository documents a direct replacement:

```bash
pnpm install
pnpm dev
pnpm build
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm db:generate
pnpm db:migrate
pnpm db:studio
```

Before marking work complete, run the narrowest useful verification command. For changes touching database access, run `pnpm db:generate`, `pnpm typecheck`, and the relevant tests.

## Project Structure

Use this structure for new files:

```text
app/
  (marketing)/
  (app)/
  api/
  layout.tsx
  page.tsx
components/
  ui/
  forms/
  app-shell/
db/
  schema.ts
  client.ts
  migrations/
lib/
  auth/
  config/
  errors/
  server/
  validation/
server/
  actions/
  queries/
  services/
tests/
  unit/
  integration/
  e2e/
```

Rules:

- Put route UI in `app/`, reusable display components in `components/`, database code in `db/`, and business logic in `server/`.
- Keep `app/api/**/route.ts` thin. Route handlers should validate input, call a service, and map errors to HTTP responses.
- Put data reads in `server/queries/` and writes in `server/services/` or `server/actions/`.
- Never import `db/client.ts` from client components.
- Do not put business logic in React components. Components render state; services decide behavior.

## Naming Conventions

- Components: `PascalCase.tsx`.
- Hooks: `useThing.ts`.
- Server actions: `thing.actions.ts`.
- Queries: `thing.queries.ts`.
- Services: `thing.service.ts`.
- Zod schemas: `thing.schema.ts`.
- Tests: `thing.test.ts` or `thing.spec.ts`.
- Database tables: plural snake_case, for example `users`, `billing_events`.
- TypeScript types: singular PascalCase, for example `User`, `BillingEvent`.

Reason: predictable names make Claude Code search and modify related files without guessing.

## App Router Rules

- Use Server Components by default.
- Add `"use client"` only for browser state, event handlers, effects, or browser-only APIs.
- Fetch server data in Server Components or `server/queries/`.
- Mutations go through server actions or route handlers, not client-side direct database calls.
- Keep route segments meaningful: `(marketing)` for public pages, `(app)` for authenticated product pages.
- Use `loading.tsx`, `error.tsx`, and `not-found.tsx` for user-visible async states.
- Prefer `redirect()` and `notFound()` from Next.js over manual branching where appropriate.

Do not convert a Server Component to a Client Component just to pass one interactive child. Isolate the interactive child instead.

## SQLite and Drizzle Rules

- `db/schema.ts` is the source of truth for tables, indexes, and relations.
- `db/client.ts` is the only place that constructs a database client.
- Local development uses a file database, for example `DATABASE_URL=file:./data/dev.db`.
- Production uses Turso/libSQL environment variables, for example `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN`.
- All user input must be validated with Zod before reaching a query or mutation.
- Never concatenate SQL strings with user input.
- Prefer Drizzle query builders. Use raw SQL only for queries Drizzle cannot express, and parameterize every value.
- Add indexes when introducing lookup patterns used by pages, APIs, jobs, or auth checks.

Reason: SQLite is simple and fast, but unsafe raw SQL and missing indexes become production incidents quickly.

## Migration Rules

- Every schema change requires a generated migration in `db/migrations/`.
- Never hand-edit an existing committed migration.
- Never change `db/schema.ts` without running `pnpm db:generate`.
- Migrations must be forward-only. If rollback is needed, add a new corrective migration.
- Destructive changes require a staged plan:
  1. Add the new column/table.
  2. Backfill data.
  3. Switch reads and writes.
  4. Remove old data in a later PR.
- Do not drop columns, rename tables, or rewrite primary keys in the same PR as unrelated UI work.
- For Turso, assume migrations may run against production data and must be idempotent where possible.

## API and Server Action Rules

- Validate request bodies, params, and search params with Zod.
- Return typed success and error shapes.
- Map expected domain errors to stable messages.
- Log unexpected errors on the server, but never leak stack traces to users.
- Server actions must revalidate the affected path or tag when they change user-visible data.
- Route handlers must set correct HTTP status codes.

Use this response pattern for route handlers:

```ts
return Response.json({ data }, { status: 200 });
```

Use this error shape:

```ts
return Response.json({ error: { code, message } }, { status });
```

## Component Patterns

- Keep components small and purpose-driven.
- Prefer composition over prop explosions.
- Client components should receive already-shaped data, not raw database rows.
- Form components should use a Zod schema shared with the server action.
- Avoid global client state unless multiple distant routes need the same live state.
- Do not use `useEffect` for data fetching that can happen on the server.
- Use accessible HTML first, then enhance.
- Every interactive component must have keyboard behavior and visible focus states.

Reason: most SaaS UI bugs come from unclear data ownership between server rendering, forms, and client state.

## Auth and Multi-Tenant Rules

- Treat `userId` and `workspaceId` as required context for authenticated product routes.
- Never trust `workspaceId` from the client without checking membership on the server.
- Put authorization checks near the data access boundary.
- Queries must filter by tenant context when reading tenant-owned data.
- Mutations must verify permission before writing.
- Avoid boolean admin flags on user records. Use membership roles or permissions.

## Configuration Rules

- All environment variables are declared in `lib/config/env.ts`.
- Validate environment variables at process start with Zod.
- Do not read `process.env` throughout the app.
- Never commit `.env` files.
- Use `.env.example` for required variable names without secrets.

## Testing Rules

- Unit test pure functions, validation schemas, and permission checks.
- Integration test database queries with a temporary SQLite file.
- E2E test only critical flows: sign in, create workspace, create/update/delete core resource, billing gate.
- Every bug fix gets a regression test unless the reason not to is documented in the PR.
- If a change touches migrations, test against an empty database and a database with existing rows.

## Pull Request Checklist

Before opening a PR:

- `pnpm typecheck` passes.
- `pnpm lint` passes.
- Relevant tests pass.
- Migrations are generated when schema changes.
- README or `.env.example` is updated when commands or env vars change.
- The PR description lists user-visible changes and verification commands.

## What We Do Not Do

- Do not add Prisma. Drizzle is the chosen ORM because it keeps SQLite/Turso migrations explicit and lightweight.
- Do not add Redux or MobX. Server state belongs on the server; local UI state stays local.
- Do not add tRPC unless the project explicitly adopts it. Route handlers and server actions are enough.
- Do not introduce a second database for queues, sessions, or analytics without an architecture decision.
- Do not write ad-hoc SQL string interpolation.
- Do not use `any` to bypass TypeScript errors.
- Do not put secrets in client components, logs, tests, or fixtures.
- Do not create generic abstractions before two real call sites exist.
- Do not mix formatting-only changes with behavior changes.

## Claude Code Behavior

- First read this file, the nearest README, `package.json`, `db/schema.ts`, and the files directly touched by the request.
- Prefer small, reviewable diffs.
- Preserve existing public APIs unless the task explicitly asks to change them.
- When uncertain, inspect the codebase instead of inventing conventions.
- Explain verification commands in the PR or final response.
- If a request would violate this file, state the conflict and propose the smallest compliant alternative.
