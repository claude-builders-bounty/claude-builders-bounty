# CLAUDE.md

This file is the working agreement for Claude Code in this repository. The project is a production-minded SaaS application built with Next.js 15 App Router, TypeScript, React Server Components, and SQLite through either `better-sqlite3` for local/server deployments or Turso/libSQL for hosted edge-friendly deployments.

Use this as the first source of truth before reading implementation files. If code and this guide disagree, follow the code and update this guide in the same PR.

## Stack And Versions

- Runtime: Node.js 22 LTS or newer.
  Why: Next.js 15 and modern SQLite adapters assume current Web APIs, stable ESM behavior, and fast local tooling.
- Framework: Next.js 15 App Router with React Server Components by default.
  Why: server-first rendering keeps auth, billing, and tenant data close to the database and avoids shipping private logic to the browser.
- Language: TypeScript with `strict` enabled.
  Why: SaaS code has many cross-boundary shapes, and unchecked `any` values become billing, auth, and data-leak bugs.
- Database: SQLite via `better-sqlite3` for single-region Node deployments, or Turso/libSQL for replicated hosted deployments.
  Why: SQLite is reliable for early SaaS products when writes are simple, migrations are explicit, and serverless connection patterns are controlled.
- Styling: Tailwind CSS plus small composable components.
  Why: product UI needs consistency and speed without building a private design system too early.
- Validation: Zod or Valibot at all external boundaries.
  Why: route params, form payloads, webhook bodies, and environment variables are runtime inputs, not TypeScript values.
- Auth: Auth.js, Lucia-style sessions, or a small signed-cookie session module.
  Why: auth must be boring and auditable; avoid custom token flows unless the repo already has them.
- Payments: Stripe in server-only modules and webhook handlers.
  Why: price IDs, customer IDs, and subscription states are privileged data.

## Default Commands

Run commands from the repository root unless a package-specific README says otherwise.

```bash
npm install
npm run dev
npm run build
npm run lint
npm run typecheck
npm run test
npm run db:migrate
npm run db:studio
```

If the project uses `pnpm`, `bun`, or `yarn`, keep the existing package manager and translate commands without changing lockfiles.

Rule: do not add a new package manager.
Why: mixed lockfiles make deploys non-reproducible and waste review time.

Rule: run `lint`, `typecheck`, and the narrowest relevant test before finishing.
Why: SaaS changes often pass visually but fail because a server action, migration, or route handler has a type-only break.

## Environment Variables

Keep all required variables documented in `.env.example` and validated at startup.

Required baseline:

```bash
DATABASE_URL="file:./data/app.db"
AUTH_SECRET="replace-with-32-byte-secret"
APP_URL="http://localhost:3000"
STRIPE_SECRET_KEY=""
STRIPE_WEBHOOK_SECRET=""
```

Rule: server-only secrets live in modules imported only from Server Components, route handlers, server actions, or background jobs.
Why: a stray import from a Client Component can expose secrets in a browser bundle or fail the build.

Rule: read environment variables through one typed config module such as `src/lib/env.ts`.
Why: scattered `process.env.X` calls make defaults, test overrides, and deployment checks inconsistent.

Rule: fail fast when a required variable is missing.
Why: a SaaS app that boots with partial config usually fails later in signup, checkout, or webhook flows where recovery is harder.

## Folder Structure

Use this structure for new greenfield work:

```text
.
+-- app/
|   +-- (auth)/
|   +-- (dashboard)/
|   +-- api/
|   +-- layout.tsx
|   +-- page.tsx
+-- components/
|   +-- ui/
|   +-- product/
+-- db/
|   +-- migrations/
|   +-- schema.sql
|   +-- seed.ts
+-- src/
|   +-- actions/
|   +-- auth/
|   +-- lib/
|   +-- repositories/
|   +-- services/
|   +-- validators/
+-- tests/
|   +-- unit/
|   +-- integration/
|   +-- e2e/
+-- public/
+-- .env.example
+-- package.json
```

Rule: `app/` owns routing, layouts, metadata, loading states, and route handlers.
Why: route shape is a framework concern; business logic hidden inside route files is hard to reuse and test.

Rule: `components/ui/` contains reusable primitives such as buttons, inputs, dialogs, tables, and menus.
Why: primitives should not know about tenants, projects, invoices, or users.

Rule: `components/product/` contains domain components such as subscription cards, workspace switchers, or usage charts.
Why: domain UI changes more often than primitives and should be allowed to import product types.

Rule: `src/repositories/` is the only layer that writes SQL directly.
Why: keeping SQL at the repository boundary prevents ad hoc queries from bypassing tenant scoping and audit fields.

Rule: `src/services/` coordinates workflows across repositories, auth, billing, and email.
Why: server actions and route handlers should stay thin enough to inspect for auth and validation mistakes.

Rule: `src/actions/` contains server actions that validate input, authorize the user, call services, and revalidate paths.
Why: this keeps form workflows predictable and makes it clear which functions are callable from the client.

Rule: `src/validators/` contains schemas for forms, route params, webhook payloads, and API responses.
Why: validators are shared boundary contracts; hiding them inside components makes them difficult to reuse.

## Naming Conventions

Rule: files that export React components use `PascalCase.tsx`; route files keep the App Router names `page.tsx`, `layout.tsx`, `loading.tsx`, and `route.ts`.
Why: component names stay searchable while framework files remain conventional.

Rule: server-only modules use explicit names such as `stripe.server.ts`, `session.server.ts`, or `db.server.ts`.
Why: the suffix warns reviewers and Claude not to import them into Client Components.

Rule: repository functions use verb-object names, for example `createWorkspace`, `listProjectsForUser`, `updateSubscriptionStatus`.
Why: explicit names make authorization expectations visible at call sites.

Rule: database tables use plural snake_case names, and columns use snake_case.
Why: SQL stays idiomatic while TypeScript mapping can expose camelCase where helpful.

Rule: IDs are named for their domain, for example `workspaceId`, `userId`, and `stripeCustomerId`.
Why: generic `id` values are easy to mix across tenant boundaries.

## SQLite And Migration Rules

SQLite is durable, but it rewards simple, explicit schema changes.

Rule: every schema change gets a numbered migration in `db/migrations/`.
Why: production data must move forward in the same order on every machine and deploy target.

Rule: migration filenames use `NNNN_short_description.sql`, for example `0004_add_workspace_members.sql`.
Why: stable ordering prevents drift and makes code review obvious.

Rule: migrations are forward-only unless the project already has a reversible migration tool.
Why: SQLite rollback support is limited for several DDL operations; backup and forward repair are safer than pretending every change is reversible.

Rule: enable foreign keys on every connection.
Why: SQLite supports foreign keys only when `PRAGMA foreign_keys = ON`; without it, tests can pass while production accumulates orphaned records.

Rule: use WAL mode for long-running Node deployments.
Why: `PRAGMA journal_mode = WAL` improves read concurrency for dashboard-heavy SaaS workloads.

Rule: store timestamps as ISO 8601 UTC text or integer epoch milliseconds, and pick one convention per project.
Why: mixed timestamp formats make billing intervals, trial windows, and audit logs unreliable.

Rule: never use SQLite rowid as a public identifier.
Why: sequential IDs leak customer counts and make enumeration easier.

Rule: use stable public IDs such as UUIDv7, ULID, CUID2, or Stripe-style prefixed IDs.
Why: sortable, non-sequential public IDs are safer in URLs and logs.

Rule: every tenant-owned table includes `workspace_id` or the local tenant key.
Why: tenant isolation cannot rely on joins that developers remember to add later.

Rule: repository reads for tenant data must include tenant scope in the SQL `WHERE` clause.
Why: filtering in JavaScript after a broad query is a data exposure risk.

Rule: wrap multi-step writes in transactions.
Why: onboarding, checkout completion, and invitation acceptance should not leave half-created records.

Rule: do not run migrations from request handlers.
Why: concurrent requests can race, and slow migration locks make the app look randomly down.

Rule: seed scripts may create development users and plans, but never production secrets.
Why: seeds often get copied into examples and CI logs.

Preferred schema style:

```sql
CREATE TABLE workspaces (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE workspace_members (
  workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'member')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (workspace_id, user_id)
);

CREATE INDEX idx_workspace_members_user_id ON workspace_members(user_id);
```

Why this style: constraints live near the data, tenant membership is explicit, and query indexes match common access paths.

## Data Access Patterns

Rule: route handlers and server actions call services, not raw SQL.
Why: services centralize authorization, business rules, and side effects.

Rule: repositories return plain typed objects, not framework responses.
Why: repository code should be testable without Next.js.

Rule: use prepared statements for all SQL.
Why: prepared statements protect against injection and are faster for repeated dashboard queries.

Rule: prefer narrow column lists over `SELECT *`.
Why: adding a column such as `password_hash` should not accidentally expose it to an API response.

Rule: use explicit pagination for list endpoints.
Why: SaaS tables grow quietly until an unbounded dashboard query becomes an outage.

Rule: model write commands separately from read queries.
Why: reads optimize for display shape; writes optimize for invariants and auditability.

## Auth And Authorization

Rule: authentication answers "who are you"; authorization answers "can you do this in this workspace"; implement both.
Why: most SaaS vulnerabilities are authorization bugs after successful login.

Rule: check authorization inside services, even if the UI hides actions.
Why: server actions and API routes can be called directly.

Rule: never trust `workspaceId` or `role` from client input without checking membership in the database.
Why: hidden form fields and JSON bodies are attacker-controlled.

Rule: keep session lookup cheap and cached per request when possible.
Why: layout trees may call auth helpers multiple times during a single render.

Rule: log security-sensitive events without logging secrets.
Why: audit trails help support users, but tokens, cookies, and password reset links must not enter logs.

## Server Components, Client Components, And Actions

Rule: make components Server Components unless they need browser state, effects, event handlers, or DOM APIs.
Why: Server Components reduce bundle size and keep data fetching near the database.

Rule: Client Components should receive serializable props only.
Why: functions, database handles, class instances, and secrets cannot cross the server-client boundary safely.

Rule: colocate server actions near the workflow they serve, but move reusable business logic to services.
Why: colocated actions keep forms readable; services prevent workflow duplication.

Rule: validate all server action inputs before authorization and mutation.
Why: validation gives clear user errors and avoids passing malformed values into security checks.

Rule: call `revalidatePath` or `revalidateTag` after mutations that affect rendered data.
Why: App Router caches aggressively, and stale SaaS dashboards create support issues.

Rule: use optimistic UI only for reversible, low-risk changes.
Why: billing changes, role changes, and destructive actions should reflect server truth.

## Component Patterns

Rule: page components assemble data and layout; product components render domain UI; UI components render primitives.
Why: each layer then has one reason to change.

Rule: forms use a shared field error shape from validators.
Why: consistent error mapping avoids one-off form state bugs.

Rule: tables define empty, loading, and error states in the same component.
Why: SaaS dashboards spend real time in all three states.

Rule: destructive actions require a confirmation dialog or typed confirmation for high-risk resources.
Why: accidental workspace, project, or subscription changes are expensive to undo.

Rule: accessibility is part of done.
Why: keyboard navigation, labels, focus states, and ARIA relationships are cheaper to build in than retrofit.

Rule: avoid hiding business rules in component conditionals.
Why: UI checks are presentation; services must enforce the rule.

## Route Handlers And APIs

Rule: route handlers parse, validate, authorize, call a service, and return a typed response.
Why: this sequence is easy to audit and hard to misuse.

Rule: return stable error codes for client-handled failures.
Why: clients should not parse English messages to decide what to do.

Rule: webhook handlers verify signatures before parsing business meaning.
Why: unsigned webhook bodies are untrusted input.

Rule: make webhook processing idempotent.
Why: Stripe and similar providers retry deliveries, and duplicate events must not duplicate entitlements.

Rule: avoid long-running work in request-response paths.
Why: email, imports, and AI calls need retries and should move to jobs when they become slow or flaky.

## Testing Expectations

Rule: unit test validators, services, and repositories.
Why: these layers hold the business rules and are faster than browser tests.

Rule: integration test migrations against a real SQLite database.
Why: SQLite DDL and constraints are the source of truth, and mocks miss migration failures.

Rule: add one happy-path Playwright test for signup or first workspace creation once auth exists.
Why: SaaS onboarding is the path that proves routing, forms, DB writes, and sessions work together.

Rule: test webhook idempotency with repeated event IDs.
Why: billing bugs are expensive and often caused by retries.

Rule: each bug fix should include a regression test at the lowest useful layer.
Why: narrow tests are easier to understand and keep future refactors honest.

## Error Handling And Observability

Rule: user-facing errors should be specific enough to act on and vague enough not to leak internals.
Why: "You do not have access to this workspace" is useful; raw SQL errors are not.

Rule: log structured context for server failures, including user ID and workspace ID when available.
Why: production support needs correlation without exposing request bodies or secrets.

Rule: handle unique constraint errors deliberately.
Why: duplicate slugs, emails, and invitations are normal user behavior, not unknown server failures.

Rule: add health checks for database reachability in deployment environments.
Why: a SaaS app can boot while the database path, volume, or Turso token is wrong.

## Security Rules

Rule: never put secrets in Client Components, `public` env vars, test snapshots, or seed data.
Why: these surfaces are easy to publish.

Rule: use CSRF protection or same-site cookie defenses for cookie-authenticated mutations.
Why: server actions and POST routes still need request-origin assumptions to be explicit.

Rule: normalize and validate redirect URLs.
Why: open redirects create account takeover and phishing paths.

Rule: rate-limit login, signup, password reset, invite acceptance, and AI-heavy endpoints.
Why: these endpoints are abuse targets even in small SaaS apps.

Rule: keep admin-only routes behind service-level role checks.
Why: route groups are organization, not security.

## Performance Guidelines

Rule: prefer server-side filtering and pagination over client-side filtering of large lists.
Why: dashboards should stay fast as customers grow.

Rule: add indexes when adding a query pattern that filters or sorts by a column.
Why: SQLite is fast when indexes match access patterns and slow when every tenant scan is full-table.

Rule: avoid fetching the same current user, workspace, or subscription repeatedly in one request.
Why: duplicated auth and billing queries add latency to every page.

Rule: keep Client Component islands small.
Why: SaaS users spend hours in the app, and large bundles make every workflow feel heavier.

## What We Do Not Do

Do not create a generic `utils.ts` dumping ground.
Why: helpers without ownership become unreviewable and often mix client, server, and database concerns.

Do not import database modules from Client Components.
Why: it breaks the server-client boundary and can leak implementation details into the browser bundle.

Do not use raw SQL outside repositories.
Why: tenant scoping, prepared statements, and transactions need one enforceable boundary.

Do not put business decisions only in React conditional rendering.
Why: attackers can call server endpoints without using the UI.

Do not introduce a global state library until there is a concrete cross-route client state problem.
Why: most SaaS state belongs in the database, URL, or Server Component tree.

Do not add background jobs, queues, or caches before the workflow proves it needs them.
Why: early SaaS apps benefit more from simple reliable database-backed flows.

Do not make migrations depend on application services.
Why: migrations must run in minimal deploy environments before the app is healthy.

Do not silently swallow errors in server actions.
Why: users need actionable feedback, and operators need logs.

Do not store money values as floating point numbers.
Why: billing math needs integer cents or provider-owned price IDs.

Do not trust AI-generated code that touches auth, billing, migrations, or tenant isolation without focused review.
Why: these areas carry the highest customer and revenue risk.

## How Claude Should Work In This Repo

1. Read this file and any local README before editing.
2. Identify whether the change touches routing, UI, database, auth, billing, or deployment.
3. Make the smallest cohesive change that satisfies the request and preserves the architecture above.
4. Add or update tests for changed business rules, migrations, validators, and user workflows.
5. Run the narrowest useful checks first, then broader checks when shared behavior changed.
6. Summarize changed files, validation commands, and any follow-up risks.

Rule: when unsure about a schema or security decision, choose the boring explicit path and leave a short note in the PR.
Why: SaaS maintainers value predictable behavior over clever abstractions.
