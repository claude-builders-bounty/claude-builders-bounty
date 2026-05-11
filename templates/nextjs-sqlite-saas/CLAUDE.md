# CLAUDE.md - Next.js 15 + SQLite SaaS

Use this file as the default project context for a greenfield SaaS app built with Next.js 15 App Router, TypeScript, Tailwind CSS, and SQLite through `better-sqlite3` for local deployments or Turso/libSQL for hosted deployments.

## Stack And Versions

- Runtime: Node.js 22 LTS, TypeScript strict mode, Next.js 15 App Router, React Server Components by default.
- Database: SQLite. Use `better-sqlite3` for single-server apps and Turso/libSQL only when edge or hosted replication is required.
- Validation: Zod at every server boundary.
- Styling: Tailwind CSS plus small local components.
- Testing: unit tests for pure logic, integration tests for server actions and route handlers, and one happy-path Playwright test per paid workflow.

Reason: this stack keeps SaaS iteration fast while preserving a clear line between server-only data access and client interactivity.

## Folder Structure

```text
app/
  (marketing)/
  (app)/
    dashboard/
    settings/
  api/
components/
  ui/
  forms/
db/
  client.ts
  migrations/
  queries/
lib/
  auth/
  env.ts
  validation/
server/
  actions/
  services/
tests/
  integration/
  unit/
```

- `app/(marketing)` contains public pages and must not import database clients.
- `app/(app)` contains authenticated SaaS pages. Fetch data in server components, not client effects.
- `db/client.ts` is the only module that opens a SQLite connection.
- `db/queries` contains SQL access functions.
- `server/services` coordinates use cases such as onboarding, billing, invites, exports, and account deletion.
- `lib/env.ts` validates environment variables once at startup.

Reason: this structure prevents data access from spreading into UI files and keeps refactors cheap when the SaaS grows.

## Naming Conventions

- Route folders use kebab-case: `team-members`, `billing-history`.
- React components use PascalCase filenames: `PlanSelector.tsx`.
- Server actions end in `.action.ts`: `update-profile.action.ts`.
- Database query modules end in `.query.ts`: `users.query.ts`.
- Validation schemas end in `.schema.ts`: `invite.schema.ts`.
- Test files mirror the module under test: `users.query.test.ts`.
- SQL migrations use `YYYYMMDDHHMM_description.sql`, for example `202605111030_create_users.sql`.

Reason: suffixes make import direction obvious and reduce accidental client imports of server-only code.

## Dev Commands

Use these commands unless `package.json` says otherwise:

```bash
npm run dev
npm run lint
npm run typecheck
npm run test
npm run test:e2e
npm run db:migrate
npm run db:studio
```

Before opening a PR, run `lint`, `typecheck`, tests affected by the change, and `db:migrate` against a disposable SQLite database when migrations changed.

Reason: SQLite migration mistakes are easy to miss until runtime, so migration verification is part of normal development.

## SQL And Migration Conventions

- Write explicit SQL migrations in `db/migrations`. Do not rely on implicit sync or destructive ORM push commands.
- Every schema change gets a forward migration and a rollback note in the migration comment when rollback is practical.
- Use additive migrations first: create nullable column, backfill, then enforce `NOT NULL` in a later migration.
- Always enable foreign keys when opening a SQLite connection: `PRAGMA foreign_keys = ON`.
- Use transactions for multi-step writes and any migration that touches existing data.
- Never delete user data in a migration unless the migration name and PR description explicitly call out the deletion.
- Store timestamps as ISO 8601 UTC text unless the existing schema already uses integer epoch milliseconds.
- Put PII in the smallest possible table surface and document retention/deletion behavior in the service that owns it.

Reason: SQLite is reliable when schema changes are deliberate; unsafe migration shortcuts create data loss risk.

## Component Patterns

- Default to server components. Add `"use client"` only for browser state, event handlers, focus management, or client-only APIs.
- Keep forms progressive: server action handles the write, Zod validates input, and the UI renders field-level errors.
- Use URL search params for shareable filters and tabs; use local state for transient UI only.
- Keep route pages thin. Move business decisions into `server/services`.
- Use optimistic UI only when the rollback path is obvious and tested.
- Components should accept domain objects or view models, not database rows with unused fields.

Reason: App Router works best when data loading stays server-side and client components stay intentionally small.

## API And Server Action Patterns

- Route handlers are for external clients, webhooks, file downloads, or integrations. Prefer server actions for first-party forms.
- Authenticate at the top of every server action and route handler.
- Authorize against the resource, not just the session. Check organization membership, role, and ownership before reads and writes.
- Return typed result objects from server actions: `{ ok: true, data }` or `{ ok: false, fieldErrors, formError }`.
- Do not throw user-facing validation errors; reserve thrown errors for unexpected failures.
- Log server-side failures with enough context to debug, but never log secrets, tokens, full cookies, card data, or raw PII payloads.

Reason: SaaS bugs are usually authorization or boundary bugs, so every boundary needs the same shape.

## Patterns To Follow

- Define one service function per user intent, such as `inviteTeamMember` or `cancelSubscription`.
- Keep SQL in query modules and compose it in services.
- Add tests around money, permissions, deletion, exports, and migrations.
- Update docs when adding environment variables, migrations, billing states, or background jobs.
- Prefer small PRs that include a migration, service code, UI, and tests for one workflow.
- Use `lib/env.ts` for environment parsing and type-safe configuration instead of reading `process.env` throughout the app.

Reason: user intent is a better boundary than framework file type, and configuration bugs should fail early.

## Anti-Patterns To Avoid

- Do not import `db/client.ts` into client components. It leaks server-only code into the browser bundle.
- Do not put business rules in JSX. It makes testing and authorization review harder.
- Do not create catch-all `utils` modules. Name modules after the domain they serve.
- Do not use `any` for request input, SQL rows, or payment provider payloads.
- Do not silently swallow server action errors. Return a typed error or log and rethrow.
- Do not run destructive SQL outside a transaction.
- Do not add a new dependency for a problem already solved by the platform or one small helper.
- Do not store secrets in `.env.local.example`, docs, tests, screenshots, or fixtures.

Reason: these shortcuts make a small SaaS feel faster for a week and slower for every month after.

## Definition Of Done

- User-facing workflow works from an empty SQLite database after `npm run db:migrate`.
- Relevant unit or integration tests cover validation, authorization, and persistence.
- `npm run lint` and `npm run typecheck` pass.
- New environment variables are documented in `.env.example`.
- New migrations are committed and named correctly.
- PR description lists verification commands and any data migration risk.

Reason: greenfield projects become production projects suddenly; this checklist keeps the handoff clean.
