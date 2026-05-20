# CLAUDE.md

This file is the operating guide for Claude Code in a greenfield SaaS app built
with Next.js 15 App Router, TypeScript, SQLite, and either `better-sqlite3` for
a local/serverful app or Turso/libSQL for hosted SQLite.

## Stack And Versions

- Use Next.js 15 with the App Router in `src/app`. Reason: Server Components,
  Server Actions, Route Handlers, and layouts are the default architecture for
  current Next.js apps.
- Use TypeScript in strict mode. Reason: SaaS code touches auth, billing, and
  user data; weak types turn product bugs into data bugs.
- Use SQLite as the primary database. Reason: SQLite is simple, fast,
  transactional, and enough for most early SaaS products before distributed data
  is needed.
- Use `better-sqlite3` for a single Node server, local app, or self-hosted
  deployment. Reason: it is synchronous by design, predictable, and avoids
  connection-pool complexity SQLite does not need.
- Use Turso/libSQL when the app is deployed to serverless or needs replicated
  reads. Reason: serverless environments do not guarantee durable local disk,
  and Turso gives SQLite semantics with hosted persistence.
- Use Server Actions for trusted mutations from app UI. Reason: form submissions
  stay close to the route that owns them without creating unnecessary public API
  endpoints.
- Use Route Handlers only for webhooks, external integrations, health checks,
  and public API surfaces. Reason: external callers need stable HTTP contracts;
  internal UI does not.

## Dev Commands

Prefer these scripts in `package.json`:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest",
    "db:migrate": "tsx scripts/migrate.ts",
    "db:make": "tsx scripts/create-migration.ts",
    "db:studio": "drizzle-kit studio"
  }
}
```

- Run `npm run typecheck` after changing shared types, database access, auth, or
  billing. Reason: these changes usually break contracts outside the edited
  file.
- Run `npm run test` after changing business logic, validation, or database
  code. Reason: route smoke tests do not catch data invariants.
- Run `npm run build` before opening a PR. Reason: Next.js catches server/client
  boundary mistakes only during production build.

## Folder Structure

Use this structure unless an existing project already has a clear convention:

```text
src/
  app/
    (marketing)/
      page.tsx
      pricing/page.tsx
    (app)/
      dashboard/page.tsx
      settings/page.tsx
    api/
      webhooks/stripe/route.ts
    layout.tsx
    globals.css
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
    auth/
    billing/
    organizations/
    projects/
  lib/
    env.ts
    errors.ts
    ids.ts
    time.ts
  server/
    actions/
    auth.ts
    permissions.ts
  tests/
    factories/
    integration/
scripts/
  migrate.ts
  create-migration.ts
```

- Put route files under `src/app`, not under feature folders. Reason: the App
  Router uses filesystem routing; hiding routes inside feature folders makes
  navigation harder to audit.
- Put business logic under `src/features/<domain>`. Reason: a feature should be
  understandable without searching through route files.
- Put database schema and queries under `src/db`. Reason: data shape is a shared
  contract, not a component detail.
- Put reusable visual primitives under `src/components/ui`. Reason: UI
  primitives should not import feature logic.
- Put product-specific composed components under the feature or route that owns
  them. Reason: shared folders become junk drawers if every component starts
  there.

## Naming Conventions

- Use kebab-case for file and folder names: `project-list.tsx`,
  `create-project-form.tsx`. Reason: URLs, imports, and generated paths stay
  readable across operating systems.
- Use PascalCase for React components: `ProjectList`, `CreateProjectForm`.
  Reason: React tooling and JSX conventions rely on component casing.
- Use camelCase for functions and variables: `createProject`, `currentUser`.
  Reason: it matches TypeScript and JavaScript conventions.
- Use `getX` for reads, `createX` for inserts, `updateX` for updates, and
  `deleteX` for deletes. Reason: action names should reveal side effects before
  reading the implementation.
- Use `requireX` for authorization gates that throw: `requireUser`,
  `requireOrganizationRole`. Reason: callers can tell the function stops
  execution when access is invalid.
- Name Server Actions with an `Action` suffix: `createProjectAction`. Reason: it
  separates UI form handlers from pure domain functions.

## Server And Client Boundaries

- Default to Server Components. Reason: less client JavaScript, direct data
  access, and fewer loading states.
- Add `"use client"` only for state, effects, browser APIs, optimistic UI, or
  event handlers. Reason: client components pull their dependency tree into the
  browser bundle.
- Never import `src/db`, secrets, or server-only modules into a client
  component. Reason: this can leak implementation details and break the build.
- Pass plain serializable data from Server Components to Client Components.
  Reason: React cannot serialize database clients, Dates with methods, class
  instances, or functions.
- Keep mutation logic on the server. Reason: clients can request changes; only
  the server can validate identity, permissions, and invariants.

## Database Rules

- Keep the schema in `src/db/schema.ts`. Reason: migrations, queries, and tests
  need one source of truth.
- Store migrations in `src/db/migrations`. Reason: schema history must be
  committed and reviewable.
- Never edit an applied migration. Reason: deployed databases cannot replay your
  local history rewrite.
- Create a new migration for every schema change. Reason: production should move
  forward through explicit, reversible steps.
- Wrap multi-table writes in a transaction. Reason: partial writes create broken
  customer state.
- Use foreign keys and `ON DELETE` behavior deliberately. Reason: SaaS data
  usually has ownership chains; accidental orphan records become privacy and
  billing bugs.
- Prefer integer timestamps or ISO strings consistently. Reason: SQLite has no
  native datetime type, so consistency matters more than taste.
- Use application-generated IDs such as `cuid2`, UUID v7, or ULIDs for public
  records. Reason: sequential row IDs leak growth and are awkward across sync or
  import paths.
- Add indexes for lookup paths used by auth, organization membership, slugs, and
  billing IDs. Reason: SQLite is fast, but table scans become visible at the
  exact moment a SaaS starts working.

## Query Patterns

- Put raw database calls in `src/db/queries/<domain>.ts`. Reason: routes and
  components should not duplicate SQL.
- Return typed plain objects, not driver-specific rows. Reason: callers should
  not care whether the app uses `better-sqlite3`, libSQL, or a test adapter.
- Validate inputs before calling queries. Reason: queries should protect data
  integrity, not parse UI state.
- Handle empty results explicitly. Reason: `undefined` is not a product
  decision.
- Do not build SQL with string interpolation. Reason: parameterized queries
  prevent injection and quoting mistakes.

## Migration Conventions

- Migration filenames must sort in execution order: `0001_create_users.sql`,
  `0002_add_organizations.sql`. Reason: SQLite migrations should be boring and
  deterministic.
- Each migration should do one conceptual thing. Reason: small migrations are
  easier to review and recover from.
- Include both schema and backfill changes when the app needs existing rows to
  keep working. Reason: code and data have to deploy together.
- For destructive changes, use a two-step migration: add new shape, backfill,
  then remove old shape later. Reason: deploys can overlap with old code during
  rollouts.
- Test migrations against an empty database and a database with representative
  existing data. Reason: greenfield and production upgrade paths fail
  differently.

## Auth And Permissions

- Centralize session lookup in `src/server/auth.ts`. Reason: every route should
  agree on who the user is.
- Centralize permission checks in `src/server/permissions.ts`. Reason: access
  rules are product policy, not UI decoration.
- Check authorization inside every Server Action and Route Handler. Reason:
  hidden buttons are not security.
- Store external provider IDs separately from internal user IDs. Reason: users
  can change providers; internal ownership should stay stable.
- Treat organization membership as a first-class table. Reason: B2B SaaS
  permissions almost always outgrow a single `user.role` field.

## Component Patterns

- Keep pages thin: fetch data, check access, compose feature components. Reason:
  pages should explain the route, not contain the whole product.
- Keep forms in dedicated components. Reason: form state, validation messages,
  pending states, and accessibility need focus.
- Use accessible labels and error messages for every input. Reason: forms are
  where SaaS apps make or lose money.
- Prefer Server Actions plus `useActionState` for forms. Reason: it gives
  progressive enhancement and structured server validation.
- Show pending and error states for every mutation. Reason: users need to know
  whether a paid or destructive action happened.
- Avoid global client state unless state truly spans routes. Reason: URL state,
  server data, and component state cover most SaaS needs with less complexity.

## Validation And Errors

- Validate all external input with a schema library such as Zod. Reason:
  TypeScript does not validate runtime form data, webhooks, or API payloads.
- Return field-level errors for forms. Reason: users can fix specific inputs
  faster than generic failure messages.
- Log server errors with context but never with secrets. Reason: debugging needs
  correlation, not leaked credentials.
- Convert expected failures into typed results. Reason: invalid form input is
  not an exception; a failed database write might be.
- Use a shared `AppError` shape only if multiple features benefit from it.
  Reason: premature error frameworks become harder to use than `throw`.

## Environment Variables

- Define environment parsing in `src/lib/env.ts`. Reason: the app should fail at
  startup if required configuration is missing.
- Separate public variables with `NEXT_PUBLIC_`. Reason: anything public is
  shipped to browsers.
- Never read `process.env` throughout the codebase. Reason: scattered
  configuration makes tests and deployments fragile.
- Provide `.env.example` with safe placeholders. Reason: setup should not
  require reading source files.

## Testing Rules

- Test pure business logic with unit tests. Reason: fast tests catch rules
  without booting Next.js.
- Test database queries against a temporary SQLite database. Reason: mocks do
  not catch SQL syntax, constraints, or transaction behavior.
- Test Server Actions at the function boundary. Reason: they contain validation,
  authorization, and mutations.
- Add at least one integration test for each critical paid workflow. Reason:
  billing, onboarding, and permissions fail across module boundaries.
- Do not snapshot large React trees. Reason: snapshots usually approve noise and
  miss behavior.

## Pull Request Checklist

Before opening a PR, verify:

- `npm run typecheck`
- `npm run lint`
- `npm run test`
- `npm run build`
- New migrations run on an empty SQLite database
- New migrations run on a database with representative existing rows
- Server Actions validate input and check permissions
- Client Components do not import server-only modules
- Public routes do not expose private organization data

## What We Do Not Do

- Do not add Prisma by default. Reason: Prisma can be useful, but SQLite-first
  SaaS projects often benefit from simpler SQL, smaller deploys, and fewer
  generated layers.
- Do not use API routes for internal form submissions. Reason: Server Actions
  are simpler for trusted app UI and avoid duplicating validation plumbing.
- Do not put every component in `src/components`. Reason: feature ownership
  disappears when all UI is globally shared.
- Do not make everything a Client Component. Reason: it increases bundle size
  and blocks direct server data access.
- Do not store money as floating-point numbers. Reason: billing must use integer
  minor units such as cents.
- Do not trust webhook payloads before signature verification. Reason: webhooks
  are public HTTP endpoints.
- Do not hide database writes inside React components. Reason: writes need
  validation, authorization, transactions, and tests.
- Do not skip migrations because the project is early. Reason: early projects
  become production projects by accident.
- Do not add queues, event buses, or service layers until there is a real async
  workflow. Reason: architecture should answer current product pressure, not
  decorate it.

## Claude Code Operating Rules

- Read existing files before changing structure. Reason: project conventions
  beat this template when they already exist.
- Make the smallest change that satisfies the task. Reason: SaaS repos
  accumulate accidental architecture quickly.
- Preserve server/client boundaries. Reason: most Next.js bugs in this stack
  come from importing the wrong thing into the browser.
- Update tests with behavior changes. Reason: untested SaaS workflows become
  manual QA debt.
- Explain database changes in PRs. Reason: reviewers need to understand data
  migration risk immediately.
- If requirements are ambiguous, choose the path that protects user data and
  avoids irreversible writes. Reason: product uncertainty should not create data
  loss.
