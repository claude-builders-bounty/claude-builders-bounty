# CLAUDE.md

Guidance for Claude Code when working in this Next.js 15 App Router + SQLite SaaS project.

## Stack And Versions

- Use Next.js 15 with the App Router, React 19, TypeScript in strict mode, Server Components by default, and Server Actions for mutations.
  Reason: this keeps data access close to the server boundary and avoids accidental client-side database or secret access.
- Use SQLite for local and small production deployments through either `better-sqlite3` or Turso/libSQL.
  Reason: both keep the schema portable while supporting fast local development.
- Use one SQL access layer under `src/db`.
  Reason: scattered SQL makes transactions, migrations, and test setup hard to audit.

## Dev Commands

Run these before handing work back:

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

Use these during development:

```bash
npm run dev
npm run db:migrate
npm run db:seed
npm run db:studio
```

If a command is missing, add it to `package.json` instead of documenting an ad hoc command.
Reason: Claude and future contributors need one stable command surface.

## Folder Structure

Use this layout unless the existing project already has a stricter convention:

```text
src/
  app/
    (marketing)/
    (app)/
    api/
  components/
    ui/
    forms/
    layout/
  db/
    client.ts
    schema.ts
    migrations/
    queries/
  features/
    billing/
    auth/
    dashboard/
  lib/
    auth/
    env.ts
    result.ts
  server/
    actions/
    services/
  tests/
    fixtures/
    integration/
```

Rules:

- Route files stay thin and compose feature modules.
  Reason: App Router folders become unreadable when business logic sits in `page.tsx`.
- Shared UI primitives go in `src/components/ui`; domain components go inside `src/features/<feature>`.
  Reason: primitive components should remain reusable, but feature components should keep their business context.
- Put all direct database reads and writes in `src/db/queries` or `src/server/services`.
  Reason: this prevents accidental queries from Client Components and makes transactions testable.

## Naming Conventions

- Use kebab-case for route folders and file names: `team-settings/page.tsx`.
  Reason: URLs and file paths stay readable across platforms.
- Use PascalCase for React components: `TeamSwitcher.tsx`.
  Reason: it matches React diagnostics and import conventions.
- Use camelCase for functions and variables, and SCREAMING_SNAKE_CASE only for true process constants.
  Reason: it keeps config distinct from runtime values.
- Name Server Actions with a verb and an `Action` suffix, for example `createWorkspaceAction`.
  Reason: call sites make mutation boundaries obvious.
- Name query functions after the data they return: `getWorkspaceBySlug`, `listInvoicesForWorkspace`.
  Reason: this keeps query intent clear without reading the SQL first.

## SQL And Migration Conventions

- Every schema change must include a migration file under `src/db/migrations`.
  Reason: changing `schema.ts` alone leaves deployed databases behind.
- Migrations must be append-only after merge.
  Reason: editing old migrations breaks teammates and production deploys.
- Prefer explicit column lists in `INSERT` and `SELECT`.
  Reason: SQLite accepts broad queries, but explicit columns survive schema growth.
- Wrap multi-step writes in a transaction.
  Reason: SaaS flows often create users, workspaces, memberships, and audit rows together.
- Never run destructive SQL without a migration and a rollback note.
  Reason: SQLite is easy to mutate locally, so destructive operations need extra review.
- Use foreign keys and enable `PRAGMA foreign_keys = ON` in the database client.
  Reason: SQLite does not enforce them unless explicitly enabled.
- Store timestamps as ISO 8601 text or integer milliseconds, and use one convention across the schema.
  Reason: mixed timestamp formats create sorting and timezone bugs.

## Component Patterns

- Default to Server Components. Add `"use client"` only for state, browser APIs, or event handlers.
  Reason: Server Components reduce bundle size and keep secrets server-side.
- Fetch data in Server Components or server services, then pass serializable props to Client Components.
  Reason: Client Components should not know about database clients or secrets.
- Keep form validation schemas next to the feature that owns the form.
  Reason: validation is domain logic, not generic UI logic.
- Prefer small form components that accept `defaultValues` and submit to a Server Action.
  Reason: this makes edit and create flows share behavior without hiding mutations.
- Use optimistic UI only after the server path is tested.
  Reason: optimistic state can hide failed writes and permission errors.

## Auth And Authorization

- Authenticate once at the route, action, or service boundary.
  Reason: nested components should not duplicate session parsing.
- Authorize every workspace-scoped query by `workspaceId` and current user membership.
  Reason: SaaS data leaks usually happen through missing tenant filters.
- Do not trust IDs from forms, route params, or search params.
  Reason: all of them are user-controlled input.

## Environment And Config

- Read environment variables only through `src/lib/env.ts`.
  Reason: one parser gives clear startup errors and keeps server-only values out of the client.
- Prefix only public browser values with `NEXT_PUBLIC_`.
  Reason: every `NEXT_PUBLIC_` value is shipped to users.
- Do not add fallback secrets in code.
  Reason: accidental defaults become production vulnerabilities.

## Testing Rules

- Unit test pure utilities and SQL query builders.
  Reason: these fail fast and explain most regressions.
- Integration test Server Actions that write to SQLite.
  Reason: action behavior depends on validation, auth, SQL, and cache invalidation together.
- Use a temporary SQLite database per test file.
  Reason: shared test databases create ordering bugs.
- Test tenant boundaries for every workspace-scoped feature.
  Reason: authorization bugs are higher impact than UI regressions.

## Patterns To Follow

- Return typed result objects from services: `{ ok: true, data }` or `{ ok: false, error }`.
  Reason: Server Actions can map known errors to form messages without throwing for expected failures.
- Keep cache invalidation next to the mutation that changes the data.
  Reason: the developer changing a write path can see which pages must refresh.
- Use `redirect` only after successful mutations.
  Reason: failed mutations should return field or form errors.
- Keep SQL close to named query functions.
  Reason: named functions document business intent better than inline SQL in components.

## Anti-Patterns

- Do not import the database client into Client Components.
  Reason: it will either fail at build time or leak server assumptions into browser code.
- Do not put business logic in `page.tsx`.
  Reason: pages should compose data, actions, and UI; services should own decisions.
- Do not add generic `utils.ts` dumping grounds.
  Reason: unclear ownership makes future cleanup expensive.
- Do not create migrations from production state manually.
  Reason: migrations must be reproducible from the repository.
- Do not catch every error and return `"Something went wrong"`.
  Reason: expected errors need user-safe messages, unexpected errors need logs.
- Do not skip authorization in background jobs.
  Reason: jobs still operate on tenant-scoped data.

## Before Opening A PR

Confirm:

- New routes are Server Components unless they need client interactivity.
- Database changes include migrations and tests.
- Tenant-scoped reads include membership checks.
- `npm run lint`, `npm run typecheck`, `npm test`, and `npm run build` pass or are clearly documented if unavailable.
- The PR description lists schema changes, user-visible behavior, and any follow-up work.
