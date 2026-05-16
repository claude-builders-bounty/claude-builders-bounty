# CLAUDE.md

This file is the source of truth for Claude Code when working on this SaaS codebase.
Follow it before making plans, edits, migrations, tests, or pull requests.

## Stack And Versions

- Use Next.js 15 with the App Router in `app/`. Reason: App Router is the production path for server components, server actions, nested layouts, and route handlers.
- Use React 19 and TypeScript in strict mode. Reason: this keeps UI code typed across server and client boundaries and catches most shape changes before runtime.
- Use SQLite as the product database. Reason: the app is small enough to ship with a simple relational database, and SQLite keeps local setup fast.
- Use `better-sqlite3` for local or single-node deployments. Reason: it is synchronous, reliable, and maps cleanly to server-only code in route handlers, actions, and jobs.
- Use Turso/libSQL only when the deployment target needs a remote SQLite-compatible database. Reason: it preserves SQLite semantics while avoiding writable filesystem assumptions on serverless platforms.
- Use Drizzle ORM for schema definitions, typed queries, and migrations. Reason: schema and migration history must live in version control instead of being reconstructed from production.
- Use Tailwind CSS and small local components for styling. Reason: the app needs fast iteration without a heavyweight design dependency.
- Use Server Components by default. Reason: SaaS screens usually read account, billing, and project data before rendering, and keeping those reads on the server prevents accidental client data leaks.
- Use Client Components only for interactive state, browser APIs, optimistic UI, or third-party widgets. Reason: every `"use client"` boundary increases bundle size and limits server-only imports.

## Commands Claude Should Use

Run these commands from the repository root unless a task explicitly says otherwise.

| Task | Command | Reason |
|---|---|---|
| Install dependencies | `pnpm install` | `pnpm` keeps installs deterministic and avoids mixed lockfiles. |
| Start dev server | `pnpm dev` | Next.js dev mode is the fastest way to verify routing, RSC boundaries, and UI states. |
| Typecheck | `pnpm typecheck` | TypeScript catches route params, server action payloads, and database shape errors before tests run. |
| Lint | `pnpm lint` | Linting catches forbidden imports, hook misuse, and common App Router mistakes. |
| Unit tests | `pnpm test` | Unit tests cover pure utilities, validation, permissions, and database helpers without a browser. |
| End-to-end tests | `pnpm test:e2e` | E2E tests verify signup, login, dashboard, and billing flows as users experience them. |
| Generate migrations | `pnpm db:generate` | Generated migrations make schema changes reviewable and repeatable. |
| Apply local migrations | `pnpm db:migrate` | Applying migrations locally proves the checked-in SQL can build the current database. |
| Open DB studio | `pnpm db:studio` | A visual DB check is useful after migrations, seed changes, or suspicious query results. |
| Seed local data | `pnpm db:seed` | Seed data gives Claude stable accounts, projects, and subscriptions for UI verification. |
| Full verification | `pnpm verify` | One command must run typecheck, lint, tests, and migration validation before PRs. |

If a command is missing, add the smallest script needed to `package.json` and explain why. Do not invent one-off shell commands when a repeated workflow deserves a script.

## Project Structure

Use this structure for greenfield work and preserve it unless an existing file already establishes a stronger local pattern.

```text
app/
  (marketing)/
    page.tsx
    pricing/page.tsx
  (app)/
    dashboard/page.tsx
    settings/page.tsx
    layout.tsx
  api/
    webhooks/
      stripe/route.ts
  actions/
    projects.ts
  layout.tsx
  error.tsx
  not-found.tsx
components/
  ui/
  forms/
  nav/
db/
  schema.ts
  migrate.ts
  seed.ts
  client.ts
  queries/
    projects.ts
    users.ts
  migrations/
lib/
  auth/
  billing/
  env.ts
  permissions.ts
  validation/
tests/
  unit/
  e2e/
public/
```

- Put route files only under `app/`. Reason: routing behavior should be visible from the filesystem and match Next.js conventions.
- Put reusable presentational components in `components/`. Reason: UI reuse should not depend on route group names.
- Put business rules in `lib/`. Reason: billing, auth, permission, and validation rules must be testable without rendering pages.
- Put database access in `db/`. Reason: database imports must stay server-only and easy to audit.
- Put route-specific server actions in `app/actions/` only when they are tied to forms in `app/`. Reason: this keeps user flows discoverable without turning actions into a global service layer.
- Put shared queries in `db/queries/`. Reason: repeated SQL should have one typed implementation and one test surface.
- Put migration files in `db/migrations/`. Reason: database history belongs beside the schema it changes.
- Put E2E tests in `tests/e2e/` and unit tests in `tests/unit/`. Reason: setup, runtime, and failure modes are different enough to keep separate.

## Naming Conventions

- Use kebab-case for route segment folders, for example `team-settings`. Reason: URLs should be lowercase and readable.
- Use PascalCase for React component files that export a component, for example `ProjectSwitcher.tsx`. Reason: component files should match JSX names in stack traces and editor search.
- Use camelCase for functions and variables. Reason: this matches TypeScript and JavaScript conventions.
- Use snake_case for database table and column names. Reason: SQLite, SQL migrations, and query logs are clearer with stable lowercase identifiers.
- Use singular names for domain objects in TypeScript, for example `Project`, and plural names for tables, for example `projects`. Reason: code handles one object at a time while SQL stores collections.
- Use `*.server.ts` for modules that may import `db`, secrets, `fs`, or `server-only`. Reason: server-only boundaries must be obvious during review.
- Use `*.client.tsx` only when a component must be imported from another Client Component. Reason: most components should remain server-renderable until proven otherwise.
- Prefix server actions with a verb, for example `createProjectAction`. Reason: action names should reveal side effects.
- Name migration files with sortable timestamps and a short action, for example `202605160945_create_projects.sql`. Reason: review and rollback discussions need chronological context.

## Environment Rules

- Validate environment variables in `lib/env.ts` with a schema. Reason: missing secrets should fail at boot, not halfway through checkout or login.
- Never read `process.env` directly outside `lib/env.ts`. Reason: scattered environment reads make tests and deployments inconsistent.
- Keep `.env.example` updated with every required variable and safe placeholder values. Reason: a new contributor should be able to boot the app without guessing.
- Treat database URLs, auth secrets, webhook secrets, and payment keys as server-only. Reason: leaking any of them compromises users or money movement.
- Never commit `.env`, local databases, production dumps, or customer exports. Reason: the repository must be safe to clone and share.

## SQL And Migration Conventions

- Change the database through migrations only. Reason: schema drift breaks production deploys and makes bug reports unreproducible.
- Every schema change must update `db/schema.ts` and add a migration in `db/migrations/`. Reason: TypeScript types and real database structure must move together.
- Prefer additive migrations: create a nullable column, backfill, then enforce `NOT NULL` later. Reason: additive steps are safer for production data and easier to review.
- Never rewrite, rename, or delete a migration that has been merged. Reason: merged migrations may already have run on another machine or in production.
- Include indexes with the migration that introduces the query pattern. Reason: performance fixes should ship with the code that needs them.
- Use foreign keys for ownership relationships such as `projects.owner_id -> users.id`. Reason: app-level checks are not enough to protect relational integrity.
- Use `created_at` and `updated_at` timestamps on mutable business tables. Reason: support, billing, and audit work need temporal context.
- Use soft deletes only when the business needs recovery or audit history. Reason: soft deletes increase query complexity and can hide bugs.
- For destructive data changes, write a reversible plan in the PR body. Reason: reviewers need to understand data loss, backfills, and rollback options.
- Wrap multi-row writes in transactions. Reason: SaaS workflows such as signup, project creation, and billing state changes must not partially succeed.
- Do not use `SELECT *` in shared queries. Reason: explicit columns keep payloads small and prevent accidental data exposure.
- Use `WHERE user_id = ?` or an equivalent ownership predicate on user-scoped queries. Reason: multi-tenant data leaks are the highest-risk class of SaaS bug.
- Treat raw SQL as server-only. Reason: SQL strings can expose schema details and invite injection if they leak into client code.

## Database Access Pattern

- Import the database client only from `db/client.ts`. Reason: one entry point makes runtime selection between `better-sqlite3` and Turso auditable.
- Keep query functions narrow and named after the business operation, for example `listProjectsForUser(userId)`. Reason: broad generic query helpers grow unclear permission behavior.
- Validate external input before it reaches query functions. Reason: query code should assume typed domain values, not raw form payloads.
- Return plain serializable objects from query functions. Reason: Server Components, route handlers, and tests can all consume JSON-safe data.
- Keep authorization close to data access for user-scoped reads and writes. Reason: route-level checks are easy to forget when queries are reused.
- Use transactions for operations that create or modify more than one table. Reason: billing plans, invites, and project setup need all-or-nothing behavior.

## App Router Patterns

- Use route groups for audience boundaries, for example `(marketing)` and `(app)`. Reason: marketing pages and authenticated app pages need different layouts and data assumptions.
- Put auth checks in the authenticated route group layout. Reason: every nested page should inherit the same protection.
- Use `loading.tsx`, `error.tsx`, and `not-found.tsx` where a route performs meaningful data work. Reason: users need stable states for slow reads, failures, and missing records.
- Use `generateMetadata` for pages with public SEO value. Reason: marketing and docs pages should not rely on generic metadata.
- Keep route handlers thin. Reason: request parsing belongs in route handlers, while business logic belongs in `lib/` or `db/queries/`.
- Use Server Actions for form mutations that are part of rendered app flows. Reason: actions reduce API boilerplate while preserving progressive form behavior.
- Use route handlers for webhooks and third-party callbacks. Reason: those integrations need raw request handling, signatures, and status codes.

## Component Patterns

- Build screens from Server Components first. Reason: initial data can be fetched securely without extra client requests.
- Move only the interactive leaf into a Client Component. Reason: smaller client islands load faster and reduce hydration errors.
- Pass serializable props across server-to-client boundaries. Reason: functions, database clients, Dates, and class instances do not cross the boundary safely.
- Keep `components/ui/` primitive and business-agnostic. Reason: buttons, inputs, dialogs, and menus should not know about projects, billing, or users.
- Keep domain components close to their route until reused twice. Reason: premature shared components make product changes slower.
- Use forms with server actions for create, update, and delete flows. Reason: forms preserve accessibility and work naturally with pending/error states.
- Show empty, loading, error, and permission-denied states for every data-heavy screen. Reason: SaaS users see incomplete states often during onboarding and team setup.
- Do not hide destructive actions behind ambiguous copy. Reason: billing, account, and project deletion flows need clear user intent.
- Avoid large client-side state managers by default. Reason: most SaaS state is server-owned and should be refreshed after mutations.

## Validation And Forms

- Use one schema per external input shape in `lib/validation/`. Reason: forms, API routes, and tests should share the same constraints.
- Validate on the server even if the client already validates. Reason: client checks are usability hints, not security boundaries.
- Normalize strings before saving, including trim and case normalization where appropriate. Reason: duplicate teams, emails, and slugs are often whitespace or case bugs.
- Return field-level errors from server actions. Reason: users need precise feedback without losing form context.
- Use optimistic UI only after the server action has a clear rollback path. Reason: SaaS workflows involving money or permissions should not show false success.

## Auth, Accounts, And Permissions

- Model users, accounts, sessions, memberships, and invites explicitly. Reason: SaaS permissions change over time and should not be inferred from email alone.
- Check authentication before reading user-scoped data. Reason: unauthenticated requests should fail before they can reveal existence of records.
- Check authorization inside mutations and shared query helpers. Reason: UI-level gating does not protect direct requests or reused actions.
- Use role constants, not string literals scattered across components. Reason: permission changes should be made in one place.
- Log security-relevant events such as invite creation, role change, billing change, and account deletion. Reason: audits and support rely on durable event context.
- Do not store access tokens in Client Components or browser local storage unless the auth provider explicitly requires it. Reason: XSS turns client storage into account takeover.

## Billing And Webhooks

- Treat billing provider state as the source of truth for payment status. Reason: local state can become stale when payments fail, renew, or are disputed.
- Verify webhook signatures before parsing business data. Reason: unsigned webhooks are forgeable.
- Make webhook handlers idempotent. Reason: providers retry events and may deliver them out of order.
- Store provider customer and subscription IDs in dedicated columns. Reason: support and reconciliation need stable references.
- Do not unlock paid features in the browser. Reason: entitlements must be checked on the server where users cannot tamper with them.

## Testing Rules

- Add unit tests for validation, permission checks, billing entitlement logic, and database query helpers. Reason: these bugs are costly and easy to test without a browser.
- Add E2E tests for signup/login, create project, invite member, change role, and billing gate flows. Reason: those are the paths that prove the SaaS works as a product.
- Use a disposable SQLite database for tests. Reason: tests must not depend on developer local state.
- Reset database state between tests. Reason: test order should never affect results.
- Test migrations from an empty database and from the previous schema when possible. Reason: production deploys run migrations against existing data.
- Do not skip failing tests to make progress. Reason: a skipped regression is worse than an honest failing PR.

## Security Rules

- Use parameterized queries or Drizzle query builders only. Reason: raw string interpolation in SQL can create injection vulnerabilities.
- Keep all secrets and database clients out of Client Components. Reason: client bundles are visible to users.
- Rate limit public mutations such as login, signup, invite, password reset, and webhook-like endpoints. Reason: public endpoints attract abuse.
- Validate file uploads by content type, size, and storage path before accepting them. Reason: file handling bugs frequently become data leaks or denial-of-service issues.
- Redact secrets, tokens, emails, and payment identifiers in logs. Reason: logs are widely accessible during debugging and incident response.
- Prefer deny-by-default permission checks. Reason: new roles and routes should not accidentally inherit access.

## Pull Request Workflow

- Start by reading nearby files and matching existing patterns. Reason: consistency matters more than personal preference.
- Keep each PR focused on one product change. Reason: small PRs are easier to review and safer to revert.
- Include database migration notes in the PR body when schema changes. Reason: reviewers need deploy and rollback context.
- Run `pnpm verify` before asking for review. Reason: the reviewer should spend time on product and correctness, not avoidable breakage.
- Include screenshots or short screen recordings for visible UI changes. Reason: App Router and Tailwind changes can look correct in code but fail in layout.
- Include test evidence in the PR body. Reason: future maintainers should know what was verified and where risk remains.

## What We Do Not Do And Why

- Do not add Pages Router files under `pages/`. Reason: mixing routers creates duplicate conventions and confusing data-loading behavior.
- Do not create API routes for mutations that are only used by local forms. Reason: Server Actions are simpler and keep validation near the UI flow.
- Do not import `db/` from Client Components. Reason: database clients and secrets must never enter browser bundles.
- Do not use raw SQL string interpolation. Reason: it risks injection and makes query review harder.
- Do not change production data manually to "fix" a migration. Reason: manual fixes are invisible to other environments and future deploys.
- Do not add global state libraries for server-owned data. Reason: server revalidation and focused client islands solve most SaaS state needs.
- Do not add generic repository or service layers unless they remove real duplication. Reason: thin abstractions often hide permissions and make queries harder to audit.
- Do not hide errors with broad `catch` blocks. Reason: SaaS support needs real failure causes, and users need actionable messages.
- Do not leave TODO comments as a substitute for implementation. Reason: this project optimizes for shippable product increments.
- Do not add paid dependencies without a clear reason in the PR. Reason: dependency cost and licensing affect the business, not only the code.

## Default Decisions When Requirements Are Missing

Claude should not stop for clarifying questions when the safe default is obvious. Use these defaults and note them in the summary.

- Use `pnpm` for scripts and lockfiles. Reason: deterministic installs reduce CI and onboarding drift.
- Use Drizzle migrations in `db/migrations/`. Reason: schema history must be reviewable.
- Use `better-sqlite3` for local development. Reason: it is the fastest zero-service SQLite setup.
- Use Turso/libSQL only behind `db/client.ts`. Reason: hosted database choice should not leak through the app.
- Use server actions for authenticated form mutations. Reason: they fit App Router and reduce duplicated endpoint code.
- Use route handlers for webhooks and public machine-to-machine callbacks. Reason: those require HTTP-level control.
- Use role names `owner`, `admin`, `member`, and `viewer`. Reason: these cover common SaaS collaboration needs without custom policy design.
- Use `projects` as the first tenant-scoped resource in examples. Reason: it is neutral and easy to adapt to most SaaS products.
- Use conservative UI over clever UI. Reason: SaaS users need clarity, speed, and trust more than novelty.

## Done Criteria For Claude

A change is done only when all relevant items are true:

- The app builds or the typecheck passes. Reason: broken types usually mean broken routes or data contracts.
- New or changed database schema has a migration. Reason: schema changes must be reproducible.
- User-scoped reads and writes include authorization checks. Reason: tenant isolation is mandatory.
- Mutations validate input on the server. Reason: client validation is bypassable.
- Tests cover changed validation, permission, query, or billing behavior. Reason: these are the highest-risk areas.
- UI changes include loading, empty, error, and denied states where applicable. Reason: real SaaS users hit all four states.
- The summary lists commands run and any commands that could not run. Reason: reviewers need honest verification status.
