# CLAUDE.md

This project is a greenfield SaaS application built with Next.js 15 App Router, TypeScript, Tailwind CSS, and SQLite. Use this file as the source of truth when planning, editing, reviewing, or generating code.

## Stack & Versions

- Runtime: Node.js 20 LTS or newer.
  Reason: Next.js 15, React 19, and modern build tooling are best supported on current LTS Node releases.
- Framework: Next.js 15 with the App Router in `src/app`.
  Reason: Server Components, layouts, route handlers, metadata, and streaming belong in App Router projects.
- Language: TypeScript in strict mode.
  Reason: SaaS code usually fails at boundaries; strict types catch invalid request, auth, billing, and DB states early.
- UI: Tailwind CSS plus small local components in `src/components/ui`.
  Reason: shipping fast is easier when styling remains close to the component and shared primitives stay boring.
- Database: SQLite, using Drizzle ORM for schema and migrations.
  Reason: Drizzle keeps SQLite schema, query types, and generated migrations in one reviewable workflow.
- Local DB driver: `better-sqlite3`.
  Reason: local development and tests should be simple, synchronous, and file-backed.
- Production DB option: Turso/libSQL.
  Reason: Turso keeps the SQLite model while adding hosted replication and connection management.
- Validation: Zod at every external boundary.
  Reason: TypeScript only checks our code; Zod checks user input, env vars, webhook payloads, and route params.
- Tests: Vitest for unit/integration tests and Playwright only for critical browser flows.
  Reason: most SaaS regressions are business rules and DB access bugs; browser tests should cover only high-value paths.

## Dev Commands

Prefer these scripts. If they are missing, add them before adding feature code.

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
    "db:generate": "drizzle-kit generate",
    "db:migrate": "drizzle-kit migrate",
    "db:studio": "drizzle-kit studio"
  }
}
```

- Run `npm run typecheck` after changing public types, DB schema, server actions, or route handlers.
- Run `npm run lint` after touching React components, hooks, app routes, or config files.
- Run `npm run test` after changing business rules, DB queries, auth, billing, or validation.
- Run `npm run build` before considering work complete if you changed routing, metadata, server/client boundaries, env handling, or bundling.
- Do not run migrations against production unless the user explicitly asks for a deploy or release step.

## Folder Structure

Use this structure unless the user gives a conflicting project convention.

```text
src/
  app/
    (marketing)/
    (auth)/
    (dashboard)/
    api/
    layout.tsx
    page.tsx
  components/
    ui/
    forms/
    layout/
  features/
    accounts/
      components/
      actions.ts
      queries.ts
      schemas.ts
      types.ts
    billing/
    organizations/
  lib/
    auth/
    db/
      client.ts
      schema.ts
      migrations.ts
    env.ts
    errors.ts
    ids.ts
  server/
    permissions.ts
    rate-limit.ts
    telemetry.ts
  tests/
    db/
    fixtures/
drizzle/
  migrations/
  meta/
public/
```

Rules:

- Keep route files thin. `src/app/**/page.tsx`, `layout.tsx`, and route handlers should orchestrate; domain work goes in `src/features` or `src/server`.
  Reason: App Router files are framework entry points, not a place to hide business logic.
- Put reusable UI primitives in `src/components/ui` and domain-specific UI in `src/features/<domain>/components`.
  Reason: primitives should not import domain state, auth, billing, or DB code.
- Put DB schema in `src/lib/db/schema.ts`; do not scatter table definitions across features.
  Reason: SQLite migrations need a single schema graph.
- Put feature queries in `src/features/<domain>/queries.ts` and mutations/server actions in `actions.ts`.
  Reason: queries and mutations have different caching, validation, and permission concerns.
- Put shared server-only policies in `src/server`.
  Reason: auth, rate limits, permissions, and telemetry must not leak into client bundles.
- Use `src/lib/env.ts` as the only place that reads `process.env` directly.
  Reason: env validation should fail fast and keep secrets out of client code.

## Naming Conventions

- Files and folders: kebab-case, except Next.js reserved files such as `page.tsx`, `layout.tsx`, `route.ts`, `loading.tsx`, and `error.tsx`.
- React components: PascalCase exports from kebab-case files.
- Server actions: verb-first names, for example `createOrganization`, `updateProfile`, `deleteInvite`.
- Query helpers: noun-first names, for example `getOrganizationBySlug`, `listInvoicesForAccount`.
- Zod schemas: suffix with `Schema`, for example `createInviteSchema`.
- DB tables: plural snake_case, for example `organizations`, `organization_members`, `billing_events`.
- DB columns: snake_case in SQLite, camelCase in TypeScript objects if using Drizzle mappings.
- Route groups: use parentheses for layout concerns only, for example `(marketing)` and `(dashboard)`.

## SQL & Migration Conventions

Use Drizzle migrations for every schema change.

- Generate migrations with `npm run db:generate`; apply them locally with `npm run db:migrate`.
  Reason: generated SQL is reviewable and keeps schema drift visible.
- Never edit a migration that has already been applied outside the current branch.
  Reason: SQLite migration history must be append-only once shared.
- Keep one logical schema change per migration.
  Reason: small migrations are easier to review, roll forward, and debug.
- Use integer primary keys or stable text IDs consistently per table; prefer text IDs generated by the app for public-facing resources.
  Reason: public SaaS URLs and webhook payloads should not expose sequential internal IDs.
- Every tenant-owned table must include `organization_id` or `account_id`.
  Reason: tenant scoping must be enforceable in every query.
- Add indexes for foreign keys, unique slugs, lookup columns, and columns used in list filters.
  Reason: SQLite is fast when access paths are explicit.
- Enable foreign keys on every SQLite connection.
  Reason: SQLite does not reliably protect relations unless `PRAGMA foreign_keys = ON` is active.
- Store timestamps as integer milliseconds or ISO text consistently; default to integer milliseconds.
  Reason: SQLite has no native timestamp type, and mixed formats make queries fragile.
- Include `created_at` and `updated_at` on mutable domain tables.
  Reason: support, audit, sync, and billing investigations need time context.
- Wrap multi-step writes in transactions.
  Reason: SaaS mutations often touch accounts, memberships, audit events, and billing state together.
- Use parameterized Drizzle queries or prepared SQL. Never concatenate user input into SQL strings.
  Reason: SQLite is still vulnerable to injection.
- Do not use destructive migrations such as dropping columns, dropping tables, or mass deletes without a written backfill and rollback plan in the PR.
  Reason: SQLite has limited online migration options, and SaaS data loss is rarely acceptable.
- For Turso/libSQL, avoid assumptions that depend on local filesystem access, WAL settings, or long-running exclusive locks.
  Reason: hosted SQLite has different operational constraints than `better-sqlite3`.

## Database Access

- Create the DB client once in `src/lib/db/client.ts`.
  Reason: scattered clients make tests, transactions, and Turso configuration inconsistent.
- Export typed table objects and query helpers; do not export raw connection details to client components.
  Reason: the browser must never receive DB credentials or server-only modules.
- Keep reads side-effect free.
  Reason: Server Components can re-run and should remain safe under caching and streaming.
- Put permission checks next to the query or mutation that needs them.
  Reason: callers forget; data access functions should defend tenant boundaries themselves.
- Return null for not-found reads and throw typed errors for forbidden or invalid state.
  Reason: not found, unauthorized, and invalid transitions need different UI responses.

## App Router Patterns

- Default to Server Components.
  Reason: they reduce shipped JavaScript and can access server-only data safely.
- Add `"use client"` only for interactivity, browser APIs, local component state, or client-only libraries.
  Reason: accidental client boundaries increase bundle size and can leak server imports.
- Fetch data in Server Components or server-only query functions, not in client `useEffect` for initial page load.
  Reason: initial SaaS screens should render with data and auth state already resolved.
- Use Route Handlers in `src/app/api/**/route.ts` for webhooks and external API integrations.
  Reason: route handlers provide clear HTTP boundaries and are easy to test.
- Use Server Actions for form mutations owned by the app UI.
  Reason: they keep validation, auth, mutation, and cache invalidation close to the form workflow.
- Always validate Server Action input with Zod before checking permissions or writing to the DB.
  Reason: malformed input should fail before it reaches business logic.
- After mutations, call `revalidatePath`, `revalidateTag`, or `redirect` deliberately.
  Reason: App Router caching will otherwise show stale dashboards.
- Use `notFound()` for missing public resources and typed forbidden responses for private tenant resources.
  Reason: leaking whether private records exist is a security issue.

## Component Patterns

- Build forms as small client components that call server actions.
  Reason: validation messages and pending states need client interactivity, while writes stay server-side.
- Keep page-level layout in `layout.tsx`; keep repeated dashboard chrome in `src/components/layout`.
  Reason: nested layouts should express route hierarchy, not arbitrary visual grouping.
- Pass plain serializable props from Server Components to Client Components.
  Reason: functions, DB rows with special prototypes, and class instances do not cross the server/client boundary safely.
- Use accessible labels, field errors, and disabled or pending states for every form.
  Reason: SaaS forms are operational tools; ambiguity creates support work.
- Prefer composition over large prop matrices.
  Reason: internal dashboards change quickly, and over-configured components become hard to reason about.
- Use optimistic UI only when the server action is idempotent or rollback is obvious.
  Reason: SaaS state often affects billing, permissions, or team data.

## Auth, Tenancy & Permissions

- Treat every dashboard route as tenant-scoped unless explicitly public.
- Resolve the current user and organization on the server before loading tenant data.
- Pass `organizationId` into every tenant query; never infer tenant from a client-provided slug alone.
- Check role permissions inside mutations even if the UI hides the button.
- Log security-sensitive actions such as role changes, invite creation, API key creation, and billing changes.

Reason: client UI is a convenience layer, not an authorization boundary.

## Environment Variables

Read env vars only through `src/lib/env.ts`.

Expected server env vars:

```text
DATABASE_URL=
DATABASE_AUTH_TOKEN=
AUTH_SECRET=
APP_URL=
```

Rules:

- Validate env vars with Zod at startup.
- Prefix public values with `NEXT_PUBLIC_` only when they are safe for the browser.
- Never read secrets in Client Components.
- In tests, use a temp SQLite file or in-memory database and explicit test env values.

## Error Handling

- Use typed domain errors for expected failures such as `ForbiddenError`, `NotFoundError`, and `InvalidStateError`.
- Do not expose raw database errors to users.
- In Server Actions, return field-level validation errors and a form-level message.
- In Route Handlers, return JSON with stable error codes for API clients and webhooks.
- Log unexpected server errors with enough context to debug, excluding secrets and personal data.

Reason: SaaS users need actionable messages, while operators need safe diagnostics.

## Testing Rules

- Test schema-sensitive code against SQLite, not mocks.
  Reason: SQLite behavior around constraints, transactions, and date formats matters.
- Use factories in `tests/fixtures` for users, organizations, memberships, and subscription states.
  Reason: auth and tenancy tests need realistic relationships.
- Test every permission branch for mutations that touch tenant data.
  Reason: missing negative tests are the usual source of cross-tenant bugs.
- Add regression tests for migrations that transform existing data.
  Reason: greenfield today becomes production data tomorrow.
- Do not add browser tests for every component.
  Reason: Playwright should cover flows such as signup, login, invite, checkout, and critical CRUD, not pure rendering.

## What We Do Not Do

- Do not put business logic in `page.tsx` files.
  Reason: it becomes untestable and tightly coupled to routing.
- Do not fetch initial dashboard data from client components with `useEffect`.
  Reason: users see loading shells, auth logic duplicates, and SEO/streaming benefits are lost.
- Do not create a new DB client in every query.
  Reason: it makes transactions and hosted DB config unreliable.
- Do not edit applied migrations.
  Reason: shared migration history must remain reproducible.
- Do not add an ORM, state manager, component library, or auth provider just because it is popular.
  Reason: every dependency must solve a current project problem.
- Do not store money as floating-point numbers.
  Reason: billing values need integer cents or provider-native decimal strings.
- Do not trust route params, search params, form data, webhook payloads, or headers without validation.
  Reason: every external boundary is user input.
- Do not let client-provided organization IDs decide authorization.
  Reason: tenant isolation must be checked server-side.
- Do not hide errors by returning empty arrays for forbidden queries.
  Reason: forbidden and empty are different states with different security and UX implications.
- Do not introduce global mutable state outside the DB client and test-only fixtures.
  Reason: Next.js server execution can be concurrent and long-lived.

## Working Agreement For Claude

When making changes:

1. Identify the route, feature, schema, and permission boundary before editing.
2. Prefer small vertical changes over broad refactors.
3. Add or update validation schemas with every new external input.
4. Add or update DB indexes with every new list filter or lookup path.
5. Keep Server Components server-only and Client Components minimal.
6. Run the relevant commands from the Dev Commands section.
7. Explain any migration, auth, or caching risk in the final response.

When unsure:

- Ask before changing database shape, authentication provider, billing logic, or deployment assumptions.
- Choose the simpler server-side implementation first.
- Keep the SQLite production path valid even when testing locally with `better-sqlite3`.
