# CLAUDE.md

This file is the project contract for a greenfield SaaS built with Next.js 15 App Router and SQLite. Follow these rules unless the user explicitly changes the architecture in the current task.

## Stack And Versions

- Use Next.js 15 with the App Router. Reason: App Router keeps routing, layouts, loading states, server components, route handlers, and server actions in one consistent model.
- Use React 19 and TypeScript in strict mode. Reason: the app should catch data-shape mistakes before they reach users.
- Use Node 22 LTS or newer, pinned in `.nvmrc` or `.node-version`. Reason: everyone should run the same runtime locally, in CI, and in production.
- Use `pnpm` as the package manager. Reason: it gives deterministic installs and avoids lockfile drift across contributors.
- Use SQLite as the primary database. Use `better-sqlite3` for local/serverful deployments and Turso/libSQL when the database must be remote or edge-compatible. Reason: the data layer should stay SQLite-first while allowing a production hosting choice.
- Use Drizzle ORM plus Drizzle Kit for schema and migrations. Reason: schema, migration generation, and TypeScript query types stay close to SQL without hiding the database.
- Use Zod for runtime validation at environment, form, route handler, and server action boundaries. Reason: TypeScript does not validate untrusted runtime input.
- Use Tailwind CSS plus small, accessible React components. Reason: SaaS UI should be fast to scan, predictable, and easy to maintain.

## Dev Commands

Assume these scripts exist in `package.json`; add or update them when creating the project:

```bash
pnpm dev          # start Next.js locally
pnpm build        # production build
pnpm start        # run the production build locally
pnpm lint         # eslint
pnpm typecheck    # tsc --noEmit
pnpm test         # unit/integration tests
pnpm test:e2e     # Playwright smoke tests
pnpm db:generate  # generate Drizzle migrations from db/schema.ts
pnpm db:migrate   # apply migrations
pnpm db:studio    # open Drizzle Studio
```

Run `pnpm lint`, `pnpm typecheck`, and the smallest relevant test command before calling work complete. Reason: broken types, lint failures, and missing migration coverage are cheap to catch locally.

## Folder Structure

Use this structure for new code:

```text
app/
  (auth)/
  (dashboard)/
  (marketing)/
  api/
  layout.tsx
  page.tsx
components/
  forms/
  layout/
  ui/
db/
  client.ts
  migrations/
  queries/
  schema.ts
features/
  billing/
  organizations/
  users/
lib/
  auth/
  env.ts
  errors.ts
  logger.ts
  utils.ts
scripts/
tests/
  e2e/
  fixtures/
  unit/
```

- Put route segments, layouts, pages, loading states, and route handlers under `app/`. Reason: App Router files are framework entry points and should be easy to find.
- Put reusable, domain-neutral UI in `components/ui`. Reason: these components should not import business logic or database code.
- Put reusable form shells in `components/forms`. Reason: forms often share field rendering, error display, and pending-state behavior without sharing domain mutations.
- Put domain code in `features/<domain>`. Reason: SaaS behavior changes by domain, and features should own their UI, validation, actions, and tests.
- Put database connection, schema, migrations, and query helpers in `db/`. Reason: database access should be auditable and should not spread across random components.
- Put app-wide utilities in `lib/`. Reason: shared helpers should be deliberately small and not become a hidden domain layer.
- Put executable maintenance tasks in `scripts/`. Reason: one-off production or migration work should be reviewable, repeatable, and safe to run from CI or a terminal.

## Naming Conventions

- Use kebab-case for folders and non-component files, such as `billing-portal.ts` and `create-checkout-session.ts`. Reason: file names stay readable on case-sensitive and case-insensitive filesystems.
- Use PascalCase for React component names and component files, such as `AccountMenu.tsx`. Reason: React components are types and should stand out from utilities.
- Use camelCase for TypeScript variables, functions, and Drizzle object keys. Reason: it matches JavaScript conventions and keeps inferred types ergonomic.
- Use snake_case for SQLite table and column names. Reason: SQL remains readable and portable across direct queries, migrations, and external tools.
- Name server actions with an action suffix, such as `createOrganizationAction`. Reason: call sites should make mutation boundaries obvious.
- Name query helpers by what they return, such as `getUserById` or `listInvoicesForOrganization`. Reason: read paths should communicate scope and authorization expectations.
- Name migrations with Drizzle's generated timestamp prefix and commit them unchanged after review. Reason: migration order must be deterministic.

## SQL And Migration Conventions

- Treat `db/schema.ts` as the source of truth for schema changes. Reason: generated migrations should come from the typed schema instead of ad hoc SQL.
- Generate migrations with `pnpm db:generate`, then review the SQL before committing. Reason: generated SQL can still contain destructive or inefficient changes.
- Apply migrations locally with `pnpm db:migrate` before testing code that depends on them. Reason: TypeScript can compile while the database is still missing columns or tables.
- Never edit a migration that has already been merged. Reason: existing environments may have already applied it.
- Use expand-and-contract migrations for risky changes. Reason: adding nullable columns, backfilling, enforcing constraints, and dropping old columns in separate releases avoids production data loss.
- Wrap multi-step writes in transactions. Reason: SaaS mutations often update several tables and must not leave partial state.
- Enable SQLite foreign keys on every connection. Reason: SQLite requires `PRAGMA foreign_keys = ON` per connection, and orphaned rows are expensive to clean up later.
- Give every user-owned table `id`, `created_at`, and `updated_at`. Reason: stable IDs and audit timestamps are baseline SaaS requirements.
- Prefer soft deletion for customer-owned business records. Reason: billing, audit, and support workflows often need historical records.
- Use explicit indexes for lookup columns, foreign keys, and common dashboard filters. Reason: SQLite performs well when access paths are deliberate.
- Use raw SQL only when Drizzle cannot express the query cleanly. Reason: raw SQL is acceptable, but every raw query must still use bound parameters and have a focused test.
- Keep database code out of Client Components. Reason: secrets and server-only modules must never enter the browser bundle.

## Database Access Pattern

- Export one database client from `db/client.ts`. Reason: connection setup, foreign-key pragmas, logging, and adapter switching belong in one place.
- Put cross-domain reads in `db/queries` only when more than one feature uses them. Reason: shared query helpers should be earned by reuse.
- Keep feature-specific queries beside the feature under `features/<domain>/queries.ts`. Reason: domain reads are easier to change when they live near the UI and actions they support.
- Validate authorization inside server actions or query helpers, not in Client Components. Reason: client-side checks are only UX hints and are not security.
- Pass a transaction object through helper functions during mutations. Reason: nested helpers should participate in the caller's transaction instead of opening separate writes.
- Return plain objects from data helpers. Reason: Server Component props and serialized responses should not depend on class instances or driver-specific objects.

## App Router Patterns

- Prefer Server Components by default. Reason: initial data loading, auth checks, and redirects are faster and safer on the server.
- Use Client Components only for browser APIs, local interactive state, optimistic UI, or third-party components that require the DOM. Reason: unnecessary client boundaries increase bundle size and hydration work.
- Keep `page.tsx` files thin. Reason: pages should compose feature components and data loaders, not become large business-logic files.
- Use `loading.tsx` for route-level pending states and `error.tsx` for recoverable route-level failures. Reason: App Router already provides these boundaries.
- Use route groups such as `(dashboard)` and `(marketing)` to separate layouts without changing URLs. Reason: SaaS apps usually have different navigation shells for public and authenticated surfaces.
- Use route handlers in `app/api` for webhooks, external callbacks, uploads, and endpoints consumed outside the React app. Reason: server actions are better for internal form mutations, while route handlers are better public HTTP contracts.
- Set `export const runtime = "nodejs"` on routes that use `better-sqlite3`. Reason: `better-sqlite3` cannot run in the Edge runtime.

## Server Actions And Forms

- Use server actions for authenticated, app-internal mutations. Reason: they keep form handling close to the UI and avoid unnecessary API routes.
- Validate every server action input with Zod before touching the database. Reason: form data, URL params, and client-provided IDs are untrusted.
- Return a typed result object such as `{ ok: true }` or `{ ok: false, fieldErrors, formError }`. Reason: forms need predictable success and failure states.
- Revalidate exact paths or tags after successful mutations. Reason: stale dashboard data is confusing and broad revalidation hides performance problems.
- Keep side effects after validation and authorization. Reason: emails, webhooks, and billing calls should not fire for invalid or unauthorized requests.
- Use idempotency keys for billing and webhook-driven mutations. Reason: external providers retry, and duplicate charges or records are unacceptable.

## Component Patterns

- Build small components with explicit props. Reason: clear props make Server and Client Component boundaries easier to see.
- Keep domain components in `features/<domain>/components`. Reason: a billing component that imports billing actions is not a shared UI primitive.
- Keep UI primitives in `components/ui` free of app-specific text, routing, auth, and database imports. Reason: primitives should be reusable and easy to test.
- Use accessible HTML first, then enhance with custom components. Reason: dialogs, menus, forms, and buttons must work for keyboard and screen-reader users.
- Put pending, empty, error, and permission-denied states in the same feature surface as the happy path. Reason: SaaS screens are operational tools and must handle real data states.
- Pass serializable props from Server Components into Client Components. Reason: non-serializable values break hydration and create hidden runtime failures.
- Avoid fetching first-paint data in `useEffect`. Reason: Server Components can fetch before render and avoid loading waterfalls.

## Environment And Configuration

- Put environment parsing in `lib/env.ts` and import from there. Reason: the app should fail fast when required configuration is missing.
- Do not read `process.env` throughout the codebase. Reason: scattered env access makes runtime requirements impossible to audit.
- Separate server-only and client-exposed variables. Reason: secrets must never be bundled into client JavaScript.
- Prefix browser-safe variables with `NEXT_PUBLIC_` only when they are truly public. Reason: the prefix exposes values to every user.
- Use `.env.example` for required keys without real secrets. Reason: onboarding should be possible without leaking credentials.

## Auth And Authorization

- Check authentication in layouts for protected route groups. Reason: unauthenticated users should be redirected before protected UI renders.
- Check authorization at the data access or mutation boundary. Reason: hiding buttons is not a security boundary.
- Include `organizationId` or tenant scope in every multi-tenant query. Reason: tenant leaks are the highest-risk class of SaaS bug.
- Do not trust IDs from params, forms, or search params without ownership checks. Reason: direct object reference bugs are easy to introduce in dashboards.
- Log security-relevant denials without logging secrets or raw tokens. Reason: support and incident response need traces without creating new exposure.

## Testing Expectations

- Use unit tests for pure utilities, validation schemas, and query builders. Reason: these fail quickly and catch many regressions.
- Use integration tests with a temporary SQLite database for server actions and query helpers. Reason: migrations, constraints, and transactions need a real database.
- Use Playwright for one smoke path per critical user workflow, such as signup, creating an organization, and editing billing details. Reason: App Router behavior needs browser-level coverage.
- Seed tests through factories in `tests/fixtures`. Reason: tests should be readable and not duplicate table setup.
- Test authorization failures as deliberately as success paths. Reason: SaaS bugs often come from missing tenant or role checks.

## What We Do Not Do

- Do not use the Pages Router. Reason: mixing routing systems doubles conventions and makes layouts harder to reason about.
- Do not put business logic directly in `page.tsx` or `route.ts`. Reason: entry points should coordinate feature code, not become the feature code.
- Do not import server-only modules into Client Components. Reason: this can leak secrets or break browser builds.
- Do not use `better-sqlite3` in Edge runtime routes. Reason: it depends on native Node bindings.
- Do not hand-write migrations for normal schema changes. Reason: generated migrations keep schema and SQL in sync; hand-written SQL is reserved for reviewed exceptions.
- Do not concatenate strings into SQL. Reason: parameter binding prevents injection and avoids quoting bugs.
- Do not use `any` to silence type errors. Reason: the type error is usually pointing at a real contract mismatch.
- Do not create a generic `helpers.ts` or `utils.ts` inside every folder. Reason: vague helper files hide responsibilities and become dumping grounds.
- Do not add global state for server data. Reason: Server Components, caching, and database queries should own server state.
- Do not make a new abstraction before the second real use case. Reason: premature abstraction slows feature work and makes the first use case harder to change.
- Do not ignore loading, empty, and error states. Reason: production SaaS users spend a lot of time outside perfect data conditions.

## Claude Code Working Rules

- Before editing, inspect nearby files and follow the existing pattern when it does not conflict with this document. Reason: local consistency beats a theoretical ideal.
- For schema changes, update `db/schema.ts`, generate a migration, review it, and run the affected tests. Reason: code and database shape must move together.
- For user-facing changes, verify responsive layout and accessibility-relevant states. Reason: dashboard UI must remain usable on real devices and assistive tech.
- For auth, billing, or tenant-scoped changes, add at least one failure-path test. Reason: these areas carry high business and security risk.
- If a requested change conflicts with these rules, explain the tradeoff and make the smallest safe exception. Reason: the document guides engineering judgment, but the user's task still matters.
